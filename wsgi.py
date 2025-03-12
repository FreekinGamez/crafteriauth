import sys
import os
from pathlib import Path

# Initialize the virtual environment
venv_path = '/var/www/auth/.venv'
python_path = os.path.join(venv_path, 'bin')
site_packages = os.path.join(venv_path, 'lib', 'python3.x', 'site-packages')
os.environ['PATH'] = f"{python_path}:{os.environ['PATH']}"
sys.path.insert(0, site_packages)

# Add the project directory to the Python path
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Import the Flask app
from backend.app import app as application

# Initialize the application
from backend.app import init_app
if not init_app():
    print("Failed to initialize application")

# The application variable is what WSGI servers look for
if __name__ == "__main__":
    application.run()

