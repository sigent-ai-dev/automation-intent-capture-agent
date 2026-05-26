---
name: "intent-steer"
description: "Create high-level architectural steering decisions anchored to the captured intent — Phase 2 of IDD."
argument-hint: "Optional: additional context for steering decisions"
compatibility: "Requires .intent/ directory (run intent init first)"
metadata:
  author: "intent-kit"
  source: "templates/commands/steer.md"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

`/intent.steer` is Phase 2. It consumes the intent from Phase 1 and produces architectural steering decisions (ADRs) and a project-specific steering document.

### Gate Check

Before proceeding, validate:
1. `.intent/intent.md` exists
2. `.intent/state.json` shows `phase_complete: true` for capture
3. No OPEN clarifications remain in intent.md (if any exist, ERROR with list)

If gate fails: ERROR "Phase 1 (capture) is not complete. Run /intent.capture first." and list what's missing.

### Execution Flow

1. **Load context**:
   - Read `.intent/intent.md` — the captured intent
   - Read `memory/constitution.md` — project principles (if exists)
   - Read any existing ADRs in `.intent/adr/`
   - Read user input for additional steering context

2. **Identify decision points**:
   Analyze the intent and quality attributes to identify architectural decisions that must be made. Common categories:
   - Compute platform (serverless, containers, VMs)
   - Data persistence (SQL, NoSQL, object storage, file-based)
   - Authentication & authorisation model
   - Networking & exposure (public, private, hybrid)
   - Observability strategy
   - Deployment model (environments, promotion, rollback)
   - Integration patterns (sync, async, event-driven)

   For each: what are the options, what does the intent + quality attributes suggest?

3. **Produce ADRs** (one per decision):

   Create in `.intent/adr/draft/` using the RADE format:

   ```markdown
   ---
   adr: [NNN]
   title: [Decision title]
   status: draft
   date: [DATE]
   intent-reference: [QA-NNN or SC-NNN that drives this decision]
   ---

   # ADR [NNN] — [Title]

   ## Reference
   This decision serves: [INT-NNN], specifically [QA-NNN / SC-NNN].
   Without this decision, [what would be unresolved].

   ## Alternatives
   | Option | Pros | Cons |
   |--------|------|------|
   | [A] | [...] | [...] |
   | [B] | [...] | [...] |
   | [C] | [...] | [...] |

   ## Decision
   [What was chosen and the one-sentence rationale]

   ## Effects
   - [Consequence 1]
   - [Consequence 2]
   - [Trade-off accepted]
   ```

   **Critical**: The Reference field is mandatory. An ADR without a reference is rejected.

4. **Produce steering.md**:

   Write `.intent/steering.md` capturing project-specific conventions and guardrails that aren't load-bearing enough for individual ADRs but shape all downstream work.

5. **Write audit entry** to `.intent/audit.md`.

6. **Update state.json**:
   ```json
   {
     "current_phase": "steer",
     "phase_complete": true,
     "adr_count": N,
     "steering_produced": true
   }
   ```

7. **Report**: List ADRs produced, steering rules, and readiness for `/intent.define`.

## Guidelines

- Each ADR must reference a specific quality attribute or success criterion.
- Prefer fewer, higher-quality ADRs over many trivial ones.
- Steering decisions should be made at the RIGHT altitude — don't pick specific library versions, do pick architectural patterns.
- If the user provides additional context (e.g., "we use AWS", "the team knows Python"), incorporate it into the alternatives analysis.
- Present ADRs in draft status — the user can promote them to accepted after review.
