"""
Test authentication module
"""
import pytest
from datetime import timedelta
from jose import jwt

from src.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from src.config import get_settings

settings = get_settings()

def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    
    # Hash password
    hashed = get_password_hash(password)
    
    # Verify correct password
    assert verify_password(password, hashed) == True
    
    # Verify incorrect password
    assert verify_password("wrongpassword", hashed) == False
    
    # Ensure hash is different each time
    hashed2 = get_password_hash(password)
    assert hashed != hashed2

def test_create_access_token():
    """Test access token creation"""
    data = {"sub": "test_user_id"}
    token = create_access_token(data)
    
    # Decode token
    decoded = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    
    assert decoded["sub"] == "test_user_id"
    assert "exp" in decoded
    assert decoded.get("type") != "refresh"  # Access tokens don't have type

def test_create_access_token_with_expiry():
    """Test access token with custom expiry"""
    data = {"sub": "test_user_id"}
    expires_delta = timedelta(minutes=5)
    token = create_access_token(data, expires_delta)
    
    decoded = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    
    assert decoded["sub"] == "test_user_id"

def test_create_refresh_token():
    """Test refresh token creation"""
    data = {"sub": "test_user_id"}
    token = create_refresh_token(data)
    
    decoded = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    
    assert decoded["sub"] == "test_user_id"
    assert decoded["type"] == "refresh"
    assert "exp" in decoded