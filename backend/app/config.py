"""
AutiCare Configuration Manager
Tüm sensitive ve non-sensitive configuration'lar burada yönetilir.
Environment variables ile dişarıdan override edilebilir.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import json


class Settings(BaseSettings):
    """
    Application Configuration
    .env dosyasından otomatik olarak yüklenir
    """
    
    # ============ SECURITY ============
    SECRET_KEY: str  # JWT secret key (MUST be set in .env)
    ALGORITHM: str = "HS256"  # JWT algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days in minutes
    
    # ============ DATABASE ============
    DATABASE_URL: str  # MUST be set in .env (e.g., mysql+pymysql://user:pass@host/db)
    
    # ============ OPENAI & LLM ============
    OPENAI_API_KEY: str  # MUST be set in .env
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # ============ EMAIL & NOTIFICATIONS ============
    RESEND_API_KEY: str  # MUST be set in .env
    FROM_EMAIL: str  # MUST be set in .env
    
    # ============ AI & CREWAI ============
    CREWAI_STORAGE_DIR: str = "AutiCare"
    
    # ============ CORS & FRONTEND ============
    ALLOWED_ORIGINS: list  # MUST be set in .env (comma-separated or JSON array)
    FRONTEND_URL: str  # Frontend base URL (for redirects, etc.)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
       
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try JSON array first
            if v.startswith('['):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [url.strip() for url in v.split(',')]
        return v
    
    def validate_critical_configs(self):
        """Startup'ta kritik configuration'ları kontrol et"""
        # Security
        if not self.SECRET_KEY or self.SECRET_KEY == "supersecretkey123changethis":
            raise ValueError(
                "❌ CRITICAL: SECRET_KEY environment variable'ı ayarlanmalı ve güvenli olmalı! "
                "Generator: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        
        # Database
        if not self.DATABASE_URL:
            raise ValueError("❌ CRITICAL: DATABASE_URL environment variable'ı ayarlanmalı!")
        
        # API Keys
        if not self.OPENAI_API_KEY:
            raise ValueError("❌ CRITICAL: OPENAI_API_KEY environment variable'ı ayarlanmalı!")
        if not self.RESEND_API_KEY:
            raise ValueError("❌ CRITICAL: RESEND_API_KEY environment variable'ı ayarlanmalı!")
        if not self.FROM_EMAIL:
            raise ValueError("❌ CRITICAL: FROM_EMAIL environment variable'ı ayarlanmalı!")
        
        # CORS & Frontend
        if not self.ALLOWED_ORIGINS:
            raise ValueError("❌ CRITICAL: ALLOWED_ORIGINS environment variable'ı ayarlanmalı!")
        if not self.FRONTEND_URL:
            raise ValueError("❌ CRITICAL: FRONTEND_URL environment variable'ı ayarlanmalı!")


# Global settings instance
settings = Settings()

# Startup'ta validate et
settings.validate_critical_configs()
