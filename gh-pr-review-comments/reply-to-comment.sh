#!/bin/bash
# Reply to an inline review comment on a GitHub PR
# Usage: ./reply-to-comment.sh <owner/repo> <pr_number> <comment_id> <body>

set -e

if [ $# -lt 4 ]; then
    echo "Usage: $0 <owner/repo> <pr_number> <comment_id> <body>" >&2
    echo "Example: $0 owner/repo 49 123456 'Fixed in latest commit.'" >&2
    exit 1
fi

REPO="$1"
PR_NUMBER="$2"
COMMENT_ID="$3"
BODY="$4"

gh api "repos/${REPO}/pulls/${PR_NUMBER}/comments/${COMMENT_ID}/replies" \
    -f body="$BODY"