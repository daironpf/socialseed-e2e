"""Tests for Authentication Module.

This module tests the enterprise authentication features.
"""

import pytest
from unittest.mock import Mock, patch

from socialseed_e2e.auth import (
    APIKeyAuth,
    APIKeyConfig,
    AuthSuite,
    AuthenticationError,
    GrantType,
    JWTClaims,
    JWTValidator,
    MTLSAuth,
    MTLSConfig,
    OAuth2Client,
    OAuth2Config,
    TokenResponse,
    TokenType,
)


class TestTokenResponse:
    """Tests for TokenResponse."""

    def test_initialization(self):
        """Test token response initialization."""
        token = TokenResponse(access_token="test_token")
        assert token.access_token == "test_token"
        assert token.token_type == TokenType.BEARER
        assert token.expires_in == 3600

    def test_is_expired_false(self):
        """Test token not expired."""
        import datetime
        from socialseed_e2e.auth import datetime as auth_datetime

        token = TokenResponse(
            access_token="test", expires_in=3600, obtained_at=auth_datetime.now()
        )
        assert token.is_expired is False


class TestOAuth2Config:
    """Tests for OAuth2Config."""

    def test_initialization(self):
        """Test OAuth2 config initialization."""
        config = OAuth2Config(
            client_id="my_client",
            client_secret="my_secret",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
        )
        assert config.client_id == "my_client"
        assert config.client_secret == "my_secret"


class TestOAuth2Client:
    """Tests for OAuth2Client."""

    def test_initialization(self):
        """Test OAuth2 client initialization."""
        config = OAuth2Config(
            client_id="my_client",
            client_secret="my_secret",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
        )
        client = OAuth2Client(config)
        assert client.config == config

    def test_get_authorization_url(self):
        """Test getting authorization URL."""
        config = OAuth2Config(
            client_id="my_client",
            client_secret="my_secret",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
            redirect_uri="http://localhost:8080/callback",
        )
        client = OAuth2Client(config)

        url = client.get_authorization_url(state="test_state")
        assert "client_id=my_client" in url
        assert "response_type=code" in url
        assert "state=test_state" in url


class TestAPIKeyAuth:
    """Tests for APIKeyAuth."""

    def test_initialization(self):
        """Test API key auth initialization."""
        config = APIKeyConfig(key="my_key")
        auth = APIKeyAuth(config)
        assert auth.config.key == "my_key"

    def test_get_headers(self):
        """Test getting headers."""
        config = APIKeyConfig(key="my_key", header_name="X-API-Key")
        auth = APIKeyAuth(config)

        headers = auth.get_headers()
        assert headers["X-API-Key"] == "my_key"

    def test_add_to_url(self):
        """Test adding API key to URL."""
        config = APIKeyConfig(key="my_key", query_param="api_key")
        auth = APIKeyAuth(config)

        url = auth.add_to_url("https://api.example.com/users")
        assert "api_key=my_key" in url


class TestMTLSAuth:
    """Tests for MTLSAuth."""

    def test_initialization(self):
        """Test mTLS auth initialization."""
        config = MTLSConfig(cert_path="/path/to/cert.pem", key_path="/path/to/key.pem")
        auth = MTLSAuth(config)
        assert auth.config.cert_path == "/path/to/cert.pem"


class TestJWTValidator:
    """Tests for JWTValidator."""

    def test_initialization(self):
        """Test JWT validator initialization."""
        validator = JWTValidator(secret="my_secret")
        assert validator.secret == "my_secret"

    def test_extract_bearer_token(self):
        """Test extracting bearer token."""
        validator = JWTValidator()
        token = validator.extract_bearer_token("Bearer my_token")
        assert token == "my_token"

    def test_extract_bearer_token_invalid(self):
        """Test extracting invalid bearer token."""
        validator = JWTValidator()
        token = validator.extract_bearer_token("Basic my_token")
        assert token is None


class TestJWTClaims:
    """Tests for JWTClaims."""

    def test_initialization(self):
        """Test JWT claims initialization."""
        claims = JWTClaims(sub="user123", iss="auth.example.com")
        assert claims.sub == "user123"
        assert claims.iss == "auth.example.com"


class TestAuthSuite:
    """Tests for AuthSuite."""

    def test_initialization(self):
        """Test auth suite initialization."""
        suite = AuthSuite()
        assert suite is not None

    def test_create_oauth2_client(self):
        """Test creating OAuth2 client."""
        suite = AuthSuite()
        config = OAuth2Config(
            client_id="my_client",
            client_secret="my_secret",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
        )

        client = suite.create_oauth2_client(config)
        assert isinstance(client, OAuth2Client)
        assert len(suite.oauth_clients) == 1

    def test_create_api_key_auth(self):
        """Test creating API key auth."""
        suite = AuthSuite()
        auth = suite.create_api_key_auth("my_key")

        assert isinstance(auth, APIKeyAuth)
        assert len(suite.api_key_auths) == 1

    def test_create_jwt_validator(self):
        """Test creating JWT validator."""
        suite = AuthSuite()
        validator = suite.create_jwt_validator("my_secret")

        assert isinstance(validator, JWTValidator)
        assert len(suite.jwt_validators) == 1


class TestGrantType:
    """Tests for GrantType enum."""

    def test_grant_types(self):
        """Test grant types."""
        assert GrantType.AUTHORIZATION_CODE.value == "authorization_code"
        assert GrantType.CLIENT_CREDENTIALS.value == "client_credentials"
        assert (
            GrantType.DEVICE_CODE.value
            == "urn:ietf:params:oauth:grant-type:device_code"
        )
        assert GrantType.REFRESH_TOKEN.value == "refresh_token"


class TestTokenType:
    """Tests for TokenType enum."""

    def test_token_types(self):
        """Test token types."""
        assert TokenType.BEARER.value == "Bearer"
        assert TokenType.MAC.value == "MAC"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_error(self):
        """Test authentication error."""
        error = AuthenticationError("Test error")
        assert str(error) == "Test error"
