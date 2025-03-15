import os
import uuid
import datetime
import requests
import logging
from flask import Flask, request, render_template, redirect, url_for, jsonify, make_response
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_service')

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration
CRAFTERI_AUTH_URL = "http://localhost:5000"
TEST_SERVICE_URL = "http://localhost:5001"  # This service
API_KEY = "niggas123"  # API key for accessing Crafteri Auth API

# Database configuration (using the same database as the auth service)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'auth_db')
DB_USER = os.environ.get('DB_USER', 'auth')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'AtMDs.23.95h')

# Create Flask app
app = Flask(__name__, 
    template_folder=str(Path(__file__).parent / 'templates'),
    static_folder=str(Path(__file__).parent / 'static'))

app.secret_key = os.urandom(24)

# Database functions
def get_db_connection():
    """Get a connection to the database"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def init_db():
    """Initialize the database by creating tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Create testserviceusers table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS testserviceusers (
            id SERIAL PRIMARY KEY,
            crafteri_user_id INTEGER UNIQUE NOT NULL,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP NULL
        )
        """)
        
        # Create testservicetokens table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS testservicetokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES testserviceusers(id),
            token_value VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL
        )
        """)
        
        conn.commit()
        logger.info("Test service database tables initialized")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def verify_crafteri_token(token):
    """Verify the token with Crafteri Auth Service"""
    url = f"{CRAFTERI_AUTH_URL}/api/verify-token"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    payload = {"token": token}
    
    logger.info(f"Sending token verification request to: {url}")
    logger.info(f"Using API key: {API_KEY}")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Token verification failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None

def get_or_create_user(crafteri_user):
    """Get or create a user in the test service database"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Try to get existing user
        cur.execute("""
        SELECT id, crafteri_user_id, username, email, created_at, last_login 
        FROM testserviceusers 
        WHERE crafteri_user_id = %s
        """, (crafteri_user['id'],))
        
        user = cur.fetchone()
        
        if user:
            # User exists, update last login
            cur.execute("""
            UPDATE testserviceusers SET last_login = NOW() WHERE id = %s
            """, (user['id'],))
            conn.commit()
            return dict(user)
        else:
            # User doesn't exist, create new one
            cur.execute("""
            INSERT INTO testserviceusers (crafteri_user_id, username, email)
            VALUES (%s, %s, %s)
            RETURNING id, crafteri_user_id, username, email, created_at, last_login
            """, (
                crafteri_user['id'],
                crafteri_user['username'],
                crafteri_user['email']
            ))
            new_user = cur.fetchone()
            conn.commit()
            return dict(new_user)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error getting/creating user: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def create_session_token(user_id):
    """Create a session token for the user"""
    token_value = str(uuid.uuid4())
    expires_at = datetime.datetime.now() + datetime.timedelta(days=7)  # 7 days session
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
        INSERT INTO testservicetokens (user_id, token_value, expires_at)
        VALUES (%s, %s, %s)
        RETURNING id
        """, (user_id, token_value, expires_at))
        
        token_id = cur.fetchone()[0]
        conn.commit()
        
        return {
            'token': token_value,
            'expires_at': expires_at
        }
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating session token: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_user_by_session_token(token):
    """Get user by session token"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
        SELECT u.id, u.crafteri_user_id, u.username, u.email, u.created_at, u.last_login
        FROM testserviceusers u
        JOIN testservicetokens t ON u.id = t.user_id
        WHERE t.token_value = %s AND t.expires_at > NOW()
        """, (token,))
        
        user = cur.fetchone()
        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error getting user by session token: {e}")
        return None
    finally:
        cur.close()
        conn.close()

# Routes
@app.route('/')
def home():
    # Check if user is logged in via session cookie
    session_token = request.cookies.get('session_token')
    if session_token:
        user = get_user_by_session_token(session_token)
        if user:
            return render_template('dashboard.html', user=user)
    
    # Not logged in, show home page with login button
    return render_template('home.html')

@app.route('/login')
def login():
    # Redirect to Crafteri Auth with this service's URL for callback
    redirect_url = f"{CRAFTERI_AUTH_URL}/login?service={TEST_SERVICE_URL}/auth/callback"
    return redirect(redirect_url)

@app.route('/auth/callback')
def auth_callback():
    # Get token from query parameters
    token = request.args.get('token')
    if not token:
        return "Error: No token provided", 400
    
    # Verify token with Crafteri Auth
    result = verify_crafteri_token(token)
    if not result or not result.get('valid', False):
        return "Error: Invalid token", 401
    
    # Get user info from the verification result
    crafteri_user = result.get('user')
    
    # Get or create user in our database
    user = get_or_create_user(crafteri_user)
    if not user:
        return "Error: Failed to process user", 500
    
    # Create session token
    session = create_session_token(user['id'])
    if not session:
        return "Error: Failed to create session", 500
    
    # Create response with redirect to home
    response = make_response(redirect(url_for('home')))
    
    # Set session cookie
    response.set_cookie(
        'session_token',
        session['token'],
        expires=session['expires_at'],
        httponly=True
    )
    
    return response

@app.route('/logout')
def logout():
    # Create response and delete session cookie
    response = make_response(redirect(url_for('home')))
    response.delete_cookie('session_token')
    return response

@app.route('/profile')
def profile():
    # Check if user is logged in
    session_token = request.cookies.get('session_token')
    if not session_token:
        return redirect(url_for('home'))
    
    user = get_user_by_session_token(session_token)
    if not user:
        # Invalid session, clear it
        response = make_response(redirect(url_for('home')))
        response.delete_cookie('session_token')
        return response
    
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    # Initialize database
    init_db()
    # Run the app
    app.run(debug=True, port=5001)
