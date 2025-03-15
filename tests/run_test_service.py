import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the test service
from tests.test_service import app, init_db

if __name__ == "__main__":
    # Initialize database tables
    try:
        init_db()
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    
    # Print instructions
    print("\n=== CRAFTERI AUTH TEST SERVICE ===")
    print("\nStarting test service at http://localhost:5001")
    print("\nTo use this service:")
    print("1. Make sure your Crafteri Auth service is running at http://localhost:5000")
    print("2. Register this service in Crafteri Auth by creating an entry in registered_services")
    print("3. Set the API key in test_service.py to match client_secret in registered_services")
    print("4. Visit http://localhost:5001 in your browser")
    print("5. Click 'Login with Crafteri' to test the SSO flow")
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=5001, debug=True)
