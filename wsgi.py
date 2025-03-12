import sys
import os

# Add application directory to path
sys.path.insert(0, '/var/www/auth')

# If using virtualenv (recommended)
activate_this = '/var/www/auth/.venv/bin/activate'
if os.path.exists(activate_this):
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))

from app import app as application

