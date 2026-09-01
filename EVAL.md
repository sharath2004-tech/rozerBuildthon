# Evaluation

_Generated 2026-09-01 18:07 — n=8,000 synthetic failed payments, seed=7._

## Why there is a holdout

A share of failed payments recover on their own: the customer notices, retries, and pays with no intervention. Any system that reports a raw recovery rate is therefore claiming credit for revenue it did not cause. The holdout arm receives no action at all, which makes the organic rate visible and lets every other number be stated as lift *over* it.

The ground-truth simulator is intentionally a different model from the policy's own scoring — different functional forms, different constants. If they shared a model the evaluation would only show that the model agrees with itself.

## Arms

| arm | recovery rate | recovered GMV | actions | escalations | suppressed | action cost | net margin |
|---|---|---|---|---|---|---|---|
| `holdout` | 16.86% | Rs.1,696,041 | 0 | 0 | 8,000 | Rs.0 | Rs.593,615 |
| `baseline` | 23.04% | Rs.2,323,981 | 8,000 | 0 | 0 | Rs.24,000 | Rs.789,393 |
| `agent_no_timing` | 30.24% | Rs.2,711,722 | 5,566 | 653 | 1,781 | Rs.40,102 | Rs.909,000 |
| `agent_no_gates` | 44.24% | Rs.4,294,312 | 7,347 | 653 | 0 | Rs.42,755 | Rs.1,460,254 |
| `agent` | 37.81% | Rs.3,265,067 | 5,566 | 653 | 1,781 | Rs.40,102 | Rs.1,102,671 |

## Incremental effect vs holdout

| comparison | metric | point estimate | 95% CI |
|---|---|---|---|
| baseline − holdout | recovery rate | +6.17% | [+4.89%, +7.38%] |
| baseline − holdout | net margin / case | +24.47 | [+11.76, +37.51] |
| agent − holdout | recovery rate | +20.95% | [+19.57%, +22.30%] |
| agent − holdout | net margin / case | +63.63 | [+51.19, +76.52] |

## Agent vs baseline

Net margin per case: **+39.16** (95% CI [+26.09, +52.72]) against the retry-everything baseline.

The baseline fires 8,000 charge attempts to the agent's 5,566. Fewer, better-timed actions is the whole thesis: the agent declines to retry terminal declines at all, defers soft declines toward payday, and chases abandoned checkouts within minutes instead of treating every failure identically.

## Ablations — where the lift actually comes from

Attributing the whole gain to 'AI' would be lazy. Removing one component at a time shows which part is load-bearing.

| arm | what changed | recovery rate | net margin / case |
|---|---|---|---|
| `baseline` | retry everything, immediately | 23.04% | +98.67 |
| `agent_no_timing` | right action per family, fired immediately | 30.24% | +113.63 |
| `agent` | right action + scheduled timing + gates | 37.81% | +137.83 |
| `agent_no_gates` | right action + timing, **gateway bypassed** | 44.24% | +182.53 |

**Scheduling is worth +24.21 net margin per case** (95% CI [+11.06, +37.49]) on top of simply choosing the right action — comparing `agent` against `agent_no_timing`. Deciding *when* is not a garnish on deciding *what*; it is a large share of the value.

**The gateway costs -44.70 net margin per case in this simulator** (95% CI [-59.84, -29.48]). That sign is expected and is reported rather than hidden: the harness models recovered revenue but not the cost of a DND violation, an unapproved high-value charge, or a customer messaged at 3am. Guardrails buy avoided tail risk, which this evaluation is structurally unable to price. Any recovery system whose eval shows guardrails as pure upside is measuring the wrong thing.

## Honest caveats

- The population is synthetic. These numbers demonstrate that the evaluation *method* works and that the policy beats a naive baseline **under the simulator's assumptions**. They are not a claim about production lift.
- `NEEDS_APPROVAL` cases are counted as not executed, so the agent gets no credit for high-value recoveries a merchant would likely have approved. This understates the agent.
- Organic recovery is modelled as a single draw rather than a process over time, so repeated organic attempts are not represented.
- Action costs are estimates, and the retry cost bundles a guess at the expected cost of consuming scheme attempt allowance.
