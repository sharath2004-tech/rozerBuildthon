"""
Mock Payment Gateway for Testing

Simulates Razorpay payment processing without real API calls or money.
"""

from enum import Enum
from typing import Dict, Optional
import random


class MockPaymentStatus(Enum):
    """Mock payment outcome statuses"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ALREADY_PROCESSED = "already_processed"
    INVALID_REQUEST = "invalid_request"


class MockPaymentGateway:
    """
    Mock Razorpay gateway for testing recovery workflows.
    
    Deterministic by default but can simulate various failure scenarios.
    """
    
    def __init__(self, success_rate: float = 0.7, seed: Optional[int] = None):
        """
        Initialize mock gateway.
        
        Args:
            success_rate: Probability of successful retry (0.0 to 1.0)
            seed: Random seed for reproducible tests
        """
        self.success_rate = success_rate
        self.rng = random.Random(seed) if seed is not None else random.Random(42)
        self.processed_payments: Dict[str, MockPaymentStatus] = {}
        self.retry_counts: Dict[str, int] = {}
        
    def retry_payment(self, payment_id: str, amount_inr: float, 
                     idempotency_key: Optional[str] = None) -> Dict:
        """
        Simulate payment retry.
        
        Args:
            payment_id: Payment identifier
            amount_inr: Amount in INR
            idempotency_key: Deduplication key
            
        Returns:
            Dict with status, message, and details
        """
        # Check for duplicate
        if idempotency_key and idempotency_key in self.processed_payments:
            return {
                "status": MockPaymentStatus.ALREADY_PROCESSED.value,
                "payment_id": payment_id,
                "message": "Payment already processed",
                "success": False
            }
        
        # Invalid request checks
        if amount_inr <= 0:
            return {
                "status": MockPaymentStatus.INVALID_REQUEST.value,
                "payment_id": payment_id,
                "message": "Invalid amount",
                "success": False
            }
        
        # Track retry count
        self.retry_counts[payment_id] = self.retry_counts.get(payment_id, 0) + 1
        
        # Simulate timeout (5% chance)
        if self.rng.random() < 0.05:
            return {
                "status": MockPaymentStatus.TIMEOUT.value,
                "payment_id": payment_id,
                "message": "Gateway timeout",
                "success": False
            }
        
        # Simulate success/failure based on success_rate
        success = self.rng.random() < self.success_rate
        
        status = MockPaymentStatus.SUCCESS if success else MockPaymentStatus.FAILED
        
        # Store result
        if idempotency_key:
            self.processed_payments[idempotency_key] = status
        
        return {
            "status": status.value,
            "payment_id": payment_id,
            "amount_inr": amount_inr,
            "message": "Payment successful" if success else "Payment failed",
            "success": success,
            "retry_count": self.retry_counts[payment_id]
        }
    
    def send_payment_link(self, customer_id: str, amount_inr: float, 
                         payment_id: str) -> Dict:
        """
        Simulate sending payment link to customer.
        
        Args:
            customer_id: Customer identifier
            amount_inr: Amount in INR
            payment_id: Payment identifier
            
        Returns:
            Dict with link_id and status
        """
        link_id = f"link_{payment_id}_{self.rng.randint(1000, 9999)}"
        
        return {
            "status": "sent",
            "link_id": link_id,
            "customer_id": customer_id,
            "amount_inr": amount_inr,
            "expires_in_hours": 24,
            "message": "Payment link sent successfully"
        }
    
    def update_instrument(self, customer_id: str, payment_id: str) -> Dict:
        """
        Simulate requesting instrument update.
        
        Args:
            customer_id: Customer identifier
            payment_id: Payment identifier
            
        Returns:
            Dict with request status
        """
        return {
            "status": "requested",
            "customer_id": customer_id,
            "payment_id": payment_id,
            "message": "Instrument update requested"
        }
    
    def reset(self):
        """Reset gateway state for new test."""
        self.processed_payments.clear()
        self.retry_counts.clear()
    
    def get_retry_count(self, payment_id: str) -> int:
        """Get number of retries for a payment."""
        return self.retry_counts.get(payment_id, 0)


class DeterministicMockGateway(MockPaymentGateway):
    """
    Deterministic mock gateway for predictable testing.
    
    Always succeeds or always fails based on configuration.
    """
    
    def __init__(self, always_succeed: bool = True):
        super().__init__(success_rate=1.0 if always_succeed else 0.0, seed=42)
        self.always_succeed = always_succeed
    
    def retry_payment(self, payment_id: str, amount_inr: float,
                     idempotency_key: Optional[str] = None) -> Dict:
        """Always return deterministic result."""
        # Check for duplicate
        if idempotency_key and idempotency_key in self.processed_payments:
            return {
                "status": MockPaymentStatus.ALREADY_PROCESSED.value,
                "payment_id": payment_id,
                "message": "Payment already processed",
                "success": False
            }
        
        # Invalid request checks
        if amount_inr <= 0:
            return {
                "status": MockPaymentStatus.INVALID_REQUEST.value,
                "payment_id": payment_id,
                "message": "Invalid amount",
                "success": False
            }
        
        # Track retry count
        self.retry_counts[payment_id] = self.retry_counts.get(payment_id, 0) + 1
        
        # Deterministic result
        status = MockPaymentStatus.SUCCESS if self.always_succeed else MockPaymentStatus.FAILED
        
        if idempotency_key:
            self.processed_payments[idempotency_key] = status
        
        return {
            "status": status.value,
            "payment_id": payment_id,
            "amount_inr": amount_inr,
            "message": "Payment successful" if self.always_succeed else "Payment failed",
            "success": self.always_succeed,
            "retry_count": self.retry_counts[payment_id]
        }
