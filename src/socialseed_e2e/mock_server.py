"""Mock API Server for E2E Testing.

This module provides a simple Flask-based mock API server that can be used
for testing without a real backend.

Usage:
    python -m socialseed_e2e.mock_server

The server runs on port 8765 by default.
"""

from socialseed_e2e.mock_api import MockAPIServer


def main():
    """Run the mock API server."""
    server = MockAPIServer(port=8765)
    print(f"🚀 Mock API Server running at http://localhost:{server.port}")
    print("📋 Available endpoints:")
    print("   GET    /health           - Health check")
    print("   GET    /api/users        - List users")
    print("   POST   /api/users        - Create user")
    print("   GET    /api/users/{id}   - Get user")
    print("   PUT    /api/users/{id}  - Update user")
    print("   DELETE /api/users/{id}   - Delete user")
    print("   POST   /api/auth/login   - Login")
    print("   POST   /api/auth/register - Register")
    print("\nPress Ctrl+C to stop")
    server.app.run(host="0.0.0.0", port=server.port, debug=False)


if __name__ == "__main__":
    main()
