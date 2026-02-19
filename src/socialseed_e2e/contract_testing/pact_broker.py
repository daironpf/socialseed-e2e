"""Pact Broker Integration for contract testing.

This module provides integration with Pact Broker for publishing,
retrieving, and managing contracts in a centralized broker.

Example:
    >>> from socialseed_e2e.contract_testing import PactBrokerClient
    >>> broker = PactBrokerClient("https://pact-broker.example.com")
    >>> broker.publish_contract(contract_json, "consumer-app", "provider-api", "1.0.0")
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


@dataclass
class PactBrokerConfig:
    """Configuration for Pact Broker connection."""

    base_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 30

    def get_auth(self) -> Optional[Any]:
        """Get authentication object for requests."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        elif self.username and self.password:
            return HTTPBasicAuth(self.username, self.password)
        return None


@dataclass
class ContractVersion:
    """Represents a contract version in the broker."""

    consumer: str
    provider: str
    version: str
    created_at: datetime
    tags: List[str]
    branch: Optional[str] = None
    build_url: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VerificationResult:
    """Result of contract verification."""

    success: bool
    provider: str
    provider_version: str
    consumer: str
    consumer_version: str
    verification_date: datetime
    test_results: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CompatibilityResult:
    """Result of compatibility check between consumer and provider."""

    compatible: bool
    consumer: str
    consumer_version: str
    provider: str
    provider_version: str
    conflicts: List[Dict[str, Any]]
    summary: str


