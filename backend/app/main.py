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

app = FastAPI(
    title="AI Revenue Recovery Agent",
    description=(
        "Bounded recovery agent. The LLM recommends; deterministic rules "
        "authorise. No model output reaches the money path."
    ),
    version="0.2.0",
)


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
    return {"status": "ok", "version": app.version}


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
