-- MySQL Setup Script for Evaluation System
-- Run this script as MySQL root user to create the database and user

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS evaluation 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Step 2: Create the database user
CREATE USER IF NOT EXISTS 'eval_user'@'localhost' IDENTIFIED BY 'eval_password';

-- Step 3: Grant all privileges on the evaluation database
GRANT ALL PRIVILEGES ON evaluation.* TO 'eval_user'@'localhost';

-- Step 4: Flush privileges to take effect
FLUSH PRIVILEGES;

-- Step 5: Verify the setup
SHOW DATABASES;
SELECT user FROM mysql.user WHERE user='eval_user';
SHOW GRANTS FOR 'eval_user'@'localhost';

-- If you need to change the password later:
-- ALTER USER 'eval_user'@'localhost' IDENTIFIED BY 'new_secure_password';
-- FLUSH PRIVILEGES;
