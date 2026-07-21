# obsidian-personal

> temporary adapter skill because
> [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) were not
> enough. I'm hoping to retire this skill in favor or my (possibly
> over-engineered) obsidian agentic workflow project
> ([clemux/obsidian-agent-workflow](https://github.com/clemux/obsidian-agent-workflow))
>
> Contain hard-coded paths and such, so it doesn't make sense to try and use is
> as is (like the majority of the skills in this repo).

## What it adds over `kepano/obsidian-skills`

- Explicit vault targeting and vault-relative paths for automation.
- Connection preflight, one bounded retry, parallel reads, and serialized writes.
- Template discovery before creating structured notes.
- Checks of live plugin state before using optional features.
- Shell-safe writes with read-back verification.
- Documentation of headless Base query limitations.
