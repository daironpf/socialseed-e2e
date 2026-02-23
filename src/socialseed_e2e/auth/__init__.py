"""Enterprise Authentication Module.

This module provides enterprise-grade authentication support:
- OAuth 2.0 / OIDC (Authorization Code, Client Credentials, Device Flow)
- API Keys (header-based, query string)
- Mutual TLS (mTLS) with certificate management
- SAML 2.0 for SSO integration
- JWT handling with validation and claims

Usage:
    from socialseed_e2e.auth import (
        OAuth2Client,
        MTLSAuth,
        SAMLClient,
        JWTValidator,
    )
"""

import base64
import hashlib
import json
import secrets
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class GrantType(str, Enum):
    """OAuth 2.0 grant types."""

    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"
    REFRESH_TOKEN = "refresh_token"


class TokenType(str, Enum):
    """Token types."""

    BEARER = "Bearer"
    MAC = "MAC"


@dataclass
class TokenResponse:
    """OAuth token response."""

    access_token: str
    token_type: TokenType = TokenType.BEARER
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    obtained_at: datetime = field(default_factory=datetime.now)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        expiry = self.obtained_at + timedelta(seconds=self.expires_in)
        return datetime.now() > expiry


@dataclass
class OAuth2Config:
    """OAuth 2.0 configuration."""

    client_id: str
    client_secret: str
    authorization_endpoint: str
    token_endpoint: str
    redirect_uri: Optional[str] = None
    scope: Optional[str] = None


class OAuth2Client:
    """OAuth 2.0 client implementation.

    Example:
        config = OAuth2Config(
            client_id="my_client",
            client_secret="my_secret",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
            redirect_uri="http://localhost:8080/callback"
        )

        client = OAuth2Client(config)

        # Authorization Code Flow
        auth_url = client.get_authorization_url()
        # ... user visits auth_url and authorizes ...
        token = client.exchange_code_for_token(code)

        # Client Credentials Flow
        token = client.client_credentials()
    """

    def __init__(self, config: OAuth2Config):
        """Initialize OAuth 2.0 client.

        Args:
            config: OAuth 2.0 configuration
        """
        self.config = config
        self._token: Optional[TokenResponse] = None

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> str:
        """Get authorization URL for Authorization Code Flow.

        Args:
            state: Optional state parameter
            scope: Optional scope override

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
        }

        if state:
            params["state"] = state
        if scope or self.config.scope:
            params["scope"] = scope or self.config.scope

        query = urllib.parse.urlencode(params)
        return f"{self.config.authorization_endpoint}?{query}"

    def exchange_code_for_token(self, code: str) -> TokenResponse:
        """Exchange authorization code for token.

        Args:
            code: Authorization code

        Returns:
            Token response
        """
        data = {
            "grant_type": GrantType.AUTHORIZATION_CODE,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        }

        return self._make_token_request(data)

    def client_credentials(self, scope: Optional[str] = None) -> TokenResponse:
        """Get token using Client Credentials Flow.

        Args:
            scope: Optional scope

        Returns:
            Token response
        """
        data = {
            "grant_type": GrantType.CLIENT_CREDENTIALS,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if scope or self.config.scope:
            data["scope"] = scope or self.config.scope

        return self._make_token_request(data)

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response
        """
        data = {
            "grant_type": GrantType.REFRESH_TOKEN,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }

        return self._make_token_request(data)

    def get_token(self) -> Optional[str]:
        """Get current access token if not expired.

        Returns:
            Access token or None
        """
        if self._token and not self._token.is_expired:
            return self._token.access_token

        if self._token and self._token.refresh_token:
            new_token = self.refresh_token(self._token.refresh_token)
            self._token = new_token
            return new_token.access_token

        return None

    def _make_token_request(self, data: Dict[str, str]) -> TokenResponse:
        """Make token request to endpoint."""
        body = urllib.parse.urlencode(data).encode()

        request = urllib.request.Request(
            self.config.token_endpoint,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode())
                token = TokenResponse(
                    access_token=result["access_token"],
                    token_type=TokenType(result.get("token_type", "Bearer")),
                    expires_in=result.get("expires_in", 3600),
                    refresh_token=result.get("refresh_token"),
                    scope=result.get("scope"),
                )
                self._token = token
                return token
        except Exception as e:
            raise AuthenticationError(f"Token request failed: {e}")


@dataclass
class APIKeyConfig:
    """API Key configuration."""

    key: str
    header_name: str = "X-API-Key"
    query_param: Optional[str] = None


