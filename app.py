from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import jwt
import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/auth_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define models directly in app.py
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    tokens = db.relationship('Token', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Token(db.Model):
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_value = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    issued_for = db.Column(db.String(255), nullable=True)  # Service domain
    
    def __repr__(self):
        return f'<Token {self.id} for User {self.user_id}>'
    
    @property
    def is_expired(self):
        return datetime.datetime.utcnow() > self.expires_at

class RegisteredService(db.Model):
    __tablename__ = 'registered_services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    client_id = db.Column(db.String(36), unique=True, nullable=False)
    client_secret = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Service {self.name}>'

# Generate token utility function
def generate_token(user_id, service=None):
    """Generate a JWT token for the user"""
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    
    payload = {
        'sub': user_id,
        'iat': datetime.datetime.utcnow(),
        'exp': expiration,
    }
    
    if service:
        payload['aud'] = service
    
    # Create JWT token
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
    
    # Store token in database
    new_token = Token(
        user_id=user_id,
        token_value=token,
        expires_at=expiration,
        issued_for=service
    )
    db.session.add(new_token)
    db.session.commit()
    
    return token

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
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return render_template('login.html', error="Invalid email or password")
        
        # Update last login time
        user.last_login = datetime.datetime.utcnow()
        db.session.commit()
        
        # Generate CrafteriToken
        token = generate_token(user.id, session.get('redirect_service'))
        
        # If there's a service to redirect to, do it with the token
        redirect_service = session.get('redirect_service')
        if redirect_service:
            registered_service = RegisteredService.query.filter_by(domain=redirect_service).first()
            if registered_service:
                redirect_url = f"https://{redirect_service}/auth/callback?token={token}"
                return redirect(redirect_url)
        
        # Otherwise just log in normally
        session['user_id'] = user.id
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
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('signup.html', error="Email already exists")
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Log the user in and generate token
        session['user_id'] = new_user.id
        token = generate_token(new_user.id, session.get('redirect_service'))
        
        # Redirect if needed
        redirect_service = session.get('redirect_service')
        if redirect_service:
            registered_service = RegisteredService.query.filter_by(domain=redirect_service).first()
            if registered_service:
                redirect_url = f"https://{redirect_service}/auth/callback?token={token}"
                return redirect(redirect_url)
        
        return redirect(url_for('dashboard'))

# Dashboard (protected route)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('redirect_service', None)
    return redirect(url_for('login'))

# Token verification endpoint for third-party services
@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    token = request.json.get('token', '')
    
    try:
        # Decode and verify token
        payload = jwt.decode(
            token, 
            app.config['SECRET_KEY'], 
            algorithms=["HS256"]
        )
        
        # Check if token exists in database (optional but adds security)
        token_record = Token.query.filter_by(token_value=token).first()
        if not token_record:
            return jsonify({'valid': False, 'error': 'Token not found'}), 401
        
        # Check token expiration
        if datetime.datetime.utcnow() > datetime.datetime.fromtimestamp(payload['exp']):
            return jsonify({'valid': False, 'error': 'Token expired'}), 401
        
        # Get user information
        user = User.query.get(payload['sub'])
        if not user:
            return jsonify({'valid': False, 'error': 'User not found'}), 401
        
        # Return user information
        return jsonify({
            'valid': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Invalid token'}), 401

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
    existing_service = RegisteredService.query.filter_by(domain=domain).first()
    if existing_service:
        return jsonify({'error': 'Service domain already registered'}), 400
        
    # Create new service
    new_service = RegisteredService(
        name=name,
        domain=domain,
        client_id=str(uuid.uuid4()),
        client_secret=os.urandom(32).hex()
    )
    db.session.add(new_service)
    db.session.commit()
    
    return jsonify({
        'service': {
            'name': new_service.name,
            'domain': new_service.domain,
            'client_id': new_service.client_id,
            'client_secret': new_service.client_secret
        }
    }), 201

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True)
