"""
Authentication middleware for JWT validation.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AuthenticationError, InvalidTokenError, TokenExpiredError
from app.core.logging import get_logger
from app.core.security import decode_token

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""

    # Public paths that don't require authentication
    PUBLIC_PATHS = [
        "/",
        "/api/v1/health",
        "/api/v1/docs",
        "/api/v1/redoc",
        "/api/v1/openapi.json",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
    ]

    async def dispatch(self, request: Request, call_next):
        """Process request and validate JWT if needed.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip authentication for public paths
        if any(request.url.path.startswith(path) for path in self.PUBLIC_PATHS):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning("missing_auth_header", path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Missing authorization header"},
            )

        try:
            # Extract Bearer token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise AuthenticationError("Invalid authorization header format")

            token = parts[1]

            # Decode and validate token
            payload = decode_token(token)

            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.token_payload = payload

            logger.debug("auth_success", user_id=request.state.user_id, path=request.url.path)

            return await call_next(request)

        except TokenExpiredError:
            logger.warning("token_expired", path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Token has expired"},
            )

        except (InvalidTokenError, AuthenticationError) as e:
            logger.warning("auth_failed", error=str(e), path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": str(e)},
            )

        except Exception as e:
            logger.error("auth_error", error=str(e), path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Authentication error"},
            )
