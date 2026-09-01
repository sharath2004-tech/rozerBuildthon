"""
Deterministic Policy Gateway -- the financial decision boundary.

This module is the final authority on whether a recovery action executes.
An LLM may *propose* an action; only the gates below may *authorise* one.

Design rules, in priority order:

  1. Fail closed. If the situation is not understood, do not act.
  2. Every decision names the rule that produced it (`rule_id`). A decision
     with no rule behind it is a bug, not a permission.
  3. No I/O, no LLM calls, no clock reads. Everything comes from the
     RecoveryContext, so every gate is reproducible in a unit test.
  4. Gates are ordered most-catastrophic-first. The first gate to fire wins,
     which means a later permissive rule can never override an earlier
     restrictive one.

The gate IDs are stable and are written into the audit log, so they are
effectively part of the public interface. Do not renumber them.
"""

from __future__ import annotations

from app.models.domain import (
    ActionType,
    Disposition,
    FailureClass,
    PolicyDecision,
    Rail,
    RecoveryContext,
)

# --------------------------------------------------------------------------
# Policy configuration.
#
# These are the numbers a merchant would actually want to tune, so they live
# in one place rather than being scattered through the branches.
# --------------------------------------------------------------------------

#: Above this value nothing executes automatically, however confident the
#: model is. Chosen to sit below the common AFA threshold so that any
#: transaction large enough to need extra authentication also gets a human.
AUTO_ACTION_VALUE_CEILING_INR: float = 5_000.0

#: Card schemes penalise excessive retries on the same mandate/instrument.
MAX_RETRY_ATTEMPTS: int = 3

#: Anti-nag guard. More than this many touches in 24h and we stop, because
#: the cost of annoying a paying customer exceeds the value of one recovery.
MAX_ACTIONS_PER_24H: int = 2

#: Local quiet hours for customer-facing messages (24h clock, [start, end)).
QUIET_HOURS_START: int = 21
QUIET_HOURS_END: int = 9

#: Actions that put a message in front of a human being. These are subject
#: to consent, DND and quiet-hours gates. RETRY is machine-to-machine and
#: therefore is not.
_CUSTOMER_FACING: frozenset[ActionType] = frozenset(
    {
        ActionType.REMINDER,
        ActionType.CHECKOUT_RECOVERY,
        ActionType.UPDATE_INSTRUMENT,
    }
)

