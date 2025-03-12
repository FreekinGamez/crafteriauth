from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Import modules
from . import db
from .login import login_user, get_user_by_id
from .signup import signup_user
from .gentoken import generate_token
from .verifytoken import verify_token

# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__, 
           template_folder=str(project_root / 'templates'),
           static_folder=str(project_root / 'static'))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Home route redirects to login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Get the service that is requesting authentication
        service = request.args.get('service', None)
        session['redirect_service'] = service
        return render_template('login.html', service=service)
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        redirect_service = session.get('redirect_service')
        
        # Use login module to authenticate
        result = login_user(email, password, redirect_service)
        
        if not result['success']:
            return render_template('login.html', error=result['error'])
        
        # If there's a service to redirect to, do it with the token
        if 'redirect_service' in result and 'token' in result:
            redirect_url = f"https://{result['redirect_service']}/auth/callback?token={result['token']}"
            return redirect(redirect_url)
        
        # Otherwise just log in normally
        session['user_id'] = result['user']['id']
        return redirect(url_for('dashboard'))

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        service = request.args.get('service', None)
        return render_template('signup.html', service=service)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        redirect_service = session.get('redirect_service')
        
        # Use signup module to register user
        result = signup_user(username, email, password, redirect_service)
        
        if not result['success']:
            return render_template('signup.html', error=result['error'])
        
        # Log the user in
        session['user_id'] = result['user']['id']
        
        # Redirect if needed
        if 'redirect_service' in result and 'token' in result:
            redirect_url = f"https://{result['redirect_service']}/auth/callback?token={result['token']}"
            return redirect(redirect_url)
        
        return redirect(url_for('dashboard'))

# Dashboard (protected route)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    
    if not user:
        # If user doesn't exist anymore, log out
        session.pop('user_id', None)
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', user=user)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('redirect_service', None)
    return redirect(url_for('login'))

# Token verification endpoint for third-party services
@app.route('/api/verify-token', methods=['POST'])
def verify_token_endpoint():
    token = request.json.get('token', '')
    
    # Use verifytoken module to verify the token
    result = verify_token(token)
    
    if not result['valid']:
        return jsonify({'valid': False, 'error': result['error']}), 401
    
    return jsonify({'valid': True, 'user': result['user']})

# Service registration API (for admin use)
@app.route('/api/register-service', methods=['POST'])
def register_service():
    # This endpoint should be protected and only accessible by admins
    # For now, this is just a demo
    
    name = request.json.get('name')
    domain = request.json.get('domain')
    
    if not name or not domain:
        return jsonify({'error': 'Name and domain are required'}), 400
        
    # Check if service already exists
    existing_service = get_service_by_domain(domain)
    if existing_service:
        return jsonify({'error': 'Service domain already registered'}), 400
        
    # Create new service
    service_id = create_service(name, domain)
    
    if not service_id:
        return jsonify({'error': 'Failed to register service'}), 500
        
    new_service = get_service_by_domain(domain)
    
    return jsonify({
        'service': {
            'name': new_service['name'],
            'domain': new_service['domain'],
            'client_id': new_service['client_id'],
            'client_secret': new_service['client_secret']
        }
    }), 201

def get_service_by_domain(domain):
    """Get a service by domain"""
    query = """
    SELECT id, name, domain, client_id, client_secret, created_at, is_active
    FROM registered_services
    WHERE domain = %s
    """
    row = db.execute_query(query, (domain,), fetchone=True)
    
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'domain': row[2],
            'client_id': row[3],
            'client_secret': row[4],
            'created_at': row[5],
            'is_active': row[6]
        }
    return None

def create_service(name, domain):
    """Create a new service"""
    client_id = str(uuid.uuid4())
    client_secret = os.urandom(32).hex()
    
    query = """
    INSERT INTO registered_services (name, domain, client_id, client_secret)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """
    row = db.execute_query(query, (name, domain, client_id, client_secret), fetchone=True, commit=True)
    
    if row:
        return row[0]  # Return the new service ID
    return None

# Initialize the application
def init_app():
    """Initialize the application"""
    if not db.init_db():
        logger.error("Failed to initialize database. Exiting.")
        return False
    
    logger.info("Application initialized successfully.")
    return True

if __name__ == '__main__':
    if init_app():
        app.run(debug=False)
    else:
        print("Application failed to initialize. Check logs for details.")
