import sys
import os

# Add application directory to path
sys.path.insert(0, '/var/www/auth')

# If using virtualenv (recommended)
venv_path = '/var/www/auth/.venv'
python_path = os.path.join(venv_path, 'bin')
site_packages = os.path.join(venv_path, 'lib', 'python3.x', 'site-packages')
os.environ['PATH'] = f"{python_path}:{os.environ['PATH']}"
sys.path.insert(0, site_packages)

from app import app as application

