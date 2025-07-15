#!/usr/bin/env python3
"""Test simple de l'authentification"""
import requests

API_URL = "http://localhost:8088"

# 1. Test register
print("1. Test register...")
response = requests.post(f"{API_URL}/auth/register", json={
    "username": "test123",
    "email": "test123@example.com",
    "password": "password123"
})
print(f"Status: {response.status_code}")
print(f"Response: {response.text}\n")

# 2. Test login
print("2. Test login...")
response = requests.post(f"{API_URL}/auth/token", data={
    "username": "test123",
    "password": "password123"
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"Token: {token[:50]}...\n")
    
    # 3. Test /me endpoint
    print("3. Test /me endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
else:
    print(f"Response: {response.text}")