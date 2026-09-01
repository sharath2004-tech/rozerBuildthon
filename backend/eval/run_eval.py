"""
Entry point for the offline evaluation.

    python -m eval.run_eval --n 8000 --seed 7

Prints a comparison table and writes EVAL.md at the repo root.
"""

from __future__ import annotations

import argparse
import statistics
from datetime import datetime
from pathlib import Path

from eval.harness import (
    ArmResult,
    agent_no_gates_policy,
    agent_no_timing_policy,
    agent_policy,
    baseline_policy,
    bootstrap_ci,
    generate_population,
    holdout_policy,
    run_arm,
)


def _fmt_inr(v: float) -> str:
    return f"Rs.{v:,.0f}"


def build_report(n: int, seed: int) -> str:
    population = generate_population(n, seed=seed)

    holdout = run_arm("holdout", population, holdout_policy, seed=seed + 1)
    baseline = run_arm("baseline", population, baseline_policy, seed=seed + 1)
    no_timing = run_arm("agent_no_timing", population, agent_no_timing_policy, seed=seed + 1)
    no_gates = run_arm("agent_no_gates", population, agent_no_gates_policy, seed=seed + 1)
    agent = run_arm("agent", population, agent_policy, seed=seed + 1)

    arms: list[ArmResult] = [holdout, baseline, no_timing, no_gates, agent]

    lines: list[str] = []
    w = lines.append

    w("# Evaluation")
    w("")
    w(f"_Generated {datetime.now():%Y-%m-%d %H:%M} — "
      f"n={n:,} synthetic failed payments, seed={seed}._")
    w("")
    w("## Why there is a holdout")
    w("")
    w("A share of failed payments recover on their own: the customer notices, "
      "retries, and pays with no intervention. Any system that reports a raw "
      "recovery rate is therefore claiming credit for revenue it did not "
      "cause. The holdout arm receives no action at all, which makes the "
      "organic rate visible and lets every other number be stated as lift "
      "*over* it.")
    w("")
    w("The ground-truth simulator is intentionally a different model from the "
      "policy's own scoring — different functional forms, different constants. "
      "If they shared a model the evaluation would only show that the model "
      "agrees with itself.")
    w("")
    w("## Arms")
    w("")
    w("| arm | recovery rate | recovered GMV | actions | escalations | suppressed | action cost | net margin |")
    w("|---|---|---|---|---|---|---|---|")
    for a in arms:
        w(f"| `{a.name}` | {a.recovery_rate:6.2%} | {_fmt_inr(a.recovered_gmv)} "
          f"| {a.actions_taken:,} | {a.escalations:,} | {a.blocked:,} "
          f"| {_fmt_inr(a.action_cost)} | {_fmt_inr(a.net_margin)} |")
    w("")

    w("## Incremental effect vs holdout")
    w("")
    w("| comparison | metric | point estimate | 95% CI |")
    w("|---|---|---|---|")

    for arm in (baseline, agent):
        rate_pt, rate_lo, rate_hi = bootstrap_ci(
            [float(x) for x in arm.per_case_recovered],
            [float(x) for x in holdout.per_case_recovered],
        )
        w(f"| {arm.name} − holdout | recovery rate | {rate_pt:+.2%} "
          f"| [{rate_lo:+.2%}, {rate_hi:+.2%}] |")

        net_pt, net_lo, net_hi = bootstrap_ci(arm.per_case_net, holdout.per_case_net)
        w(f"| {arm.name} − holdout | net margin / case | {net_pt:+,.2f} "
          f"| [{net_lo:+,.2f}, {net_hi:+,.2f}] |")
    w("")

    ag_pt, ag_lo, ag_hi = bootstrap_ci(agent.per_case_net, baseline.per_case_net)
    w("## Agent vs baseline")
    w("")
    w(f"Net margin per case: **{ag_pt:+,.2f}** (95% CI [{ag_lo:+,.2f}, {ag_hi:+,.2f}]) "
      f"against the retry-everything baseline.")
    w("")
    w(f"The baseline fires {baseline.actions_taken:,} charge attempts to the "
      f"agent's {agent.actions_taken:,}. Fewer, better-timed actions is the "
      f"whole thesis: the agent declines to retry terminal declines at all, "
      f"defers soft declines toward payday, and chases abandoned checkouts "
      f"within minutes instead of treating every failure identically.")
    w("")

    w("## Ablations — where the lift actually comes from")
    w("")
    w("Attributing the whole gain to 'AI' would be lazy. Removing one "
      "component at a time shows which part is load-bearing.")
    w("")
    w("| arm | what changed | recovery rate | net margin / case |")
    w("|---|---|---|---|")
    for a, desc in (
        (baseline, "retry everything, immediately"),
        (no_timing, "right action per family, fired immediately"),
        (agent, "right action + scheduled timing + gates"),
        (no_gates, "right action + timing, **gateway bypassed**"),
    ):
        w(f"| `{a.name}` | {desc} | {a.recovery_rate:6.2%} "
          f"| {statistics.fmean(a.per_case_net):+,.2f} |")
    w("")

    timing_pt, timing_lo, timing_hi = bootstrap_ci(agent.per_case_net, no_timing.per_case_net)
    w(f"**Scheduling is worth {timing_pt:+,.2f} net margin per case** "
      f"(95% CI [{timing_lo:+,.2f}, {timing_hi:+,.2f}]) on top of simply "
      f"choosing the right action — comparing `agent` against "
      f"`agent_no_timing`. Deciding *when* is not a garnish on deciding "
      f"*what*; it is a large share of the value.")
    w("")

    gates_pt, gates_lo, gates_hi = bootstrap_ci(agent.per_case_net, no_gates.per_case_net)
    w(f"**The gateway costs {gates_pt:+,.2f} net margin per case in this "
      f"simulator** (95% CI [{gates_lo:+,.2f}, {gates_hi:+,.2f}]). That sign "
      f"is expected and is reported rather than hidden: the harness models "
      f"recovered revenue but not the cost of a DND violation, an unapproved "
      f"high-value charge, or a customer messaged at 3am. Guardrails buy "
      f"avoided tail risk, which this evaluation is structurally unable to "
      f"price. Any recovery system whose eval shows guardrails as pure upside "
      f"is measuring the wrong thing.")
    w("")

    w("## Honest caveats")
    w("")
    w("- The population is synthetic. These numbers demonstrate that the "
      "evaluation *method* works and that the policy beats a naive baseline "
      "**under the simulator's assumptions**. They are not a claim about "
      "production lift.")
    w("- `NEEDS_APPROVAL` cases are counted as not executed, so the agent gets "
      "no credit for high-value recoveries a merchant would likely have "
      "approved. This understates the agent.")
    w("- Organic recovery is modelled as a single draw rather than a process "
      "over time, so repeated organic attempts are not represented.")
    w("- Action costs are estimates, and the retry cost bundles a guess at the "
      "expected cost of consuming scheme attempt allowance.")
    w("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    report = build_report(args.n, args.seed)
    print(report)

    out = Path(args.out) if args.out else Path(__file__).resolve().parents[2] / "EVAL.md"
    out.write_text(report, encoding="utf-8")
    print(f"\n[written] {out}")


if __name__ == "__main__":
    main()
