# 6. Reproducing and reviewing

FORKED is early, and its own benchmark has **not been independently reproduced** — that is the
release gate in [`docs/08`](../08-benchmarks-and-validation.md) §8.6, and it is the most useful thing
a newcomer can do. This page is for you if you want to check our claims instead of trusting them.

## Reproduce the benchmark (about 5 minutes)

You need [uv](https://docs.astral.sh/uv/). No API key, no network, no model.

```bash
git clone https://github.com/MauricioFonck/forked && cd forked
uv sync --locked                                   # exact versions pinned by uv.lock
uv run python -m benchmarks.fcrb --out results/    # exit 0 = no scenario failed
```

Open `results/REPORT.md`. Everything except the timing section is deterministic: run it twice and
compare `results/results.json` (ignoring `overhead` and `environment`).

What to check, and what a good reviewer does:

1. **Do all ten scenarios pass on your machine?** Note your OS and Python version.
2. **Try to break it.** The benchmark must be able to fail. Change FORKED on purpose (for example make
   `RedactionPolicy` stop redacting, or make replay call the tool) and confirm the matching scenario
   fails. If a scenario stays green when the behavior it covers is broken, that is a bug in the benchmark.
3. **Read the baseline fairly.** Only a plain-log baseline is executed; the others are listed with the
   reason they were not. Tell us if a comparison is unfair or missing.
4. **Look for overclaiming** in the README and these docs. Anything stronger than the evidence
   should be reported.

## Review the project

| If you are… | Look at |
|---|---|
| a security person | [SECURITY.md](../../SECURITY.md); try to leak a secret, run a denied write, or make `verify` accept a forgery |
| an agent / observability developer | [4. Instrumenting your workflow](04-instrumenting-your-workflow.md); is the adapter seam right? what is missing? |
| a researcher | [Hypotheses](../02-problem-and-research-hypotheses.md) and [claim levels](02-concepts.md); is anything claimed causally that should not be? |
| a maintainer of a similar tool | [Competitive landscape](../03-competitive-landscape.md); what did we get wrong or miss? |

## Report back

* **You reproduced it** (or could not): open a
  [reproduction report](https://github.com/MauricioFonck/forked/issues/new?template=reproduction_report.yml).
  A failure to reproduce is as valuable as a success.
* **You found a bug:** a [bug report](https://github.com/MauricioFonck/forked/issues/new?template=bug_report.yml).
* **You have an idea or a critique:** a [proposal](https://github.com/MauricioFonck/forked/issues/new?template=proposal.yml).
* **You found a way around a guarantee:** do **not** open an issue — see [SECURITY.md](../../SECURITY.md).
