from flask import Flask, jsonify
import os
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'appuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'changeme')
DB_NAME = os.getenv('DB_NAME', 'appdb')

@app.get('/api/health')
def health():
    return {'status': 'ok'}

@app.get('/api')
def index():
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
