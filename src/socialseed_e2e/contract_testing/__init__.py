"""Consumer-Driven Contract Testing for socialseed-e2e.

Ensures that API consumers and providers stay compatible by defining
and verifying contracts.
"""

from .consumer import ConsumerContract
from .provider import ProviderVerifier
from .registry import LocalContractRegistry

__all__ = ["ConsumerContract", "ProviderVerifier", "LocalContractRegistry"]
