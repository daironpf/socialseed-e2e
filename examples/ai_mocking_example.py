"""Example: Using AI Mocking for External APIs.

This example demonstrates how to use the AI Mocking system
to test code that depends on external APIs without requiring
real API keys or internet connectivity.
"""

import os
import requests
from typing import Dict, Any


class PaymentService:
    """Service that integrates with Stripe for payments."""

    def __init__(self):
        self.base_url = os.getenv("STRIPE_BASE_URL", "https://api.stripe.com")
        self.api_key = os.getenv("STRIPE_SECRET_KEY")

    def create_customer(self, email: str, name: str = None) -> Dict[str, Any]:
        """Create a new Stripe customer."""
        response = requests.post(
            f"{self.base_url}/v1/customers",
            headers={"Authorization": f"Bearer {self.api_key}"},
            data={"email": email, "name": name} if name else {"email": email},
        )
        response.raise_for_status()
        return response.json()

    def create_payment_intent(
        self, amount: int, currency: str = "usd"
    ) -> Dict[str, Any]:
        """Create a payment intent."""
        response = requests.post(
            f"{self.base_url}/v1/payment_intents",
            headers={"Authorization": f"Bearer {self.api_key}"},
            data={
                "amount": amount,
                "currency": currency,
                "automatic_payment_methods[enabled]": "true",
            },
        )
        response.raise_for_status()
        return response.json()


class GeocodingService:
    """Service that integrates with Google Maps for geocoding."""

    def __init__(self):
        self.base_url = os.getenv("MAPS_BASE_URL", "https://maps.googleapis.com")
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    def geocode_address(self, address: str) -> Dict[str, Any]:
        """Convert address to coordinates."""
        response = requests.get(
            f"{self.base_url}/maps/api/geocode/json",
            params={"address": address, "key": self.api_key},
        )
        response.raise_for_status()
        return response.json()

    def get_directions(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get directions between two locations."""
        response = requests.get(
            f"{self.base_url}/maps/api/directions/json",
            params={
                "origin": origin,
                "destination": destination,
                "key": self.api_key,
            },
        )
        response.raise_for_status()
        return response.json()


# Example usage in E2E tests
if __name__ == "__main__":
    # When running with mocks, set these environment variables:
    # export STRIPE_BASE_URL=http://localhost:8001
    # export MAPS_BASE_URL=http://localhost:8002
    # export STRIPE_SECRET_KEY=sk_test_mock
    # export GOOGLE_MAPS_API_KEY=mock_key

    print("Testing with mock servers...")

    # Test payment service
    payment = PaymentService()

    try:
        customer = payment.create_customer("test@example.com", "Test User")
        print(f"✅ Created customer: {customer['id']}")

        intent = payment.create_payment_intent(2000, "usd")
        print(f"✅ Created payment intent: {intent['id']}")
        print(f"   Status: {intent['status']}")
        print(f"   Client Secret: {intent['client_secret'][:20]}...")
    except Exception as e:
        print(f"❌ Payment service error: {e}")

    # Test geocoding service
    geocoding = GeocodingService()

    try:
        result = geocoding.geocode_address("1600 Amphitheatre Parkway")
        print(f"\n✅ Geocoded address")
        print(f"   Status: {result['status']}")
        if result["results"]:
            location = result["results"][0]["geometry"]["location"]
            print(f"   Coordinates: {location['lat']}, {location['lng']}")
    except Exception as e:
        print(f"❌ Geocoding service error: {e}")

    print("\n✨ All tests completed!")
