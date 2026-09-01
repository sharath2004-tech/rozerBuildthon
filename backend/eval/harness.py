"""
Offline evaluation harness.

The point of this module is to answer the only question that matters about a
recovery system: *did it recover revenue that would not have arrived anyway?*

Most recovery demos report a recovery rate. A recovery rate is close to
meaningless on its own, because a meaningful share of failed payments recover
organically -- the customer notices, retries, and pays without any
intervention at all. A system that does nothing still shows a non-zero
"recovery rate". Claiming credit for it is the standard mistake.

So this harness runs three arms over the same generated population:

    holdout    no action taken at all      -> measures the organic rate
    baseline   retry everything, at once   -> the naive policy
    agent      policy gateway + scheduler  -> the system under test

and reports *incremental* lift over the holdout, with a bootstrap confidence
interval, plus net value after action costs.

Methodological note, and the thing to say out loud in the pitch: the
ground-truth simulator below is deliberately NOT the same model as
`app.services.scoring`. It uses different functional forms and different
constants. If the simulator and the policy shared a model, the evaluation
would only prove that the model agrees with itself. Keeping them independent
means the agent can genuinely score worse than baseline -- and early on, it
did.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Callable, Iterable

from app.models.domain import ActionType, Disposition, FailureClass, Rail, RecoveryContext
from app.rules import recovery_rules as R
from app.services.scoring import (
    ACTION_COST_INR,
    DEFAULT_MARGIN_RATE,
    recommend_delay_minutes,
)

# --------------------------------------------------------------------------
# Population generation
# --------------------------------------------------------------------------

#: Rough mix of failure families in an Indian payments stream. Abandonment
#: dominates because of mandatory 2FA on cards and UPI collect timeouts.
_FAMILY_MIX: list[tuple[FailureClass, float]] = [
    (FailureClass.AUTH_ABANDONED, 0.34),
    (FailureClass.SOFT_DECLINE, 0.24),
    (FailureClass.TECHNICAL, 0.16),
    (FailureClass.HARD_DECLINE, 0.11),
    (FailureClass.ISSUER_DOWN, 0.07),
    (FailureClass.MANDATE_PROBLEM, 0.05),
    (FailureClass.UNKNOWN, 0.03),
]

_RAIL_MIX: list[tuple[Rail, float]] = [
    (Rail.UPI, 0.52),
    (Rail.CARD, 0.28),
    (Rail.NETBANKING, 0.11),
    (Rail.WALLET, 0.05),
    (Rail.EMANDATE, 0.04),
]


def _weighted(rng: random.Random, choices: list[tuple]) -> object:
    r = rng.random()
    acc = 0.0
    for value, w in choices:
        acc += w
        if r <= acc:
            return value
    return choices[-1][0]


def _lognormal_amount(rng: random.Random) -> float:
    """
    Order values are heavily right-skewed: many small payments, a thin tail of
    large ones. A uniform distribution would hide the whole point of ranking
    by expected value.
    """
    return round(min(max(rng.lognormvariate(6.4, 1.15), 20.0), 250_000.0), 2)


@dataclass(frozen=True)
class GeneratedEvent:
    """A failed payment plus the latent traits the simulator needs."""

    ctx: RecoveryContext
    #: Latent per-customer propensity to sort things out unaided. Not visible
    #: to the policy -- this is ground truth the agent does not get to see.
    diligence: float
    #: Latent flag: is the underlying obstacle actually resolvable at all?
    resolvable: bool


def generate_population(n: int, seed: int = 7, now: datetime | None = None) -> list[GeneratedEvent]:
    rng = random.Random(seed)
    now = now or datetime(2026, 9, 26, 11, 0)   # late month: payday effects live
    out: list[GeneratedEvent] = []

    for i in range(n):
        family: FailureClass = _weighted(rng, _FAMILY_MIX)      # type: ignore[assignment]
        rail: Rail = _weighted(rng, _RAIL_MIX)                  # type: ignore[assignment]
        lifetime = int(abs(rng.gauss(8, 9)))

        ctx = RecoveryContext(
            payment_id=f"pay_{i:06d}",
            customer_id=f"cust_{rng.randrange(1, max(2, n // 3)):06d}",
            amount_inr=_lognormal_amount(rng),
            rail=rail,
            failure_class=family,
            raw_failure_code=family.value,
            retry_count=0,
            hours_since_failure=round(abs(rng.gauss(0.4, 0.5)), 2),
            prior_actions_24h=0,
            lifetime_payments=lifetime,
            lifetime_recoveries=min(lifetime, int(abs(rng.gauss(0.7, 1.2)))),
            has_messaging_consent=rng.random() < 0.78,
            is_dnd_registered=rng.random() < 0.09,
            already_recovered=False,
            action_in_flight=False,
            idempotency_key=f"idem_{i:06d}",
            now=now,
        )

        # Hard declines and revoked mandates are structurally unresolvable
        # without a new instrument, whatever anyone does.
        if family is FailureClass.HARD_DECLINE:
            resolvable = rng.random() < 0.35
        elif family is FailureClass.MANDATE_PROBLEM:
            resolvable = rng.random() < 0.40
        else:
            resolvable = rng.random() < 0.88

        out.append(
            GeneratedEvent(
                ctx=ctx,
                diligence=min(max(rng.gauss(0.35, 0.18), 0.0), 0.95),
                resolvable=resolvable,
            )
        )
    return out


# --------------------------------------------------------------------------
# Ground-truth simulator  (independent of app.services.scoring by design)
# --------------------------------------------------------------------------

#: Probability the customer fixes it themselves with no intervention.
_ORGANIC: dict[FailureClass, float] = {
    FailureClass.AUTH_ABANDONED: 0.26,
    FailureClass.SOFT_DECLINE: 0.19,
    FailureClass.TECHNICAL: 0.31,
    FailureClass.ISSUER_DOWN: 0.29,
    FailureClass.HARD_DECLINE: 0.06,
    FailureClass.MANDATE_PROBLEM: 0.08,
    FailureClass.UNKNOWN: 0.14,
}

#: Which interventions actually help which family, and by how much, when
#: delivered at a good moment. Anything absent is worth nothing.
_UPLIFT: dict[tuple[FailureClass, ActionType], float] = {
    (FailureClass.AUTH_ABANDONED, ActionType.CHECKOUT_RECOVERY): 0.34,
    (FailureClass.AUTH_ABANDONED, ActionType.REMINDER): 0.16,
    (FailureClass.AUTH_ABANDONED, ActionType.RETRY): 0.02,
    (FailureClass.SOFT_DECLINE, ActionType.RETRY): 0.30,
    (FailureClass.SOFT_DECLINE, ActionType.REMINDER): 0.12,
    (FailureClass.TECHNICAL, ActionType.RETRY): 0.44,
    (FailureClass.ISSUER_DOWN, ActionType.RETRY): 0.41,
    (FailureClass.HARD_DECLINE, ActionType.UPDATE_INSTRUMENT): 0.22,
    (FailureClass.HARD_DECLINE, ActionType.RETRY): 0.00,   # cannot work, ever
    (FailureClass.MANDATE_PROBLEM, ActionType.ESCALATE): 0.15,
    (FailureClass.MANDATE_PROBLEM, ActionType.UPDATE_INSTRUMENT): 0.12,
}


def _timing_quality(family: FailureClass, delay_min: int, now: datetime) -> float:
    """
    Fraction of the available uplift actually captured, given when we acted.
    Piecewise and family-specific, with different breakpoints from the
    policy's own curves so the two cannot trivially agree.
    """
    if family is FailureClass.AUTH_ABANDONED:
        if delay_min <= 10:
            return 1.0
        if delay_min <= 60:
            return 0.62
        if delay_min <= 360:
            return 0.28
        return 0.10

    if family is FailureClass.TECHNICAL:
        if delay_min < 5:
            return 0.40          # same transient still in effect
        if delay_min <= 120:
            return 1.0
        return 0.55

    if family is FailureClass.ISSUER_DOWN:
        return 0.30 if delay_min < 120 else 1.0

    if family is FailureClass.SOFT_DECLINE:
        # Ground truth: balance arrives on payday. Acting before it does is
        # mostly wasted, whatever the policy believes.
        act_at = now + timedelta(minutes=delay_min)
        import calendar

        last = calendar.monthrange(act_at.year, act_at.month)[1]
        dom = act_at.day
        near_payday = dom <= 4 or dom >= last - 2
        if delay_min < 240:
            return 0.35
        return 1.0 if near_payday else 0.55

    return 0.7


def simulate(
    event: GeneratedEvent,
    action: ActionType,
    delay_min: int,
    rng: random.Random,
) -> bool:
    """Did this payment end up recovered? Ground truth."""
    fam = event.ctx.failure_class

    organic = _ORGANIC[fam] * (0.5 + event.diligence)
    if not event.resolvable:
        organic *= 0.15

    if action in (ActionType.SUPPRESS, ActionType.ESCALATE):
        uplift = _UPLIFT.get((fam, action), 0.0)
    else:
        uplift = _UPLIFT.get((fam, action), 0.0) * _timing_quality(fam, delay_min, event.ctx.now)

    if not event.resolvable:
        uplift *= 0.10

    p = min(0.97, organic + uplift)
    return rng.random() < p


# --------------------------------------------------------------------------
# Arms
# --------------------------------------------------------------------------

@dataclass
class ArmResult:
    name: str
    n: int
    recovered: int
    recovered_gmv: float
    action_cost: float
    actions_taken: int
    escalations: int
    blocked: int
    per_case_recovered: list[int]
    per_case_net: list[float]

    @property
    def recovery_rate(self) -> float:
        return self.recovered / self.n if self.n else 0.0

    @property
    def net_margin(self) -> float:
        return self.recovered_gmv * DEFAULT_MARGIN_RATE - self.action_cost


Policy = Callable[[GeneratedEvent], tuple[ActionType, int, bool]]


def holdout_policy(_: GeneratedEvent) -> tuple[ActionType, int, bool]:
    """Do nothing. Measures the organic recovery rate."""
    return ActionType.SUPPRESS, 0, False


def baseline_policy(_: GeneratedEvent) -> tuple[ActionType, int, bool]:
    """Retry everything, immediately. The naive policy most systems start at."""
    return ActionType.RETRY, 0, True


def agent_policy(event: GeneratedEvent) -> tuple[ActionType, int, bool]:
    """
    The system under test: deterministic default action, authorised by the
    policy gateway, scheduled by the timing model.

    NEEDS_APPROVAL is treated as *not executed* in this harness. That is the
    conservative reading -- it means the agent gets no credit for high-value
    recoveries a human would probably have approved. Overstating automation
    would flatter the result.
    """
    proposed = R.default_action(event.ctx)
    decision = R.evaluate(event.ctx, proposed)

    if decision.disposition is Disposition.ALLOWED:
        return decision.action, recommend_delay_minutes(event.ctx), True
    if decision.action is ActionType.ESCALATE:
        return ActionType.ESCALATE, 0, False
    return ActionType.SUPPRESS, 0, False


def agent_no_timing_policy(event: GeneratedEvent) -> tuple[ActionType, int, bool]:
    """
    Ablation: correct action per failure family, gates applied, but every
    action fired immediately. Isolates the contribution of the scheduler.
    """
    proposed = R.default_action(event.ctx)
    decision = R.evaluate(event.ctx, proposed)
    if decision.disposition is Disposition.ALLOWED:
        return decision.action, 0, True
    if decision.action is ActionType.ESCALATE:
        return ActionType.ESCALATE, 0, False
    return ActionType.SUPPRESS, 0, False


def agent_no_gates_policy(event: GeneratedEvent) -> tuple[ActionType, int, bool]:
    """
    Ablation: correct action and correct timing, but the policy gateway is
    bypassed entirely -- everything executes.

    Read the result of this arm carefully. It will often score *better* on net
    margin than the gated agent, because the simulator models revenue but not
    the cost of a compliance breach, a DND violation, an unapproved
    high-value charge, or the churn caused by messaging someone at 3am.
    Guardrails are not free; their return is avoided tail risk that this
    harness cannot see. That is a limitation of the evaluation, not an
    argument against the guardrails -- and it is worth stating plainly rather
    than quietly picking whichever arm flatters the system.
    """
    proposed = R.default_action(event.ctx)
    if proposed is ActionType.ESCALATE:
        return ActionType.ESCALATE, 0, False
    return proposed, recommend_delay_minutes(event.ctx), True


def run_arm(name: str, population: Iterable[GeneratedEvent], policy: Policy, seed: int) -> ArmResult:
    rng = random.Random(seed)
    res = ArmResult(name, 0, 0, 0.0, 0.0, 0, 0, 0, [], [])

    for event in population:
        action, delay, executed = policy(event)
        res.n += 1

        cost = ACTION_COST_INR.get(action, 0.0) if action is not ActionType.SUPPRESS else 0.0
        if action is ActionType.ESCALATE:
            res.escalations += 1
        if executed:
            res.actions_taken += 1
        elif action is ActionType.SUPPRESS:
            res.blocked += 1

        recovered = simulate(event, action if executed or action is ActionType.ESCALATE
                             else ActionType.SUPPRESS, delay, rng)

        res.action_cost += cost
        res.per_case_recovered.append(1 if recovered else 0)
        gain = event.ctx.amount_inr * DEFAULT_MARGIN_RATE if recovered else 0.0
        res.per_case_net.append(gain - cost)
        if recovered:
            res.recovered += 1
            res.recovered_gmv += event.ctx.amount_inr

    return res


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def bootstrap_ci(
    treated: list[float],
    control: list[float],
    iterations: int = 2000,
    seed: int = 11,
) -> tuple[float, float, float]:
    """
    Bootstrap CI for the difference in means between two arms.

    Reported because a single point estimate off one simulated population is
    not evidence of anything. Returns (point_estimate, lo95, hi95).
    """
    rng = random.Random(seed)
    point = statistics.fmean(treated) - statistics.fmean(control)
    diffs = []
    for _ in range(iterations):
        t = statistics.fmean(rng.choices(treated, k=len(treated)))
        c = statistics.fmean(rng.choices(control, k=len(control)))
        diffs.append(t - c)
    diffs.sort()
    lo = diffs[int(0.025 * len(diffs))]
    hi = diffs[int(0.975 * len(diffs))]
    return point, lo, hi
