"""
Test configuration module
"""
import pytest
from src.config import Settings, get_settings

def test_settings_defaults():
    """Test default settings values"""
    settings = Settings()
    
    assert settings.APP_NAME == "Multi-Agent System"
    assert settings.VERSION == "2.0.0"
    assert settings.DEBUG == False
    assert settings.ENVIRONMENT == "production"

def test_settings_env_override(monkeypatch):
    """Test environment variable override"""
    monkeypatch.setenv("APP_NAME", "Test MAS")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    
    settings = Settings()
    
    assert settings.APP_NAME == "Test MAS"
    assert settings.DEBUG == True
    assert settings.DATABASE_URL == "postgresql://test:test@localhost/test"

def test_get_settings_cached():
    """Test that get_settings returns cached instance"""
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2