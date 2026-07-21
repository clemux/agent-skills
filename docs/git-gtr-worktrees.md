# git-gtr-worktrees

Uses [git-worktree-runner](https://github.com/coderabbitai/git-worktree-runner) (`git gtr`) to
create, enter, inspect, and clean up Git worktrees.

Before creating a worktree, check the repository instructions, current branch, worktree list, and
`.gtrconfig` when present.

## Commands

| Task | Command |
| --- | --- |
| Create a worktree | `git gtr new <branch>` |
| Run a command in one | `git gtr run <branch> -- <command>` |
| Enter one | `git gtr go <branch>` |
| List worktrees | `git gtr list` |
| Remove one | `git gtr rm <branch>` |

Use plain `git worktree` only after explaining the fallback and getting approval. Inspect the
worktree, branch, and uncommitted changes before cleanup.

> I'm not sure it makes sense to use git gtr and this skill rather than harnesses official support
> for worktrees, or better tested skills like the one in
> [superpowers](https://github.com/obra/superpowers).
>
> Keeping it for now because it has served me well. At the very least, it benefits from git gtr
> hooks (for `mise trust` for example) and easy copy of files such as claude local settings.
