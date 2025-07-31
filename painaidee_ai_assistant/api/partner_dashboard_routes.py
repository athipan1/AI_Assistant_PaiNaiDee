"""
Partner Dashboard API routes for managing partners and API keys
Provides partner registration, API key management, and analytics
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from models.partner_auth import (
    partner_auth_manager, 
    Partner, 
    ApiKey, 
    PartnerTier, 
    ApiKeyStatus
)

def get_partner_api_key(request: Request) -> str:
    """Extract partner API key from headers"""
    return request.headers.get("X-Partner-Key")

def get_admin_key(request: Request) -> str:
    """Extract admin key from headers"""
    return request.headers.get("X-Admin-Key")

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/partner", tags=["Partner Dashboard"])

# Request/Response models
class PartnerRegistrationRequest(BaseModel):
    """Request model for partner registration"""
    name: str = Field(..., description="Partner name", min_length=2, max_length=100)
    email: EmailStr = Field(..., description="Partner email address")
    company: str = Field(..., description="Company name", min_length=2, max_length=100)
    tier: PartnerTier = Field(PartnerTier.FREE, description="Initial subscription tier")
    contact_info: Optional[Dict[str, str]] = Field(None, description="Additional contact information")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")

class PartnerRegistrationResponse(BaseModel):
    """Response model for partner registration"""
    partner_id: str
    name: str
    email: str
    company: str
    tier: str
    api_key: str
    created_at: str
    message: str

class ApiKeyCreateRequest(BaseModel):
    """Request model for creating API keys"""
    name: str = Field(..., description="API key name/description", min_length=1, max_length=100)

class ApiKeyResponse(BaseModel):
    """Response model for API key information"""
    key_id: str
    name: str
    status: str
    tier: str
    created_at: str
    expires_at: Optional[str]
    last_used_at: Optional[str]
    usage_count: int
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    requests_per_month: int

class PartnerInfoResponse(BaseModel):
    """Response model for partner information"""
    partner_id: str
    name: str
    email: str
    company: str
    tier: str
    created_at: str
    updated_at: str
    is_active: bool
    api_keys_count: int
    total_requests: int

class UsageAnalyticsResponse(BaseModel):
    """Response model for usage analytics"""
    partner_id: str
    total_api_keys: int
    active_api_keys: int
    total_requests: int
    tier: str
    current_period_usage: Dict[str, int]
    rate_limits: Dict[str, Any]
    keys_info: List[Dict[str, Any]]

# Public registration endpoint (no auth required)
@router.post("/register",
            response_model=PartnerRegistrationResponse,
            summary="Register New Partner",
            description="Register as a new partner to get API access")
async def register_partner(request: PartnerRegistrationRequest) -> PartnerRegistrationResponse:
    """
    Register as a new partner to access the PaiNaiDee Public API.
    
    This endpoint creates a new partner account and generates an initial API key.
    Partners start with a FREE tier by default.
    """
    try:
        # Check if email already exists
        existing_partners = [p for p in partner_auth_manager.partners.values() if p.email == request.email]
        if existing_partners:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already registered"
            )
        
        # Create partner
        partner_id = partner_auth_manager.create_partner(
            name=request.name,
            email=request.email,
            company=request.company,
            tier=request.tier,
            contact_info=request.contact_info
        )
        
        if not partner_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create partner account"
            )
        
        # Create initial API key
        api_key = partner_auth_manager.create_api_key(partner_id, "Default API Key")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create initial API key"
            )
        
        partner = partner_auth_manager.get_partner_info(partner_id)
        
        return PartnerRegistrationResponse(
            partner_id=partner_id,
            name=partner.name,
            email=partner.email,
            company=partner.company,
            tier=partner.tier.value,
            api_key=api_key,
            created_at=partner.created_at.isoformat(),
            message="Partner registered successfully! Save your API key securely - it won't be shown again."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering partner: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

# Admin endpoint for managing partners (requires admin auth)
@router.get("/list",
           response_model=List[PartnerInfoResponse],
           summary="List All Partners (Admin)",
           description="Get list of all registered partners (admin only)")
async def list_partners(
    admin_key: str = Depends(get_admin_key),
    skip: int = 0,
    limit: int = 100
) -> List[PartnerInfoResponse]:
    """
    Get a list of all registered partners (admin functionality).
    
    Requires admin authentication via X-Admin-Key header.
    """
    # Simple admin key check (in production, use proper admin auth)
    if admin_key != "admin_painaidee_2025":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required"
        )
    
    try:
        partners = list(partner_auth_manager.partners.values())[skip:skip+limit]
        response = []
        
        for partner in partners:
            partner_keys = partner_auth_manager.get_partner_api_keys(partner.partner_id)
            total_requests = sum(key.usage_count for key in partner_keys)
            
            response.append(PartnerInfoResponse(
                partner_id=partner.partner_id,
                name=partner.name,
                email=partner.email,
                company=partner.company,
                tier=partner.tier.value,
                created_at=partner.created_at.isoformat(),
                updated_at=partner.updated_at.isoformat(),
                is_active=partner.is_active,
                api_keys_count=len(partner_keys),
                total_requests=total_requests
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing partners: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving partners"
        )

# Partner-specific endpoints (require partner API key auth)
@router.get("/info",
           response_model=PartnerInfoResponse,
           summary="Get Partner Information",
           description="Get information about your partner account")
async def get_partner_info(
    partner_api_key: str = Depends(get_partner_api_key)
) -> PartnerInfoResponse:
    """
    Get information about your partner account.
    
    Requires your API key in the X-Partner-Key header.
    """
    if not partner_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Partner API key required in X-Partner-Key header"
        )
    
    # Validate API key and get partner info
    key_info = partner_auth_manager.validate_api_key(partner_api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    try:
        partner = partner_auth_manager.get_partner_info(key_info.partner_id)
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partner not found"
            )
        
        partner_keys = partner_auth_manager.get_partner_api_keys(partner.partner_id)
        total_requests = sum(key.usage_count for key in partner_keys)
        
        return PartnerInfoResponse(
            partner_id=partner.partner_id,
            name=partner.name,
            email=partner.email,
            company=partner.company,
            tier=partner.tier.value,
            created_at=partner.created_at.isoformat(),
            updated_at=partner.updated_at.isoformat(),
            is_active=partner.is_active,
            api_keys_count=len(partner_keys),
            total_requests=total_requests
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting partner info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving partner information"
        )

@router.get("/api-keys",
           response_model=List[ApiKeyResponse],
           summary="List API Keys",
           description="Get list of your API keys")
async def list_api_keys(
    partner_api_key: str = Depends(get_partner_api_key)
) -> List[ApiKeyResponse]:
    """
    Get a list of all your API keys.
    
    Shows key information without revealing the actual key values.
    """
    if not partner_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Partner API key required in X-Partner-Key header"
        )
    
    key_info = partner_auth_manager.validate_api_key(partner_api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    try:
        partner_keys = partner_auth_manager.get_partner_api_keys(key_info.partner_id)
        
        response = []
        for key in partner_keys:
            response.append(ApiKeyResponse(
                key_id=key.key_id,
                name=key.name,
                status=key.status.value,
                tier=key.tier.value,
                created_at=key.created_at.isoformat(),
                expires_at=key.expires_at.isoformat() if key.expires_at else None,
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                usage_count=key.usage_count,
                requests_per_minute=key.requests_per_minute,
                requests_per_hour=key.requests_per_hour,
                requests_per_day=key.requests_per_day,
                requests_per_month=key.requests_per_month
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving API keys"
        )

@router.post("/api-keys",
            summary="Create New API Key",
            description="Create a new API key for your account")
async def create_api_key(
    request: ApiKeyCreateRequest,
    partner_api_key: str = Depends(get_partner_api_key)
) -> Dict[str, str]:
    """
    Create a new API key for your partner account.
    
    The API key will only be shown once - save it securely!
    """
    if not partner_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Partner API key required in X-Partner-Key header"
        )
    
    key_info = partner_auth_manager.validate_api_key(partner_api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    try:
        new_api_key = partner_auth_manager.create_api_key(key_info.partner_id, request.name)
        if not new_api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create API key. You may have reached the maximum number of keys for your tier."
            )
        
        return {
            "api_key": new_api_key,
            "name": request.name,
            "message": "API key created successfully! Save it securely - it won't be shown again.",
            "created_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating API key"
        )

@router.delete("/api-keys/{key_id}",
              summary="Revoke API Key",
              description="Revoke an API key")
async def revoke_api_key(
    key_id: str,
    partner_api_key: str = Depends(get_partner_api_key)
) -> Dict[str, str]:
    """
    Revoke an API key. This action cannot be undone.
    """
    if not partner_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Partner API key required in X-Partner-Key header"
        )
    
    key_info = partner_auth_manager.validate_api_key(partner_api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    try:
        # Check if the key belongs to this partner
        target_key = partner_auth_manager.api_keys.get(key_id)
        if not target_key or target_key.partner_id != key_info.partner_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Don't allow revoking the key being used for this request
        if target_key.key_id == key_info.key_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revoke the API key currently being used"
            )
        
        # Revoke the key
        target_key.status = ApiKeyStatus.REVOKED
        partner_auth_manager._save_api_keys()
        
        return {
            "message": "API key revoked successfully",
            "key_id": key_id,
            "revoked_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error revoking API key"
        )

@router.get("/analytics",
           response_model=UsageAnalyticsResponse,
           summary="Usage Analytics",
           description="Get detailed usage analytics for your account")
async def get_usage_analytics(
    partner_api_key: str = Depends(get_partner_api_key)
) -> UsageAnalyticsResponse:
    """
    Get detailed usage analytics for your partner account.
    
    Shows API usage statistics, rate limit status, and key performance.
    """
    if not partner_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Partner API key required in X-Partner-Key header"
        )
    
    key_info = partner_auth_manager.validate_api_key(partner_api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    try:
        analytics = partner_auth_manager.get_usage_analytics(key_info.partner_id)
        
        # Get current rate limit status
        allowed, rate_info = partner_auth_manager.check_rate_limit(key_info.key_id)
        
        # Calculate current period usage
        current_usage = {
            "requests_this_minute": rate_info["requests_per_minute"]["current"],
            "requests_this_hour": rate_info["requests_per_hour"]["current"],
            "requests_this_day": rate_info["requests_per_day"]["current"],
            "requests_this_month": rate_info["requests_per_month"]["current"]
        }
        
        return UsageAnalyticsResponse(
            partner_id=analytics["partner_id"],
            total_api_keys=analytics["total_api_keys"],
            active_api_keys=analytics["active_api_keys"],
            total_requests=analytics["total_requests"],
            tier=analytics["tier"],
            current_period_usage=current_usage,
            rate_limits=rate_info,
            keys_info=analytics["keys_info"]
        )
        
    except Exception as e:
        logger.error(f"Error getting usage analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving analytics"
        )

# Dashboard health check
@router.get("/health",
           summary="Dashboard Health Check",
           description="Check partner dashboard API health")
async def dashboard_health_check() -> Dict[str, Any]:
    """
    Check the health status of the Partner Dashboard API.
    """
    try:
        # Test basic functionality
        total_partners = len(partner_auth_manager.partners)
        total_keys = len(partner_auth_manager.api_keys)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_partners": total_partners,
                "total_api_keys": total_keys,
                "partner_auth_system": "operational"
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }