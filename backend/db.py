import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db')

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Database configuration
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'auth_db')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# Initialize connection pool
connection_pool = None

def init_db():
    """Initialize the database connection pool"""
    global connection_pool
    
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        logger.info(f"Database pool initialized: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        
        # Create tables if they don't exist
        create_tables()
        
        return True
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return False

def get_connection():
    """Get a connection from the pool"""
    if connection_pool:
        return connection_pool.getconn()
    else:
        raise Exception("Database pool not initialized. Call init_db() first.")

def release_connection(conn):
    """Return a connection to the pool"""
    if connection_pool:
        connection_pool.putconn(conn)

def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """Execute a database query with optional parameters"""
    conn = None
    cursor = None
    result = None
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        
        if commit:
            conn.commit()
            
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_connection(conn)

def create_tables():
    """Create database tables if they don't exist"""
    # Users table
    execute_query("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        last_login TIMESTAMP NULL
    )
    """, commit=True)
    
    # Tokens table
    execute_query("""
    CREATE TABLE IF NOT EXISTS tokens (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        token_value VARCHAR(500) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        expires_at TIMESTAMP NOT NULL,
        issued_for VARCHAR(255) NULL
    )
    """, commit=True)
    
    # Registered services table
    execute_query("""
    CREATE TABLE IF NOT EXISTS registered_services (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        domain VARCHAR(255) UNIQUE NOT NULL,
        client_id VARCHAR(36) UNIQUE NOT NULL,
        client_secret VARCHAR(64) NULL,
        created_at TIMESTAMP DEFAULT NOW(),
        is_active BOOLEAN DEFAULT TRUE
    )
    """, commit=True)
    
    logger.info("Database tables created if they didn't exist")
