# accessibility-testing

Historical guidance for Lighthouse audits and WCAG color-contrast checks in a Quasar project. It
is mapped to no harness by default and retained as an unvalidated reference.

## Status

Historical; not recommended for direct use.

`install.conf.sample` maps it to no harness:

```
accessibility-testing   none
```

This matches [`README.md`](../README.md): "Historical; not recommended. Legacy Lighthouse and
contrast-checking workflow." It is not fit to run as-is.

## Why it was retired

- **Frontmatter/body mismatch.** The skill's `description` advertises "verifying WCAG compliance"
  and triggers on "screen reader", but the body of
  [`accessibility-testing/SKILL.md`](../accessibility-testing/SKILL.md) contains no
  screen-reader or assistive-technology procedure of any kind. Its actual scope is a Lighthouse
  score check plus a manual color-contrast ratio check — a small subset of what WCAG conformance
  requires.
- **Framework-specific.** The workflow assumes Quasar: it references a boot file
  (`src/boot/dark-mode.ts`), Quasar components (`q-btn`, `q-separator`), and Quasar's `$q.dark`
  API. It is not written to generalize to other frontend stacks.
- **Environment-specific.** It hardcodes `http://localhost:9000` and `pnpm lint`, without
  adaptation guidance for another layout or package manager.
- **Side-effecting.** The documented commands write `./report.json` and `./report_dark.json`
  directly into the project's working directory via `--output-path`, and the dark-mode workflow
  instructs editing a source file in place ("Temporarily force dark mode in boot file ... Remove
  the temporary line after testing") — a manual step with no automated cleanup or verification
  that it was reverted.

## Known risks

If re-enabled or invoked as-is:

- An agent could report a passing Lighthouse accessibility score as evidence the target meets WCAG
  compliance. **A Lighthouse score is not evidence of WCAG compliance.** Lighthouse's accessibility
  category checks a bounded set of automatable rules; WCAG success
  criteria include many checks — keyboard operability, focus order, screen-reader announcement
  correctness, meaningful sequence, and more — that Lighthouse cannot evaluate. Automated tooling
  such as Lighthouse or axe-core is generally understood to catch only a minority of WCAG issues;
  this proportion is release- and codebase-dependent and not independently verified for this
  skill (unverified).
- Report files (`report.json`, `report_dark.json`) get written into the caller's project directory
  with no cleanup step described, and could be committed by accident.
- The "temporarily force dark mode" step edits application source in place; if the described
  removal step is skipped, dark mode could ship forced on.
- The commands assume a dev server is already running on a fixed port and a specific package
  manager and lint command are present; run unmodified against a project that doesn't match those
  assumptions, they simply fail or target the wrong server.

## Migration / replacement

There is no current replacement skill in this repository. A safe replacement would need to:

- Separate an automated-tooling check (Lighthouse, axe-core, or similar, kept current — see
  [`skills.md`](skills.md) for the repository's skill index) from any claim about WCAG conformance,
  and state explicitly that automated results must be supplemented with manual review.
- Include real assistive-technology testing (e.g. keyboard-only navigation, and testing with an
  actual screen reader such as VoiceOver, NVDA, or JAWS) if the skill's description is going to
  keep claiming screen-reader coverage.
- Be framework-agnostic, or explicitly scoped and named as framework-specific (e.g.
  `accessibility-testing-quasar`) rather than described in general WCAG terms.
- Avoid writing generated report files into the project's working tree, or document how to keep
  them out of version control.
- Parameterize the dev-server URL, lint command, and package manager instead of hardcoding them.

## Verification status

Never validated. There is no evidence in the repository — no eval run, no recorded trigger test,
no changelog entry — that this skill's instructions were exercised against a real project. Treat
every command in [`accessibility-testing/SKILL.md`](../accessibility-testing/SKILL.md) as unverified
until tried.

## Example

Illustrative only — not a captured run; the skill has not been verified. This shows the kind of
transcript excerpt the skill's Lighthouse workflow would produce against a placeholder project:

```
$ npx lighthouse http://localhost:9000 --preset=desktop --output=json \
    --output-path=./report.json --chrome-flags="--headless --no-sandbox"
...
$ jq '.categories.accessibility.score' ./report.json
0.91
```

A score of `0.91` here means Lighthouse's automated accessibility checks mostly passed — it does
not mean the page meets WCAG AA or AAA, and it says nothing about screen-reader usability.
