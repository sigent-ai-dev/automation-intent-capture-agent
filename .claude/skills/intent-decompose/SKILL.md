---
name: "intent-decompose"
description: "Break the big idea into right-sized features ready for Spec Kit — Phase 4 of IDD."
argument-hint: "Optional: filtering or guidance"
compatibility: "Requires .intent/ directory (run intent init first)"
metadata:
  author: "intent-kit"
  source: "templates/commands/decompose.md"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

`/intent.decompose` is Phase 4 — the critical transition from IDD to feature-level work. It breaks the big idea into right-sized features that can each enter Spec Kit's `/speckit.specify` workflow independently.

### Gate Check

Before proceeding, validate:
1. `.intent/intent.md` exists and is complete
2. `.intent/state.json` shows define phase complete
3. Either `.intent/architecture.md` or `.intent/business-design.md` exists

If gate fails: ERROR "Phase 3 (define) is not complete. Run /intent.define first."

### Execution Flow

1. **Load context**:
   - `.intent/intent.md` — the intent with success criteria
   - `.intent/architecture.md` or `.intent/business-design.md` — the design
   - All ADRs in `.intent/adr/`
   - `.intent/steering.md`
   - User input (optional filtering/guidance)

2. **Identify feature boundaries**:

   For each Success Criterion (SC-NNN) in the intent:
   - What capabilities must exist for this criterion to be met?
   - Can each capability be delivered independently?
   - What's the minimal set of features that, combined, satisfy SC-NNN?

   For each component in the architecture:
   - What user-facing capabilities does this component enable?
   - Can these be delivered incrementally?

3. **Draft features**:

   For each proposed feature, capture:
   ```markdown
   ### [NNN]. [Imperative title — e.g., "Implement portfolio optimisation API"]

   **Intent reference**: INT-001
   **Success criteria**: SC-001, SC-003
   **Type**: feat | chore | refactor | docs | test
   **Size**: XS | S | M | L | XL
   **Priority**: P0 | P1 | P2 | P3

   **Context**: [1-2 sentences: why this feature exists in service of the intent]

   **Acceptance criteria**:
   - [ ] [Testable claim 1]
   - [ ] [Testable claim 2]
   - [ ] [Testable claim 3]

   **Out of scope**: [What this explicitly doesn't cover]

   **Dependencies**:
   - Blocked by: [feature NNN, or "none"]
   - Blocks: [feature NNN, or "none"]

   **Spec Kit ready**: [yes — can enter /speckit.specify | no — needs spike first]
   ```

4. **Apply decomposition rules**:

   **Size validation**:
   - XL (> 2 weeks) → MUST decompose further. Split and re-draft.
   - L (1-2 weeks) → acceptable but review for splitting opportunities
   - M (3-5 days) → ideal
   - S (1-2 days) → fine for focused work
   - XS (< 1 day) → fine for chores/fixes

   **Anti-pattern detection**:
   - Feature references 0 success criteria → OUT OF SCOPE (remove or justify)
   - Feature references 3+ unrelated success criteria → EPIC-SHAPED (split)
   - Multiple features have identical acceptance criteria → OVERLAP (merge or differentiate)
   - Feature has no acceptance criteria → INCOMPLETE (add or remove)
   - Circular dependencies exist → REDESIGN (break the cycle)

5. **Produce dependency map**:

   ```markdown
   ## Dependency Order

   ### Wave 1 (no dependencies — can start immediately)
   - Feature NNN: [title]
   - Feature NNN: [title]

   ### Wave 2 (depends on Wave 1)
   - Feature NNN: [title] (blocked by: NNN)

   ### Wave 3 (depends on Wave 2)
   - Feature NNN: [title] (blocked by: NNN)
   ```

6. **Produce Spec Kit integration summary**:

   For each feature marked "Spec Kit ready: yes", produce a structured invocation block in this exact format:

   ```markdown
   ## Ready for /speckit.specify

   ### 1. [Feature title]

   **Intent**: INT-001
   **Advances**: SC-001, SC-003
   **Constrained by**: ADR-003 (Use event-driven architecture)

   **Invocation**:

   /speckit.specify [Feature title] — [context sentence]. Intent: INT-001. Advances SC-001, SC-003. Constrained by ADR-003: [decision summary]. Acceptance criteria seed: (1) [AC from decomposed feature] (2) [AC from decomposed feature] (3) [AC from decomposed feature]

   ---

   ### 2. [Feature title]

   ...
   ```

   **Format rules for the invocation string**:
   - Single continuous string (no line breaks) — ready for copy-paste
   - Starts with feature title followed by em-dash and context
   - MUST contain "Intent: INT-NNN"
   - MUST contain "Advances SC-NNN" (at least one)
   - SHOULD contain "Constrained by ADR-NNN: [summary]" if relevant ADRs exist
   - MUST contain "Acceptance criteria seed:" followed by numbered AC from the feature
   - MUST end with "Traceability: INT-NNN > SC-NNN > [feature-short-name]"

   **Traceability preservation**: When `/speckit.specify` processes this invocation, it should produce a spec containing:

   ```markdown
   ## Traceability

   - **Intent**: INT-001
   - **Success Criteria**: SC-001, SC-003
   - **Constraints**: ADR-003
   - **Decomposed from**: .intent/backlog/features.md#1
   ```

   This section is free text — Spec Kit preserves it without modification.

   **ID stability**: Feature numbering in `features.md` is positional (1, 2, 3...) and MUST NOT change once assigned. If features are added, they get the next available number. If features are removed, their numbers are retired (not reused).

   For features marked "Spec Kit ready: no", add a separate section:

   ```markdown
   ## Needs Spike

   - [Feature title] — Reason: [why not ready]
   ```

7. **Write outputs**:
   - `.intent/backlog/features.md` — the full feature list
   - `.intent/backlog/dependency-map.md` — the dependency graph
   - `.intent/backlog/speckit-ready.md` — the Spec Kit integration commands (format above)

8. **Write audit entry** and **update state.json**.

9. **Report**:
   - Total features decomposed
   - Size distribution (XS/S/M/L/XL)
   - Priority distribution (P0/P1/P2/P3)
   - Features ready for Spec Kit vs needing spike
   - Suggested first wave for implementation

## Guidelines

- Each feature must be independently deliverable and testable.
- Prefer more, smaller features over fewer, larger ones — as long as each is independently meaningful.
- The priority ordering should reflect the intent's success criteria — P0 features are those without which the intent CANNOT be satisfied.
- Chores (CI setup, boilerplate, auth wiring) are legitimate features — they serve the intent even though they're not user-facing.
- If you find yourself writing a feature that feels like "the whole project" — the intent is too narrow for IDD, or the decomposition needs more passes.
- XL features are NEVER acceptable in the final output. Split them.
