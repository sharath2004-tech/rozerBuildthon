"""
Complete Agent Evaluation System

Tests all 45 scenarios and produces comprehensive metrics.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.domain import (
    RecoveryContext, Rail, FailureClass, ActionType, Disposition
)
from app.rules import recovery_rules as R
from app.rules.taxonomy import classify
from tests.mocks.mock_payment_gateway import DeterministicMockGateway


class AgentEvaluator:
    """Comprehensive agent evaluation system."""
    
    def __init__(self):
        self.test_cases = self.load_test_cases()
        self.results = []
        self.metrics = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "detection_accurate": 0,
            "action_accurate": 0,
            "safety_compliant": 0,
            "recovery_simulated_success": 0
        }
        self.failures = []
        self.mock_gateway = DeterministicMockGateway(always_succeed=True)
    
    def load_test_cases(self) -> List[Dict]:
        """Load test cases from JSON."""
        test_file = Path(__file__).parent / "data" / "revenue_recovery_test_cases.json"
        with open(test_file) as f:
            return json.load(f)
    
    def create_context(self, test_case: Dict) -> RecoveryContext:
        """Convert test case to RecoveryContext."""
        # Map rail string to enum
        rail_map = {
            "upi": Rail.UPI,
            "card": Rail.CARD,
            "netbanking": Rail.NETBANKING,
            "wallet": Rail.WALLET,
            "emandate": Rail.EMANDATE
        }
        
        # Classify failure
        failure_code = test_case.get("failure_code")
        failure_class = classify(failure_code) if failure_code else FailureClass.UNKNOWN
        
        # Build context
        ctx = RecoveryContext(
            payment_id=test_case["payment_id"],
            customer_id=f"cust_{test_case['payment_id'][4:]}",
            amount_inr=test_case["amount_inr"],
            rail=rail_map.get(test_case["rail"], Rail.UNKNOWN),
            failure_class=failure_class,
            raw_failure_code=failure_code,
            retry_count=test_case.get("retry_count", 0),
            hours_since_failure=test_case.get("hours_since_failure", 0.0),
            prior_actions_24h=test_case.get("prior_actions_24h", 0),
            lifetime_payments=test_case.get("lifetime_payments", 0),
            lifetime_recoveries=test_case.get("lifetime_recoveries", 0),
            has_messaging_consent=test_case.get("has_messaging_consent", True),
            is_dnd_registered=test_case.get("is_dnd_registered", False),
            already_recovered=test_case.get("already_recovered", False),
            action_in_flight=test_case.get("action_in_flight", False),
            idempotency_key=test_case.get("idempotency_key", f"idem_{test_case['payment_id']}"),
            now=datetime(2026, 9, 2, test_case.get("current_hour", 14), 0)
        )
        
        return ctx
    
    def evaluate_test_case(self, test_case: Dict) -> Dict:
        """
        Evaluate a single test case.
        
        Returns:
            Dict with test results and pass/fail status
        """
        test_id = test_case["id"]
        expected = test_case["expected"]
        
        # Create context
        ctx = self.create_context(test_case)
        
        # Get agent's decision
        proposed_action = R.default_action(ctx)
        decision = R.evaluate(ctx, proposed_action)
        
        # Evaluate results
        result = {
            "test_id": test_id,
            "name": test_case["name"],
            "amount_inr": test_case["amount_inr"],
            "actual_action": decision.action.value,
            "actual_disposition": decision.disposition.value,
            "actual_rule_id": decision.rule_id,
            "actual_reason": decision.reason,
            "expected": expected,
            "passed": True,
            "failures": []
        }
        
        # Check disposition
        if "disposition" in expected:
            if decision.disposition.value != expected["disposition"]:
                result["passed"] = False
                result["failures"].append({
                    "type": "wrong_disposition",
                    "expected": expected["disposition"],
                    "actual": decision.disposition.value
                })
        
        # Check recommended action
        if "recommended_action" in expected:
            if decision.action.value != expected["recommended_action"]:
                result["passed"] = False
                result["failures"].append({
                    "type": "wrong_action",
                    "expected": expected["recommended_action"],
                    "actual": decision.action.value
                })
        
        # Check specific rule
        if "rule_id" in expected:
            if decision.rule_id != expected["rule_id"]:
                result["passed"] = False
                result["failures"].append({
                    "type": "wrong_rule",
                    "expected": expected["rule_id"],
                    "actual": decision.rule_id
                })
        
        # Check should_attempt_recovery
        if "should_attempt_recovery" in expected:
            should_recover = decision.disposition == Disposition.ALLOWED
            if should_recover != expected["should_attempt_recovery"]:
                result["passed"] = False
                result["failures"].append({
                    "type": "wrong_recovery_decision",
                    "expected": expected["should_attempt_recovery"],
                    "actual": should_recover
                })
        
        # Check failure class
        if "failure_class" in expected:
            if ctx.failure_class.value != expected["failure_class"]:
                result["passed"] = False
                result["failures"].append({
                    "type": "wrong_failure_classification",
                    "expected": expected["failure_class"],
                    "actual": ctx.failure_class.value
                })
        
        # Simulate recovery if allowed
        if decision.disposition == Disposition.ALLOWED:
            recovery_result = self.mock_gateway.retry_payment(
                ctx.payment_id,
                ctx.amount_inr,
                ctx.idempotency_key
            )
            result["recovery_attempted"] = True
            result["recovery_success"] = recovery_result["success"]
        else:
            result["recovery_attempted"] = False
            result["recovery_success"] = False
        
        return result
    
    def run_all_tests(self) -> Dict:
        """Run all test cases and compile metrics."""
        print("=" * 70)
        print("AI REVENUE RECOVERY AGENT - COMPREHENSIVE EVALUATION")
        print("=" * 70)
        print(f"\nTotal test scenarios: {len(self.test_cases)}")
        print("\nRunning tests...\n")
        
        for i, test_case in enumerate(self.test_cases, 1):
            result = self.evaluate_test_case(test_case)
            self.results.append(result)
            
            # Update metrics
            self.metrics["total_tests"] += 1
            
            if result["passed"]:
                self.metrics["passed"] += 1
                print(f"✅ {i:2d}. {test_case['name'][:50]:50s} PASS")
            else:
                self.metrics["failed"] += 1
                self.failures.append(result)
                print(f"❌ {i:2d}. {test_case['name'][:50]:50s} FAIL")
            
            # Track specific metrics
            if not result["failures"] or "wrong_failure_classification" not in [f["type"] for f in result["failures"]]:
                self.metrics["detection_accurate"] += 1
            
            if not result["failures"] or "wrong_action" not in [f["type"] for f in result["failures"]]:
                self.metrics["action_accurate"] += 1
            
            # Safety compliance: no blocked tests should have wrong_disposition
            if result["actual_disposition"] == "blocked" and not [f for f in result.get("failures", []) if f["type"] == "wrong_disposition"]:
                self.metrics["safety_compliant"] += 1
            
            if result.get("recovery_success", False):
                self.metrics["recovery_simulated_success"] += 1
        
        # Calculate percentages
        total = self.metrics["total_tests"]
        self.metrics["pass_rate"] = (self.metrics["passed"] / total * 100) if total > 0 else 0
        self.metrics["detection_accuracy"] = (self.metrics["detection_accurate"] / total * 100) if total > 0 else 0
        self.metrics["action_accuracy"] = (self.metrics["action_accurate"] / total * 100) if total > 0 else 0
        self.metrics["safety_compliance_rate"] = (self.metrics["safety_compliant"] / total * 100) if total > 0 else 0
        
        # Calculate recovery success rate (only for tests that attempted recovery)
        recovery_attempted = sum(1 for r in self.results if r.get("recovery_attempted", False))
        if recovery_attempted > 0:
            self.metrics["recovery_success_rate"] = (
                self.metrics["recovery_simulated_success"] / recovery_attempted * 100
            )
        else:
            self.metrics["recovery_success_rate"] = 0.0
        
        return self.metrics
    
    def print_report(self):
        """Print comprehensive evaluation report."""
        print("\n" + "=" * 70)
        print("EVALUATION RESULTS")
        print("=" * 70)
        
        print(f"\n📊 Overall Metrics:")
        print(f"   Total Tests:              {self.metrics['total_tests']}")
        print(f"   Passed:                   {self.metrics['passed']}")
        print(f"   Failed:                   {self.metrics['failed']}")
        print(f"   Pass Rate:                {self.metrics['pass_rate']:.1f}%")
        
        print(f"\n🎯 Accuracy Metrics:")
        print(f"   Detection Accuracy:       {self.metrics['detection_accuracy']:.1f}%")
        print(f"   Action Accuracy:          {self.metrics['action_accuracy']:.1f}%")
        print(f"   Safety Compliance:        {self.metrics['safety_compliance_rate']:.1f}%")
        print(f"   Recovery Success Rate:    {self.metrics['recovery_success_rate']:.1f}%")
        
        if self.failures:
            print(f"\n❌ Failed Tests ({len(self.failures)}):")
            for failure in self.failures:
                print(f"\n   {failure['test_id']} - {failure['name']}")
                for f in failure['failures']:
                    print(f"      • {f['type']}: expected={f.get('expected')}, actual={f.get('actual')}")
        
        # Categorize failures
        failure_types = {}
        for failure in self.failures:
            for f in failure['failures']:
                failure_type = f['type']
                failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
        
        if failure_types:
            print(f"\n📋 Failure Categories:")
            for ftype, count in sorted(failure_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {ftype:30s}: {count}")
        
        print("\n" + "=" * 70)
    
    def save_report(self, filename: str = "evaluation_report.json"):
        """Save evaluation report to JSON."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "results": self.results,
            "failures": self.failures
        }
        
        output_path = Path(__file__).parent / filename
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {output_path}")


def main():
    """Run complete evaluation."""
    evaluator = AgentEvaluator()
    evaluator.run_all_tests()
    evaluator.print_report()
    evaluator.save_report()
    
    # Return exit code based on pass rate
    if evaluator.metrics["pass_rate"] >= 90.0:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
