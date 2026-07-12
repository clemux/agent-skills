#!/usr/bin/env bash
# Link every skill in this repo into each harness's skill directory.
#
# Symlinks, never copies: a copy in a harness directory drifts silently from the
# repo, and nothing tells you which version is authoritative.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOTS=("$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.agents/skills")

dry_run=0
force=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) dry_run=1 ;;
        --force)   force=1 ;;
        -h|--help)
            echo "usage: install.sh [--dry-run] [--force]"
            echo "  --dry-run  report what would change, write nothing"
            echo "  --force    replace detached copies with symlinks (destructive)"
            exit 0
            ;;
        *) echo "unknown argument: $arg" >&2; exit 2 ;;
    esac
done

linked=0
skipped=0
copies=0

for skill_dir in "$REPO"/*/; do
    skill="$(basename "$skill_dir")"
    [ -f "$skill_dir/SKILL.md" ] || continue

    for root in "${ROOTS[@]}"; do
        [ -d "$root" ] || continue
        target="$root/$skill"

        if [ -L "$target" ]; then
            # Already a symlink. Correct only if it resolves back into this repo;
            # a link pointing at another harness's copy is still drift.
            if [ "$(readlink -f "$target")" = "${skill_dir%/}" ]; then
                continue
            fi
            echo "relink  $target (pointed outside the repo)"
            [ "$dry_run" -eq 1 ] || { rm "$target"; ln -s "${skill_dir%/}" "$target"; }
            linked=$((linked + 1))
        elif [ -e "$target" ]; then
            # A real directory: a detached copy. Refuse unless --force, since it may
            # hold edits that were never brought back into the repo.
            copies=$((copies + 1))
            if [ "$force" -eq 1 ]; then
                echo "REPLACE $target (detached copy -> symlink)"
                [ "$dry_run" -eq 1 ] || { rm -rf "$target"; ln -s "${skill_dir%/}" "$target"; }
            else
                echo "COPY    $target — detached copy; diff it against the repo, then rerun with --force"
                skipped=$((skipped + 1))
            fi
        else
            echo "link    $target"
            [ "$dry_run" -eq 1 ] || ln -s "${skill_dir%/}" "$target"
            linked=$((linked + 1))
        fi
    done
done

echo
echo "linked: $linked   detached copies: $copies   skipped: $skipped"
if [ "$copies" -gt 0 ] && [ "$force" -eq 0 ]; then
    echo "Detached copies are the drift this repo exists to prevent."
    echo "Diff each against the repo, salvage any real edits, then rerun with --force."
fi
