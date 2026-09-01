"""
Recovery scoring: probability, timing, and expected value.

Three quantities that the original single 0-100 "risk score" conflated, and
which need to be separate because they answer different questions:

  p_recover   -- how likely is this to succeed if we act?      (a belief)
  timing      -- when is that likelihood highest?              (a schedule)
  priority    -- is acting worth what it costs?                 (a decision)

The old score also had a structural bug worth naming, because it is a nice
illustration of why these must be separated: it applied a flat
`-3 * days_since_failure` decay, encoding "sooner is always better". That is
right for an abandoned checkout, where intent goes cold in minutes, and
exactly wrong for insufficient funds, where the money genuinely is not there
yet and the probability of success *rises* as the customer approaches payday.
A single monotonic decay cannot express both. `timing_multiplier` below is
reason-dependent for this reason.

Everything here is an interpretable heuristic with stated priors, not a
trained model. That is a deliberate choice: with synthetic data a fitted
model would report meaningless accuracy. `estimate_recovery_probability` is
the seam where a real model drops in once outcome data exists -- the
signature stays, the body changes.
"""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta

from app.models.domain import ActionType, FailureClass, Rail, RecoveryContext

# --------------------------------------------------------------------------
# Priors
#
# Base success rates per failure family, given one well-timed action. These
# are informed guesses stated openly rather than fitted values presented as
# fact; the eval harness measures policy *lift*, which is robust to the
# absolute level being somewhat off.
# --------------------------------------------------------------------------

_BASE_P: dict[FailureClass, float] = {
    FailureClass.TECHNICAL: 0.72,        # nothing actually wrong; a retry usually lands
    FailureClass.ISSUER_DOWN: 0.68,      # succeeds once the window closes
    FailureClass.AUTH_ABANDONED: 0.45,   # intent was real but attention has moved on
    FailureClass.SOFT_DECLINE: 0.38,     # depends almost entirely on timing
    FailureClass.MANDATE_PROBLEM: 0.20,  # needs a regulated re-auth
    FailureClass.HARD_DECLINE: 0.12,     # only via a new instrument
    FailureClass.UNKNOWN: 0.00,          # never acted on; see gate G01
}

#: Rail effects. UPI re-collects convert well and are cheap; e-mandate
#: failures are structurally harder because the instrument itself is impaired.
_RAIL_FACTOR: dict[Rail, float] = {
    Rail.UPI: 1.12,
    Rail.CARD: 1.00,
    Rail.NETBANKING: 0.94,
    Rail.WALLET: 1.05,
    Rail.EMANDATE: 0.82,
    Rail.UNKNOWN: 0.90,
}

#: Marginal cost of one action, in rupees. Retry cost bundles gateway fees
#: with the expected cost of consuming a scheme attempt allowance.
ACTION_COST_INR: dict[ActionType, float] = {
    ActionType.RETRY: 3.00,
    ActionType.REMINDER: 0.35,
    ActionType.CHECKOUT_RECOVERY: 0.60,
    ActionType.UPDATE_INSTRUMENT: 0.60,
    ActionType.ESCALATE: 45.00,   # a few minutes of an analyst's attention
    ActionType.SUPPRESS: 0.00,
}

#: Merchant contribution margin. Recovering Rs.1,000 of GMV is not worth
#: Rs.1,000 to the merchant, so expected value is computed on margin.
DEFAULT_MARGIN_RATE: float = 0.35


# --------------------------------------------------------------------------
# Timing
# --------------------------------------------------------------------------

def _days_until_payday(now: datetime) -> int:
    """
    Distance in days to the next plausible salary credit.

    Indian salary cycles cluster hard on the 1st and on the last working day
    of the month, so a balance-related failure late in the month is often a
    few days from resolving itself. This is the single most useful timing
    signal for soft declines and is absent from most dunning systems.
    """
    last_day = calendar.monthrange(now.year, now.month)[1]
    candidates = []

    # Last working day of this month (walk back off the weekend).
    d = now.replace(day=last_day)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    candidates.append(d)

    # First of next month.
    first_next = (now.replace(day=last_day) + timedelta(days=1))
    candidates.append(first_next)

    future = [(c.date() - now.date()).days for c in candidates]
    future = [f for f in future if f >= 0]
    return min(future) if future else 0


def timing_multiplier(
    failure_class: FailureClass,
    hours_since_failure: float,
    now: datetime,
) -> float:
    """
    How much of this failure's recoverable probability is available *now*.

    Returns a multiplier in roughly [0.15, 1.25]. Deliberately different in
    shape per failure family:

      AUTH_ABANDONED  monotonic decay, ~45min half-life -- perishable intent
      TECHNICAL       low immediately, peaks ~30-90min, then slowly decays
      ISSUER_DOWN     suppressed until the outage plausibly clears
      SOFT_DECLINE    non-monotonic -- rises toward payday
      others          mildly decaying
    """
    h = max(0.0, hours_since_failure)

    if failure_class is FailureClass.AUTH_ABANDONED:
        # Perishable. Half-life 0.75h: catch them while the tab is still open.
        return max(0.15, 0.5 ** (h / 0.75))

    if failure_class is FailureClass.TECHNICAL:
        # Retrying into the same transient fault is wasteful; wait a beat.
        if h < 0.25:
            return 0.55
        if h <= 1.5:
            return 1.20
        return max(0.35, 1.20 * (0.5 ** ((h - 1.5) / 24.0)))

    if failure_class is FailureClass.ISSUER_DOWN:
        # Assume a typical window of a couple of hours.
        if h < 2.0:
            return 0.25
        return 1.15

    if failure_class is FailureClass.SOFT_DECLINE:
        # The money is not there yet. Waiting is not decay, it is strategy.
        days_out = _days_until_payday(now)
        if days_out <= 1:
            payday = 1.25          # salary just landed or lands tomorrow
        elif days_out <= 3:
            payday = 1.05
        elif days_out <= 7:
            payday = 0.80
        else:
            payday = 0.60
        # An immediate retry on an empty account is near-worthless regardless.
        immediacy_penalty = 0.45 if h < 6 else 1.0
        return payday * immediacy_penalty

    return max(0.30, 0.5 ** (h / 72.0))


