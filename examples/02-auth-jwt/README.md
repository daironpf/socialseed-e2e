# 🔐 JWT Authentication Example

A complete JWT authentication example using socialseed-e2e with Flask API.

## Overview

This example demonstrates:
- **User Registration**: POST /api/auth/register
- **User Login**: POST /api/auth/login (returns JWT tokens)
- **Token Refresh**: POST /api/auth/refresh
- **Protected Endpoints**: GET /api/protected (requires valid JWT)

## 📁 Project Structure

```
02-auth-jwt/
├── api.py                           # Flask API with JWT
├── requirements.txt                 # Python dependencies
├── e2e.conf                         # socialseed-e2e configuration
├── services/
│   └── auth-api/
│       ├── auth_api_page.py        # Auth service page with JWT handling
│       ├── data_schema.py          # Pydantic models
│       └── modules/
│           ├── 01_register_flow.py # Registration tests
│           ├── 02_login_flow.py    # Login and token tests
│           ├── 03_refresh_token_flow.py # Token refresh tests
│           └── 04_protected_endpoints.py # Protected access tests
└── README.md                        # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API

```bash
python api.py
```

The API will start on http://localhost:5001 with authentication endpoints.

### 3. Verify Test Discovery

```bash
e2e run
```

Should show **4 tests** detected and ready.

### ⚠️ Current Status (v0.1.0)

Test execution is in **placeholder mode**. All test modules are complete and detected, but full test runner execution is coming in v0.2.0.

**What's working:**
- ✅ Complete JWT authentication API
- ✅ 4 test modules covering all flows
- ✅ Test discovery (shows "Ready")
- ✅ Service Page with token management

## 🔐 Authentication Flow

### 1. Register a User

```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

Response:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### 2. Login

```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepass123"
  }'
```

Response:
```json
{
  "message": "Login successful",
  "user": {...},
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

### 3. Access Protected Endpoint

```bash
curl -X GET http://localhost:5001/api/protected \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### 4. Refresh Token

```bash
curl -X POST http://localhost:5001/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

## 📊 Token Handling

### Access Token
- **Short-lived**: 15 minutes (configurable)
- **Used for**: Accessing protected endpoints
- **Format**: JWT with user_id, username, type='access'

### Refresh Token
- **Long-lived**: 7 days (configurable)
- **Used for**: Obtaining new access tokens
- **Format**: JWT with user_id, username, type='refresh'

### Token Storage in Tests

The `AuthApiPage` class handles token storage automatically:

```python
# After login, tokens are stored automatically
login_response = auth_api.login("user", "pass")
auth_api.store_tokens(login_response.json())

# Access protected endpoint (uses stored access_token)
response = auth_api.get_protected()

# Refresh tokens
refresh_response = auth_api.refresh_token_request()
auth_api.store_tokens(refresh_response.json())
```

## 🧪 Test Modules

### 01_register_flow.py
Tests user registration:
- Valid registration (201)
- Duplicate username (409)
- Duplicate email (409)
- Validation errors (400)

### 02_login_flow.py
Tests login and tokens:
- Valid login with tokens (200)
- Invalid credentials (401)
- Token structure validation
- User data in response

### 03_refresh_token_flow.py
Tests token refresh:
- Refresh with valid token (200)
- New tokens are different
- Invalid refresh token (401)
- Malformed token (401)

### 04_protected_endpoints.py
Tests protected access:
- Access without token (401)
- Access with valid token (200)
- Access with invalid token (401)
- Profile endpoint access

## 🔧 Service Page Features

The `AuthApiPage` provides:

```python
# Authentication
register(username, email, password) -> APIResponse
login(username, password) -> APIResponse
refresh_token_request() -> APIResponse
logout() -> None

# Token management
store_tokens(response_data) -> None
get_auth_headers() -> Dict[str, str]

# Protected endpoints
get_protected() -> APIResponse
get_profile() -> APIResponse

# Utility
health_check() -> APIResponse
```

## 📝 Key Concepts

### JWT Token Structure

```json
{
  "user_id": 1,
  "username": "john_doe",
  "type": "access",
  "exp": 1704123456,
  "iat": 1704122556
}
```

### Authorization Header

Always use Bearer format:
```
Authorization: Bearer <jwt_token>
```

### Token Expiration

- Access tokens expire in 15 minutes
- Refresh tokens expire in 7 days
- Expired tokens return 401 Unauthorized

## 🐛 Troubleshooting

### Port 5001 in use

Change port in `api.py`:
```python
app.run(host='0.0.0.0', port=5002, debug=True)
```

Update `e2e.conf`:
```yaml
services:
  auth-api:
    base_url: http://localhost:5002
```

### Database reset

```bash
rm auth.db
python api.py  # Recreates with empty users
```

### Invalid token errors

Ensure you're using the correct token type:
- Access token for protected endpoints
- Refresh token for /api/auth/refresh

## 🎓 Learning Outcomes

After this example, you'll understand:

1. ✅ JWT authentication flow (access + refresh tokens)
2. ✅ Token storage and management in tests
3. ✅ Bearer token Authorization headers
4. ✅ Token refresh strategies
5. ✅ Testing authentication-required endpoints
6. ✅ Handling 401/403 responses

## 📚 Next Steps

- Combine with CRUD example for authenticated CRUD operations
- Implement token blacklisting (logout)
- Add role-based access control (RBAC)
- Explore refresh token rotation strategies

---

**Secure Testing!** 🔒
