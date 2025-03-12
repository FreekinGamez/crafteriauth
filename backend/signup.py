from werkzeug.security import generate_password_hash
import logging
from . import db

# Configure logging
logger = logging.getLogger('signup')

def signup_user(username, email, password, redirect_service=None):
    """Register a new user
    
    Args:
        username (str): User's username
        email (str): User's email
        password (str): User's password
        redirect_service (str, optional): Service to redirect to after signup
        
    Returns:
        dict: Result containing success status, user data if successful, error if unsuccessful
    """
    # Check if user already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        logger.warning(f"Signup attempt with existing email: {email}")
        return {
            'success': False,
            'error': 'Email already exists'
        }
    
    # Create password hash
    password_hash = generate_password_hash(password)
    
    # Create new user
    new_user_id = create_user(username, email, password_hash)
    
    if not new_user_id:
        logger.error(f"Failed to create user with email: {email}")
        return {
            'success': False,
            'error': 'Failed to create account'
        }
    
    # Get the user data
    new_user = get_user_by_id(new_user_id)
    
    result = {
        'success': True,
        'user': {
            'id': new_user['id'],
            'username': new_user['username'],
            'email': new_user['email']
        }
    }
    
    # If redirect service specified, generate token
    if redirect_service:
        # Import here to avoid circular imports
        from .gentoken import generate_token
        token = generate_token(new_user_id, redirect_service)
        result['token'] = token
        result['redirect_service'] = redirect_service
    
    logger.info(f"New user created: {email}")
    return result

def get_user_by_email(email):
    """Get a user by email"""
    query = "SELECT id, username, email, created_at, last_login FROM users WHERE email = %s"
    row = db.execute_query(query, (email,), fetchone=True)
    
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[3],
            'last_login': row[4]
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

def create_user(username, email, password_hash):
    """Create a new user"""
    query = """
    INSERT INTO users (username, email, password_hash)
    VALUES (%s, %s, %s)
    RETURNING id
    """
    row = db.execute_query(query, (username, email, password_hash), fetchone=True, commit=True)
    
    if row:
        return row[0]  # Return the new user ID
    return None
