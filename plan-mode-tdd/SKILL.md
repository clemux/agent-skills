---
name: plan-mode-tdd
description: Structure Plan mode outputs as a TDD-first sequence. Use when the user asks for a plan or planning mode workflow and wants tests-first, then implementation, then verification, then review-agent pass, then commit.
---

# Plan Mode TDD

## Overview

Force TDD sequencing in Plan mode. Decompose the feature into discrete behavior changes, each with its own full TDD cycle: tests first, then implementation, then verification, then review, then commit. Keep steps short and action-oriented.

## Workflow

Break the feature into a **sequence of distinct behavior changes**. For each change, follow this cycle:

1. Draft/update a failing test that captures the behavior change.
2. Implement the minimal code to make the test pass.
3. Run relevant tests and note the exact command(s) in the plan.
4. Run the `feature-dev:code-reviewer` agent and address findings.
5. Commit with a concise message.

Each change gets its own complete cycle before moving to the next. The plan should list each change as a separate group of steps, not batch all tests together or all implementations together.

## Notes

- If no tests exist, add a new failing test before implementation.
- If the task is too small for tests, still include a test placeholder step and explain why a full test is skipped.
- If multiple test layers apply, prefer the highest-value test type first (e2e, then integration, then unit).
