import os
import datetime
import logging
import jwt
from . import db
from pathlib import Path
from dotenv import load_dotenv
from .login import get_user_by_id

# Configure logging
logger = logging.getLogger('verifytoken')

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Get secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')

def verify_token(token):
    """Verify a JWT token
    
    Args:
        token (str): JWT token to verify
        
    Returns:
        dict: Result containing validation status and user info if valid
    """
    try:
        # Decode and verify token
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        
        # Check if token exists in database
        token_record = get_token(token)
        if not token_record:
            logger.warning(f"Token not found in database: {token[:20]}...")
            return {
                'valid': False,
                'error': 'Token not found'
            }
        
        # Check token expiration
        if datetime.datetime.utcnow() > token_record['expires_at']:
            logger.warning(f"Token expired: {token[:20]}...")
            return {
                'valid': False,
                'error': 'Token expired'
            }
        
        # Get user information
        user = get_user_by_id(payload['sub'])
        if not user:
            logger.warning(f"User not found for token: {token[:20]}...")
            return {
                'valid': False,
                'error': 'User not found'
            }
        
        # Return user information
        logger.info(f"Token verified for user: {user['email']}")
        return {
            'valid': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }
    except jwt.ExpiredSignatureError:
        logger.warning(f"Token expired (JWT validation): {token[:20]}...")
        return {'valid': False, 'error': 'Token expired'}
    except jwt.InvalidTokenError:
        logger.warning(f"Invalid token: {token[:20]}...")
        return {'valid': False, 'error': 'Invalid token'}
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return {'valid': False, 'error': 'Verification error'}

def get_token(token_value):
    """Get token by value"""
    query = """
    SELECT id, user_id, created_at, expires_at, issued_for
    FROM tokens
    WHERE token_value = %s
    """
    row = db.execute_query(query, (token_value,), fetchone=True)
    
    if row:
        return {
            'id': row[0],
            'user_id': row[1],
            'created_at': row[2],
            'expires_at': row[3],
            'issued_for': row[4]
        }
    return None
