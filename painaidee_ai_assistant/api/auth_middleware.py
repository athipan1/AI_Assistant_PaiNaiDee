"""
FastAPI middleware for partner API authentication and rate limiting
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import time
import logging

from models.partner_auth import partner_auth_manager, ApiKey

logger = logging.getLogger(__name__)

# Security scheme for API key authentication
security = HTTPBearer(
    scheme_name="API Key Bearer Token",
    description="Enter your PaiNaiDee API key in the format: Bearer painaidee_xxxxxxxx"
)

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API key authentication and rate limiting"""
    
    def __init__(self, app, protected_paths: list = None):
        super().__init__(app)
        # Paths that require API key authentication
        self.protected_paths = protected_paths or [
            "/api/ai/ask",
            "/api/recommend/trip",
            "/api/image-tour-preview",
            "/api/tourism/",
            "/api/ai/",
            "/api/recommend/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Check if path requires authentication
        needs_auth = any(request.url.path.startswith(path) for path in self.protected_paths)
        
        if needs_auth:
            # Get API key from header
            api_key = None
            auth_header = request.headers.get("Authorization")
            
            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header[7:]  # Remove "Bearer " prefix
            
            if not api_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "API key required",
                        "message": "Please provide a valid API key in the Authorization header",
                        "format": "Authorization: Bearer painaidee_xxxxxxxx"
                    }
                )
            
            # Validate API key
            key_info = partner_auth_manager.validate_api_key(api_key)
            if not key_info:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Invalid API key",
                        "message": "The provided API key is invalid, expired, or revoked"
                    }
                )
            
            # Check rate limits
            allowed, rate_info = partner_auth_manager.check_rate_limit(key_info.key_id)
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "API rate limit exceeded for your subscription tier",
                        "rate_limits": rate_info,
                        "tier": key_info.tier.value
                    },
                    headers={
                        "X-RateLimit-Limit-Minute": str(key_info.requests_per_minute),
                        "X-RateLimit-Limit-Hour": str(key_info.requests_per_hour),
                        "X-RateLimit-Limit-Day": str(key_info.requests_per_day),
                        "X-RateLimit-Remaining-Minute": str(max(0, key_info.requests_per_minute - rate_info["requests_per_minute"]["current"])),
                        "X-RateLimit-Remaining-Hour": str(max(0, key_info.requests_per_hour - rate_info["requests_per_hour"]["current"])),
                        "X-RateLimit-Reset-Minute": rate_info["requests_per_minute"]["reset_at"],
                    }
                )
            
            # Add partner info to request state
            request.state.partner_key_id = key_info.key_id
            request.state.partner_id = key_info.partner_id
            request.state.partner_tier = key_info.tier
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Record API usage if authenticated
        if needs_auth and hasattr(request.state, 'partner_key_id'):
            partner_auth_manager.record_api_usage(request.state.partner_key_id)
            
            # Add rate limit headers to response
            key_info = partner_auth_manager.api_keys.get(request.state.partner_key_id)
            if key_info:
                _, rate_info = partner_auth_manager.check_rate_limit(key_info.key_id)
                response.headers["X-RateLimit-Limit-Minute"] = str(key_info.requests_per_minute)
                response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, key_info.requests_per_minute - rate_info["requests_per_minute"]["current"]))
                response.headers["X-RateLimit-Reset-Minute"] = rate_info["requests_per_minute"]["reset_at"]
                response.headers["X-Partner-Tier"] = key_info.tier.value
        
        response.headers["X-Process-Time"] = str(process_time)
        return response

async def get_current_partner(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[ApiKey]:
    """Dependency to get current partner from API key"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    api_key = credentials.credentials
    key_info = partner_auth_manager.validate_api_key(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check rate limits
    allowed, rate_info = partner_auth_manager.check_rate_limit(key_info.key_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(key_info.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": rate_info["requests_per_minute"]["reset_at"]
            }
        )
    
    return key_info

def require_tier(minimum_tier: str):
    """Decorator to require minimum partner tier"""
    def decorator(partner: ApiKey = Depends(get_current_partner)):
        tier_levels = {
            "free": 0,
            "basic": 1,
            "premium": 2,
            "enterprise": 3
        }
        
        current_level = tier_levels.get(partner.tier.value, 0)
        required_level = tier_levels.get(minimum_tier, 0)
        
        if current_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint requires {minimum_tier} tier or higher. Your current tier: {partner.tier.value}"
            )
        
        return partner
    
    return decorator