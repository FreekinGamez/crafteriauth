from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv
from functools import wraps

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

# Helper function to extract domain from URL
def extract_domain(url):
    """Extract domain from URL for display purposes"""
    if not url:
        return None
        
    # Remove protocol if present
    if '://' in url:
        domain = url.split('://', 1)[1]
    else:
        domain = url
        
    # Take only the part before the first slash if there is one
    if '/' in domain:
        domain = domain.split('/', 1)[0]
        
    return domain

# Replace the domain-based auth with API key auth
def check_api_auth():
    """Check API authorization based on API key"""
    # Get API key from request headers
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        logger.warning("API request missing API key")
        return False
    
    # Look up service by API key (stored in client_secret)
    service = get_service_by_api_key(api_key)
    if not service:
        logger.warning(f"API request with invalid API key: {api_key[:8]}...")
        return False
    
    # Check if service is active
    if not service['is_active']:
        logger.warning(f"API request from inactive service: {service['name']}")
        return False
    
    # API key is valid and service is active
    logger.info(f"Authenticated API request from service: {service['name']}")
    return True

# Add this function to each API endpoint
def api_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not check_api_auth():
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# Home route redirects to login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Get the service that is requesting authentication
        service_url = request.args.get('service', None)
        session['redirect_service'] = service_url
        
        # Extract domain for display purposes using the helper function
        service_domain = extract_domain(service_url)
        
        return render_template('login.html', service=service_domain)
    
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
            # Use the full service URL directly without appending /auth/callback
            redirect_url = f"{result['redirect_service']}?token={result['token']}"
            return redirect(redirect_url)
        
        # Otherwise just log in normally
        session['user_id'] = result['user']['id']
        return redirect(url_for('dashboard'))

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        service_url = request.args.get('service', None)
        session['redirect_service'] = service_url
        
        # Extract domain for display purposes using the helper function
        service_domain = extract_domain(service_url)
                
        return render_template('signup.html', service=service_domain)
    
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
            # Use the full service URL directly without appending /auth/callback
            redirect_url = f"{result['redirect_service']}?token={result['token']}"
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
@api_auth_required  # Add security to this endpoint
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

# The following endpoints have been removed:
# - /api/getuserbytoken
# - /api/getuserbyid
# - /api/getuserbyname
# - /api/getuserbyemail

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

# Add helper function to get service by API key
def get_service_by_api_key(api_key):
    """Get a service by API key (client_secret)"""
    query = """
    SELECT id, name, domain, client_id, client_secret, created_at, is_active
    FROM registered_services
    WHERE client_secret = %s
    """
    row = db.execute_query(query, (api_key,), fetchone=True)
    
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

# Update how we create a service to make it clear this is an API key
def create_service(name, domain):
    """Create a new service with a unique ID and API key"""
    client_id = str(uuid.uuid4())
    # Generate an API key (using os.urandom for good entropy)
    api_key = os.urandom(16).hex()
    
    query = """
    INSERT INTO registered_services (name, domain, client_id, client_secret)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """
    row = db.execute_query(query, (name, domain, client_id, api_key), fetchone=True, commit=True)
    
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
