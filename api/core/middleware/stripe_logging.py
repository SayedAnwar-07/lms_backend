import logging
logger = logging.getLogger(__name__)

class StripeLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if '/payment/' in request.path:
            logger.info(f"Payment Request: {request.method} {request.path}")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"Body: {request.body.decode() if request.body else None}")
            logger.info(f"Response: {response.status_code} {response.content}")
            
        return response