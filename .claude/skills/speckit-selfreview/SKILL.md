---
name: "speckit-selfreview"
description: "Perform a rigorous self-review of the current branch's PR before requesting human review."
argument-hint: ""
compatibility: "Requires GitHub repo with gh CLI"
metadata:
  author: "speckit-extras"
  source: "speckit-extras/extension/commands/speckit.selfreview.md"
  version: "2.0.0"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

`/speckit.selfreview` performs a structured self-review of the current branch's diff against its linked spec, issue, and conventions. The bar: "if the most rigorous reviewer on the team looked at this, what would they flag?"

### Execution Flow

**Step 1 — Gather context.**

Read all of:
- The PR diff (`git diff main...HEAD` or `gh pr diff <number>`)
- **Every file touched by the diff in full** — not just diff hunks. Read the complete file to understand how changes integrate with surrounding code.
- The spec this PR implements (`specs/<NNN-feature>/spec.md`) — understand the contract, not just the code
- Every issue the PR claims to close — check every Acceptance Criterion literally
- Adjacent code (how do existing modules handle the same patterns?)
- Project conventions (`CLAUDE.md`, `.claude/rules/`, `memory/constitution.md`, linting config)

**Step 2 — Run static analysis.**

Detect and run the project's configured tooling. Check for these in order:

| Detect | Run | Scope |
|--------|-----|-------|
| `package.json` has `lint` script | `npm run lint` | Full project |
| `package.json` has `typecheck` or `tsc` script | `npm run typecheck` or `npx tsc --noEmit` | Full project |
| `pyproject.toml` or `ruff.toml` exists | `ruff check .` | Full project |
| `pyproject.toml` has `[tool.mypy]` or `mypy.ini` exists | `mypy .` | Full project |
| `Makefile` has `lint` target | `make lint` | Full project |
| `.eslintrc*` or `eslint.config.*` exists | `npx eslint --no-warn-ignored $(git diff --name-only main...HEAD)` | Changed files |
| `Cargo.toml` exists | `cargo clippy -- -D warnings` | Full project |
| `go.mod` exists | `golangci-lint run ./...` | Full project |
| `shellcheck` available + `.sh` files in diff | `shellcheck <changed .sh files>` | Changed files |

Rules:
- Run at most 3 tools (prioritise: type checker > linter > formatter)
- If a tool is not installed, log as I-severity: "Tool X not available — skipping"
- If a tool exits non-zero, each distinct error becomes a finding (M-severity for warnings, H-severity for errors)
- Do NOT install tools — only run what's already available

**Step 3 — Run tests.**

Detect and run the project's test suite:

| Detect | Run |
|--------|-----|
| `package.json` has `test` script | `npm test` |
| `pyproject.toml` or `pytest.ini` or `tests/` dir | `pytest` (or `python -m pytest`) |
| `Cargo.toml` exists | `cargo test` |
| `go.mod` exists | `go test ./...` |
| `Makefile` has `test` target | `make test` |

Rules:
- If tests fail, each failure is a **C-severity** finding (broken functionality)
- If no test runner detected, log as I-severity: "No test suite configured"
- Timeout: 5 minutes max. If exceeded, log as I-severity and continue.

**Step 4 — Check test coverage (heuristic).**

For each new exported symbol (function, class, constant) introduced in the diff:
1. Identify the symbol name and its file path
2. Search for test files that reference it (grep test directories for the symbol name)
3. If no test references found → M-severity finding: "New export `symbolName` in `file` has no test coverage"

Rules:
- Only check **new** exports (additions in the diff), not modified ones
- "Exported" means: public functions/classes in Python, exported in JS/TS, public in Go/Rust, non-underscore-prefixed
- Don't flag: type definitions, interfaces, constants that are trivial values, re-exports

**Step 5 — Classify findings.**

Every finding gets a severity:

| Severity | Meaning | Action |
|----------|---------|--------|
| **C** (Critical) | Functionality doesn't do what it claims, breaks something, violates a load-bearing contract. Core function is a stub/no-op, state corruption, security hole, test failure. | Fix immediately — blocks merge |
| **H** (High) | Material bug, unsafe pattern, doc/code mismatch that misleads consumers, type error, lint error | Fix immediately — blocks merge |
| **M** (Medium) | Design concern, missed edge case, convention violation, lint warning, untested new export | Fix unless documented reason to defer |
| **L** (Low) | Style, naming, minor clarity | Fix if quick, otherwise note |
| **I** (Info) | Observation, tool unavailable, no action needed | Document only |

**Step 6 — Check seven specific areas:**

- **A. Contract adherence** — does the implementation match the spec exactly? Are deviations documented?
- **B. Issue closing accuracy** — for each "Closes #N", does the PR fully satisfy every AC? If any AC requires work in another PR, flag it.
- **C. Stubs and no-ops** — is any function a stub claiming to do something it doesn't? Are tests tautological (asserting defaults equal themselves)?
- **D. State management** — are transitions atomic? Can prior state leak? Are counters reset correctly?
- **E. Error handling** — failures visible or silently swallowed? Error messages name the offending value? `try/except` scoped tightly?
- **F. Convention alignment** — lint rules, import ordering, docstring style, test patterns, commit message format.
- **G. Downstream risks** — what assumptions do consumers inherit? Is the API shape stable enough to build on?

**Step 7 — Produce output** as Markdown:

```markdown
# Self-Review: [branch-name]

## Tooling Results

| Tool | Status | Issues |
|------|--------|--------|
| eslint | ✓ pass | 0 |
| tsc | ✗ fail | 3 errors |
| jest | ✓ pass | 42 tests |
| coverage | — | 2 new exports untested |

## Findings

| # | Sev | File | Line | Source | Description |
|---|-----|------|------|--------|-------------|
| 1 | C | src/engine.py | 42 | review | `optimise()` is a no-op — returns empty dict |
| 2 | H | src/api.ts | 18 | tsc | Type error: Property 'id' missing |
| 3 | M | src/utils.ts | 55 | coverage | New export `formatDate` has no test |
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

**Step 8 — Act on findings:**

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
11. **Untested new exports** — public function/class added with no test referencing it
12. **Lint violations in diff** — code that fails the project's own lint rules

## When to Invoke

- Before requesting review on any PR with >100 lines changed
- After receiving review comments (re-run to check fixes)
- Before marking a feature "In Review"