class PactBrokerClient:
    """Client for interacting with Pact Broker.

    Provides methods for:
    - Publishing contracts
    - Retrieving contracts
    - Tag-based versioning
    - Verification result publishing
    - Webhook management
    - Can-I-Deploy checks

    Attributes:
        config: PactBrokerConfig instance with connection details
    """

    def __init__(self, config: PactBrokerConfig):
        """Initialize Pact Broker client.

        Args:
            config: Configuration for broker connection
        """
        self.config = config
        self.session = requests.Session()
        self.session.verify = config.verify_ssl

        # Set up authentication
        auth = config.get_auth()
        if isinstance(auth, dict):
            self.session.headers.update(auth)
        elif auth:
            self.session.auth = auth

        logger.info(f"PactBrokerClient initialized for {config.base_url}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to broker.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            requests.RequestException: On request failure
        """
        url = urljoin(self.config.base_url, endpoint)
        kwargs.setdefault("timeout", self.config.timeout)
        kwargs.setdefault("headers", {"Content-Type": "application/json"})

        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def publish_contract(
        self,
        contract_content: str,
        consumer: str,
        provider: str,
        version: str,
        tags: Optional[List[str]] = None,
        branch: Optional[str] = None,
        build_url: Optional[str] = None,
    ) -> bool:
        """Publish a contract to the broker.

        Args:
            contract_content: Contract JSON content
            consumer: Consumer application name
            provider: Provider application name
            version: Contract version
            tags: Optional tags (e.g., "prod", "staging")
            branch: Git branch name
            build_url: URL to CI build

        Returns:
            True if published successfully

        Example:
            >>> broker.publish_contract(
            ...     contract_json,
            ...     "order-service",
            ...     "payment-service",
            ...     "1.2.3",
            ...     tags=["prod"]
            ... )
        """
        try:
            # Publish the contract
            endpoint = (
                f"/pacts/provider/{provider}/consumer/{consumer}/version/{version}"
            )

            response = self._make_request("PUT", endpoint, data=contract_content)

            # Add tags if specified
            if tags:
                for tag in tags:
                    self.tag_version(consumer, version, tag)

            # Record branch if specified
            if branch:
                self.record_branch(consumer, version, branch)

            logger.info(
                f"Published contract {consumer}->{provider} v{version} "
                f"with tags: {tags or []}"
            )
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to publish contract: {e}")
            return False

    def get_contract(
        self, consumer: str, provider: str, version: str = "latest"
    ) -> Optional[str]:
        """Retrieve a contract from the broker.

        Args:
            consumer: Consumer name
            provider: Provider name
            version: Contract version (default: latest)

        Returns:
            Contract JSON content or None if not found
        """
        try:
            endpoint = f"/pacts/provider/{provider}/consumer/{consumer}/{version}"
            response = self._make_request("GET", endpoint)
            return response.text

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Contract not found: {consumer}->{provider}@{version}")
                return None
            raise

    def get_latest_contract(
        self, consumer: str, provider: str, tag: Optional[str] = None
    ) -> Optional[str]:
        """Get latest contract, optionally filtered by tag.

        Args:
            consumer: Consumer name
            provider: Provider name
            tag: Optional tag to filter by

        Returns:
            Contract JSON content or None
        """
        if tag:
            endpoint = f"/pacts/provider/{provider}/consumer/{consumer}/latest/{tag}"
        else:
            endpoint = f"/pacts/provider/{provider}/consumer/{consumer}/latest"

        try:
            response = self._make_request("GET", endpoint)
            return response.text

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def tag_version(self, application: str, version: str, tag: str) -> bool:
        """Tag a contract version.

        Args:
            application: Application name (consumer or provider)
            version: Version to tag
            tag: Tag name

        Returns:
            True if successful
        """
        try:
            endpoint = f"/pacticipants/{application}/versions/{version}/tags/{tag}"
            self._make_request("PUT", endpoint)
            logger.info(f"Tagged {application}@{version} with '{tag}'")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to tag version: {e}")
            return False

    def record_branch(self, application: str, version: str, branch: str) -> bool:
        """Record the branch for a version.

        Args:
            application: Application name
            version: Version
            branch: Branch name

        Returns:
            True if successful
        """
        try:
            endpoint = (
                f"/pacticipants/{application}/versions/{version}/branches/{branch}"
            )
            self._make_request("PUT", endpoint)
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to record branch: {e}")
            return False

    def get_versions(
        self, application: str, tag: Optional[str] = None
    ) -> List[ContractVersion]:
        """Get all versions for an application.

        Args:
            application: Application name
            tag: Optional tag filter

        Returns:
            List of ContractVersion objects
        """
        try:
            if tag:
                endpoint = f"/pacticipants/{application}/latest-version/{tag}"
            else:
                endpoint = f"/pacticipants/{application}/versions"

            response = self._make_request("GET", endpoint)
            data = response.json()

            versions = []
            for version_data in data.get("versions", []):
                versions.append(
                    ContractVersion(
                        consumer=application,
                        provider="",  # Will be filled from pact data
                        version=version_data["number"],
                        created_at=datetime.fromisoformat(
                            version_data["createdAt"].replace("Z", "+00:00")
                        ),
                        tags=version_data.get("tags", []),
                        branch=version_data.get("branch"),
                        build_url=version_data.get("buildUrl"),
                    )
                )

            return versions

        except requests.RequestException as e:
            logger.error(f"Failed to get versions: {e}")
            return []

    def publish_verification_result(
        self,
        provider: str,
        provider_version: str,
        consumer: str,
        consumer_version: str,
        success: bool,
        test_results: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Publish verification result to broker.

        Args:
            provider: Provider name
            provider_version: Provider version
            consumer: Consumer name
            consumer_version: Consumer version
            success: Whether verification passed
            test_results: Detailed test results
            metadata: Additional metadata

        Returns:
            True if published successfully
        """
        try:
            endpoint = f"/pacts/provider/{provider}/consumer/{consumer}/pact-version/{consumer_version}/verification-results"

            payload = {
                "success": success,
                "providerApplicationVersion": provider_version,
                "testResults": test_results or [],
                "metadata": metadata or {},
            }

            response = self._make_request("POST", endpoint, json=payload)

            logger.info(
                f"Published verification result for {provider}@{provider_version} "
                f"against {consumer}@{consumer_version}: {'PASSED' if success else 'FAILED'}"
            )
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to publish verification result: {e}")
            return False

    def can_i_deploy(
        self,
        application: str,
        version: str,
        environment: str,
        target: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Check if an application version can be deployed.

        Implements the "can-i-deploy" check to ensure compatibility
        with all consumers/providers in the target environment.

        Args:
            application: Application name
            version: Version to check
            environment: Target environment
            target: Optional target application for bi-directional check

        Returns:
            Tuple of (can_deploy, reason)

        Example:
            >>> can_deploy, reason = broker.can_i_deploy(
            ...     "payment-service",
            ...     "1.2.3",
            ...     "production"
            ... )
            >>> if can_deploy:
            ...     print("Safe to deploy!")
        """
        try:
            endpoint = "/can-i-deploy"
            params = {
                "pacticipant": application,
                "version": version,
                "to": environment,
            }

            if target:
                params["target"] = target

            response = self._make_request("GET", endpoint, params=params)
            data = response.json()

            can_deploy = data.get("summary", {}).get("deployable", False)
            reason = data.get("summary", {}).get("reason", "")

            if not can_deploy:
                # Build detailed reason from conflicts
                conflicts = data.get("summary", {}).get("compatibilityCheck", [])
                if conflicts:
                    reason = "; ".join(
                        [
                            f"{c.get('consumer', '?')}@{c.get('consumerVersion', '?')} "
                            f"incompatible with {c.get('provider', '?')}@{c.get('providerVersion', '?')}"
                            for c in conflicts
                        ]
                    )

            logger.info(
                f"Can-I-Deploy check for {application}@{version} to {environment}: "
                f"{'YES' if can_deploy else 'NO'}"
            )

            return can_deploy, reason

        except requests.RequestException as e:
            logger.error(f"Can-I-Deploy check failed: {e}")
            return False, str(e)

    def check_compatibility(
        self,
        consumer: str,
        consumer_version: str,
        provider: str,
        provider_version: str,
    ) -> CompatibilityResult:
        """Check compatibility between specific consumer and provider versions.

        Args:
            consumer: Consumer name
            consumer_version: Consumer version
            provider: Provider name
            provider_version: Provider version

        Returns:
            CompatibilityResult with details
        """
        try:
            endpoint = (
                f"/compatibility/provider/{provider}/version/{provider_version}/"
                f"consumer/{consumer}/version/{consumer_version}"
            )

            response = self._make_request("GET", endpoint)
            data = response.json()

            return CompatibilityResult(
                compatible=data.get("compatible", False),
                consumer=consumer,
                consumer_version=consumer_version,
                provider=provider,
                provider_version=provider_version,
                conflicts=data.get("conflicts", []),
                summary=data.get("summary", ""),
            )

        except requests.RequestException as e:
            logger.error(f"Compatibility check failed: {e}")
            return CompatibilityResult(
                compatible=False,
                consumer=consumer,
                consumer_version=consumer_version,
                provider=provider,
                provider_version=provider_version,
                conflicts=[],
                summary=f"Error: {str(e)}",
            )

    def get_webhooks(self) -> List[Dict[str, Any]]:
        """Get all configured webhooks.

        Returns:
            List of webhook configurations
        """
        try:
            response = self._make_request("GET", "/webhooks")
            return response.json().get("webhooks", [])

        except requests.RequestException as e:
            logger.error(f"Failed to get webhooks: {e}")
            return []

    def create_webhook(
        self,
        webhook_url: str,
        description: str,
        events: List[str],
        consumer: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Optional[str]:
        """Create a new webhook.

        Args:
            webhook_url: URL to call
            description: Webhook description
            events: List of events (e.g., ["contract_content_changed"])
            consumer: Optional consumer filter
            provider: Optional provider filter

        Returns:
            Webhook ID if created successfully
        """
        try:
            payload = {
                "description": description,
                "enabled": True,
                "request": {
                    "method": "POST",
                    "url": webhook_url,
                    "headers": {"Content-Type": "application/json"},
                },
                "events": events,
            }

            if consumer:
                payload["consumer"] = {"name": consumer}
            if provider:
                payload["provider"] = {"name": provider}

            response = self._make_request("POST", "/webhooks", json=payload)
            webhook_id = response.json().get("uuid")

            logger.info(f"Created webhook {webhook_id}: {description}")
            return webhook_id

        except requests.RequestException as e:
            logger.error(f"Failed to create webhook: {e}")
            return None

    def get_matrix(
        self,
        consumer: Optional[str] = None,
        provider: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get the pact matrix showing all consumer-provider combinations.

        Args:
            consumer: Optional consumer filter
            provider: Optional provider filter
            tag: Optional tag filter

        Returns:
            Matrix data with compatibility information
        """
        try:
            params = {}
            if consumer:
                params["q[][pacticipant]"] = consumer
            if provider:
                params["q[][pacticipant]"] = provider
            if tag:
                params["q[][tag]"] = tag

            response = self._make_request("GET", "/matrix", params=params)
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Failed to get matrix: {e}")
            return {}
