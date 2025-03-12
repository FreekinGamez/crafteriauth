import subprocess
import sys

def install_dependencies():
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully!")

if __name__ == "__main__":
    install_dependencies()
