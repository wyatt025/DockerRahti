from functools import wraps
import os
from authlib.integrations.flask_client import OAuth
from flask import Flask, jsonify, redirect, session
import mysql.connector

app = Flask(__name__)
# Flask signs the login session with this key; kept in a Kubernetes Secret.
app.secret_key = os.getenv('FLASK_SECRET_KEY')
# Restrict browser access to the session cookie and require HTTPS in production.
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
)

oauth = OAuth(app)
# Register GitHub's OAuth endpoints so Flask can start login and fetch the profile.
github = oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'read:user'},
)


def login_required(handler):
    # Reject protected API requests until the OAuth callback has stored a user.
    @wraps(handler)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return jsonify(error='authentication_required'), 401
        return handler(*args, **kwargs)

    return wrapped


@app.get('/auth/login')
def login():
    # Start GitHub login using the exact callback URI registered with GitHub.
    redirect_uri = os.getenv('OAUTH_REDIRECT_URI')
    if not all((app.secret_key, github.client_id, github.client_secret, redirect_uri)):
        return 'OAuth is not configured. Set the GitHub OAuth Secret and callback URL.', 503
    return github.authorize_redirect(redirect_uri)


@app.get('/auth/callback')
def auth_callback():
    # Exchange GitHub's authorization response for a profile and save it in session.
    github.authorize_access_token()
    response = github.get('user')
    response.raise_for_status()
    profile = response.json()
    session['user'] = {
        'login': profile['login'],
        'name': profile.get('name'),
        'avatar_url': profile.get('avatar_url'),
    }
    return redirect('/')


@app.get('/api/me')
def current_user():
    # Let the static frontend decide whether to show login or visitor data.
    return jsonify(user=session.get('user'))


@app.post('/auth/logout')
def logout():
    # Remove the signed-in user from the browser session.
    session.clear()
    return '', 204

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'appuser')
# Local development fallback only; set DB_PASSWORD from a Secret in deployments.
DB_PASSWORD = os.getenv('DB_PASSWORD', 'changeme')
DB_NAME = os.getenv('DB_NAME', 'appdb')

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.get('/api')
@login_required
def index():
    # Only authenticated users reach the existing MySQL visit counter.
    conn = mysql.connector.connect(
       host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME,
    )
    cur = conn.cursor()
    
    # 1. WRITE OPERATION: Insert a new timestamp record into the visits table   
    cur.execute("INSERT INTO visits (visit_time) VALUES (NOW())")
    conn.commit() # Saves the write to the database
    
    # 2. READ OPERATION: Count entries and grab the database server time via SELECT NOW()
    cur.execute("SELECT COUNT(*), NOW() FROM visits")
    row = cur.fetchone()
    
    cur.close()
    conn.close()
    
    # Return the real database values as a JSON response
    return jsonify(
        message="Hello from MySQL via Flask on Rahti!",
        total_visits=row[0],
        database_server_time=str(row[1])
    )

if __name__ == '__main__':
 # Dev-only fallback
    app.run(host='0.0.0.0', port=8000, debug=True)
