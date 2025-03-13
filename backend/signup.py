import logging
import bcrypt
from . import db
from .api import get_user_by_email, get_user_by_id

# Configure logging
logger = logging.getLogger('signup')

def signup_user(username, email, password, redirect_service=None):
    """Register a new user"""
    # Check if user already exists
    existing_user_result = get_user_by_email(email)
    if existing_user_result['success']:
        logger.warning(f"Signup attempt with existing email: {email}")
        return {
            'success': False,
            'error': 'Email already exists'
        }
    
    # Create password hash using bcrypt
    # Convert password to bytes if it's not already
    password_bytes = password.encode('utf-8') if isinstance(password, str) else password
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Create new user
    new_user_id = create_user(username, email, password_hash)
    
    if not new_user_id:
        logger.error(f"Failed to create user with email: {email}")
        return {
            'success': False,
            'error': 'Failed to create account'
        }
    
    # Get the user data
    new_user_result = get_user_by_id(new_user_id)
    new_user = new_user_result['user']
    
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
