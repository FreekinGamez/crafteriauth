
-- Create tables for the test service
CREATE TABLE IF NOT EXISTS testserviceusers (
    id SERIAL PRIMARY KEY,
    crafteri_user_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS testservicetokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES testserviceusers(id),
    token_value VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_testserviceusers_crafteri_user_id ON testserviceusers(crafteri_user_id);
CREATE INDEX IF NOT EXISTS idx_testservicetokens_user_id ON testservicetokens(user_id);
CREATE INDEX IF NOT EXISTS idx_testservicetokens_token_value ON testservicetokens(token_value);
