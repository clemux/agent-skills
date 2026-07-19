<!--
Adapted from the benchmark-analysis approach in Anthropic's Apache-2.0
skill-creator bundle at commit 06a4dfeffbfee567b419357dbb693ecbd4ff740a.
-->

# Benchmark analysis

After aggregation, inspect both the summary and individual runs.

- Identify assertions that always pass in every configuration. They may be valid but non-discriminating.
- Identify assertions that always fail. Check whether the task, assertion, or skill is defective.
- Flag high standard deviation, inconsistent failures, and configuration results driven by one outlier.
- Look for regressions hidden by a higher overall pass rate.
- Compare duration and token totals only when the same model, run count, inputs, and sandbox were used.
- Distinguish cached-input effects from output or reasoning growth when usage data provides those fields.
- Read transcripts for repeated wasted work, tool errors, retries, or missing dependencies.
- Check that baseline runs did not accidentally discover the candidate skill.
- Avoid causal claims from tiny samples. Describe one-run results as examples, not stable estimates.

Write a short `analysis` section into `benchmark.json` or an adjacent note with:

- strongest evidence for improvement;
- regressions or tradeoffs;
- flaky or weak evals;
- recommended skill revision;
- recommended held-out cases for the next iteration.
