"""
FastAPI surface.

Thin by design. The endpoint normalises input, runs scoring, asks the policy
gateway for authorisation, and returns the decision together with the reason
and the rule that produced it. It does not itself decide anything.

Note the response shape: `disposition` and `rule_id` are first-class, not
debug output. A merchant integrating this needs to distinguish "we retried"
from "we would have retried but the value ceiling sent it to you for
approval", and an auditor needs the rule.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.models.domain import ActionType, Rail, RecoveryContext
from app.rules import recovery_rules as R
from app.rules.taxonomy import classify, known_codes
from app.services.scoring import (
    estimate_recovery_probability,
    expected_value_inr,
    recommend_delay_minutes,
    score_breakdown,
)
from app.db import init_db, health_check

app = FastAPI(
    title="AI Revenue Recovery Agent",
    description=(
        "Bounded recovery agent. The LLM recommends; deterministic rules "
        "authorise. No model output reaches the money path."
    ),
    version="0.3.0",
)

# Add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("⚠️ App will continue but database features won't work")


class PaymentEvent(BaseModel):
    """Inbound failed-payment event."""

    payment_id: str
    customer_id: str
    amount_inr: float = Field(gt=0)
    rail: Rail = Rail.UNKNOWN
    failure_code: str | None = None

    retry_count: int = Field(default=0, ge=0)
    hours_since_failure: float = Field(default=0.0, ge=0)
    prior_actions_24h: int = Field(default=0, ge=0)

    lifetime_payments: int = Field(default=0, ge=0)
    lifetime_recoveries: int = Field(default=0, ge=0)

    has_messaging_consent: bool = False
    is_dnd_registered: bool = False
    already_recovered: bool = False
    action_in_flight: bool = False

    idempotency_key: str | None = None


def _to_context(ev: PaymentEvent, now: datetime | None = None) -> RecoveryContext:
    return RecoveryContext(
        payment_id=ev.payment_id,
        customer_id=ev.customer_id,
        amount_inr=ev.amount_inr,
        rail=ev.rail,
        failure_class=classify(ev.failure_code),
        raw_failure_code=ev.failure_code,
        retry_count=ev.retry_count,
        hours_since_failure=ev.hours_since_failure,
        prior_actions_24h=ev.prior_actions_24h,
        lifetime_payments=ev.lifetime_payments,
        lifetime_recoveries=ev.lifetime_recoveries,
        has_messaging_consent=ev.has_messaging_consent,
        is_dnd_registered=ev.is_dnd_registered,
        already_recovered=ev.already_recovered,
        action_in_flight=ev.action_in_flight,
        idempotency_key=ev.idempotency_key,
        now=now or datetime.now(),
    )


@app.get("/health")
def health() -> dict:
    """Health check endpoint with database status."""
    db_status = health_check()
    return {
        "status": "ok",
        "version": app.version,
        **db_status
    }


@app.get("/policy/gates")
def policy_gates() -> dict:
    """
    The full gate inventory. Exposed because a merchant is entitled to know
    the rules that govern automated action on their account, and because
    keeping this generated from the implementation stops the documentation
    drifting from behaviour.
    """
    return {"gates": R.explain_gates(), "known_failure_codes": known_codes()}


@app.post("/analyze")
def analyze(event: PaymentEvent) -> dict:
    """
    Score a failed payment and return an authorised decision.

    This endpoint does not execute anything. Execution is a separate,
    explicitly-invoked step so that analysis is always safe to call.
    """
    ctx = _to_context(event)

    proposed = R.default_action(ctx)
    decision = R.evaluate(ctx, proposed)

    delay = recommend_delay_minutes(ctx)
    p = estimate_recovery_probability(ctx)

    return {
        "payment_id": ctx.payment_id,
        "amount_inr": ctx.amount_inr,
        "failure_class": ctx.failure_class.value,
        "raw_failure_code": ctx.raw_failure_code,
        "p_recover": p,
        "expected_value_inr": expected_value_inr(ctx, decision.action, p_recover=p),
        "proposed_action": proposed.value,
        "authorised_action": decision.action.value,
        "disposition": decision.disposition.value,
        "rule_id": decision.rule_id,
        "reason": decision.reason,
        "executable": decision.is_executable,
        "scheduled_for": (
            (ctx.now + timedelta(minutes=delay)).isoformat()
            if decision.is_executable and decision.action is not ActionType.SUPPRESS
            else None
        ),
        "delay_minutes": delay,
        "breakdown": score_breakdown(ctx, decision.action),
    }


# ===== Analytics Endpoints for Dashboard =====

@app.get("/analytics/recovery-metrics")
def get_recovery_metrics(period: str = "7d"):
    """Get recovery metrics for dashboard."""
    from app.db import engine
    from sqlalchemy import text
    
    if engine is None:
        # Return demo data if no database
        return {
            "period": period,
            "total_at_risk": 125000.0,
            "recovered": 89500.0,
            "pending": 28000.0,
            "blocked": 7500.0,
            "recovery_rate": 0.716,
            "auto_recovery_rate": 0.652,
            "avg_recovery_time_hours": 4.2,
            "total_workflows": 247
        }
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_workflows,
                SUM(amount_inr) as total_at_risk,
                SUM(CASE WHEN disposition = 'AUTO_RETRY' THEN amount_inr ELSE 0 END) as recovered,
                SUM(CASE WHEN disposition = 'NEEDS_APPROVAL' THEN amount_inr ELSE 0 END) as pending,
                SUM(CASE WHEN disposition = 'BLOCKED' THEN amount_inr ELSE 0 END) as blocked
            FROM recovery_workflows
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)).fetchone()
        
        if result:
            total_at_risk = float(result[1] or 0)
            recovered = float(result[2] or 0)
            
            return {
                "period": period,
                "total_at_risk": total_at_risk,
                "recovered": recovered,
                "pending": float(result[3] or 0),
                "blocked": float(result[4] or 0),
                "recovery_rate": recovered / total_at_risk if total_at_risk > 0 else 0,
                "auto_recovery_rate": recovered / total_at_risk if total_at_risk > 0 else 0,
                "avg_recovery_time_hours": 4.2,
                "total_workflows": result[0] or 0
            }
        
        return {
            "period": period,
            "total_at_risk": 0,
            "recovered": 0,
            "pending": 0,
            "blocked": 0,
            "recovery_rate": 0,
            "auto_recovery_rate": 0,
            "avg_recovery_time_hours": 0,
            "total_workflows": 0
        }


@app.get("/analytics/batch-results")
def get_batch_results(period: str = "7d", limit: int = 50):
    """Get batch results for dashboard."""
    from app.db import engine
    from sqlalchemy import text
    
    if engine is None:
        # Return demo data
        return {
            "period": period,
            "batches": [
                {
                    "batch_id": "BATCH_20260901_001",
                    "total_payments": 45,
                    "auto_retried": 32,
                    "needs_approval": 10,
                    "blocked": 3,
                    "success_rate": 0.711,
                    "created_at": "2026-09-01T10:30:00Z"
                }
            ]
        }
    
    with engine.connect() as conn:
        results = conn.execute(text("""
            SELECT batch_id, total_payments, auto_retried, needs_approval, 
                   blocked, success_rate, created_at
            FROM batch_results
            WHERE created_at >= NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
        
        batches = []
        for row in results:
            batches.append({
                "batch_id": row[0],
                "total_payments": row[1],
                "auto_retried": row[2],
                "needs_approval": row[3],
                "blocked": row[4],
                "success_rate": float(row[5] or 0),
                "created_at": row[6].isoformat() if row[6] else None
            })
        
        return {"period": period, "batches": batches}


