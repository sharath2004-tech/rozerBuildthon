# AI Revenue Recovery Agent

**Razorpay AI Buildathon 2026 — Track 3 (AI Revenue Recovery)**

A bounded recovery agent for failed payments. It classifies why a payment
failed, decides what the appropriate intervention is, decides *when* to
deliver it, and then asks a deterministic policy gateway whether it is
allowed to act at all.

The design commitment, and the thing everything else follows from:

> **The LLM recommends. Deterministic rules authorise. Nothing reaches the
> money path on a model's say-so.**

---

## The question this project actually answers

Not "can an agent retry failed payments" — anything can retry a payment. The
harder questions, in order:

1. **Why did it fail?** A canonical taxonomy, with hard declines separated
   from soft ones. Retrying an expired card cannot succeed, consumes scheme
   attempt allowance, and can attract penalties.
2. **What should we do?** Action follows failure family, not a single score.
   An abandoned checkout needs a live link; a dead card needs a new card.
3. **When?** The most under-served question in dunning. An abandoned checkout
   is worth chasing in five minutes. An insufficient-funds failure is worth
   chasing near payday — retrying it immediately is close to worthless,
   because the money genuinely is not there yet.
4. **Are we allowed to?** Consent, DND, quiet hours, retry caps, frequency
   caps, value ceilings, idempotency.
5. **Did it recover revenue that would not have arrived anyway?** Measured
   against a no-action holdout, because a meaningful share of failed payments
   recover organically and claiming credit for those is the standard mistake.

---

## Results

From `python -m eval.run_eval` (n=8,000 synthetic failures, seed 7). Full
report with confidence intervals in [EVAL.md](EVAL.md).

| arm | what it does | recovery rate | net margin / case |
|---|---|---|---|
| `holdout` | nothing at all | 16.86% | +74.20 |
| `baseline` | retry everything, immediately | 23.04% | +98.67 |
| `agent_no_timing` | right action, fired immediately | 30.24% | +113.63 |
| **`agent`** | **right action, scheduled, gated** | **37.81%** | **+137.83** |

Incremental recovery rate over holdout: **+20.95pp** (95% CI +19.57 to
+22.30). The baseline manages +6.17pp for *more* charge attempts — 8,000
against the agent's 5,566.

Decomposing that lift matters more than the headline:

- choosing the right action per failure family is worth ~7pp
- **scheduling is worth another ~7.6pp**, or +24.21 net margin per case
- the guardrails *cost* 44.70 per case **in this simulator**, and that number
  is reported rather than buried — see below

### The uncomfortable finding

Bypassing the policy gateway scores **better** on simulated net margin
(44.24% recovery, +182.53/case) than running with it. This is reported
deliberately. The harness prices recovered revenue but cannot price a DND
violation, an unapproved high-value charge, or the churn from messaging
someone at 3am. Guardrails buy avoided tail risk, which an offline simulator
is structurally unable to value.

Any recovery system whose evaluation shows guardrails as pure upside is
measuring the wrong thing.

---

## Architecture

```
CSV / webhook events
        |
        v
  Ingestion + normalisation          (Pydantic)
        |
        v
  Failure taxonomy                   rules/taxonomy.py
  raw code -> FailureClass           unmapped -> UNKNOWN
        |
        v
  Scoring                            services/scoring.py
  p_recover | timing | expected value
        |
        v
+-----------------------------------------+
|  DETERMINISTIC POLICY GATEWAY           |   rules/recovery_rules.py
|  the financial decision boundary        |
|                                         |
|  G01 unknown failure -> fail closed     |
|  G02 already recovered                  |
|  G03 action in flight (race guard)      |
|  G04 hard decline never retried         |
|  G05 mandate flows stay manual          |
|  G06 retry cap                          |
|  G07 frequency cap                      |
|  G08 issuer downtime defer              |
|  G09 consent / DND                      |
|  G10 quiet hours                        |
|  G11 idempotency key required           |
|  G12 value ceiling -> human approval    |
+-----------------------------------------+
     |            |               |
  ALLOWED   NEEDS_APPROVAL     BLOCKED
     |            |               |
     v            v               v
  execute    human queue      suppress
     |
     v
  outcome recording -> eval / dashboard
```

The LLM sits **beside** this pipeline, never inside it. It classifies
unrecognised failure strings (constrained to the taxonomy enum), drafts
customer message copy (behind an output validator enforcing schema, length,
timing bounds and a forbidden-term filter), and explains decisions in prose.
It never selects an action, computes an amount, or mints an idempotency key.
If every model call fails, the system degrades to deterministic templates and
keeps running.

---

## Layout

```
backend/
  app/
    models/domain.py          RecoveryContext, PolicyDecision, enums
    rules/taxonomy.py         failure code -> FailureClass
    rules/recovery_rules.py   the policy gateway  <- start here
    services/scoring.py       probability, timing, expected value
  eval/
    harness.py                population generator + ground-truth simulator
    run_eval.py               arms, ablations, bootstrap CIs
  tests/
    test_policy_gateway.py    30 guardrail tests
EVAL.md                       generated evaluation report
DECISIONS.md                  what was cut and why
WHAT_BROKE.md                 engineering log
```

`rules/recovery_rules.py` and `eval/` are the two files worth reading first.

---

## Running it

```bash
cd backend
python -m venv venv && venv\Scripts\activate      # Windows
pip install -r requirements.txt

pytest tests/ -q                                  # 30 guardrail tests
python -m eval.run_eval --n 8000 --seed 7         # regenerates EVAL.md
```

No API key is required for the tests or the evaluation — both are fully
deterministic. `GEMINI_API_KEY` in `backend/.env` enables message generation;
without it the system falls back to templates. Copy `.env.example` to `.env`.

Razorpay integration uses **test-mode credentials only**.

---

## What this deliberately does not do

Scope decisions, with reasoning, are in [DECISIONS.md](DECISIONS.md). The
short version: one LLM provider instead of five, because a five-provider
fallback chain is five auth schemes and five failure modes in service of a
problem nobody has; Streamlit instead of React, because the dashboard is not
the interesting part; and no live webhook listener, because correct HMAC
signature verification against recorded payloads demonstrates the same
competence without the deployment surface.
