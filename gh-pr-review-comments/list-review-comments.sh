#!/bin/bash
# List inline code review comments on a GitHub PR
# Usage: ./list-review-comments.sh [owner/repo] [pr_number]

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
    --jq '.[] | "ID: \(.id)\nFile: \(.path)\nLine: \(.line // .original_line)\nAuthor: \(.user.login)\nBody: \(.body)\n---"'