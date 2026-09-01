# Engineering log — what broke and how it was fixed

Kept live during development. The buildathon asks for this explicitly, and it
is the most useful section to write honestly: the bugs a payments system
produces are specific, and how you found them says more than a feature list.

---

## 1. Unknown failure reasons authorised a live charge (fail-open)

**Severity: high.** This was a real bug in the first version, not a
hypothetical.

The original scoring function started every payment at 50 and adjusted:

```python
score = 50
if payment.previous_payments >= 5:              score += 10
if payment.previous_successful_recoveries >= 2: score += 15
if   payment.failure_reason == "insufficient_funds": score += 5
elif payment.failure_reason == "technical_error":    score += 10
elif payment.failure_reason == "expired_card":       score -= 15
...
if score >= 75: return "retry_payment"
```

An unrecognised `failure_reason` matched none of the branches, so it received
**no adjustment at all** and was silently treated as neutral. A customer with
five prior payments and two prior recoveries therefore scored
50 + 10 + 15 = **75**, hit the `>= 75` branch, and returned `retry_payment`.

So: a failure code nobody had classified would trigger an automatic charge
attempt against a customer's card, purely because they had a good history.

**Root cause.** Absence of a matching rule was interpreted as permission. In a
money path it has to mean the opposite.

**Fix.** `taxonomy.classify()` returns `FailureClass.UNKNOWN` for anything
unmapped — including `None` and empty string — and gate `G01` blocks and
escalates on `UNKNOWN` before any other logic runs. Regression test:
`test_unknown_failure_reason_never_authorises_a_charge`.

**Generalisation applied elsewhere.** Every gate now fails closed, and
`test_every_decision_names_a_rule` asserts that no decision can be returned
without naming the rule that produced it.

---

## 2. The timing model was directionally wrong for insufficient funds

**Severity: medium — silently halves recovery on the second-largest failure
family.**

The original code applied one flat decay to every failure type:

```python
score -= payment.days_since_failure * 3
```

That encodes "sooner is always better." True for an abandoned checkout, where
purchase intent has a half-life measured in minutes. **False** for
insufficient funds, where the customer's balance genuinely is not there yet
and probability of success *rises* as they approach a salary credit. The old
code actively penalised waiting — the one thing that actually works for that
family — and would fire an immediate retry into an empty account.

**Fix.** `timing_multiplier()` is now reason-dependent and non-monotonic where
the underlying process is non-monotonic. Soft declines are scored against
distance to the next plausible payday (1st of month and last working day,
which is where Indian salary cycles cluster); abandonment decays with a
45-minute half-life; technical failures are suppressed for the first 15
minutes so a retry does not land inside the same transient fault.

**Measured effect.** The ablation arm `agent_no_timing` fires the same actions
with zero delay and recovers 30.24% against the scheduled agent's 37.81% —
scheduling alone is worth about 7.6pp, or +24.21 net margin per case.

---

## 3. Amount was absent from prioritisation entirely

The project plan's own risk table listed transaction value as a scoring
signal. The implementation never read `amount`. A Rs.40 failure and a
Rs.80,000 failure with identical history produced an identical score and
identical treatment.

**Fix.** Probability and priority were separated. `p_recover` answers "will
this work?"; `expected_value_inr = p * amount * margin - action_cost` answers
"is it worth doing?". Queue ordering uses expected value, so a large uncertain
recovery correctly outranks a small near-certain one, and the system can
decline a technically-winnable Rs.15 recovery on economic grounds.

---

## 4. Hard declines were excluded by arithmetic accident, not by a rule

Tracing the old scoring by hand: `expired_card` capped out at
50 + 10 + 15 − 15 = 60, which stayed below the 75 retry threshold. So the
system never auto-retried an expired card — but only because the numbers
happened not to reach the line. Nudge any weight upward and it would have.

A safety property that holds by coincidence is not a safety property.

**Fix.** `G04` blocks retry on `HARD_DECLINE` and `MANDATE_PROBLEM`
categorically, independent of any score, and downgrades the action to
`UPDATE_INSTRUMENT`. Four parametrised tests cover the specific codes.

---

## 5. The gate inventory silently drifted from the implementation

Caught by `test_every_decision_names_a_rule`, which asserts every returned
`rule_id` appears in `explain_gates()`. `evaluate()` could return
`G00_DEFAULT_ESCALATION` for a mandate problem, but `explain_gates()` — which
feeds the dashboard's policy view and the architecture write-up — had no entry
for it. So the documentation would have under-reported the system's own
behaviour on day one.

**Fix.** Added the missing entry. The more useful outcome is the test itself:
documentation drift is now a failing build rather than something discovered
during a demo.

---

## 6. The evaluation initially flattered the system

First version of the harness reused `services.scoring` as the ground-truth
simulator. It produced excellent numbers and they meant nothing — the
evaluation was only demonstrating that the model agreed with itself.

**Fix.** `eval/harness.py` now has an independent latent model with different
functional forms, different constants, different timing breakpoints, plus
per-customer latent traits (`diligence`, `resolvable`) that the policy never
observes. The agent can now genuinely lose, and during tuning it did.

**Second-order finding.** With an honest simulator, the ablation
`agent_no_gates` — same actions, same timing, policy gateway bypassed — scores
*better* (44.24% recovery, +182.53/case) than the gated agent. That is not a
bug in the gates. It is the harness being unable to price a DND violation, an
unapproved high-value charge, or the churn from a 3am message. The number is
left in `EVAL.md` rather than removed, because an evaluation that shows
guardrails as free upside is measuring the wrong thing.

---

## 7. Repository was not actually submittable

Less interesting but it would have sunk the submission: no git repository,
empty `requirements.txt`, empty `README.md`, and two virtualenvs sitting
inside the project tree ready to be committed. The deliverable *is* a public
repo.

**Fix.** `git init`, a `.gitignore` covering `venv/`, `.venv/`, `__pycache__`,
`.env` and `*.db`, a pinned `requirements.txt`, `.env.example` with no real
values, and this file.
