"""
Domain types for the recovery pipeline.

Deliberately free of I/O, LLM calls, and framework imports so that the
policy layer can be unit-tested in isolation. Nothing in this module
performs a financial action; it only describes one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class FailureClass(str, Enum):
    """
    Canonical failure families. The raw gateway/issuer string is mapped
    into exactly one of these before any policy runs.

    The hard/soft split is the most consequential distinction in the
    system: soft failures are transient and worth retrying, hard failures
    are terminal and retrying them wastes network attempt allowances and
    can attract scheme penalties.
    """

    SOFT_DECLINE = "soft_decline"          # insufficient funds, limit exceeded
    HARD_DECLINE = "hard_decline"          # expired/stolen card, closed account
    AUTH_ABANDONED = "auth_abandoned"      # OTP / 3DS / UPI collect not completed
    TECHNICAL = "technical"                # gateway or issuer timeout, 5xx
    ISSUER_DOWN = "issuer_down"            # known downtime window
    MANDATE_PROBLEM = "mandate_problem"    # e-mandate revoked, AFA required
    UNKNOWN = "unknown"                    # unmapped -> must fail closed


class Rail(str, Enum):
    """Payment instrument. In India this is strongly predictive of recovery."""

    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMANDATE = "emandate"
    UNKNOWN = "unknown"


class ActionType(str, Enum):
    RETRY = "retry"                            # re-attempt the charge
    REMINDER = "reminder"                      # nudge the customer to pay
    CHECKOUT_RECOVERY = "checkout_recovery"    # link back to a prefilled checkout
    UPDATE_INSTRUMENT = "update_instrument"    # ask for a new card / re-auth mandate
    ESCALATE = "escalate"                      # human queue
    SUPPRESS = "suppress"                      # deliberately do nothing


class Disposition(str, Enum):
    ALLOWED = "allowed"
    NEEDS_APPROVAL = "needs_approval"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class RecoveryContext:
    """
    Everything the policy layer is allowed to consider. Passing `now`
    explicitly (rather than calling datetime.now() inside the rules) keeps
    every gate deterministic and therefore testable.
    """

    payment_id: str
    customer_id: str
    amount_inr: float
    rail: Rail
    failure_class: FailureClass
    raw_failure_code: Optional[str] = None

    # attempt history
    retry_count: int = 0
    hours_since_failure: float = 0.0
    prior_actions_24h: int = 0

    # customer history
    lifetime_payments: int = 0
    lifetime_recoveries: int = 0

    # consent / contactability
    has_messaging_consent: bool = False
    is_dnd_registered: bool = False

    # live state — guards against acting on a settled payment
    already_recovered: bool = False
    action_in_flight: bool = False

    # execution safety
    idempotency_key: Optional[str] = None

    now: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class PolicyDecision:
    """
    The output of the gateway. `rule_id` is the audit trail: every decision,
    permissive or restrictive, names the rule that produced it. "No rule
    fired" is never a valid reason to move money.
    """

    disposition: Disposition
    action: ActionType
    rule_id: str
    reason: str

    @property
    def is_executable(self) -> bool:
        return self.disposition is Disposition.ALLOWED

    def as_audit_row(self) -> dict:
        return {
            "disposition": self.disposition.value,
            "action": self.action.value,
            "rule_id": self.rule_id,
            "reason": self.reason,
        }
