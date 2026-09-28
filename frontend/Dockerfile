# syntax=docker/dockerfile:1
FROM nginxinc/nginx-unprivileged:stable-alpine
# Copy Nginx config and static assets
COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/screenshots /usr/share/nginx/html/screenshots
COPY frontend/index.css /usr/share/nginx/html/index.css