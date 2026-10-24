import sys
import os

# Add the project root directory to the python path so imports from 'app' work seamlessly
root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import create_app

app = create_app()


class VercelPathMiddleware:
    """
    WSGI Middleware to restore original request path on Vercel.
    When Vercel rewrites requests to /api/index, Flask's WSGI environment
    receives PATH_INFO as '/api/index' or '/api/index.py'.
    This middleware restores the actual path requested by the client
    (e.g., '/', '/home', '/products', '/cart') using Vercel's HTTP_X_MATCHED_PATH.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get("HTTP_X_MATCHED_PATH")
        if matched_path:
            environ["PATH_INFO"] = matched_path
        else:
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith("/api/index.py"):
                environ["PATH_INFO"] = path_info[len("/api/index.py"):] or "/"
            elif path_info.startswith("/api/index"):
                environ["PATH_INFO"] = path_info[len("/api/index"):] or "/"
        return self.wsgi_app(environ, start_response)


# Wrap Flask's WSGI application with the Vercel path middleware
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