#: Failure families that must never be re-charged automatically.
_NEVER_RETRY: frozenset[FailureClass] = frozenset(
    {
        FailureClass.HARD_DECLINE,
        FailureClass.MANDATE_PROBLEM,
        FailureClass.UNKNOWN,
    }
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _blocked(rule: str, why: str, action: ActionType = ActionType.SUPPRESS) -> PolicyDecision:
    return PolicyDecision(Disposition.BLOCKED, action, rule, why)


def _escalate(rule: str, why: str) -> PolicyDecision:
    return PolicyDecision(Disposition.BLOCKED, ActionType.ESCALATE, rule, why)


def _approval(rule: str, why: str, action: ActionType) -> PolicyDecision:
    return PolicyDecision(Disposition.NEEDS_APPROVAL, action, rule, why)


def _allow(rule: str, why: str, action: ActionType) -> PolicyDecision:
    return PolicyDecision(Disposition.ALLOWED, action, rule, why)


def in_quiet_hours(hour: int) -> bool:
    """True if `hour` falls in the do-not-disturb window (wraps midnight)."""
    if QUIET_HOURS_START <= QUIET_HOURS_END:
        return QUIET_HOURS_START <= hour < QUIET_HOURS_END
    return hour >= QUIET_HOURS_START or hour < QUIET_HOURS_END


# --------------------------------------------------------------------------
# Default action selection
# --------------------------------------------------------------------------

def default_action(ctx: RecoveryContext) -> ActionType:
    """
    The deterministic baseline proposal, used when no model is available and
    as the comparison point for anything a model does propose.

    This is opinionated per failure family rather than score-driven, because
    *what* to do is a function of why it failed; *whether* and *when* are
    handled by the gates and the scheduler respectively.
    """
    fc = ctx.failure_class

    if fc is FailureClass.UNKNOWN:
        return ActionType.ESCALATE

    if fc is FailureClass.HARD_DECLINE:
        # The instrument is dead. Re-charging cannot succeed; the only path
        # to the money is the customer providing a new one.
        return ActionType.UPDATE_INSTRUMENT

    if fc is FailureClass.MANDATE_PROBLEM:
        # Re-authorisation is a regulated flow, not something to automate.
        return ActionType.ESCALATE

    if fc is FailureClass.AUTH_ABANDONED:
        # Intent was real and is perishable. Send them back to a live
        # checkout rather than re-charging an unauthenticated attempt.
        return ActionType.CHECKOUT_RECOVERY

    if fc in (FailureClass.TECHNICAL, FailureClass.ISSUER_DOWN):
        # Nothing wrong with the customer or the instrument.
        return ActionType.RETRY

    if fc is FailureClass.SOFT_DECLINE:
        # Worth retrying, but only once the balance plausibly exists --
        # the scheduler decides when, this only decides what.
        return ActionType.RETRY

    return ActionType.ESCALATE


# --------------------------------------------------------------------------
# The gateway
# --------------------------------------------------------------------------

def evaluate(ctx: RecoveryContext, proposed: ActionType | None = None) -> PolicyDecision:
    """
    Authorise, downgrade, or block a proposed recovery action.

    Args:
        ctx: everything known about the failed payment.
        proposed: the action under consideration. If None, the deterministic
            default for this failure family is used. A model-supplied value
            is treated as a *request*, never as an instruction.

    Returns:
        A PolicyDecision naming the gate that decided the outcome.
    """
    action = proposed if proposed is not None else default_action(ctx)

    # ---- G01 -- fail closed on an unrecognised failure reason ----------
    # The original scoring code treated an unknown reason as neutral, which
    # let a customer with good history cross the auto-retry threshold on a
    # failure nobody had classified. Unknown input must never authorise a
    # charge.
    if ctx.failure_class is FailureClass.UNKNOWN:
        return _escalate(
            "G01_UNKNOWN_FAILURE_FAILS_CLOSED",
            f"Failure code {ctx.raw_failure_code!r} is not in the taxonomy; "
            "refusing to act automatically.",
        )

    # ---- G02 -- the money is already in --------------------------------
    if ctx.already_recovered:
        return _blocked(
            "G02_ALREADY_RECOVERED",
            "Payment has already succeeded; any further action risks a "
            "duplicate charge or a redundant message.",
        )

    # ---- G03 -- race guard ---------------------------------------------
    # Without this, a scheduled retry and a manual customer payment can both
    # land. This is the single most expensive bug class in dunning.
    if ctx.action_in_flight:
        return _blocked(
            "G03_ACTION_ALREADY_IN_FLIGHT",
            "Another recovery action is in flight for this payment; "
            "serialising to avoid a double charge.",
        )

    # ---- G04 -- never re-charge a terminal failure ---------------------
    if action is ActionType.RETRY and ctx.failure_class in _NEVER_RETRY:
        downgraded = default_action(ctx)
        return _blocked(
            "G04_HARD_FAILURE_NOT_RETRYABLE",
            f"{ctx.failure_class.value} is terminal; retry cannot succeed and "
            f"consumes scheme attempt allowance. Downgrading to "
            f"{downgraded.value}.",
            action=downgraded,
        )

    # ---- G05 -- regulated mandate flows stay manual --------------------
    if ctx.failure_class is FailureClass.MANDATE_PROBLEM and action is not ActionType.ESCALATE:
        return _escalate(
            "G05_MANDATE_REQUIRES_HUMAN",
            "Mandate re-authorisation carries pre-debit-notification and "
            "additional-authentication obligations; routing to a human.",
        )

    # ---- G06 -- retry attempt cap --------------------------------------
    if action is ActionType.RETRY and ctx.retry_count >= MAX_RETRY_ATTEMPTS:
        return _escalate(
            "G06_RETRY_CAP_REACHED",
            f"Already attempted {ctx.retry_count} retries "
            f"(cap {MAX_RETRY_ATTEMPTS}); further attempts risk scheme "
            "penalties.",
        )

    # ---- G07 -- do not become spam -------------------------------------
    if action in _CUSTOMER_FACING and ctx.prior_actions_24h >= MAX_ACTIONS_PER_24H:
        return _blocked(
            "G07_FREQUENCY_CAP",
            f"{ctx.prior_actions_24h} contacts already made in 24h "
            f"(cap {MAX_ACTIONS_PER_24H}); further contact costs more "
            "goodwill than the recovery is worth.",
        )

    # ---- G08 -- do not retry into a known outage -----------------------
    if action is ActionType.RETRY and ctx.failure_class is FailureClass.ISSUER_DOWN:
        return _blocked(
            "G08_ISSUER_DOWN_DEFER",
            "Issuer is in a known downtime window; retrying now would burn "
            "an attempt. Deferring until the window closes.",
        )

    # ---- G09 -- consent is a precondition, not a preference ------------
    if action in _CUSTOMER_FACING:
        if not ctx.has_messaging_consent:
            return _blocked(
                "G09_NO_MESSAGING_CONSENT",
                "No recorded consent to contact this customer.",
            )
        if ctx.is_dnd_registered:
            return _blocked(
                "G09_DND_REGISTERED",
                "Customer is DND-registered; commercial contact is not "
                "permitted.",
            )

    # ---- G10 -- quiet hours --------------------------------------------
    if action in _CUSTOMER_FACING and in_quiet_hours(ctx.now.hour):
        return _blocked(
            "G10_QUIET_HOURS",
            f"Local time {ctx.now.hour:02d}:00 falls in quiet hours "
            f"({QUIET_HOURS_START:02d}:00-{QUIET_HOURS_END:02d}:00); "
            "deferring to the next permitted window.",
        )

    # ---- G11 -- execution safety --------------------------------------
    # Enforced late so that blocked actions are not required to carry a key,
    # but no action can reach execution without one.
    if action is ActionType.RETRY and not ctx.idempotency_key:
        return _escalate(
            "G11_MISSING_IDEMPOTENCY_KEY",
            "Refusing to attempt a charge without an idempotency key.",
        )

    # ---- G12 -- value ceiling routes to a human -----------------------
    if ctx.amount_inr > AUTO_ACTION_VALUE_CEILING_INR:
        return _approval(
            "G12_VALUE_CEILING_APPROVAL",
            f"Rs.{ctx.amount_inr:,.0f} exceeds the automatic ceiling of "
            f"Rs.{AUTO_ACTION_VALUE_CEILING_INR:,.0f}; action is sound but "
            "needs merchant sign-off.",
            action=action,
        )

    # ---- Permitted ----------------------------------------------------
    if action is ActionType.ESCALATE:
        return _escalate("G00_DEFAULT_ESCALATION", "No automatable path; queued for review.")

    return _allow(
        "G99_PERMITTED",
        f"{action.value} permitted for {ctx.failure_class.value} on "
        f"{ctx.rail.value} at attempt {ctx.retry_count + 1}.",
        action,
    )


def explain_gates() -> dict[str, str]:
    """
    Machine-readable gate inventory, for the dashboard's policy tab and for
    the architecture write-up. Keeping this next to the gates means the
    documentation cannot silently drift from the implementation.
    """
    return {
        "G00_DEFAULT_ESCALATION": "No automatable path for this failure family -> human queue.",
        "G01_UNKNOWN_FAILURE_FAILS_CLOSED": "Unmapped failure reason -> escalate, never act.",
        "G02_ALREADY_RECOVERED": "Payment already succeeded -> stop.",
        "G03_ACTION_ALREADY_IN_FLIGHT": "Serialise actions per payment to prevent double charges.",
        "G04_HARD_FAILURE_NOT_RETRYABLE": "Terminal declines are never re-charged.",
        "G05_MANDATE_REQUIRES_HUMAN": "Mandate re-authorisation is a regulated manual flow.",
        "G06_RETRY_CAP_REACHED": f"At most {MAX_RETRY_ATTEMPTS} retry attempts.",
        "G07_FREQUENCY_CAP": f"At most {MAX_ACTIONS_PER_24H} customer contacts per 24h.",
        "G08_ISSUER_DOWN_DEFER": "Never retry into a known issuer outage.",
        "G09_NO_MESSAGING_CONSENT": "Consent and DND status gate all customer contact.",
        "G10_QUIET_HOURS": f"No contact between {QUIET_HOURS_START}:00 and {QUIET_HOURS_END}:00.",
        "G11_MISSING_IDEMPOTENCY_KEY": "No charge attempt without an idempotency key.",
        "G12_VALUE_CEILING_APPROVAL": f"Above Rs.{AUTO_ACTION_VALUE_CEILING_INR:,.0f} a human signs off.",
        "G99_PERMITTED": "All gates passed.",
    }
