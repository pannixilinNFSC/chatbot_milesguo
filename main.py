"""
Cloud Functions entry point (2nd gen).
Wraps the FastAPI app for Google Cloud Functions.
"""
from mangum import Mangum
from server import app

# Wrap FastAPI app for Cloud Functions
handler = Mangum(app)

def cloud_function(request):
    """
    Cloud Functions HTTP entry point (2nd gen).
    
    Args:
        request: Flask Request object from Cloud Functions
    
    Returns:
        Response object
    """
    return handler(request.environ, lambda status, headers: None)
