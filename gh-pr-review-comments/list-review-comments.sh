#!/bin/bash
# List unresolved inline code review comments on a GitHub PR
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

OWNER="${REPO%%/*}"
NAME="${REPO#*/}"

# Exactly one slash, non-empty either side. Do not compare OWNER to NAME to detect a
# missing slash: that wrongly rejects repos whose owner and name match, e.g. cli/cli.
if [ "$OWNER" = "$REPO" ] || [ -z "$OWNER" ] || [ -z "$NAME" ] || [ "$NAME" != "${NAME%%/*}" ]; then
    echo "Invalid repo format: ${REPO}. Expected owner/repo" >&2
    exit 1
fi

# $owner/$name/$number/$endCursor below are GraphQL variables, bound by -f/-F.
# shellcheck disable=SC2016
gh api graphql --paginate \
    -f owner="$OWNER" \
    -f name="$NAME" \
    -F number="$PR_NUMBER" \
    -f query='
query($owner: String!, $name: String!, $number: Int!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          isResolved
          comments(first: 100) {
            nodes {
              databaseId
              path
              line
              originalLine
              author {
                login
              }
              body
            }
          }
        }
      }
    }
  }
}' \
    --jq '.data.repository.pullRequest.reviewThreads.nodes[]
        | select(.isResolved | not)
        | .comments.nodes[]
        | "ID: \(.databaseId)\nFile: \(.path)\nLine: \(.line // .originalLine)\nAuthor: \(.author.login)\nBody: \(.body)\n---"'
