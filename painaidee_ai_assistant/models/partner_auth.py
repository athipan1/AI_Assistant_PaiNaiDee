"""
Partner Authentication and API Key Management System
Handles partner registration, API key generation, and rate limiting.
"""

import uuid
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os

class PartnerTier(Enum):
    """Partner subscription tiers with different rate limits"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class ApiKeyStatus(Enum):
    """API Key status states"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"

@dataclass
class Partner:
    """Partner information structure"""
    partner_id: str
    name: str
    email: str
    company: str
    tier: PartnerTier
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    contact_info: Optional[Dict] = None
    webhook_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['tier'] = self.tier.value
        return data

@dataclass
class ApiKey:
    """API Key structure with rate limiting info"""
    key_id: str
    partner_id: str
    key_hash: str  # Hashed version of actual key
    name: str
    tier: PartnerTier
    status: ApiKeyStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    # Rate limiting settings
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    requests_per_month: int = 100000
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        data['last_used_at'] = self.last_used_at.isoformat() if self.last_used_at else None
        data['tier'] = self.tier.value
        data['status'] = self.status.value
        return data

@dataclass
class RateLimitInfo:
    """Rate limiting tracking information"""
    key_id: str
    minute_count: int = 0
    hour_count: int = 0
    day_count: int = 0
    month_count: int = 0
    minute_reset: datetime = None
    hour_reset: datetime = None
    day_reset: datetime = None
    month_reset: datetime = None

