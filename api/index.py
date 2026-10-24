import sys
import os

# Add the project root directory to the python path so imports from 'app' work seamlessly
root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
