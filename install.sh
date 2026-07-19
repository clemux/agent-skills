#!/usr/bin/env bash
# Link each skill in this repo into the harness skill roots it targets.
#
# Symlinks, never copies: a copy in a harness directory drifts silently from the
# repo, and nothing tells you which version is authoritative.
#
# Targets are declared per skill in the ignored, machine-local install.conf.
# install.conf.sample provides the tracked starting point. This script makes the
# local table exact: it links the roots a skill targets and removes it from the
# roots it does not.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$REPO/install.conf"

ALL_ROOTS=(claude codex agents)
root_path() {
    case "$1" in
        claude) echo "$HOME/.claude/skills" ;;
        codex)  echo "$HOME/.codex/skills" ;;
        agents) echo "$HOME/.agents/skills" ;;
        *)      echo "unknown root in install.conf: $1" >&2; exit 2 ;;
    esac
}

dry_run=0
force=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) dry_run=1 ;;
        --force)   force=1 ;;
        -h|--help)
            echo "usage: install.sh [--dry-run] [--force]"
            echo "  --dry-run  report what would change, write nothing"
            echo "  --force    delete detached copies (destructive). Symlinks are"
            echo "             created and removed without it; they hold no content."
            exit 0
            ;;
        *) echo "unknown argument: $arg" >&2; exit 2 ;;
    esac
done

[ -f "$MANIFEST" ] || {
    echo "missing $MANIFEST" >&2
    echo "copy $REPO/install.conf.sample to $MANIFEST and customize it for this machine" >&2
    exit 2
}

declare -A TARGETS=()
while read -r skill roots; do
    [ -n "$skill" ] || continue
    if [ ! -f "$REPO/$skill/SKILL.md" ]; then
        echo "install.conf lists '$skill', which is not a skill in this repo" >&2
        exit 2
    fi
    for root_name in $roots; do
        [ "$root_name" = "none" ] || root_path "$root_name" >/dev/null
    done
    TARGETS["$skill"]="$roots"
done < <(sed 's/#.*//' "$MANIFEST")

linked=0
removed=0
copies=0

for skill_dir in "$REPO"/*/; do
    skill_dir="${skill_dir%/}"
    skill="$(basename "$skill_dir")"
    [ -f "$skill_dir/SKILL.md" ] || continue

    if [ -z "${TARGETS[$skill]+set}" ]; then
        echo "$skill is not listed in install.conf — add it ('none' installs it nowhere)" >&2
        exit 2
    fi

    for root_name in "${ALL_ROOTS[@]}"; do
        root="$(root_path "$root_name")"
        [ -d "$root" ] || continue
        target="$root/$skill"

        wanted=0
        for want in ${TARGETS[$skill]}; do
            [ "$want" = "$root_name" ] && wanted=1
        done

        if [ "$wanted" -eq 1 ]; then
            if [ -L "$target" ]; then
                # Already a symlink. Correct only if it resolves back into this repo;
                # a link pointing at another harness's copy is still drift.
                [ "$(readlink -f "$target")" = "$skill_dir" ] && continue
                echo "relink  $target (pointed outside the repo)"
                [ "$dry_run" -eq 1 ] || { rm "$target"; ln -s "$skill_dir" "$target"; }
                linked=$((linked + 1))
            elif [ -e "$target" ]; then
                # A real directory: a detached copy. Refuse unless --force, since it may
                # hold edits that were never brought back into the repo.
                copies=$((copies + 1))
                if [ "$force" -eq 1 ]; then
                    echo "REPLACE $target (detached copy -> symlink)"
                    [ "$dry_run" -eq 1 ] || { rm -rf "$target"; ln -s "$skill_dir" "$target"; }
                    linked=$((linked + 1))
                else
                    echo "COPY    $target — detached copy; diff it against the repo, then rerun with --force"
                fi
            else
                echo "link    $target"
                [ "$dry_run" -eq 1 ] || ln -s "$skill_dir" "$target"
                linked=$((linked + 1))
            fi
        else
            # Not targeted at this root, so the harness must not see it.
            if [ -L "$target" ]; then
                # A symlink holds no content: removing it cannot lose work.
                echo "unlink  $target (not targeted at $root_name)"
                [ "$dry_run" -eq 1 ] || rm "$target"
                removed=$((removed + 1))
            elif [ -e "$target" ]; then
                copies=$((copies + 1))
                if [ "$force" -eq 1 ]; then
                    echo "DELETE  $target (detached copy, not targeted at $root_name)"
                    [ "$dry_run" -eq 1 ] || rm -rf "$target"
                    removed=$((removed + 1))
                else
                    echo "COPY    $target — detached copy to delete; diff it against the repo, then rerun with --force"
                fi
            fi
        fi
    done
done

echo
echo "linked: $linked   removed: $removed   detached copies: $copies"
if [ "$copies" -gt 0 ] && [ "$force" -eq 0 ]; then
    echo "Detached copies are the drift this repo exists to prevent."
    echo "Diff each against the repo, salvage any real edits, then rerun with --force."
fi
