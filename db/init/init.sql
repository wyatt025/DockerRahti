CREATE DATABASE IF NOT EXISTS appdb;
-- Example password only; Rahti supplies the live app password through its Secret.
CREATE USER IF NOT EXISTS 'appuser'@'%' IDENTIFIED BY 'changeme';
GRANT ALL PRIVILEGES ON appdb.* TO 'appuser'@'%';
FLUSH PRIVILEGES;


USE appdb;
CREATE TABLE IF NOT EXISTS visits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visit_time DATETIME
);