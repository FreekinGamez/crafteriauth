import os
import datetime
import logging
import jwt
from . import db
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger('gentoken')

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Get secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')

def generate_token(user_id, service=None):
    """Generate a JWT token for the user
    
    Args:
        user_id (int): User ID for which to generate token
        service (str, optional): Service domain for which token is issued
        
    Returns:
        str: JWT token
    """
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    
    payload = {
        'sub': str(user_id),  # Convert to string here
        'iat': datetime.datetime.utcnow(),
        'exp': expiration,
    }
    
    if service:
        payload['aud'] = service
    
    # Create JWT token using PyJWT
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    # If token is bytes, convert to string
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    # Store token in database
    store_token(user_id, token, expiration, service)
    
    logger.info(f"Token generated for user {user_id}" + (f" for service {service}" if service else ""))
    return token

def store_token(user_id, token_value, expires_at, issued_for=None):
    """Store token in the database"""
    query = """
    INSERT INTO tokens (user_id, token_value, expires_at, issued_for)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """
    try:
        row = db.execute_query(
            query,
            (user_id, token_value, expires_at, issued_for),
            fetchone=True,
            commit=True
        )
        
        if row:
            return row[0]  # Return the new token ID
    except Exception as e:
        logger.error(f"Failed to store token: {str(e)}")
    
    return None