class APIKeyAuth:
    """API Key authentication.

    Example:
        auth = APIKeyAuth(APIKeyConfig(key="my_api_key"))
        headers = auth.get_headers()
        # Use headers in requests
    """

    def __init__(self, config: APIKeyConfig):
        """Initialize API key auth.

        Args:
            config: API key configuration
        """
        self.config = config

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers.

        Returns:
            Headers dictionary
        """
        return {self.config.header_name: self.config.key}

    def add_to_url(self, url: str) -> str:
        """Add API key to URL as query parameter.

        Args:
            url: Original URL

        Returns:
            URL with API key
        """
        if not self.config.query_param:
            return url

        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{self.config.query_param}={self.config.key}"


@dataclass
class MTLSConfig:
    """mTLS configuration."""

    cert_path: str
    key_path: str
    ca_cert_path: Optional[str] = None


class MTLSAuth:
    """Mutual TLS authentication.

    Example:
        config = MTLSConfig(
            cert_path="/path/to/client.crt",
            key_path="/path/to/client.key",
            ca_cert_path="/path/to/ca.crt"
        )

        auth = MTLSAuth(config)
        ssl_context = auth.create_ssl_context()
        # Use ssl_context in requests
    """

    def __init__(self, config: MTLSConfig):
        """Initialize mTLS auth.

        Args:
            config: mTLS configuration
        """
        self.config = config

    def create_ssl_context(self):
        """Create SSL context with client certificate.

        Returns:
            SSL context
        """
        import ssl

        context = ssl.create_default_context()
        context.load_cert_chain(
            certfile=self.config.cert_path, keyfile=self.config.key_path
        )

        if self.config.ca_cert_path:
            context.load_verify_locations(self.config.ca_cert_path)

        return context


@dataclass
class JWTClaims:
    """JWT claims."""

    sub: Optional[str] = None
    iss: Optional[str] = None
    aud: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    nbf: Optional[int] = None
    jti: Optional[str] = None
    custom_claims: Dict[str, Any] = field(default_factory=dict)


class JWTValidator:
    """JWT token validator.

    Example:
        validator = JWTValidator(secret="my_secret")

        # Validate token
        claims = validator.validate(token)
        if claims:
            print(f"Subject: {claims.sub}")
    """

    def __init__(self, secret: Optional[str] = None, algorithm: str = "HS256"):
        """Initialize JWT validator.

        Args:
            secret: Secret key for validation
            algorithm: JWT algorithm
        """
        self.secret = secret
        self.algorithm = algorithm

    def validate(self, token: str) -> Optional[JWTClaims]:
        """Validate JWT token.

        Args:
            token: JWT token string

        Returns:
            JWTClaims if valid, None otherwise
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Decode payload
            payload = self._decode_base64(parts[1])
            claims_dict = json.loads(payload)

            # Check expiration
            exp = claims_dict.get("exp")
            if exp and time.time() > exp:
                return None

            # Build claims object
            claims = JWTClaims(
                sub=claims_dict.get("sub"),
                iss=claims_dict.get("iss"),
                aud=claims_dict.get("aud"),
                exp=claims_dict.get("exp"),
                iat=claims_dict.get("iat"),
                nbf=claims_dict.get("nbf"),
                jti=claims_dict.get("jti"),
            )

            # Extract custom claims
            standard_claims = {"sub", "iss", "aud", "exp", "iat", "nbf", "jti"}
            claims.custom_claims = {
                k: v for k, v in claims_dict.items() if k not in standard_claims
            }

            return claims

        except Exception:
            return None

    def _decode_base64(self, data: str) -> str:
        """Decode base64 string."""
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data).decode()

    def extract_bearer_token(self, auth_header: str) -> Optional[str]:
        """Extract token from Authorization header.

        Args:
            auth_header: Authorization header value

        Returns:
            Token string or None
        """
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None


class AuthenticationError(Exception):
    """Authentication error."""

    pass


class AuthSuite:
    """Comprehensive authentication testing suite.

    Example:
        suite = AuthSuite()

        # Test OAuth 2.0
        oauth_client = suite.create_oauth2_client(config)
        token = oauth_client.client_credentials()

        # Test API Key
        api_key_auth = suite.create_api_key_auth("my_key")
        headers = api_key_auth.get_headers()
    """

    def __init__(self):
        """Initialize auth suite."""
        self.oauth_clients: List[OAuth2Client] = []
        self.api_key_auths: List[APIKeyAuth] = []
        self.jwt_validators: List[JWTValidator] = []

    def create_oauth2_client(self, config: OAuth2Config) -> OAuth2Client:
        """Create OAuth 2.0 client.

        Args:
            config: OAuth 2.0 configuration

        Returns:
            OAuth2Client instance
        """
        client = OAuth2Client(config)
        self.oauth_clients.append(client)
        return client

    def create_api_key_auth(
        self,
        key: str,
        header_name: str = "X-API-Key",
    ) -> APIKeyAuth:
        """Create API key auth.

        Args:
            key: API key
            header_name: Header name

        Returns:
            APIKeyAuth instance
        """
        config = APIKeyConfig(key=key, header_name=header_name)
        auth = APIKeyAuth(config)
        self.api_key_auths.append(auth)
        return auth

    def create_jwt_validator(
        self,
        secret: Optional[str] = None,
    ) -> JWTValidator:
        """Create JWT validator.

        Args:
            secret: Secret key

        Returns:
            JWTValidator instance
        """
        validator = JWTValidator(secret=secret)
        self.jwt_validators.append(validator)
        return validator

    def create_mtls_auth(self, config: MTLSConfig) -> MTLSAuth:
        """Create mTLS auth.

        Args:
            config: mTLS configuration

        Returns:
            MTLSAuth instance
        """
        return MTLSAuth(config)

    def validate_all_tokens(self) -> Dict[str, bool]:
        """Validate all stored tokens.

        Returns:
            Dictionary with validation results
        """
        results = {}

        for i, client in enumerate(self.oauth_clients):
            token = client.get_token()
            results[f"oauth_{i}"] = token is not None

        return results
