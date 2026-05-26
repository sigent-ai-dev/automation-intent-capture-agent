---
name: "speckit-selfreview"
description: "Perform a rigorous self-review of the current branch's PR before requesting human review."
argument-hint: "Optional PR number (e.g., #42)"
compatibility: "Requires GitHub repo with PRs"
metadata:
  author: "speckit-extras"
  source: "speckit-extras/templates/commands/selfreview.md"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

`/speckit-selfreview` performs a structured self-review of the current branch's diff against its linked spec, issue, and conventions. The bar: "if the most rigorous reviewer on the team looked at this, what would they flag?"

### Execution Flow

**Step 1 — Gather context.**

Read all of:
- The PR diff (`git diff main...HEAD` or `gh pr diff <number>`)
- The spec this PR implements (`specs/<NNN-feature>/spec.md`) — understand the contract, not just the code
- Every issue the PR claims to close — check every Acceptance Criterion literally
- Adjacent code (how do existing modules handle the same patterns?)
- Project conventions (`CLAUDE.md`, `.claude/rules/`, `memory/constitution.md`, linting config)

**Step 2 — Classify findings.**

Every finding gets a severity:

| Severity | Meaning | Action |
|----------|---------|--------|
| **C** (Critical) | Functionality doesn't do what it claims, breaks something, violates a load-bearing contract. Core function is a stub/no-op, state corruption, security hole. | Fix immediately — blocks merge |
| **H** (High) | Material bug, unsafe pattern, doc/code mismatch that misleads consumers | Fix immediately — blocks merge |
| **M** (Medium) | Design concern, missed edge case, convention violation | Fix unless documented reason to defer |
| **L** (Low) | Style, naming, minor clarity | Fix if quick, otherwise note |
| **I** (Info) | Observation, no action needed | Document only |

**Step 3 — Check seven specific areas:**

- **A. Contract adherence** — does the implementation match the spec exactly? Are deviations documented?
- **B. Issue closing accuracy** — for each "Closes #N", does the PR fully satisfy every AC? If any AC requires work in another PR, flag it.
- **C. Stubs and no-ops** — is any function a stub claiming to do something it doesn't? Are tests tautological (asserting defaults equal themselves)?
- **D. State management** — are transitions atomic? Can prior state leak? Are counters reset correctly?
- **E. Error handling** — failures visible or silently swallowed? Error messages name the offending value? `try/except` scoped tightly?
- **F. Convention alignment** — lint rules, import ordering, docstring style, test patterns, commit message format.
- **G. Downstream risks** — what assumptions do consumers inherit? Is the API shape stable enough to build on?

**Step 4 — Produce output** as Markdown:

```markdown
# Self-Review: [branch-name]

## Findings

| # | Sev | File | Line | Description |
|---|-----|------|------|-------------|
| 1 | C | src/engine.py | 42 | `optimise()` is a no-op — returns empty dict |
| 2 | H | tests/test_engine.py | 15 | Test asserts default equals default (tautological) |
| ... |

## Contract Adherence

[Does implementation match spec? Deviations?]

## Issue Closing Assessment

| Issue | Claim | Actual | Verdict |
|-------|-------|--------|---------|
| #42 | Closes | All AC met | ✓ Closes |
| #43 | Closes | AC-3 unmet (needs integration PR) | ↓ Refs |

## Verdict

[APPROVE | REQUEST CHANGES | COMMENT] — [reasoning]

## Recommended Changes

[Specific fixes, prioritised by severity]

## Downstream Risks

[What consumers need to know]
```

**Step 5 — Act on findings:**

- Fix all C and H findings immediately (produce commits)
- Fix M unless documented reason to defer
- L if quick, otherwise note for follow-up
- I document but don't action
- Update PR body if closing claims changed
- Commit fixes: `fix: self-review remediations — <summary>`

## Anti-patterns to Catch

These are the recurring failures that waste review cycles:

1. **The stub problem** — function exists, tests pass, core logic is a no-op
2. **Triple-hardcoded values** — version/config in model default + UI + test with no single source
3. **Broad try/except** — catches `Exception` where it should catch specific types
4. **Prompt text drift** — design doc says one thing, implementation says another
5. **FR wording vs delivery mismatch** — spec says MUST, implementation omits
6. **Issue AC requires integration** — PR closes issue but one AC needs separate PR
7. **Private symbol coupling** — using `_foo` across module boundaries
8. **Mutable fields in frozen structures** — list where tuple would be safer
9. **Missing input validation** — `KeyError` instead of clear `ValueError`
10. **Tautological tests** — asserting that defaults equal themselves

## When to Invoke

- Before requesting review on any PR with >100 lines changed
- After receiving review comments (re-run to check fixes)
- Before marking a feature "In Review"
