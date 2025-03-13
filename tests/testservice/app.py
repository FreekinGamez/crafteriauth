from flask import Flask, redirect, render_template, request, url_for, session, flash, make_response
import requests
import os
import logging
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'test_service_secret_key'

# Configuration
CRAFTERI_AUTH_URL = "http://localhost:5000"  # Your CrafteriAuth server URL
API_KEY = "cbe09fb9562e365518cd93c1223a92c9"  # Your API key from .env
SERVICE_URL = "http://localhost:5001"  # This test service URL

@app.route('/')
def index():
    # Check if user is logged in (has token cookie)
    token = request.cookies.get('auth_token')
    if token:
        logger.info(f"Found token cookie: {token[:10]}...")
        # Redirect to home page if already logged in
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login')
def login():
    # Generate the callback URL
    callback_url = f"{SERVICE_URL}/auth/callback"
    logger.info(f"Redirecting to CrafteriAuth with callback: {callback_url}")
    
    # Redirect to CrafteriAuth
    auth_url = f"{CRAFTERI_AUTH_URL}/login?service={callback_url}"
    return redirect(auth_url)

@app.route('/auth/callback')
def auth_callback():
    # Get token from query parameters
    token = request.args.get('token')
    
    logger.info(f"Callback received. Token present: {bool(token)}")
    if token:
        logger.info(f"Token prefix: {token[:10]}...")
    
    if not token:
        flash('Authentication failed: No token received.')
        return redirect(url_for('index'))
    
    # Verify the token
    logger.info("Verifying token with CrafteriAuth...")
    result = verify_token(token)
    logger.info(f"Token verification result: {result}")
    
    if not result.get('valid', False):
        flash(f'Invalid authentication token. Reason: {result.get("error", "Unknown")}')
        return redirect(url_for('index'))
    
    # Create response with authenticated redirect
    response = make_response(redirect(url_for('home')))
    
    # Set token cookie (secure in production)
    logger.info("Setting auth_token cookie")
    response.set_cookie('auth_token', token, httponly=True, max_age=86400)
    
    return response

@app.route('/home')
def home():
    # Get token from cookie
    token = request.cookies.get('auth_token')
    
    if not token:
        flash('Please log in first.')
        return redirect(url_for('index'))
    
    logger.info(f"Home page accessed with token: {token[:10]}...")
    
    # Get user information using the token
    user_info = get_user_info(token)
    
    if not user_info:
        logger.error("Failed to get user info")
        flash('Could not retrieve user information. Please log in again.')
        # Clear invalid token and redirect to login
        response = make_response(redirect(url_for('index')))
        response.delete_cookie('auth_token')
        return response
    
    return render_template('home.html', user=user_info)

@app.route('/logout')
def logout():
    # Clear the token cookie
    response = make_response(redirect(url_for('index')))
    response.delete_cookie('auth_token')
    return response

def verify_token(token):
    """Verify token with CrafteriAuth"""
    try:
        logger.info(f"Sending token verification request to {CRAFTERI_AUTH_URL}/api/verify-token")
        response = requests.post(
            f"{CRAFTERI_AUTH_URL}/api/verify-token",
            json={"token": token},
            headers={
                "Content-Type": "application/json",
                "API-Key": API_KEY  # Added API Key
            }
        )
        
        logger.info(f"Verification response status: {response.status_code}")
        logger.info(f"Verification response content: {response.text[:100]}...")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Token verification failed: {response.text}")
            return {"valid": False, "error": f"API error: {response.status_code}"}
    except Exception as e:
        logger.exception(f"Error verifying token: {str(e)}")
        return {"valid": False, "error": str(e)}

def get_user_info(token):
    """Get user information from CrafteriAuth using token"""
    try:
        logger.info(f"Getting user info with token: {token[:10]}...")
        response = requests.post(
            f"{CRAFTERI_AUTH_URL}/api/getuserbytoken",
            json={"token": token},
            headers={
                "Content-Type": "application/json",
                "API-Key": API_KEY
            }
        )
        
        logger.info(f"User info response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('user')
        
        logger.error(f"Failed to get user info: {response.text}")
        return None
    except Exception as e:
        logger.exception(f"Error getting user info: {str(e)}")
        return None

if __name__ == '__main__':
    logger.info("Starting test service on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
