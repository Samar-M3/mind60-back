"""
Illustrative middleware to ensure Firebase is initialised and CORS headers stay tight.
Currently unused but ready for future per-request hooks.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.core.firebase import init_firebase


class FirebaseInitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        init_firebase()
        response: Response = await call_next(request)
        return response

