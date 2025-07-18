"""
Configuration management with environment validation
"""

from typing import List, Optional, Dict, Any
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import validator, field_validator
from pydantic.networks import PostgresDsn, RedisDsn, HttpUrl, AnyHttpUrl

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "Multi-Agent System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    TESTING: bool = False
    
    # API
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    API_V1_PREFIX: str = "/api/v1"
    ENABLE_DOCS: bool = True
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: RedisDsn
    REDIS_POOL_SIZE: int = 10
    REDIS_DECODE_RESPONSES: bool = True
    
    # Message Broker (Optional - we use Redis for now)
    RABBITMQ_URL: Optional[str] = None
    RABBITMQ_EXCHANGE: str = "mas_events"
    RABBITMQ_QUEUE_TTL: int = 3600000  # 1 hour
    
    # LLM Providers
    LMSTUDIO_BASE_URL: str = "http://localhost:1234/v1"
    OLLAMA_HOST: str = "http://localhost:11434"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TIMEOUT: int = 30
    
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-sonnet"
    ANTHROPIC_MAX_TOKENS: int = 4000
    
    LLM_PROVIDER: str = "openai"  # openai, ollama, lmstudio, mock
    LLM_BASE_URL: Optional[str] = None  # For Ollama/LM Studio
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4000
    ENABLE_MOCK_LLM: bool = False  # Enable mock mode for testing
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Monitoring
    SENTRY_DSN: Optional[HttpUrl] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    PROMETHEUS_ENABLED: bool = True
    JAEGER_ENABLED: bool = True
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831
    
    # Agent System
    MAX_AGENTS_PER_USER: int = 10
    MAX_AGENTS_TOTAL: int = 1000
    AGENT_TIMEOUT: int = 300  # seconds
    AGENT_MEMORY_LIMIT: int = 512  # MB
    
    # Tools
    ENABLE_CODE_EXECUTION: bool = True
    CODE_EXECUTION_TIMEOUT: int = 30
    CODE_EXECUTION_MEMORY_LIMIT: str = "256m"
    CODE_EXECUTION_CPU_LIMIT: str = "0.5"
    
    # Storage
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@mas-system.com"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

settings = get_settings()