def recommend_delay_minutes(ctx: RecoveryContext) -> int:
    """
    When to act, in minutes from now. This is the scheduler's opinion and the
    part of the system that actually moves the recovery rate.
    """
    fc = ctx.failure_class

    if fc is FailureClass.AUTH_ABANDONED:
        return 5                                  # while intent is warm
    if fc is FailureClass.TECHNICAL:
        return 30                                 # let the transient clear
    if fc is FailureClass.ISSUER_DOWN:
        return 150                                # after the window
    if fc is FailureClass.SOFT_DECLINE:
        days_out = _days_until_payday(ctx.now)
        if days_out <= 1:
            return 60                             # money is arriving
        return min(days_out, 7) * 24 * 60         # wait for payday
    if fc is FailureClass.HARD_DECLINE:
        return 15                                 # ask for a new instrument
    return 60


# --------------------------------------------------------------------------
# Probability
# --------------------------------------------------------------------------

def estimate_recovery_probability(ctx: RecoveryContext) -> float:
    """
    P(this payment is recovered | we take the default action now).

    Seam for a real model. Until outcome data exists, a documented heuristic
    beats a model fitted on synthetic data, because at least the heuristic's
    assumptions are inspectable.
    """
    if ctx.failure_class is FailureClass.UNKNOWN:
        return 0.0

    p = _BASE_P[ctx.failure_class]
    p *= _RAIL_FACTOR.get(ctx.rail, 1.0)
    p *= timing_multiplier(ctx.failure_class, ctx.hours_since_failure, ctx.now)

    # A customer who has paid many times before is a better bet than a
    # first-timer, but with diminishing returns.
    if ctx.lifetime_payments >= 20:
        p *= 1.18
    elif ctx.lifetime_payments >= 5:
        p *= 1.10

    # Someone who has been recovered before is unusually recoverable.
    if ctx.lifetime_recoveries >= 2:
        p *= 1.15

    # Each failed attempt is evidence the obstacle is real, not transient.
    p *= 0.62 ** ctx.retry_count

    return round(min(max(p, 0.0), 0.95), 4)


# --------------------------------------------------------------------------
# Value
# --------------------------------------------------------------------------

def expected_value_inr(
    ctx: RecoveryContext,
    action: ActionType,
    p_recover: float | None = None,
    margin_rate: float = DEFAULT_MARGIN_RATE,
) -> float:
    """
    Expected net contribution of taking `action`, in rupees.

        EV = p * amount * margin - cost(action)

    This is the number that makes "do nothing" a legitimate, defensible
    output. A Rs.40 recovery attempt that costs Rs.3 and succeeds 38% of the
    time earns 40*0.35*0.38 = Rs.5.32 against Rs.3 of cost -- thin. The same
    policy on a Rs.4,000 order earns Rs.532. Ranking by expected value rather
    than by probability is what stops the queue filling with cheap, winnable,
    pointless cases.
    """
    p = estimate_recovery_probability(ctx) if p_recover is None else p_recover
    gross = p * ctx.amount_inr * margin_rate
    return round(gross - ACTION_COST_INR.get(action, 0.0), 2)


def priority_score(ctx: RecoveryContext, action: ActionType) -> float:
    """
    Queue ordering key. Expected value, not probability -- so a large
    uncertain recovery outranks a small certain one.
    """
    return expected_value_inr(ctx, action)


def is_worth_acting(ctx: RecoveryContext, action: ActionType, floor_inr: float = 1.0) -> bool:
    """
    Whether the economics justify the action at all. The gateway decides if
    we *may* act; this decides if we *should*.
    """
    return expected_value_inr(ctx, action) >= floor_inr


def score_breakdown(ctx: RecoveryContext, action: ActionType) -> dict:
    """
    Per-case explanation for the dashboard. Every number the merchant sees
    should be traceable to a factor they can argue with.
    """
    p = estimate_recovery_probability(ctx)
    return {
        "failure_class": ctx.failure_class.value,
        "rail": ctx.rail.value,
        "base_probability": _BASE_P[ctx.failure_class],
        "rail_factor": _RAIL_FACTOR.get(ctx.rail, 1.0),
        "timing_multiplier": round(
            timing_multiplier(ctx.failure_class, ctx.hours_since_failure, ctx.now), 3
        ),
        "retry_penalty": round(0.62 ** ctx.retry_count, 3),
        "p_recover": p,
        "amount_inr": ctx.amount_inr,
        "margin_rate": DEFAULT_MARGIN_RATE,
        "action": action.value,
        "action_cost_inr": ACTION_COST_INR.get(action, 0.0),
        "expected_value_inr": expected_value_inr(ctx, action, p_recover=p),
        "recommended_delay_minutes": recommend_delay_minutes(ctx),
        "days_until_payday": _days_until_payday(ctx.now),
    }