@app.get("/analytics/compliance-stats")
def get_compliance_stats(period: str = "7d"):
    """Get compliance statistics."""
    from app.db import engine
    from sqlalchemy import text
    
    if engine is None:
        # Return demo data
        return {
            "period": period,
            "total_decisions": 247,
            "auto_approved": 161,
            "human_approved": 76,
            "auto_blocked": 10,
            "override_rate": 0.031,
            "compliance_score": 0.969
        }
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                SUM(total_decisions) as total_decisions,
                SUM(auto_approved) as auto_approved,
                SUM(human_approved) as human_approved,
                SUM(auto_blocked) as auto_blocked,
                AVG(override_rate) as override_rate
            FROM compliance_stats
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        if result and result[0]:
            override_rate = float(result[4] or 0)
            return {
                "period": period,
                "total_decisions": result[0] or 0,
                "auto_approved": result[1] or 0,
                "human_approved": result[2] or 0,
                "auto_blocked": result[3] or 0,
                "override_rate": override_rate,
                "compliance_score": 1.0 - override_rate
            }
        
        return {
            "period": period,
            "total_decisions": 0,
            "auto_approved": 0,
            "human_approved": 0,
            "auto_blocked": 0,
            "override_rate": 0,
            "compliance_score": 1.0
        }
