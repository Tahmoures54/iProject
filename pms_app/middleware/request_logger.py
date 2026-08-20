import time
import logging
from flask import request, g

logger = logging.getLogger(__name__)

class RequestLogger:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        @app.before_request
        def start_timer():
            g.start_time = time.time()

        @app.after_request
        def log_request(response):
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                logger.info(f"{request.method} {request.path} {response.status_code} - {duration:.3f}s")
            return response
