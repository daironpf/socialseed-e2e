# Authentication & JWT Example

This example demonstrates JWT authentication testing.

## Running the Example

```bash
cd examples/02-auth-jwt
pip install -r requirements.txt
python api.py &
e2e run
```

## API Description

The example API provides:
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `GET /api/protected` - Protected endpoint

## Tests Included

1. Register user test
2. Login test
3. Token refresh test
4. Access protected endpoint test

## Key Concepts

- Token storage in service page
- Authenticated requests
- Token refresh flow

See the `tests/` directory for implementation details.
