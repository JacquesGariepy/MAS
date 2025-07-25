#!/usr/bin/env python3
"""
Demonstration of what the unified swarm would generate for a REST API request
"""

import asyncio
import sys
sys.path.insert(0, '/app/src')

from swarm_mas_unified import UnifiedLLMService

async def demo_rest_api_generation():
    """Show what code the swarm would generate for REST API with auth"""
    print("="*80)
    print("🚀 UNIFIED SWARM - REST API GENERATION DEMO")
    print("="*80)
    print("\nRequest: 'build a REST API with authentication and testing'\n")
    
    # Create LLM service
    llm_service = UnifiedLLMService(config={'mock_mode': False})
    
    # 1. Analyze the request
    print("📋 Phase 1: Request Analysis")
    print("-"*40)
    analysis = await llm_service.analyze_request("build a REST API with authentication and testing")
    print(f"Type: {analysis.get('type', 'N/A')}")
    print(f"Complexity: {analysis.get('complexity', 'N/A')}")
    print(f"Domains: {', '.join(analysis.get('domains', []))}")
    print(f"Agent types needed: {', '.join(analysis.get('agent_types_needed', []))}")
    
    # 2. Task decomposition
    print("\n📋 Phase 2: Task Decomposition")
    print("-"*40)
    decomposition = await llm_service.decompose_task("build a REST API with authentication and testing", analysis)
    print(f"Number of subtasks: {len(decomposition)}")
    for i, task in enumerate(decomposition, 1):
        print(f"  {i}. {task.get('description', 'N/A')} [{task.get('required_agent_type', 'N/A')}]")
    
    # 3. What would be generated
    print("\n📋 Phase 3: Code Generation (What Would Be Created)")
    print("-"*40)
    print("\n📁 Project Structure:")
    print("""
api/
├── app.py              # Main Flask/FastAPI application
├── auth.py             # JWT authentication module
├── models.py           # Database models (User, etc.)
├── routes/
│   ├── __init__.py
│   ├── users.py        # User management endpoints
│   └── auth.py         # Authentication endpoints
├── middleware/
│   ├── __init__.py
│   └── auth.py         # Auth middleware
├── tests/
│   ├── __init__.py
│   ├── test_auth.py    # Authentication tests
│   ├── test_users.py   # User endpoint tests
│   └── fixtures.py     # Test fixtures
├── requirements.txt    # Dependencies
└── README.md          # API documentation
    """)
    
    print("\n📄 Sample Generated Code:")
    print("\n1️⃣ app.py - Main Application:")
    print("""```python
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from routes import auth_routes, user_routes
from models import db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# Register blueprints
app.register_blueprint(auth_routes, url_prefix='/api/auth')
app.register_blueprint(user_routes, url_prefix='/api/users')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
```""")
    
    print("\n2️⃣ auth.py - Authentication Module:")
    print("""```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db

auth_routes = Blueprint('auth', __name__)

@auth_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User already exists'}), 409
    
    # Create user
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': access_token}), 200
```""")
    
    print("\n3️⃣ test_auth.py - Authentication Tests:")
    print("""```python
import pytest
from app import app, db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_register_user(client):
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'securepassword'
    })
    assert response.status_code == 201
    assert b'User created successfully' in response.data

def test_login_user(client):
    # First register
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'securepassword'
    })
    
    # Then login
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'securepassword'
    })
    assert response.status_code == 200
    assert 'access_token' in response.get_json()

def test_invalid_login(client):
    response = client.post('/api/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
```""")
    
    print("\n📊 Summary:")
    print("-"*40)
    print("✅ Complete REST API with Flask")
    print("✅ JWT-based authentication")
    print("✅ User registration and login")
    print("✅ Password hashing with werkzeug")
    print("✅ Comprehensive test suite")
    print("✅ Error handling and validation")
    print("✅ CORS support")
    print("✅ SQLAlchemy for database")
    
    print("\n🎯 This is what the unified swarm would generate!")
    print("   With 45 specialized agents working together:")
    print("   - Architects design the structure")
    print("   - Developers implement the code")
    print("   - Testers create the test suite")
    print("   - Security experts handle authentication")
    print("   - DevOps prepare deployment")

if __name__ == "__main__":
    asyncio.run(demo_rest_api_generation())