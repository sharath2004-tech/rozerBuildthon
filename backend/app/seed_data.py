"""
Seed the database with realistic test data for the revenue recovery dashboard.

This script populates the database with:
- Recovery workflows (successful and failed attempts)
- Batch results
- Compliance stats
- Payment logs

Run this once to populate demo data:
    python -m app.seed_data
"""

import random
import uuid
from datetime import datetime, timedelta
from app.db import engine
from sqlalchemy import text

# Sample data
FAILURE_CODES = [
    "NETWORK_ERROR",
    "INSUFFICIENT_FUNDS", 
    "BANK_TIMEOUT",
    "CARD_DECLINED",
    "INVALID_ACCOUNT",
    "PAYMENT_GATEWAY_ERROR"
]

WORKFLOW_TYPES = [
    "auto_retry",
    "payment_link",
    "manual_review",
    "voice_call"
]

DISPOSITIONS = [
    "AUTO_RETRY",
    "NEEDS_APPROVAL",
    "BLOCKED",
    "SUPPRESSED"
]

def generate_payment_id():
    """Generate realistic Razorpay-style payment ID."""
    return f"pay_{uuid.uuid4().hex[:14]}"

def generate_customer_id():
    """Generate realistic customer ID."""
    return f"cust_{uuid.uuid4().hex[:8]}"

def seed_recovery_workflows(count=100):
    """
    Seed recovery_workflows table with historical data.
    
    This represents individual payment recovery attempts.
    """
    print(f"Seeding {count} recovery workflows...")
    
    workflows = []
    for i in range(count):
        payment_id = generate_payment_id()
        customer_id = generate_customer_id()
        amount_inr = random.randint(500, 50000)  # In rupees
        
        # Create workflow with realistic distribution
        disposition = random.choices(
            DISPOSITIONS,
            weights=[60, 25, 10, 5],  # Most are auto-retry
            k=1
        )[0]
        
        # Recovery probability
        recovery_prob = random.uniform(0.40, 0.90)
        
        created_at = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23)
        )
        
        workflows.append({
            "payment_id": payment_id,
            "customer_id": customer_id,
            "amount_inr": amount_inr,
            "rail": random.choice(["UPI", "NETBANKING", "CARD", "WALLET"]),
            "failure_code": random.choice(FAILURE_CODES),
            "disposition": disposition,
            "rule_id": f"RULE_{random.randint(1, 10):03d}",
            "reason": f"Recovery workflow for {disposition}",
            "recovery_probability": recovery_prob,
            "expected_value_inr": amount_inr * recovery_prob,
            "retry_count": random.randint(0, 3),
            "created_at": created_at
        })
    
    # Insert into database
    with engine.connect() as conn:
        for wf in workflows:
            try:
                conn.execute(text("""
                    INSERT INTO recovery_workflows 
                    (payment_id, customer_id, amount_inr, rail, failure_code, disposition, 
                     rule_id, reason, recovery_probability, expected_value_inr, retry_count, created_at)
                    VALUES 
                    (:payment_id, :customer_id, :amount_inr, :rail, :failure_code, :disposition,
                     :rule_id, :reason, :recovery_probability, :expected_value_inr, :retry_count, :created_at)
                """), wf)
            except Exception as e:
                # Table might not exist, skip
                print(f"Warning: Could not insert workflow: {e}")
                break
        
        try:
            conn.commit()
            print(f"✅ Inserted {len(workflows)} recovery workflows")
        except:
            print("⚠️ recovery_workflows table does not exist, skipping")


def seed_batch_results(count=20):
    """
    Seed batch_results table with batch processing data.
    
    This represents batch recovery runs.
    """
    print(f"Seeding {count} batch results...")
    
    batches = []
    for i in range(count):
        batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d')}_{i:03d}"
        
        total_payments = random.randint(20, 100)
        auto_retried = int(total_payments * random.uniform(0.55, 0.70))
        needs_approval = int(total_payments * random.uniform(0.15, 0.25))
        blocked = total_payments - auto_retried - needs_approval
        
        total_amount_inr = random.randint(100000, 500000)
        
        # Recovery rate between 40-80%
        success_rate = random.uniform(0.40, 0.80)
        recovered_amount_inr = int(total_amount_inr * success_rate)
        
        completed_at = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23)
        )
        
        batches.append({
            "batch_id": batch_id,
            "total_payments": total_payments,
            "auto_retried": auto_retried,
            "needs_approval": needs_approval,
            "blocked": blocked,
            "total_amount_inr": total_amount_inr,
            "recovered_amount_inr": recovered_amount_inr,
            "success_rate": success_rate,
            "completed_at": completed_at
        })
    
    # Insert into database
    with engine.connect() as conn:
        for batch in batches:
            try:
                conn.execute(text("""
                    INSERT INTO batch_results 
                    (batch_id, total_payments, auto_retried, needs_approval, blocked,
                     total_amount_inr, recovered_amount_inr, success_rate, completed_at)
                    VALUES 
                    (:batch_id, :total_payments, :auto_retried, :needs_approval, :blocked,
                     :total_amount_inr, :recovered_amount_inr, :success_rate, :completed_at)
                """), batch)
            except Exception as e:
                print(f"Warning: Could not insert batch: {e}")
                break
        
        try:
            conn.commit()
            print(f"✅ Inserted {len(batches)} batch results")
        except:
            print("⚠️ batch_results table does not exist, skipping")


