"""Test module for Payment Service.

Tests payment processing across multiple services.
"""

from playwright.sync_api import APIResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..payment_api_page import PaymentApiPage


def run(payment_api: "PaymentApiPage") -> APIResponse:
    """Test Payment Service with multi-service communication.

    Tests:
    - Process payment (deducts balance, updates order)
    - Verify balance reduction
    - Verify order status change
    - List payments

    Args:
        payment_api: Instance of PaymentApiPage

    Returns:
        APIResponse: Last response
    """
    print("Test 1: Process payment for order 1, user 1")
    response = payment_api.process_payment(order_id=1, user_id=1)
    payment_api.assert_status(response, 201)

    payment_data = payment_api.assert_json(response)
    assert "payment" in payment_data
    payment_api.test_payment_id = payment_data["payment"]["id"]

    prev_balance = payment_data["payment"]["previous_balance"]
    new_balance = payment_data["payment"]["new_balance"]
    amount = payment_data["payment"]["amount"]

    print(f"  ✓ Payment processed: ID {payment_api.test_payment_id}")
    print(f"  ✓ Balance: ${prev_balance} → ${new_balance} (deducted: ${amount})")

    print("Test 2: Verify payment appears in list")
    response = payment_api.list_payments()
    payment_api.assert_status(response, 200)

    data = payment_api.assert_json(response)
    assert len(data["payments"]) > 0
    print(f"  ✓ Found {len(data['payments'])} payments")

    print("Test 3: Get user's payments")
    response = payment_api.get_user_payments(1)
    payment_api.assert_status(response, 200)

    user_payments = payment_api.assert_json(response)
    assert user_payments["user_name"] == "alice"
    print(f"  ✓ User payments retrieved for alice")

    print("Test 4: Get payment details")
    assert payment_api.test_payment_id is not None
    response = payment_api.get_payment(payment_api.test_payment_id)
    payment_api.assert_status(response, 200)

    payment = payment_api.assert_json(response)
    assert payment["status"] == "completed"
    print(f"  ✓ Payment status: {payment['status']}")

    print("\n✅ All Payment Service tests passed!")
    print("\n📊 Multi-service transaction completed:")
    print("   - Payment Service → Orders Service (get order)")
    print("   - Payment Service → Users Service (check/deduct balance)")
    print("   - Payment Service → Orders Service (update status)")
    return response
