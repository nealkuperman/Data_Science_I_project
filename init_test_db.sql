-- Create the test database
-- This runs BEFORE init.sql (files run alphabetically: 00_ before 01_)

CREATE DATABASE nba_db_test;

-- Grant permissions to our user
GRANT ALL PRIVILEGES ON DATABASE nba_db_test TO nba_user;
