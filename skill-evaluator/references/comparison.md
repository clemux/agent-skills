<!--
Adapted from the blind-comparison approach in Anthropic's Apache-2.0
skill-creator bundle at commit 06a4dfeffbfee567b419357dbb693ecbd4ff740a.
-->

# Blind comparison

Use blind A/B review only when a fresh independent judge is available and the
decision warrants the extra cost.

1. Pair outputs from the same eval prompt.
2. Randomly map configurations to labels A and B; save the secret mapping separately.
3. Give the judge the raw prompt, inputs, outputs, and neutral decision criteria.
4. Hide skill names, configuration names, expected winner, prior analysis, and user preference.
5. Require a winner, tie, or incomparable judgment with evidence.
6. Save the judgment before revealing the mapping.
7. Aggregate wins, losses, and ties per eval. Do not collapse incomparable cases into ties.
8. Investigate disagreements between blind preference and assertion scores.

Never ask a judge that has already seen the candidate design or expected result
to pretend it is blind.
