"""Provider-side contract verification for socialseed-e2e."""

import json
import requests
from typing import Any, Dict, List, Optional
from socialseed_e2e.core.base_page import BasePage


class ProviderVerifier:
    """Verifies that a provider satisfies its contracts."""

    def __init__(self, provider_url: str):
        self.provider_url = provider_url
        self.results = []

    def verify_contract(self, contract_path: str) -> bool:
        """Load and verify a contract file."""
        with open(contract_path, "r") as f:
            contract_data = json.load(f)

        print(f"\n🔍 Verifying contract: {contract_data['consumer']} -> {contract_data['provider']}")
        
        all_passed = True
        for interaction in contract_data["interactions"]:
            success = self._verify_interaction(interaction)
            if not success:
                all_passed = False
        
        return all_passed

    def _verify_interaction(self, interaction: Dict[str, Any]) -> bool:
        """Verify a single interaction."""
        desc = interaction["description"]
        req = interaction["request"]
        expected_res = interaction["response"]

        print(f"  - Interaction: {desc}")
        
        url = f"{self.provider_url}{req['path']}"
        method = req["method"]
        
        try:
            # Replay request
            response = requests.request(
                method=method,
                url=url,
                headers=req["headers"],
                json=req["body"],
                timeout=10
            )

            # Verification logic
            errors = []
            
            # Status check
            if response.status_code != expected_res["status"]:
                errors.append(f"Expected status {expected_res['status']}, got {response.status_code}")

            # Body check (basic equality for now)
            if expected_res["body"] is not None:
                actual_body = response.json() if response.content else None
                if actual_body != expected_res["body"]:
                    errors.append(f"Body mismatch. Expected: {expected_res['body']}, Got: {actual_body}")

            if not errors:
                print("    ✅ Passed")
                return True
            else:
                for err in errors:
                    print(f"    ❌ Failed: {err}")
                return False

        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            return False
