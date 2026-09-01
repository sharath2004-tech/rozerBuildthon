"""
Guardrail tests.

These are the tests worth having. Not "does the endpoint return 200", but
"can this system be made to charge a card it should not charge". Each test
below corresponds to a way real dunning systems lose money or trust.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.models.domain import (
    ActionType,
    Disposition,
    FailureClass,
    Rail,
    RecoveryContext,
)
from app.rules import recovery_rules as R
from app.rules.taxonomy import classify
from app.services.scoring import (
    estimate_recovery_probability,
    expected_value_inr,
    recommend_delay_minutes,
    timing_multiplier,
)

# A neutral midday timestamp so quiet-hours never fires incidentally.
NOON = datetime(2026, 9, 15, 12, 0, 0)


def ctx(**kw) -> RecoveryContext:
    base = dict(
        payment_id="pay_test",
        customer_id="cust_test",
        amount_inr=1000.0,
        rail=Rail.CARD,
        failure_class=FailureClass.TECHNICAL,
        has_messaging_consent=True,
        idempotency_key="idem_test",
        now=NOON,
    )
    base.update(kw)
    return RecoveryContext(**base)


# --------------------------------------------------------------------------
# The bug that was actually in the original code
# --------------------------------------------------------------------------

def test_unknown_failure_reason_never_authorises_a_charge():
    """
    Regression test for the fail-open bug: previously a customer with strong
    history and an unmapped failure reason scored 75 and returned
    'retry_payment'. Unknown input must escalate, not act.
    """
    d = R.evaluate(
        ctx(
            failure_class=FailureClass.UNKNOWN,
            raw_failure_code="some_code_nobody_mapped",
            lifetime_payments=40,
            lifetime_recoveries=5,
        )
    )
    assert d.disposition is Disposition.BLOCKED
    assert d.action is ActionType.ESCALATE
    assert d.rule_id == "G01_UNKNOWN_FAILURE_FAILS_CLOSED"
    assert not d.is_executable


def test_unmapped_code_classifies_as_unknown_not_as_a_guess():
    assert classify("totally_made_up") is FailureClass.UNKNOWN
    assert classify(None) is FailureClass.UNKNOWN
    assert classify("") is FailureClass.UNKNOWN
    assert classify("  CARD_EXPIRED  ") is FailureClass.HARD_DECLINE


# --------------------------------------------------------------------------
# Never re-charge a terminal failure
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "code",
    ["card_expired", "card_stolen", "account_closed", "do_not_honour"],
)
def test_hard_declines_are_never_retried(code):
    fc = classify(code)
    assert fc is FailureClass.HARD_DECLINE
    d = R.evaluate(ctx(failure_class=fc, raw_failure_code=code), ActionType.RETRY)
    assert not d.is_executable
    assert d.action is not ActionType.RETRY
    assert d.rule_id == "G04_HARD_FAILURE_NOT_RETRYABLE"


def test_hard_decline_is_downgraded_to_asking_for_a_new_instrument():
    d = R.evaluate(ctx(failure_class=FailureClass.HARD_DECLINE), ActionType.RETRY)
    assert d.action is ActionType.UPDATE_INSTRUMENT


def test_mandate_problems_go_to_a_human():
    d = R.evaluate(ctx(failure_class=FailureClass.MANDATE_PROBLEM), ActionType.RETRY)
    assert d.action is ActionType.ESCALATE
    assert d.rule_id in {
        "G04_HARD_FAILURE_NOT_RETRYABLE",
        "G05_MANDATE_REQUIRES_HUMAN",
    }


# --------------------------------------------------------------------------
# Double-charge prevention
# --------------------------------------------------------------------------

def test_settled_payment_blocks_all_further_action():
    d = R.evaluate(ctx(already_recovered=True), ActionType.RETRY)
    assert not d.is_executable
    assert d.rule_id == "G02_ALREADY_RECOVERED"


def test_in_flight_action_blocks_a_concurrent_one():
    """The classic race: a scheduled retry firing while the customer pays."""
    d = R.evaluate(ctx(action_in_flight=True), ActionType.RETRY)
    assert not d.is_executable
    assert d.rule_id == "G03_ACTION_ALREADY_IN_FLIGHT"


def test_charge_requires_an_idempotency_key():
    d = R.evaluate(ctx(idempotency_key=None), ActionType.RETRY)
    assert not d.is_executable
    assert d.rule_id == "G11_MISSING_IDEMPOTENCY_KEY"


def test_retry_cap_is_enforced():
    d = R.evaluate(ctx(retry_count=R.MAX_RETRY_ATTEMPTS), ActionType.RETRY)
    assert not d.is_executable
    assert d.rule_id == "G06_RETRY_CAP_REACHED"


def test_issuer_downtime_defers_rather_than_burning_an_attempt():
    d = R.evaluate(
        ctx(failure_class=FailureClass.ISSUER_DOWN, hours_since_failure=0.5),
        ActionType.RETRY,
    )
    assert not d.is_executable
    assert d.rule_id == "G08_ISSUER_DOWN_DEFER"


# --------------------------------------------------------------------------
# Contactability
# --------------------------------------------------------------------------

def test_no_consent_blocks_customer_contact():
    d = R.evaluate(ctx(has_messaging_consent=False), ActionType.REMINDER)
    assert not d.is_executable
    assert d.rule_id == "G09_NO_MESSAGING_CONSENT"


def test_dnd_blocks_customer_contact():
    d = R.evaluate(ctx(is_dnd_registered=True), ActionType.REMINDER)
    assert not d.is_executable
    assert d.rule_id == "G09_DND_REGISTERED"


def test_consent_does_not_gate_a_machine_to_machine_retry():
    """A retry sends no message, so consent is irrelevant to it."""
    d = R.evaluate(ctx(has_messaging_consent=False), ActionType.RETRY)
    assert d.is_executable


def test_quiet_hours_blocks_messages_but_the_window_wraps_midnight():
    assert R.in_quiet_hours(23) is True
    assert R.in_quiet_hours(3) is True
    assert R.in_quiet_hours(12) is False
    d = R.evaluate(ctx(now=datetime(2026, 9, 15, 23, 30)), ActionType.REMINDER)
    assert not d.is_executable
    assert d.rule_id == "G10_QUIET_HOURS"


def test_frequency_cap_stops_nagging():
    d = R.evaluate(ctx(prior_actions_24h=R.MAX_ACTIONS_PER_24H), ActionType.REMINDER)
    assert not d.is_executable
    assert d.rule_id == "G07_FREQUENCY_CAP"


# --------------------------------------------------------------------------
# Human-in-the-loop
# --------------------------------------------------------------------------

def test_high_value_needs_approval_even_when_otherwise_valid():
    d = R.evaluate(
        ctx(amount_inr=R.AUTO_ACTION_VALUE_CEILING_INR + 1), ActionType.RETRY
    )
    assert d.disposition is Disposition.NEEDS_APPROVAL
    assert d.action is ActionType.RETRY      # the action is right...
    assert not d.is_executable               # ...but not automatically
    assert d.rule_id == "G12_VALUE_CEILING_APPROVAL"


def test_a_restrictive_gate_always_beats_a_later_permissive_one():
    """Ordering guarantee: a settled payment stays blocked even when small."""
    d = R.evaluate(ctx(already_recovered=True, amount_inr=10.0), ActionType.RETRY)
    assert d.rule_id == "G02_ALREADY_RECOVERED"


def test_every_decision_names_a_rule():
    """No decision may be unattributed -- that is the audit guarantee."""
    for fc in FailureClass:
        d = R.evaluate(ctx(failure_class=fc, raw_failure_code="x"))
        assert d.rule_id
        assert d.rule_id in R.explain_gates()
        assert d.reason


# --------------------------------------------------------------------------
# Scoring: the timing bug
# --------------------------------------------------------------------------

def test_abandoned_checkout_decays_fast():
    early = timing_multiplier(FailureClass.AUTH_ABANDONED, 0.1, NOON)
    later = timing_multiplier(FailureClass.AUTH_ABANDONED, 6.0, NOON)
    assert early > later * 2


def test_soft_decline_is_not_penalised_for_waiting_the_way_abandonment_is():
    """
    The original code applied one decay curve to everything. For insufficient
    funds, an immediate retry is worth *less* than a patient one, because the
    balance has not arrived yet.
    """
    mid_month = datetime(2026, 9, 15, 12, 0)
    immediate = timing_multiplier(FailureClass.SOFT_DECLINE, 0.5, mid_month)
    patient = timing_multiplier(FailureClass.SOFT_DECLINE, 48.0, mid_month)
    assert patient > immediate


def test_soft_decline_recovers_better_near_payday():
    near_payday = datetime(2026, 9, 29, 12, 0)
    mid_month = datetime(2026, 9, 12, 12, 0)
    assert timing_multiplier(
        FailureClass.SOFT_DECLINE, 48.0, near_payday
    ) > timing_multiplier(FailureClass.SOFT_DECLINE, 48.0, mid_month)


def test_soft_decline_retry_is_scheduled_toward_payday_not_immediately():
    mid_month = ctx(failure_class=FailureClass.SOFT_DECLINE, now=datetime(2026, 9, 10, 12, 0))
    assert recommend_delay_minutes(mid_month) > 12 * 60


def test_abandonment_is_chased_within_minutes():
    assert recommend_delay_minutes(ctx(failure_class=FailureClass.AUTH_ABANDONED)) <= 15


def test_unknown_failure_has_zero_probability():
    assert estimate_recovery_probability(ctx(failure_class=FailureClass.UNKNOWN)) == 0.0


def test_each_retry_lowers_the_estimate():
    p0 = estimate_recovery_probability(ctx(retry_count=0))
    p1 = estimate_recovery_probability(ctx(retry_count=1))
    p2 = estimate_recovery_probability(ctx(retry_count=2))
    assert p0 > p1 > p2


def test_amount_drives_expected_value_even_at_equal_probability():
    """
    The original score ignored amount entirely, so a Rs.40 and a Rs.80,000
    failure with identical history ranked the same.
    """
    small = ctx(amount_inr=40.0)
    large = ctx(amount_inr=80_000.0)
    assert estimate_recovery_probability(small) == estimate_recovery_probability(large)
    assert expected_value_inr(large, ActionType.RETRY) > expected_value_inr(
        small, ActionType.RETRY
    )


def test_tiny_recoveries_are_not_worth_the_action_cost():
    trivial = ctx(amount_inr=15.0, failure_class=FailureClass.SOFT_DECLINE)
    assert expected_value_inr(trivial, ActionType.ESCALATE) < 0
