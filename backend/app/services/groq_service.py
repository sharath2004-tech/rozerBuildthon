"""
Groq AI integration for LLM-powered recovery recommendations.
Uses Groq's fast inference for real-time decision support.
"""

import os
import httpx
from typing import Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b""  # Production model

# Debug: Print on startup
if GROQ_API_KEY:
    print(f"✅ Groq API key loaded: {GROQ_API_KEY[:15]}...")
    print(f"📦 Using Groq model: {GROQ_MODEL}")
else:
    print("⚠️ GROQ_API_KEY not found in environment")


async def get_recovery_recommendation(
    payment_id: str,
    amount_inr: float,
    failure_code: str,
    customer_history: dict
) -> Optional[dict]:
    """
    Get AI-powered recovery recommendation from Groq.
    Returns suggested action, reasoning, and confidence score.
    """
    if not GROQ_API_KEY:
        return None
    
    prompt = f"""You are a revenue recovery AI agent. Analyze this failed payment and recommend the best recovery action.

Payment Details:
- Payment ID: {payment_id}
- Amount: ₹{amount_inr:,.2f}
- Failure Code: {failure_code}
- Customer Lifetime Payments: {customer_history.get('lifetime_payments', 0)}
- Previous Recoveries: {customer_history.get('lifetime_recoveries', 0)}
- Hours Since Failure: {customer_history.get('hours_since_failure', 0)}

Available Actions:
1. AUTO_RETRY - Automatically retry the payment (low risk)
2. SEND_PAYMENT_LINK - Send customer a payment link via SMS
3. VOICE_CALL - Initiate voice call for high-value payments
4. MANUAL_REVIEW - Escalate to human review
5. SUPPRESS - Do not attempt recovery (fraud/permanent failure)

Respond in JSON format:
{
  "action": "one of the actions above",
  "reason": "brief explanation why this action is recommended",
  "confidence": 0.85,
  "alternate_action": "backup action if primary fails"
}"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a revenue recovery expert. Always respond in valid JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 256
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Parse JSON from response
                import json
                recommendation = json.loads(content)
                return recommendation
            else:
                error_body = response.text
                print(f"❌ Groq API error {response.status_code}: {error_body}")
                return None
                
    except Exception as e:
        print(f"❌ Error calling Groq API: {type(e).__name__}: {e}")
        return None


def is_configured() -> bool:
    """Check if Groq is properly configured."""
    return GROQ_API_KEY is not None


def get_provider_status() -> dict:
    """Get Groq provider status for dashboard."""
    return {
        "provider": "Groq",
        "model": GROQ_MODEL,
        "configured": is_configured(),
        "status": "active" if is_configured() else "not_configured"
    }
