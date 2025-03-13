import logging
from . import db
from .verifytoken import verify_token as verify_jwt_token

# Configure logging
logger = logging.getLogger('api')

def get_user_by_token(token):
    """Get user information from a token"""
    # Use the existing verify_token function
    result = verify_jwt_token(token)
    
    if not result['valid']:
        logger.warning(f"Failed to get user by token: {result.get('error', 'Unknown error')}")
        return {
            'success': False,
            'error': result.get('error', 'Invalid token')
        }
    
    # Return user data
    return {
        'success': True,
        'user': result['user']
    }

def get_user_by_id(user_id):
    """Get user information by ID"""
    query = "SELECT id, username, email, created_at, last_login FROM users WHERE id = %s"
    row = db.execute_query(query, (user_id,), fetchone=True)
    
    if not row:
        logger.warning(f"User not found with ID: {user_id}")
        return {
            'success': False,
            'error': 'User not found'
        }
    
    return {
        'success': True,
        'user': {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[3],
            'last_login': row[4]
        }
    }

def get_user_by_email(email):
    """Get user information by email"""
    query = "SELECT id, username, email, created_at, last_login FROM users WHERE email = %s"
    row = db.execute_query(query, (email,), fetchone=True)
    
    if not row:
        logger.warning(f"User not found with email: {email}")
        return {
            'success': False,
            'error': 'User not found'
        }
    
    return {
        'success': True,
        'user': {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[3],
            'last_login': row[4]
        }
    }

def get_user_with_password_by_email(email):
    """Get a user by email, including password hash (for internal auth only)"""
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

def get_user_by_name(username):
    """Get user information by username"""
    query = "SELECT id, username, email, created_at, last_login FROM users WHERE username = %s"
    row = db.execute_query(query, (username,), fetchone=True)
    
    if not row:
        logger.warning(f"User not found with username: {username}")
        return {
            'success': False,
            'error': 'User not found'
        }
    
    return {
        'success': True,
        'user': {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'created_at': row[3],
            'last_login': row[4]
        }
    }

def update_last_login(user_id):
    """Update the user's last login timestamp"""
    query = "UPDATE users SET last_login = NOW() WHERE id = %s"
    db.execute_query(query, (user_id,), commit=True)
