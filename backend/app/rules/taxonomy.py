"""
Failure-code taxonomy.

Maps the messy free-text / coded failure reason from the gateway into one
canonical FailureClass. This is the one place where an LLM is permitted to
assist (classifying an unrecognised string), but its answer is constrained
to the enum below and an unmapped result becomes UNKNOWN rather than a
guess -- see rules.recovery_rules.G01, which fails closed on UNKNOWN.

NOTE: these code strings are modelled on common gateway/issuer reasons and
should be reconciled against Razorpay's current error-code documentation
before submission. The mapping table is intentionally data, not logic, so
that reconciliation is a one-file change.
"""

from __future__ import annotations

from app.models.domain import FailureClass

# Terminal. Retrying these is useless and can attract scheme penalties.
_HARD: set[str] = {
    "card_expired",
    "expired_card",
    "card_stolen",
    "card_lost",
    "card_reported_lost_or_stolen",
    "account_closed",
    "account_blocked",
    "invalid_card_number",
    "card_not_supported",
    "do_not_honour",
    "do_not_honor",
    "transaction_not_permitted",
    "fraud_suspected",
    "payment_blocked_by_issuer",
}

# Transient and genuinely worth another attempt -- but the *timing* differs
# sharply within this family, which is why scoring is reason-aware.
_SOFT: set[str] = {
    "insufficient_funds",
    "insufficient_balance",
    "limit_exceeded",
    "withdrawal_limit_exceeded",
    "payment_limit_exceeded",
    "velocity_limit_exceeded",
}

# Customer showed intent but never completed authentication.
_ABANDONED: set[str] = {
    "otp_not_entered",
    "payment_cancelled_by_user",
    "3ds_authentication_abandoned",
    "authentication_failed_abandoned",
    "upi_collect_expired",
    "upi_request_timed_out",
    "user_dropped_off",
}

# Infrastructure, not the customer.
_TECHNICAL: set[str] = {
    "gateway_timeout",
    "gateway_error",
    "network_error",
    "server_error",
    "payment_timed_out",
    "upstream_error",
}

_ISSUER_DOWN: set[str] = {
    "issuer_down",
    "bank_down",
    "issuer_unavailable",
    "bank_not_available",
}

_MANDATE: set[str] = {
    "mandate_revoked",
    "mandate_cancelled",
    "mandate_paused",
    "mandate_not_found",
    "afa_required",
    "additional_authentication_required",
    "pre_debit_notification_missing",
}


_TABLE: dict[str, FailureClass] = {
    **{c: FailureClass.HARD_DECLINE for c in _HARD},
    **{c: FailureClass.SOFT_DECLINE for c in _SOFT},
    **{c: FailureClass.AUTH_ABANDONED for c in _ABANDONED},
    **{c: FailureClass.TECHNICAL for c in _TECHNICAL},
    **{c: FailureClass.ISSUER_DOWN for c in _ISSUER_DOWN},
    **{c: FailureClass.MANDATE_PROBLEM for c in _MANDATE},
}


def classify(raw_code: str | None) -> FailureClass:
    """
    Deterministically map a raw failure code to a FailureClass.

    Returns UNKNOWN for anything unmapped, including None and empty string.
    UNKNOWN is not a soft default -- G01 refuses to act on it. Fail closed
    is the only safe posture when the reason a charge failed is not
    understood.
    """
    if not raw_code:
        return FailureClass.UNKNOWN
    return _TABLE.get(raw_code.strip().lower(), FailureClass.UNKNOWN)


def is_known(raw_code: str | None) -> bool:
    return classify(raw_code) is not FailureClass.UNKNOWN


def known_codes() -> list[str]:
    """Used by the LLM classifier prompt to constrain output to real codes."""
    return sorted(_TABLE.keys())
