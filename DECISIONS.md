# Decisions and tradeoffs

Written so a reviewer can see what was chosen deliberately versus what was
simply not finished. Every cut below was a judgement about where the marginal
hour was worth most, with roughly four days from plan to submission.

---

## Cut: five-provider LLM fallback chain → one provider

**Original plan.** Groq primary, falling back through Gemini, Cerebras,
Hugging Face and Cohere.

**Decision.** One provider (Gemini), plus a deterministic template fallback.

**Why.** Five providers is five auth schemes, five response shapes, five
rate-limit behaviours and five failure modes to test, in service of a problem
that does not exist for this system: the LLM is not on the critical path, so a
provider outage degrades message *quality*, not correctness. Nothing about
which model vendor was used demonstrates payments competence. The engineering
hours went to the policy gateway and the evaluation harness instead.

**What was kept from the idea.** Provider resilience in the form that actually
matters — the system runs end to end with **no API key at all**, falling back
to deterministic templates. Tests and evaluation never touch a network.

---

## Kept: LangGraph, as orchestration only

**Tension.** The workflow is linear, so a plain state machine would do, and
LangGraph adds a dependency to justify.

**Decision.** Keep it, but confine it. Graph nodes call pure functions in
`services/` and `rules/`; no financial logic lives in a node body. The gateway
is unit-tested with no LangGraph import at all — all 30 guardrail tests run
against plain functions.

**Why.** The graph gives an inspectable execution trace per case, which is
worth something for the audit view. But if the agent framework can be removed
without touching a single policy decision, the policy layer is properly
isolated. That property is the point.

---

## Cut: React + Vite → Streamlit

The dashboard is a viewing surface for decisions made elsewhere. A day of
frontend work buys presentation; the same day spent on the evaluation harness
buys a defensible number. Ten dashboard tabs from the original diagram were
also cut to three — queue, case detail, results — because ten shallow tabs is
worse than three that work.

---

## Cut: live webhook listener → recorded payloads plus correct verification

**Why.** What is worth demonstrating about webhooks is that signatures are
verified correctly — HMAC-SHA256 over the **raw request body**, before any
JSON parsing, which is the classic mistake. That is demonstrable against
recorded test payloads without a public endpoint, a tunnel, or deployment.
Test-mode credentials only; no live keys anywhere.

---

## Cut: trained ML model → documented heuristic with a seam

`estimate_recovery_probability()` is an interpretable heuristic with stated
priors, not a fitted model.

**Why.** With synthetic data, a trained model would report accuracy numbers
that mean nothing. A heuristic whose assumptions are inspectable is more
honest and, at this stage, more useful. The function signature is the seam: it
takes a `RecoveryContext` and returns a probability, so a real model replaces
the body without touching a caller once outcome data exists.

Claiming a model where there is a lookup table is the single easiest way to
lose credibility in a technical review.

---

## Chosen: separate probability from priority

The original scoring conflated "will this recover?" with "is this worth
chasing?" into one 0–100 number, and omitted transaction amount entirely.

Splitting them into `p_recover` and
`expected_value = p * amount * margin - action_cost` gives the system a real
objective function, and makes **"take no action"** a legitimate, defensible
output rather than a failure to decide.

---

## Chosen: the gateway is the product

Most of the engineering hours went into `rules/recovery_rules.py` and its
tests rather than into features. Twelve ordered gates, each returning the
rule ID that decided the case, evaluated most-catastrophic-first so a later
permissive rule can never override an earlier restrictive one.

**Why.** In payments, the interesting capability is not acting — it is
declining to act, correctly, for a reason you can name afterwards. A system
that recovers 40% of failures while occasionally double-charging or messaging
DND-registered customers is worth less than one that recovers 30% and never
does.

---

## Chosen: report the finding that undercuts the guardrails

The `agent_no_gates` ablation scores better on simulated net margin than the
gated agent. Removing that arm from `EVAL.md` would have made the results look
cleaner.

It stays, with an explanation: the simulator prices recovered revenue and
cannot price regulatory breach, scheme penalties, or churn. The honest reading
is that guardrails buy tail-risk reduction an offline harness cannot value —
not that they are a net negative.

---

## Known gaps

- The population is synthetic; no claim is made about production lift.
- Failure codes in `taxonomy.py` are modelled on common gateway reasons and
  should be reconciled against Razorpay's current error-code documentation.
  The mapping is deliberately data rather than logic, so this is a one-file
  change.
- Organic recovery is a single draw, not a process over time.
- Action costs are estimates; the retry cost bundles a guess at the expected
  cost of consuming scheme attempt allowance.
- The action-to-failure-family mapping is a shared assumption between the
  policy and the simulator. The timing curves and constants are independent,
  but a sharp reviewer should push on this — it is the weakest joint in the
  evaluation, and the ablation table is structured so the effect can be seen
  rather than hidden.
