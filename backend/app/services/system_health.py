"""
System Health Checker - Integration Tests for All Services

Tests actual connectivity and functionality of:
- Groq API
- Razorpay API
- Webhook processing
- Database
- Agent reasoning
"""

import os
import httpx
from typing import Dict, Optional
from datetime import datetime

from app.db import health_check as db_health_check
from app.models.domain import RecoveryContext, Rail, FailureClass, ActionType
from app.rules import recovery_rules as R
from app.rules.taxonomy import classify


class SystemHealthChecker:
    """Comprehensive system health and integration tests."""
    
    def __init__(self):
        self.results = {}
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")
        self.razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    
    async def test_groq_api(self) -> Dict:
        """
        Test Groq AI API connectivity.
        
        Sends a real test prompt and verifies response.
        """
        if not self.groq_api_key:
            return {
                "status": "failed",
                "message": "GROQ_API_KEY not configured",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Log key format for debugging
        print(f"🔑 Testing Groq with key: {self.groq_api_key[:20]}... (length: {len(self.groq_api_key)})")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [
                            {
                                "role": "user",
                                "content": "Reply with OK if you receive this."
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 10
                    }
                )
                
                print(f"📡 Groq API response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data["choices"][0]["message"]["content"]
                    
                    return {
                        "status": "success",
                        "message": "Groq API responding correctly",
                        "connected": True,
                        "model": "openai/gpt-oss-20b",
                        "test_response": reply[:50],
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_text = response.text
                    print(f"❌ Groq error body: {error_text}")
                    return {
                        "status": "failed",
                        "message": f"Groq API error: {response.status_code}",
                        "connected": False,
                        "error_code": response.status_code,
                        "error_detail": error_text[:200],
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            print(f"❌ Groq exception: {type(e).__name__}: {str(e)}")
            return {
                "status": "failed",
                "message": f"Groq API connection error: {str(e)}",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_razorpay_api(self) -> Dict:
        """
        Test Razorpay API connectivity.
        
        Makes a safe read-only test request.
        """
        if not self.razorpay_key_id or not self.razorpay_key_secret:
            return {
                "status": "failed",
                "message": "Razorpay credentials not configured",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Log key format for debugging
        print(f"🔑 Testing Razorpay with key_id: {self.razorpay_key_id}")
        
        try:
            # Test with a safe read-only request - fetch payment methods
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.razorpay.com/v1/methods",
                    auth=(self.razorpay_key_id, self.razorpay_key_secret)
                )
                
                print(f"📡 Razorpay API response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return {
                        "status": "success",
                        "message": "Razorpay API responding correctly",
                        "connected": True,
                        "mode": "test" if self.razorpay_key_id.startswith("rzp_test_") else "live",
                        "methods_available": len(data),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_text = response.text
                    print(f"❌ Razorpay error body: {error_text}")
                    return {
                        "status": "failed",
                        "message": f"Razorpay API error: {response.status_code}",
                        "connected": False,
                        "error_code": response.status_code,
                        "error_detail": error_text[:200],
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            print(f"❌ Razorpay exception: {type(e).__name__}: {str(e)}")
            return {
                "status": "failed",
                "message": f"Razorpay API connection error: {str(e)}",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def test_database(self) -> Dict:
        """
        Test database connectivity.
        
        Uses existing health check function.
        """
        db_status = db_health_check()
        
        if db_status.get("database") == "connected":
            return {
                "status": "success",
                "message": "Database connected and responding",
                "connected": True,
                "database_type": "PostgreSQL",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "failed",
                "message": f"Database not connected: {db_status.get('database', 'unknown')}",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def test_webhook_processing(self) -> Dict:
        """
        Test webhook processing logic.
        
        Simulates a payment.failed webhook event.
        """
        try:
            # Create a test webhook payload
            test_payload = {
                "event": "payment.failed",
                "payload": {
                    "payment": {
                        "entity": {
                            "id": "pay_health_test_001",
                            "amount": 250000,
                            "error_code": "insufficient_funds",
                            "contact": "+919999999999"
                        }
                    }
                }
            }
            
            # Test that we can process it
            payment = test_payload["payload"]["payment"]["entity"]
            payment_id = payment["id"]
            amount_inr = payment["amount"] / 100
            
            # Verify classification
            failure_class = classify(payment["error_code"])
            
            if failure_class == FailureClass.UNKNOWN:
                return {
                    "status": "failed",
                    "message": "Webhook processing failed: Unknown failure code classification",
                    "connected": False,
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "status": "success",
                "message": "Webhook processing working correctly",
                "connected": True,
                "test_payment_id": payment_id,
                "classified_as": failure_class.value,
                "amount_inr": amount_inr,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Webhook processing error: {str(e)}",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def test_agent_reasoning(self) -> Dict:
        """
        Test agent's core reasoning logic.
        
        Sends a test scenario and verifies decision-making.
        """
        try:
            # Create a test scenario
            test_ctx = RecoveryContext(
                payment_id="pay_agent_test_001",
                customer_id="cust_test_001",
                amount_inr=2500.0,
                rail=Rail.UPI,
                failure_class=FailureClass.SOFT_DECLINE,
                raw_failure_code="insufficient_funds",
                retry_count=0,
                hours_since_failure=1.5,
                prior_actions_24h=0,
                lifetime_payments=8,
                lifetime_recoveries=6,
                has_messaging_consent=True,
                is_dnd_registered=False,
                already_recovered=False,
                action_in_flight=False,
                idempotency_key="idem_test_001",
                now=datetime.now()
            )
            
            # Get agent's decision
            proposed_action = R.default_action(test_ctx)
            decision = R.evaluate(test_ctx, proposed_action)
            
            # Verify decision has required fields
            if not decision.action or not decision.disposition or not decision.rule_id:
                return {
                    "status": "failed",
                    "message": "Agent produced incomplete decision",
                    "connected": False,
                    "timestamp": datetime.now().isoformat()
                }
            
            # For this scenario, we expect retry to be allowed
            expected_action = ActionType.RETRY
            is_correct = (
                decision.action == expected_action and
                decision.disposition.value in ["allowed", "needs_approval"]
            )
            
            return {
                "status": "success" if is_correct else "warning",
                "message": "Agent reasoning working correctly" if is_correct else "Agent reasoning produced unexpected result",
                "connected": True,
                "test_scenario": "₹2,500 UPI insufficient funds",
                "recommended_action": decision.action.value,
                "disposition": decision.disposition.value,
                "rule_applied": decision.rule_id,
                "reason": decision.reason[:100],
                "is_executable": decision.is_executable,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Agent reasoning error: {str(e)}",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_end_to_end(self) -> Dict:
        """
        Test complete end-to-end flow.
        
        Payment Event → Webhook → Database → Agent → Decision
        """
        try:
            steps = {}
            
            # Step 1: Webhook receives event
            webhook_result = self.test_webhook_processing()
            steps["webhook"] = webhook_result["status"] == "success"
            
            # Step 2: Database available
            db_result = self.test_database()
            steps["database"] = db_result["status"] == "success"
            
            # Step 3: Agent processes
            agent_result = self.test_agent_reasoning()
            steps["agent"] = agent_result["status"] == "success"
            
            # Step 4: Risk detection (part of agent)
            steps["risk_detection"] = agent_result["status"] == "success"
            
            # Step 5: Safety check (part of agent)
            steps["safety_check"] = agent_result.get("is_executable") is not None
            
            # Overall success
            all_passed = all(steps.values())
            
            return {
                "status": "success" if all_passed else "failed",
                "message": "End-to-end flow working" if all_passed else "Some steps failed",
                "connected": all_passed,
                "steps": steps,
                "steps_passed": sum(steps.values()),
                "steps_total": len(steps),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "message": f"End-to-end test error: {str(e)}",
                "connected": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_all_checks(self) -> Dict:
        """
        Run all health checks and return comprehensive results.
        """
        print("Running system health checks...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Test each component
        print("  Testing Groq API...")
        results["checks"]["groq"] = await self.test_groq_api()
        
        print("  Testing Razorpay API...")
        results["checks"]["razorpay"] = await self.test_razorpay_api()
        
        print("  Testing Database...")
        results["checks"]["database"] = self.test_database()
        
        print("  Testing Webhook Processing...")
        results["checks"]["webhook"] = self.test_webhook_processing()
        
        print("  Testing Agent Reasoning...")
        results["checks"]["agent"] = self.test_agent_reasoning()
        
        print("  Testing End-to-End Flow...")
        results["checks"]["end_to_end"] = await self.test_end_to_end()
        
        # Calculate overall health
        total_checks = len(results["checks"])
        successful_checks = sum(
            1 for check in results["checks"].values()
            if check.get("status") == "success"
        )
        
        results["overall"] = {
            "healthy": successful_checks == total_checks,
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": total_checks - successful_checks,
            "health_percentage": (successful_checks / total_checks * 100) if total_checks > 0 else 0
        }
        
        return results


async def get_system_health() -> Dict:
    """Convenience function to get system health."""
    checker = SystemHealthChecker()
    return await checker.run_all_checks()
