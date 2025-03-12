import bcrypt  # Using bcrypt instead of Werkzeug
import logging
from . import db

# Configure logging
logger = logging.getLogger('login')

def login_user(email, password, redirect_service=None):
    """Log in a user with the given credentials
    
    Args:
        email (str): User's email
        password (str): User's password
        redirect_service (str, optional): Service to redirect to after login
        
    Returns:
        dict: Result containing success status, user data if successful, and error message if unsuccessful
    """
    # Check if user exists
    user = get_user_by_email(email)
    
    # Verify password with bcrypt
    if not user:
        logger.warning(f"Login attempt for non-existent email: {email}")
        return {
            'success': False,
            'error': 'Invalid email or password'
        }
        
    # Convert input password to bytes
    password_bytes = password.encode('utf-8') if isinstance(password, str) else password
    # Convert stored hash to bytes if it's not already
    stored_hash = user['password_hash'].encode('utf-8') if isinstance(user['password_hash'], str) else user['password_hash']
    
    # Check if password matches
    if not bcrypt.checkpw(password_bytes, stored_hash):
        logger.warning(f"Failed login attempt for email: {email}")
        return {
            'success': False,
            'error': 'Invalid email or password'
        }
    
    # Update last login time
    update_last_login(user['id'])
    
    result = {
        'success': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email']
        }
    }
    
    # If redirect service specified, generate token
    if redirect_service:
        # Import here to avoid circular imports
        from .gentoken import generate_token
        token = generate_token(user['id'], redirect_service)
        result['token'] = token
        result['redirect_service'] = redirect_service
        
    logger.info(f"User logged in: {user['email']}")
    return result

def get_user_by_email(email):
    """Get a user by email"""
    query = "SELECT id, username, email, password_hash, created_at, last_login FROM users WHERE email = %s"
    row = db.execute_query(query, (email,), fetchone=True)
    
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'password_hash': row[3],
            'created_at': row[4],
            'last_login': row[5]
        }
    return None

def get_user_by_id(user_id):
    """Get a user by ID"""
    query = "SELECT id, username, email, created_at, last_login FROM users WHERE id = %s"
    row = db.execute_query(query, (user_id,), fetchone=True)
    
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[3],
            'last_login': row[4]
        }
    return None

def update_last_login(user_id):
    """Update the user's last login timestamp"""
    query = "UPDATE users SET last_login = NOW() WHERE id = %s"
    db.execute_query(query, (user_id,), commit=True)