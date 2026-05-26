---
name: "speckit-decompose"
description: "Decompose design documents into right-sized GitHub issues with acceptance criteria and traceability."
argument-hint: "Path to design doc, or 'validate #N', or 'link-back <path> #N [#M ...]'"
compatibility: "Requires GitHub repo with gh CLI"
metadata:
  author: "speckit-extras"
  source: "speckit-extras/templates/commands/decompose.md"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

`/speckit-decompose` turns design documents, ADRs, architecture docs, and other source artefacts into well-formed GitHub issues. It enforces right-sizing, acceptance criteria, and traceability back to the source document.

### Three Modes

Parse the user input to determine mode:

- `<path>` → **Create mode** (decompose the document at path)
- `validate #NNN` → **Validate mode** (audit existing issue against playbook)
- `link-back <path> #NNN [#MMM ...]` → **Link-back mode** (append Related Work)

### Mode 1: Create (default)

**Step 1 — Read the source artefact.**

Supported source types:
- Architecture design documents (`architecture.md`)
- Business design documents (`business-design.md`)
- ADRs (`doc/adr/*.md`)
- Intent documents (`.intent/intent.md`)
- Design documents (`doc/design/*.md`)
- Retrospectives, runbooks, RFCs

**Step 2 — Identify decomposition units.**

For each discrete outcome, capability, or decision in the source:
- Can it be delivered independently?
- Can it be tested independently?
- Does it have a clear "done" state?

If yes to all three → it's a feature candidate.

**Step 3 — Draft issues.**

For each candidate, produce:

```markdown
### Issue: [imperative title]

**Source**: [path to source document, section reference]
**Type**: feat | chore | bug | refactor | docs | test
**Size**: XS (<1d) | S (1-2d) | M (3-5d) | L (1-2w) | XL (>2w — MUST SPLIT)
**Priority**: P0 (blocks everything) | P1 (this cycle) | P2 (next cycle) | P3 (eventually)

**Body**:

## Context

[Why this issue exists — reference the source document section]

## Acceptance Criteria

- [ ] [Testable claim 1]
- [ ] [Testable claim 2]
- [ ] [Testable claim 3]

## Out of Scope

[What this explicitly doesn't cover]

**Labels**: type:<type>, priority:<priority>, size:<size>
**Dependencies**: blocked-by #NNN (if any)
```

**Step 4 — Apply decomposition rules.**

Validate each draft against:

| Rule | Check | Action if fails |
|------|-------|-----------------|
| Has acceptance criteria | AC section non-empty | Reject — cannot create |
| Right-sized | Size ≠ XL | Split into smaller issues |
| Not epic-shaped | ≤ 2 unrelated outcomes | Split by outcome |
| Traceable | References source document | Add source reference |
| No dependency cycles | A→B→A doesn't exist | Redesign to break cycle |
| Labels complete | type + priority + size present | Add missing labels |

**Step 5 — Present for review.**

Show the full list of drafted issues to the operator:
- Count: N issues from source document
- Size distribution: XS(n) S(n) M(n) L(n)
- Priority distribution: P0(n) P1(n) P2(n) P3(n)
- Dependency chains: [list]

Ask: "Create these issues? (yes/no/edit)"

**Step 6 — Create issues on confirmation.**

```bash
gh issue create --title "<title>" --body "<body>" --label "<labels>"
```

Record each created issue number.

**Step 7 — Post-creation.**

- Write audit log entry with all issue numbers
- Offer to run link-back mode to annotate the source document

### Mode 2: Validate

**Input**: `validate #NNN`

Read the issue body and validate against the decomposition playbook:

```markdown
# Validation Report: #NNN

## Checks

| Check | Status | Notes |
|-------|--------|-------|
| Has acceptance criteria | ✓ / ✗ | [details] |
| Right-sized (not XL) | ✓ / ✗ | Estimated: [size] |
| Single outcome | ✓ / ✗ | Found [N] outcomes |
| Source referenced | ✓ / ✗ | [source or "missing"] |
| Labels complete | ✓ / ✗ | Missing: [list] |
| AC are testable | ✓ / ✗ | Vague: [list] |
| Dependencies explicit | ✓ / ✗ | [details] |

## Findings

[List issues found, with severity and recommendations]

## Verdict

[PASS | NEEDS WORK — N issues found]
```

### Mode 3: Link-back

**Input**: `link-back <path> #NNN [#MMM ...]`

Append to the source document:

```markdown
## Related Work

Issues decomposed from this document:
- #NNN — [title](link)
- #MMM — [title](link)

Decomposed: [timestamp]
```

Idempotent — if the section already exists, merge new issues without duplicating.

## Guidelines

- Each issue must be independently deliverable and testable.
- XL issues are NEVER acceptable — split before creating.
- Acceptance criteria must be testable claims, not vague descriptions.
- Always reference the source document section — reviewers need to trace back.
- Propose-then-confirm is non-negotiable. Never create issues without operator approval.
- If the source document is an intent.md, map success criteria to features (each SC gets 1+ issues).
