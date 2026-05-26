---
name: "speckit-pr"
description: "Create a pull request with generated description and closing-claim accuracy gate."
argument-hint: "Optional base branch (default: main)"
compatibility: "Requires GitHub repo"
metadata:
  author: "speckit-extras"
  source: "speckit-extras/templates/commands/pr.md"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

`/speckit-pr` creates a pull request with a quality-gated description. It generates the PR body from spec docs + git history + PR template, validates closing claims against issue acceptance criteria, and runs self-review as a mandatory pre-flight.

### Pre-flight Checks

Before opening the PR:

1. **Refuse** if working tree has uncommitted changes.
2. **Refuse** if branch has no commits ahead of base (default: `main`).
3. **Run `/speckit-selfreview`** against the diff.
4. **Refuse** if self-review returns C-severity findings (would block merge anyway — fail fast).

### Execution Flow

**Step 1 — Determine context.**

- Base branch: from user input or default `main`
- Current branch name
- Linked spec: find `specs/<NNN-feature>/spec.md` matching branch pattern
- Linked issue: extract from branch name or spec frontmatter
- PR template: `.github/PULL_REQUEST_TEMPLATE.md` (if exists)

**Step 2 — Generate PR title.**

- Derive from the spec title or the most descriptive commit message subject
- Format: imperative, scoped, < 70 characters
- Offer the operator override if the derived title is unclear

**Step 3 — Generate PR body.**

Compose from three sources:

1. **Spec summary** — extract the one-paragraph summary from `spec.md` (what and why)
2. **Git log** — squashed commit list between base and HEAD (what changed)
3. **PR template** — fill sections from the template if one exists

Structure:
```markdown
## Summary

[From spec — what this PR delivers and why]

## Changes

[From git log — grouped by area]

## Linked Issues

[Closes/Refs #N — with closing-claim assessment]

## Test Plan

[From spec acceptance criteria — what to verify]
```

**Step 4 — Closing-claim accuracy gate.**

For each issue referenced with `Closes #N`:

1. Fetch issue #N's acceptance criteria (from issue body or linked spec)
2. For each AC, search the diff for evidence (code implementing it, test covering it)
3. **If all AC have evidence** → keep `Closes #N`
4. **If any AC lacks evidence** → downgrade to `Refs #N` and add:
   ```markdown
   ## Pending Acceptance Criteria

   The following AC from #N are not fully addressed in this PR:
   - [ ] AC-3: [description] — needs [what's missing]
   ```

This is the **load-bearing discipline** — it prevents issues being closed without full delivery.

**Step 5 — Run self-review and post as comment.**

- Execute the full `/speckit-selfreview` process
- If verdict is APPROVE or COMMENT → proceed
- If verdict is REQUEST CHANGES with only M/L findings → proceed (post as comment)
- If verdict is REQUEST CHANGES with C/H findings → ABORT (fix first)

**Step 6 — Create the PR.**

```bash
gh pr create --title "<title>" --body "<body>" --base <base-branch>
```

**Step 7 — Post self-review as PR comment.**

```bash
gh pr comment <number> --body "<self-review-output>"
```

**Step 8 — Report.**

Output: PR URL, closing-claim assessment, self-review verdict.

### Inputs

- `[base-branch]` (optional) — defaults to `main`
- If `$ARGUMENTS` is a PR number, run against existing PR (re-generate description)

## Guidelines

- The closing-claim gate is non-negotiable. Never claim `Closes` when AC is unmet.
- Self-review findings posted as a PR comment give reviewers a head start — they know what the author already checked.
- If no spec exists for the branch, generate the body from git log + PR template only (graceful degradation).
- If no PR template exists, use the default structure above.
