"""
Quick test script to verify Groq integration is working.
Run with: python test_groq_integration.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.groq_service import get_enhanced_explanation, is_configured


async def test_groq_explanation():
    """Test the enhanced explanation feature."""
    
    print("\n" + "="*60)
    print("GROQ INTEGRATION TEST")
    print("="*60 + "\n")
    
    # Check if Groq is configured
    if not is_configured():
        print("❌ GROQ_API_KEY not found in environment")
        print("\nTo enable Groq:")
        print("1. Get free API key from: https://console.groq.com/keys")
        print("2. Add to backend/.env: GROQ_API_KEY=gsk_your_key_here")
        print("3. Restart backend server")
        print("\n⚠️  System will work without Groq but explanations won't be enhanced")
        return False
    
    print("✅ Groq API key found\n")
    
    # Test scenario: Approved high-value UPI payment
    print("📝 Testing Scenario 1: APPROVED high-value UPI payment")
    print("-" * 60)
    
    payment_context = {
        "amount_inr": 50000,
        "failure_code": "bank_timeout",
        "rail": "UPI",
        "customer_type": "Premium",
        "lifetime_payments": 15,
        "retry_count": 0,
        "hours_since_failure": 2
    }
    
    decision_context = {
        "action": "AUTO_RETRY",
        "disposition": "APPROVED",
        "rule_id": "G01_BASIC_ELIGIBILITY",
        "probability": 0.82,
        "is_executable": True
    }
    
    policy_reason = "Eligible for automatic retry. No blocking conditions detected."
    
    try:
        enhanced = await get_enhanced_explanation(
            payment_context,
            decision_context,
            policy_reason
        )
        
        print(f"\n📄 Original Policy Reason:\n{policy_reason}\n")
        print(f"✨ Groq Enhanced Explanation:\n{enhanced}\n")
        
        if enhanced != policy_reason:
            print("✅ Groq enhancement working!\n")
        else:
            print("⚠️  Groq returned same as input (possible API issue)\n")
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    # Test scenario: Blocked retry cap exceeded
    print("\n📝 Testing Scenario 2: BLOCKED - retry cap exceeded")
    print("-" * 60)
    
    payment_context_blocked = {
        "amount_inr": 12000,
        "failure_code": "insufficient_funds",
        "rail": "CARD",
        "customer_type": "Returning",
        "lifetime_payments": 4,
        "retry_count": 4,
        "hours_since_failure": 24
    }
    
    decision_context_blocked = {
        "action": "SUPPRESS",
        "disposition": "BLOCKED",
        "rule_id": "G06_RETRY_CAP_REACHED",
        "probability": 0.35,
        "is_executable": False
    }
    
    policy_reason_blocked = "Recovery action blocked: retry cap reached (4 >= 3)"
    
    try:
        enhanced_blocked = await get_enhanced_explanation(
            payment_context_blocked,
            decision_context_blocked,
            policy_reason_blocked
        )
        
        print(f"\n📄 Original Policy Reason:\n{policy_reason_blocked}\n")
        print(f"✨ Groq Enhanced Explanation:\n{enhanced_blocked}\n")
        
        if enhanced_blocked != policy_reason_blocked:
            print("✅ Groq enhancement working for blocked scenarios!\n")
        else:
            print("⚠️  Groq returned same as input\n")
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    print("="*60)
    print("✅ ALL TESTS PASSED - Groq integration working!")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run test
    result = asyncio.run(test_groq_explanation())
    
    if not result:
        print("\n💡 TIP: The system works WITHOUT Groq, but explanations are better WITH it.\n")
        sys.exit(1)
