"""
Groq AI integration for LLM-powered recovery recommendations.
Uses Groq's fast inference for real-time decision support.
"""

import os
import httpx
from typing import Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"  # Production model

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


async def get_enhanced_explanation(
    payment_context: dict,
    decision: dict,
    policy_reason: str
) -> str:
    """
    Generate enhanced natural language explanation for recovery decision using Groq.
    
    Args:
        payment_context: Payment details (amount, failure_code, customer info)
        decision: Decision details (action, disposition, rule_id, probability)
        policy_reason: Original deterministic policy reason
    
    Returns:
        Enhanced explanation or falls back to policy_reason if Groq unavailable
    """
    if not GROQ_API_KEY:
        return policy_reason
    
    # Build context for LLM
    prompt = f"""You are an AI explaining payment recovery decisions to merchants. Generate a clear, professional explanation.

**Payment Context:**
- Amount: ₹{payment_context.get('amount_inr', 0):,.2f}
- Failure Code: {payment_context.get('failure_code', 'unknown')}
- Payment Rail: {payment_context.get('rail', 'unknown')}
- Customer Type: {payment_context.get('customer_type', 'unknown')} ({payment_context.get('lifetime_payments', 0)} lifetime payments)
- Retry Attempts: {payment_context.get('retry_count', 0)}
- Hours Since Failure: {payment_context.get('hours_since_failure', 0)}

**Decision Made:**
- Action: {decision.get('action', 'SUPPRESS')}
- Disposition: {decision.get('disposition', 'BLOCKED')}
- Policy Rule: {decision.get('rule_id', 'UNKNOWN')}
- Recovery Probability: {decision.get('probability', 0) * 100:.0f}%
- Is Executable: {decision.get('is_executable', False)}

**Policy Reason (deterministic):**
{policy_reason}

Generate a 2-3 sentence explanation that:
1. Explains WHY this decision was made (based on the context)
2. What this means for the merchant
3. If blocked, explain the business/compliance reason clearly

Be conversational but professional. Focus on merchant value, not technical jargon.
Do NOT just repeat the policy reason - add context and insight."""

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
                        {
                            "role": "system", 
                            "content": "You are a helpful AI explaining payment recovery decisions. Be clear, concise, and merchant-focused."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 200
                },
                timeout=8.0
            )
            
            if response.status_code == 200:
                data = response.json()
                enhanced_explanation = data["choices"][0]["message"]["content"].strip()
                
                # Validate response is reasonable (not empty, not too long)
                if enhanced_explanation and len(enhanced_explanation) > 20:
                    print(f"✅ Groq enhanced explanation generated ({len(enhanced_explanation)} chars)")
                    return enhanced_explanation
                else:
                    print(f"⚠️ Groq response too short, using fallback")
                    return policy_reason
            else:
                print(f"⚠️ Groq API error {response.status_code}, using fallback")
                return policy_reason
                
    except Exception as e:
        print(f"⚠️ Groq explanation failed ({type(e).__name__}), using fallback")
        return policy_reason


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
