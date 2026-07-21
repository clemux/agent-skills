# gh-pr-review-comments

Historical helper scripts for retrieving and replying to inline GitHub pull-request review
comments.

| Script | What it does |
| --- | --- |
| `list-review-comments.sh` | Lists inline review comments. |
| `list-review-comment-ids.sh` | Lists review-comment identifiers. |
| `reply-to-comment.sh` | Replies to an inline review comment. |

## Limitations

- Replies do not resolve review threads.
- Nested comments are capped at 100.
- Listings include comments that already have replies.
- Replies are sent immediately, without a dry run.

Codex users should prefer the official `gh-address-comments` skill.

> actual note from the author: this was used on some specific side projects with some specific workflows. I don't think it has any actual value. If you work with me, please do not use it to address my comments on your PR. That would be very rude.
