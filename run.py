import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# Import from the backend package
from backend.app import app, init_app

if __name__ == "__main__":
    if init_app():
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False
        )
    else:
        print("Failed to initialize application. Check logs for details.")
