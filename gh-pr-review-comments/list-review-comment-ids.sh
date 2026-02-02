#!/bin/bash
# List review comment IDs in compact format for scripting
# Usage: ./list-review-comment-ids.sh [owner/repo] [pr_number]
# Output format: id|path|line|author

set -e

if [ $# -lt 2 ]; then
    # Try to get repo from current directory
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
    if [ -z "$REPO" ]; then
        echo "Usage: $0 <owner/repo> <pr_number>" >&2
        exit 1
    fi
    PR_NUMBER="$1"
else
    REPO="$1"
    PR_NUMBER="$2"
fi

gh api "repos/${REPO}/pulls/${PR_NUMBER}/comments" \
    --jq '.[] | "\(.id)|\(.path)|\(.line // .original_line)|\(.user.login)"'