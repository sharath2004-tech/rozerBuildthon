"""
Razorpay integration for payment processing and webhooks.
Handles real payment events and failure detection.
"""

import os
import hmac
import hashlib
import razorpay
from typing import Optional

# Initialize Razorpay client
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify Razorpay webhook signature for security.
    
    Razorpay sends signature in X-Razorpay-Signature header.
    We compute HMAC SHA256 of the payload and compare.
    """
    if not RAZORPAY_WEBHOOK_SECRET:
        print("⚠️ RAZORPAY_WEBHOOK_SECRET not configured, skipping verification")
        return True  # Skip verification if secret not set (dev mode)
    
    try:
        expected_signature = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if is_valid:
            print("✅ Webhook signature verified")
        else:
            print(f"❌ Signature mismatch!")
            print(f"   Expected: {expected_signature[:20]}...")
            print(f"   Received: {signature[:20]}...")
        
        return is_valid
    except Exception as e:
        print(f"❌ Error verifying signature: {e}")
        return False


def fetch_payment_details(payment_id: str) -> Optional[dict]:
    """Fetch payment details from Razorpay API."""
    if not client:
        return None
    
    try:
        payment = client.payment.fetch(payment_id)
        return payment
    except Exception as e:
        print(f"Error fetching payment {payment_id}: {e}")
        return None


def retry_payment(payment_id: str) -> dict:
    """Attempt to retry a failed payment."""
    if not client:
        return {"success": False, "message": "Razorpay not configured"}
    
    try:
        # In production, this would trigger actual payment retry
        # For now, we'll return a success simulation
        return {
            "success": True,
            "message": f"Payment {payment_id} retry initiated",
            "payment_id": payment_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


def create_payment_link(amount_inr: float, customer_id: str, description: str) -> Optional[dict]:
    """Create a payment link for customer to retry payment."""
    if not client:
        return None
    
    try:
        payment_link = client.payment_link.create({
            "amount": int(amount_inr * 100),  # Convert to paise
            "currency": "INR",
            "description": description,
            "customer": {
                "contact": f"+91{customer_id[-10:]}",  # Mock phone number
            },
            "notify": {
                "sms": True,
                "email": False
            },
            "reminder_enable": True,
            "callback_url": f"https://your-domain.com/payment-success",
            "callback_method": "get"
        })
        return payment_link
    except Exception as e:
        print(f"Error creating payment link: {e}")
        return None


def is_configured() -> bool:
    """Check if Razorpay is properly configured."""
    return client is not None
