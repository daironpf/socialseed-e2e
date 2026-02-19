"""Mock API module for E2E testing.

This module provides a Flask-based mock API server for testing.

Usage:
    from socialseed_e2e.mock_api import MockAPIServer

    server = MockAPIServer(port=8765)
    server.run()
"""

from .server import MockAPIServer

__all__ = ["MockAPIServer"]