def seed_compliance_stats():
    """
    Seed compliance_stats table with daily statistics.
    
    This represents compliance/policy gate decisions.
    """
    print("Seeding compliance stats...")
    
    stats = []
    for i in range(30):  # Last 30 days
        date = datetime.now().date() - timedelta(days=i)
        
        total_decisions = random.randint(50, 200)
        auto_approved = int(total_decisions * random.uniform(0.60, 0.75))
        auto_blocked = int(total_decisions * random.uniform(0.10, 0.15))
        human_approved = total_decisions - auto_approved - auto_blocked
        
        override_rate = random.uniform(0.02, 0.05)  # 2-5% override rate
        
        stats.append({
            "date": date,
            "total_decisions": total_decisions,
            "auto_approved": auto_approved,
            "human_approved": human_approved,
            "auto_blocked": auto_blocked,
            "override_rate": override_rate
        })
    
    # Insert into database
    with engine.connect() as conn:
        for stat in stats:
            try:
                conn.execute(text("""
                    INSERT INTO compliance_stats 
                    (date, total_decisions, auto_approved, human_approved, 
                     auto_blocked, override_rate)
                    VALUES 
                    (:date, :total_decisions, :auto_approved, :human_approved,
                     :auto_blocked, :override_rate)
                """), stat)
            except Exception as e:
                print(f"Warning: Could not insert compliance stat: {e}")
                break
        
        try:
            conn.commit()
            print(f"✅ Inserted {len(stats)} compliance stats")
        except:
            print("⚠️ compliance_stats table does not exist, skipping")


def seed_payment_logs(count=50):
    """
    Seed payment_logs table with webhook events.
    
    This represents payment events received from Razorpay webhooks.
    """
    print(f"Seeding {count} payment logs...")
    
    logs = []
    event_types = ["payment.failed", "payment.authorized", "payment.captured"]
    
    for i in range(count):
        payment_id = generate_payment_id()
        event_type = random.choice(event_types)
        status = "failed" if event_type == "payment.failed" else "success"
        amount_inr = random.randint(500, 50000)
        
        created_at = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23)
        )
        
        logs.append({
            "payment_id": payment_id,
            "event_type": event_type,
            "status": status,
            "amount_inr": amount_inr,
            "metadata": f'{{"test": true, "amount": {amount_inr}}}',
            "created_at": created_at
        })
    
    # Insert into database
    with engine.connect() as conn:
        for log in logs:
            try:
                conn.execute(text("""
                    INSERT INTO payment_logs 
                    (payment_id, event_type, status, amount_inr, metadata, created_at)
                    VALUES 
                    (:payment_id, :event_type, :status, :amount_inr, :metadata, :created_at)
                """), log)
            except Exception as e:
                print(f"Warning: Could not insert payment log: {e}")
                break
        
        try:
            conn.commit()
            print(f"✅ Inserted {len(logs)} payment logs")
        except:
            print("⚠️ payment_logs table does not exist, skipping")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("SEEDING DATABASE WITH TEST DATA")
    print("=" * 60)
    
    if engine is None:
        print("❌ Database not configured. Cannot seed data.")
        print("   Set DATABASE_URL in .env file")
        return
    
    print(f"Database: {engine.url}")
    print()
    
    # Seed all tables
    seed_recovery_workflows(count=100)
    seed_batch_results(count=20)
    seed_compliance_stats()
    seed_payment_logs(count=50)
    
    print()
    print("=" * 60)
    print("✅ DATABASE SEEDING COMPLETE!")
    print("=" * 60)
    print()
    print("You can now view the data in your dashboard.")
    print("To re-seed, clear the tables and run this script again.")


if __name__ == "__main__":
    main()
