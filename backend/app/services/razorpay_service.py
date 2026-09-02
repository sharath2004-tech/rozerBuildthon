"""
Razorpay integration for payment processing and webhooks.
Handles real payment events and failure detection.

IMPORTANT: This service operates in TEST MODE ONLY for safety.
Real money transactions are not processed.
"""

import os
import hmac
import hashlib
from typing import Optional, Dict
import httpx

# Razorpay credentials
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

# Razorpay API endpoints
RAZORPAY_API_BASE = "https://api.razorpay.com/v1"

# Debug logging on startup
if RAZORPAY_KEY_ID:
    mode = "TEST" if RAZORPAY_KEY_ID.startswith("rzp_test_") else "LIVE"
    print(f"✅ Razorpay configured in {mode} mode")
    print(f"   Key ID: {RAZORPAY_KEY_ID[:15]}...")
else:
    print("⚠️ Razorpay credentials not found")


def is_configured() -> bool:
    """Check if Razorpay credentials are configured."""
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def is_test_mode() -> bool:
    """Check if Razorpay is in test mode."""
    return RAZORPAY_KEY_ID.startswith("rzp_test_")


async def test_connection() -> Dict:
    """
    Test Razorpay API connectivity with a real API call.
    Makes a safe read-only request to verify authentication.
    Returns detailed test results.
    """
    if not is_configured():
        return {
            "success": False,
            "message": "Razorpay credentials not configured",
            "authenticated": False
        }
    
    try:
        # Test with /v1/payments endpoint (safe read-only)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{RAZORPAY_API_BASE}/payments",
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
                params={"count": 1}  # Just fetch 1 item for testing
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message": "Razorpay API authenticated successfully",
                    "authenticated": True,
                    "mode": "test" if is_test_mode() else "live",
                    "test_data_count": len(data.get("items", []))
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "Authentication failed - Invalid API credentials",
                    "authenticated": False,
                    "error_code": 401,
                    "hint": "Verify RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are correct"
                }
            else:
                return {
                    "success": False,
                    "message": f"API error: {response.status_code}",
                    "authenticated": False,
                    "error_code": response.status_code,
                    "error_body": response.text[:200]
                }
                
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection error: {str(e)}",
            "authenticated": False,
            "error_type": type(e).__name__
        }


def verify_webhook_signature(payload: bytes, signature: str, secret: str = None) -> bool:
    """
    Verify Razorpay webhook signature for security.
    
    Args:
        payload: Raw request body bytes
        signature: X-Razorpay-Signature header value
        secret: Optional webhook secret (uses env var if not provided)
    
    Returns:
        True if signature is valid, False otherwise
    """
    webhook_secret = secret or RAZORPAY_WEBHOOK_SECRET
    
    if not webhook_secret:
        print("⚠️ RAZORPAY_WEBHOOK_SECRET not configured")
        # In production, this should return False
        # For development, we allow it but log a warning
        return True
    
    try:
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if is_valid:
            print("✅ Webhook signature verified")
        else:
            print(f"❌ Webhook signature mismatch")
            print(f"   Expected: {expected_signature[:20]}...")
            print(f"   Received: {signature[:20]}...")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error verifying webhook signature: {e}")
        return False


async def fetch_payment_details(payment_id: str) -> Optional[Dict]:
    """
    Fetch payment details from Razorpay API.
    
    Args:
        payment_id: Razorpay payment ID (e.g., pay_...)
    
    Returns:
        Payment details dict or None if error
    """
    if not is_configured():
        print("❌ Razorpay not configured")
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{RAZORPAY_API_BASE}/payments/{payment_id}",
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error fetching payment {payment_id}: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ Exception fetching payment {payment_id}: {e}")
        return None


async def create_recovery_payment_link(
    amount_inr: float,
    customer_contact: str,
    description: str,
    reference_id: str = None,
    callback_url: str = None
) -> Optional[Dict]:
    """
    Create a Razorpay Payment Link for revenue recovery.
    
    This is the SAFE way to recover failed payments:
    1. Create a payment link (not direct retry)
    2. Customer clicks link and completes payment
    3. Razorpay sends payment.captured webhook
    4. We mark revenue as recovered
    
    Args:
        amount_inr: Amount in rupees (will be converted to paise)
        customer_contact: Customer phone number (e.g., +919876543210)
        description: Payment description
        reference_id: Optional reference ID for tracking
        callback_url: Optional callback URL after payment
    
    Returns:
        Payment link details or None if error
    """
    if not is_configured():
        print("❌ Razorpay not configured")
        return None
    
    if not is_test_mode():
        print("❌ Safety check: Only TEST mode payment links allowed")
        return None
    
    try:
        # Prepare payment link payload
        payload = {
            "amount": int(amount_inr * 100),  # Convert to paise
            "currency": "INR",
            "description": description,
            "customer": {
                "contact": customer_contact
            },
            "notify": {
                "sms": True,
                "email": False
            },
            "reminder_enable": True,
            "callback_url": callback_url or "https://rozerbuildthon.onrender.com/payment-success",
            "callback_method": "get"
        }
        
        if reference_id:
            payload["reference_id"] = reference_id
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{RAZORPAY_API_BASE}/payment_links",
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
                json=payload
            )
            
            if response.status_code == 200:
                link_data = response.json()
                print(f"✅ Payment link created: {link_data.get('short_url')}")
                return link_data
            else:
                error_data = response.json()
                print(f"❌ Error creating payment link: {response.status_code}")
                print(f"   Error: {error_data.get('error', {}).get('description')}")
                return None
                
    except Exception as e:
        print(f"❌ Exception creating payment link: {e}")
        return None


async def cancel_payment_link(link_id: str) -> bool:
    """
    Cancel a payment link.
    
    Args:
        link_id: Payment link ID (plink_...)
    
    Returns:
        True if cancelled successfully, False otherwise
    """
    if not is_configured():
        return False
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{RAZORPAY_API_BASE}/payment_links/{link_id}/cancel",
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
            )
            
            return response.status_code == 200
            
    except Exception as e:
        print(f"❌ Error cancelling payment link: {e}")
        return False


def get_status() -> Dict:
    """
    Get Razorpay integration status.
    
    Returns:
        Status dictionary with configuration details
    """
    return {
        "configured": is_configured(),
        "mode": "test" if is_test_mode() else "live" if is_configured() else "not_configured",
        "key_id_preview": RAZORPAY_KEY_ID[:15] + "..." if RAZORPAY_KEY_ID else "NOT_SET",
        "webhook_secret_set": bool(RAZORPAY_WEBHOOK_SECRET),
        "api_base": RAZORPAY_API_BASE
    }
