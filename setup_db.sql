
-- Connect to postgres database first to create our new database
\c postgres;

-- Create the auth_db database
CREATE DATABASE auth_db;

-- Create the auth user with password 'AtMDs.23.95h'
CREATE USER auth WITH PASSWORD 'AtMDs.23.95h';

-- Grant all privileges on auth_db to the auth user
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth;

-- Connect to the auth_db to create tables
\c auth_db;

-- Make sure the auth user can create tables
ALTER SCHEMA public OWNER TO auth;

-- From this point, you don't need to run these commands manually
-- since SQLAlchemy will create the tables for you when you run app.py
-- However, if you want to create them manually, here's the SQL:

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Tokens table
CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    token_value VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    issued_for VARCHAR(255)
);

-- RegisteredService table
CREATE TABLE registered_services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    client_id VARCHAR(36) UNIQUE NOT NULL,
    client_secret VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Grant all privileges on all tables to auth user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auth;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO auth;
