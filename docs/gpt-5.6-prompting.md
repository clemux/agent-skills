# gpt-5.6-prompting

Guidance for composing Codex and GPT-5.6 prompts for coding, review, diagnosis, and research tasks
delegated from Claude Code. The skill is a prompt-authoring reference: it tells the calling agent
how to structure a prompt it is about to send to Codex or another GPT-5.6-based workflow (for
example `gpt-5.6-sol`). It does not invoke Codex, run any command, or execute a prompt itself —
composing the prompt text is the entire deliverable, and sending it is left to whatever the caller
already uses to reach Codex (a built-in `review`/`adversarial-review` command, a `task` invocation,
or a plugin agent such as `codex:codex-rescue`).

## Status

Active, but marked **Not tested** in [`README.md`](../README.md). On this page, "not tested" means
the guidance was written from documentation and prompting experience and has not been validated
end-to-end against a live Codex/GPT-5.6 run as part of this repository's own verification — see
[Verification status](#verification-status).

Default harness mapping, from [`install.conf.sample`](../install.conf.sample):

```text
gpt-5.6-prompting       claude
```

The skill ships only to Claude Code by default; it is not mapped to a Codex or neutral
`~/.agents/skills` root in the sample manifest.

The frontmatter sets `user-invocable: false`
([`gpt-5.6-prompting/SKILL.md`](../gpt-5.6-prompting/SKILL.md)), so it is meant to be
model-triggered only — Claude Code loads it automatically when its description matches, and it is
not exposed as a slash command or direct user invocation.

## Triggers

Per the `description` frontmatter, the skill is meant to fire when delegating to Codex or another
GPT-5.6-based workflow for coding, review, diagnosis, or research tasks, and specifically in
preference to the Codex plugin's bundled `gpt-5-4-prompting` skill when the target model is
GPT-5.6 (e.g. `gpt-5.6-sol`). There is no separate "when to use" section in the body; the
frontmatter description is the only trigger definition.

## Prerequisites

- A way to actually reach Codex or a GPT-5.6-based workflow — this skill supplies prompt text
  only, not the delivery mechanism. Typical delivery mechanisms it assumes exist are a `review` /
  `adversarial-review` command, a `task` (optionally `task --resume-last`) invocation, or the
  Codex plugin's `codex:rescue` agent (see [Limitations](#limitations)).
- No network access, authentication, or other repository skill is required by this skill itself.

## Read/write and safety boundaries

The skill has no scripts, so it performs no reads or writes on its own — it only supplies text for
the calling agent to include in a prompt. All read/write and approval boundaries described in the
skill (e.g. `default_follow_through_policy`, `action_safety` in
[`references/prompt-blocks.md`](../gpt-5.6-prompting/references/prompt-blocks.md)) are
recommendations for what the *downstream* Codex prompt should say, not actions this skill takes.
Any external write, destructive action, or scope expansion the skill recommends gating still needs
explicit approval at the point Codex (or whatever executes the prompt) actually runs — this skill
cannot enforce that boundary itself.

## Typical workflow

1. The calling agent (Claude Code) decides to delegate a coding, review, diagnosis, or research
   task to Codex/GPT-5.6.
2. It follows the skill's prompt assembly checklist in
   [`gpt-5.6-prompting/SKILL.md`](../gpt-5.6-prompting/SKILL.md): define the task, choose the
   smallest output contract, decide on a follow-through default, add verification/grounding/safety
   blocks only where needed, and trim redundant instructions.
3. It picks a prompt shape: a built-in `review`/`adversarial-review` command for reviewing local
   git changes, a `task` prompt for diagnosis/planning/research/implementation, or
   `task --resume-last` for a follow-up delta on the same thread.
4. It composes the prompt from XML-tagged blocks (`<task>`, `<structured_output_contract>`,
   `<default_follow_through_policy>`, `<verification_loop>`, `<grounding_rules>`, etc.), copying a
   starting template from `references/codex-prompt-recipes.md` where one fits.
5. It sends the assembled prompt through whatever delivery path is available in the environment
   (built-in command, `task`, or a Codex agent) — a step outside this skill's own scope.
6. For async/high-effort review runs, it pins the diff range by immutable commit hash rather than
   `HEAD`-relative, and treats a long wait as expected rather than a failure.

## Bundled resources

The skill has no `scripts/` and no `assets/`; it is documentation-only, consistent with its role
as a prompt-composition reference rather than an executor.

There is also no `agents/` directory in the skill package itself. One reference file names an
external agent (`codex:codex-rescue`) that belongs to a separate Codex plugin — see
[Limitations](#limitations).

Three reference files, all under
[`gpt-5.6-prompting/references/`](../gpt-5.6-prompting/references/):

- **`prompt-blocks.md`** — the catalog of reusable XML-tagged prompt blocks (`task`,
  `structured_output_contract`, `compact_output_contract`, `default_follow_through_policy`,
  `completeness_contract`, `verification_loop`, `missing_context_gating`, `grounding_rules`,
  `citation_rules`, `action_safety`, `tool_persistence_rules`, `research_mode`,
  `dig_deeper_nudge`, `progress_updates`), each with its XML tag and when to use it.
- **`codex-prompt-recipes.md`** — five end-to-end starting templates: Diagnosis, Narrow Fix,
  Root-Cause Review, Research Or Recommendation, and Prompt-Patching, each composed from the
  blocks above.
- **`codex-prompt-antipatterns.md`** — paired bad/better examples covering vague task framing,
  missing output contracts, no follow-through default, repeating approval language, asking for
  more reasoning instead of a better contract, mixing unrelated jobs into one run, and unsupported
  certainty.

## Limitations

- The skill produces prompt text; it cannot verify that the prompt it helped compose actually
  produces a better Codex/GPT-5.6 result in a given environment, because it has no execution or
  feedback path of its own.
- `references/codex-prompt-recipes.md` states: "In `codex:codex-rescue`, run diagnosis and
  fix-oriented recipes in write mode by default unless the user explicitly asked for read-only
  behavior." `codex:codex-rescue` is an agent supplied by a separate Codex plugin, not by this
  repository or this skill package. Where that plugin/agent is not installed, the portable
  alternative is to compose a plain `codex exec` invocation (or equivalent local Codex CLI call)
  carrying the same assembled prompt, rather than relying on the plugin agent's write-mode
  default.
- The prompt shapes described (`review`, `adversarial-review`, `task`, `task --resume-last`) are
  named as if they are known commands in the calling environment; this skill does not define or
  ship them, so they must already exist in whatever harness dispatches to Codex.
- No test suite or eval harness for this skill's guidance ships in the package or elsewhere in the
  repository that was inspected for this page.

## Compatibility and version notes

Several claims in `gpt-5.6-prompting/SKILL.md` are tied to a specific model generation and a
specific set of (uncited) benchmark numbers. This page deliberately does not restate them as
verified facts; treat them as release-specific and re-check against current OpenAI/Codex
documentation before relying on them:

- The claim that "leaner GPT-5.6 prompts improved scores ~10–15% while cutting tokens 41–66%" is
  attributed to "OpenAI's coding-agent evals" in the skill body but is not linked to a citable
  source in the package. Release-specific and uncited as of 2026-07-21.
- The claim that "GPT-5.6 infers underlying goals better than prior generations" is a
  version-specific behavioral comparison, not independently verified here.
- The stated effort tiers (`xhigh`, and a `max` tier "above `xhigh`") are specific to the
  GPT-5.6/Codex CLI generation the skill targets and may not exist or may be renamed in other
  model or CLI versions.
- The timing expectation ("Expect high-effort runs (`--effort xhigh`) to take 5–15+ minutes") is a
  release- and environment-specific estimate, not a guaranteed bound.
- The skill is explicitly positioned as a replacement for the Codex plugin's bundled
  `gpt-5-4-prompting` skill "when targeting GPT-5.6 models" — this implies both skills may need to
  coexist, and the choice between them depends on which model a given Codex run targets.

## Verification status

- **Automated checks**: none specific to this skill were found; it ships no scripts, so there is
  nothing here for a test runner to execute.
- **Manually verified**: not established by this page. The `README.md` "Not tested" annotation
  (see [Status](#status)) is the only existing signal, and this page's review of the source files
  confirms the guidance is internally consistent (block names in `SKILL.md` match the tags defined
  in `references/prompt-blocks.md` and used in `references/codex-prompt-recipes.md`) but does not
  establish that following it produces better Codex/GPT-5.6 output.
- **Untested**: the practical effect of the guidance on real Codex/GPT-5.6 runs, including the
  specific numeric claims called out in [Compatibility and version notes](#compatibility-and-version-notes).

## Example

Illustrative only — not a captured transcript. A narrow-fix prompt assembled from
`references/codex-prompt-recipes.md`, using placeholder repository details:

```xml
<task>
Implement the smallest safe fix for the null-pointer crash in the checkout handler in
<repo-path>/checkout.py.
Preserve existing behavior outside the failing path.
</task>

<structured_output_contract>
Return:
1. summary of the fix
2. touched files
3. verification performed
4. residual risks or follow-ups
</structured_output_contract>

<default_follow_through_policy>
Default to the most reasonable low-risk interpretation and keep going.
</default_follow_through_policy>

<completeness_contract>
Resolve the task fully before stopping.
Do not stop after identifying the issue without applying the fix.
</completeness_contract>

<verification_loop>
Before finalizing, verify that the fix matches the task requirements and that the changed code is
coherent.
</verification_loop>

<action_safety>
Keep changes tightly scoped to the stated task.
Avoid unrelated refactors or cleanup.
</action_safety>
```

This text is what the calling agent would hand to Codex (via `task`, `codex exec`, or an
equivalent delivery path); the skill itself stops at producing it.

## See also

- [skills.md](skills.md) — index of all skills in this repository.