class PartnerAuthManager:
    """Manages partner authentication, API keys, and rate limiting"""
    
    def __init__(self, storage_path: str = "cache/partners"):
        self.storage_path = storage_path
        self.partners_file = os.path.join(storage_path, "partners.json")
        self.api_keys_file = os.path.join(storage_path, "api_keys.json")
        self.rate_limits_file = os.path.join(storage_path, "rate_limits.json")
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing data
        self.partners: Dict[str, Partner] = self._load_partners()
        self.api_keys: Dict[str, ApiKey] = self._load_api_keys()
        self.rate_limits: Dict[str, RateLimitInfo] = self._load_rate_limits()
        
        # Tier configurations
        self.tier_configs = {
            PartnerTier.FREE: {
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "requests_per_day": 1000,
                "requests_per_month": 10000,
                "max_api_keys": 1
            },
            PartnerTier.BASIC: {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "requests_per_month": 100000,
                "max_api_keys": 3
            },
            PartnerTier.PREMIUM: {
                "requests_per_minute": 300,
                "requests_per_hour": 5000,
                "requests_per_day": 50000,
                "requests_per_month": 500000,
                "max_api_keys": 10
            },
            PartnerTier.ENTERPRISE: {
                "requests_per_minute": 1000,
                "requests_per_hour": 20000,
                "requests_per_day": 200000,
                "requests_per_month": 2000000,
                "max_api_keys": 50
            }
        }

    def _load_partners(self) -> Dict[str, Partner]:
        """Load partners from storage"""
        if not os.path.exists(self.partners_file):
            return {}
        
        try:
            with open(self.partners_file, 'r') as f:
                data = json.load(f)
            
            partners = {}
            for partner_id, partner_data in data.items():
                partner_data['created_at'] = datetime.fromisoformat(partner_data['created_at'])
                partner_data['updated_at'] = datetime.fromisoformat(partner_data['updated_at'])
                partner_data['tier'] = PartnerTier(partner_data['tier'])
                partners[partner_id] = Partner(**partner_data)
            
            return partners
        except Exception as e:
            print(f"Error loading partners: {e}")
            return {}

    def _load_api_keys(self) -> Dict[str, ApiKey]:
        """Load API keys from storage"""
        if not os.path.exists(self.api_keys_file):
            return {}
        
        try:
            with open(self.api_keys_file, 'r') as f:
                data = json.load(f)
            
            api_keys = {}
            for key_id, key_data in data.items():
                key_data['created_at'] = datetime.fromisoformat(key_data['created_at'])
                key_data['expires_at'] = datetime.fromisoformat(key_data['expires_at']) if key_data['expires_at'] else None
                key_data['last_used_at'] = datetime.fromisoformat(key_data['last_used_at']) if key_data['last_used_at'] else None
                key_data['tier'] = PartnerTier(key_data['tier'])
                key_data['status'] = ApiKeyStatus(key_data['status'])
                api_keys[key_id] = ApiKey(**key_data)
            
            return api_keys
        except Exception as e:
            print(f"Error loading API keys: {e}")
            return {}

    def _load_rate_limits(self) -> Dict[str, RateLimitInfo]:
        """Load rate limit tracking from storage"""
        if not os.path.exists(self.rate_limits_file):
            return {}
        
        try:
            with open(self.rate_limits_file, 'r') as f:
                data = json.load(f)
            
            rate_limits = {}
            for key_id, limit_data in data.items():
                if limit_data.get('minute_reset'):
                    limit_data['minute_reset'] = datetime.fromisoformat(limit_data['minute_reset'])
                if limit_data.get('hour_reset'):
                    limit_data['hour_reset'] = datetime.fromisoformat(limit_data['hour_reset'])
                if limit_data.get('day_reset'):
                    limit_data['day_reset'] = datetime.fromisoformat(limit_data['day_reset'])
                if limit_data.get('month_reset'):
                    limit_data['month_reset'] = datetime.fromisoformat(limit_data['month_reset'])
                
                rate_limits[key_id] = RateLimitInfo(**limit_data)
            
            return rate_limits
        except Exception as e:
            print(f"Error loading rate limits: {e}")
            return {}

    def _save_partners(self):
        """Save partners to storage"""
        try:
            data = {pid: partner.to_dict() for pid, partner in self.partners.items()}
            with open(self.partners_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving partners: {e}")

    def _save_api_keys(self):
        """Save API keys to storage"""
        try:
            data = {kid: key.to_dict() for kid, key in self.api_keys.items()}
            with open(self.api_keys_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving API keys: {e}")

    def _save_rate_limits(self):
        """Save rate limits to storage"""
        try:
            data = {}
            for key_id, limit_info in self.rate_limits.items():
                limit_data = asdict(limit_info)
                limit_data['minute_reset'] = limit_info.minute_reset.isoformat() if limit_info.minute_reset else None
                limit_data['hour_reset'] = limit_info.hour_reset.isoformat() if limit_info.hour_reset else None
                limit_data['day_reset'] = limit_info.day_reset.isoformat() if limit_info.day_reset else None
                limit_data['month_reset'] = limit_info.month_reset.isoformat() if limit_info.month_reset else None
                data[key_id] = limit_data
            
            with open(self.rate_limits_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving rate limits: {e}")

    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        # Generate random key with prefix
        key_data = f"painaidee_{uuid.uuid4().hex}_{int(time.time())}"
        return key_data

    def hash_api_key(self, api_key: str) -> str:
        """Create secure hash of API key"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def create_partner(self, name: str, email: str, company: str, 
                      tier: PartnerTier = PartnerTier.FREE, 
                      contact_info: Optional[Dict] = None) -> str:
        """Create a new partner and return partner ID"""
        partner_id = str(uuid.uuid4())
        now = datetime.now()
        
        partner = Partner(
            partner_id=partner_id,
            name=name,
            email=email,
            company=company,
            tier=tier,
            created_at=now,
            updated_at=now,
            contact_info=contact_info or {}
        )
        
        self.partners[partner_id] = partner
        self._save_partners()
        
        return partner_id

    def create_api_key(self, partner_id: str, key_name: str = "Default Key") -> Optional[str]:
        """Create a new API key for a partner"""
        if partner_id not in self.partners:
            return None
        
        partner = self.partners[partner_id]
        
        # Check if partner has reached API key limit
        partner_keys = [k for k in self.api_keys.values() if k.partner_id == partner_id]
        max_keys = self.tier_configs[partner.tier]["max_api_keys"]
        
        if len(partner_keys) >= max_keys:
            return None
        
        # Generate API key
        api_key = self.generate_api_key()
        key_id = str(uuid.uuid4())
        
        # Get tier configuration
        tier_config = self.tier_configs[partner.tier]
        
        # Create API key record
        key_record = ApiKey(
            key_id=key_id,
            partner_id=partner_id,
            key_hash=self.hash_api_key(api_key),
            name=key_name,
            tier=partner.tier,
            status=ApiKeyStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=None,  # No expiration by default
            requests_per_minute=tier_config["requests_per_minute"],
            requests_per_hour=tier_config["requests_per_hour"],
            requests_per_day=tier_config["requests_per_day"],
            requests_per_month=tier_config["requests_per_month"]
        )
        
        self.api_keys[key_id] = key_record
        self._save_api_keys()
        
        # Initialize rate limiting
        self.rate_limits[key_id] = RateLimitInfo(key_id=key_id)
        self._save_rate_limits()
        
        return api_key

    def validate_api_key(self, api_key: str) -> Optional[ApiKey]:
        """Validate an API key and return key info if valid"""
        key_hash = self.hash_api_key(api_key)
        
        for key_record in self.api_keys.values():
            if key_record.key_hash == key_hash:
                # Check if key is active
                if key_record.status != ApiKeyStatus.ACTIVE:
                    return None
                
                # Check if key has expired
                if key_record.expires_at and datetime.now() > key_record.expires_at:
                    key_record.status = ApiKeyStatus.EXPIRED
                    self._save_api_keys()
                    return None
                
                return key_record
        
        return None

    def check_rate_limit(self, key_id: str) -> tuple[bool, Dict[str, Any]]:
        """Check if API key has exceeded rate limits"""
        if key_id not in self.api_keys or key_id not in self.rate_limits:
            return False, {"error": "Invalid API key"}
        
        api_key = self.api_keys[key_id]
        rate_limit = self.rate_limits[key_id]
        now = datetime.now()
        
        # Reset counters if time windows have passed
        if not rate_limit.minute_reset or now >= rate_limit.minute_reset:
            rate_limit.minute_count = 0
            rate_limit.minute_reset = now + timedelta(minutes=1)
        
        if not rate_limit.hour_reset or now >= rate_limit.hour_reset:
            rate_limit.hour_count = 0
            rate_limit.hour_reset = now + timedelta(hours=1)
        
        if not rate_limit.day_reset or now >= rate_limit.day_reset:
            rate_limit.day_count = 0
            rate_limit.day_reset = now + timedelta(days=1)
        
        if not rate_limit.month_reset or now >= rate_limit.month_reset:
            rate_limit.month_count = 0
            rate_limit.month_reset = now + timedelta(days=30)
        
        # Check limits
        limits_info = {
            "requests_per_minute": {
                "limit": api_key.requests_per_minute,
                "current": rate_limit.minute_count,
                "reset_at": rate_limit.minute_reset.isoformat()
            },
            "requests_per_hour": {
                "limit": api_key.requests_per_hour,
                "current": rate_limit.hour_count,
                "reset_at": rate_limit.hour_reset.isoformat()
            },
            "requests_per_day": {
                "limit": api_key.requests_per_day,
                "current": rate_limit.day_count,
                "reset_at": rate_limit.day_reset.isoformat()
            },
            "requests_per_month": {
                "limit": api_key.requests_per_month,
                "current": rate_limit.month_count,
                "reset_at": rate_limit.month_reset.isoformat()
            }
        }
        
        # Check if any limit is exceeded
        if (rate_limit.minute_count >= api_key.requests_per_minute or
            rate_limit.hour_count >= api_key.requests_per_hour or
            rate_limit.day_count >= api_key.requests_per_day or
            rate_limit.month_count >= api_key.requests_per_month):
            return False, limits_info
        
        return True, limits_info

    def record_api_usage(self, key_id: str):
        """Record API usage for rate limiting"""
        if key_id not in self.api_keys or key_id not in self.rate_limits:
            return
        
        api_key = self.api_keys[key_id]
        rate_limit = self.rate_limits[key_id]
        
        # Update usage counters
        rate_limit.minute_count += 1
        rate_limit.hour_count += 1
        rate_limit.day_count += 1
        rate_limit.month_count += 1
        
        # Update API key usage
        api_key.usage_count += 1
        api_key.last_used_at = datetime.now()
        
        # Save updates
        self._save_api_keys()
        self._save_rate_limits()

    def get_partner_info(self, partner_id: str) -> Optional[Partner]:
        """Get partner information"""
        return self.partners.get(partner_id)

    def get_partner_api_keys(self, partner_id: str) -> List[ApiKey]:
        """Get all API keys for a partner"""
        return [k for k in self.api_keys.values() if k.partner_id == partner_id]

    def get_usage_analytics(self, partner_id: str) -> Dict[str, Any]:
        """Get usage analytics for a partner"""
        partner_keys = self.get_partner_api_keys(partner_id)
        
        total_usage = sum(key.usage_count for key in partner_keys)
        active_keys = len([k for k in partner_keys if k.status == ApiKeyStatus.ACTIVE])
        
        analytics = {
            "partner_id": partner_id,
            "total_api_keys": len(partner_keys),
            "active_api_keys": active_keys,
            "total_requests": total_usage,
            "tier": partner_keys[0].tier.value if partner_keys else None,
            "keys_info": [
                {
                    "key_id": key.key_id,
                    "name": key.name,
                    "status": key.status.value,
                    "usage_count": key.usage_count,
                    "last_used": key.last_used_at.isoformat() if key.last_used_at else None,
                    "created_at": key.created_at.isoformat()
                }
                for key in partner_keys
            ]
        }
        
        return analytics

# Global instance
partner_auth_manager = PartnerAuthManager()