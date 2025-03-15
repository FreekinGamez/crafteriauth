
-- First, ensure you're executing these commands as a database superuser (postgres)

-- Set ownership of the tables to auth user
ALTER TABLE testserviceusers OWNER TO auth;
ALTER TABLE testservicetokens OWNER TO auth;

-- Grant all privileges on the tables
GRANT ALL PRIVILEGES ON TABLE testserviceusers TO auth;
GRANT ALL PRIVILEGES ON TABLE testservicetokens TO auth;

-- Grant privileges on the sequences used by these tables
GRANT USAGE, SELECT, UPDATE ON SEQUENCE testserviceusers_id_seq TO auth;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE testservicetokens_id_seq TO auth;

-- If you're still having issues, you might need to alter the schema permissions
GRANT ALL PRIVILEGES ON SCHEMA public TO auth;

-- Additional permissions that might be needed
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auth;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auth;
