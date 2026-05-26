---
name: "intent-define"
description: "Produce the Architecture or Business Design document from intent + steering — Phase 3 of IDD."
argument-hint: "Optional: architecture or business"
compatibility: "Requires .intent/ directory (run intent init first)"
metadata:
  author: "intent-kit"
  source: "templates/commands/define.md"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

`/intent.define` is Phase 3. It consumes the intent and steering ADRs and produces either an Architecture Design Document (technical) or a Business Design Document (business-oriented), depending on the nature of the intent.

### Gate Check

Before proceeding, validate:
1. `.intent/intent.md` exists and is complete
2. `.intent/state.json` shows steer phase complete
3. At least one ADR exists in `.intent/adr/draft/` or `.intent/adr/accepted/`

If gate fails: ERROR "Phase 2 (steer) is not complete. Run /intent.steer first."

### Document Type Selection

Analyze the intent to determine which design document type:

- **Architecture Design Document** — when the intent is primarily about building a technical system (software, infrastructure, platform)
- **Business Design Document** — when the intent is primarily about solving a business problem (process improvement, organisational change, product strategy)

If unclear, ask the user which type they need. Many intents benefit from both — produce the primary one first, note that the other may be needed.

### Execution Flow

1. **Load context**:
   - `.intent/intent.md`
   - All ADRs in `.intent/adr/`
   - `.intent/steering.md`
   - `memory/constitution.md` (if exists)

2. **Select and load template**:
   - `templates/architecture-template.md` for technical
   - `templates/business-design-template.md` for business

3. **Fill the 12 sections** using the mapping:

   **For Architecture:**
   - Context → System context, Networking
   - Intent → Intent reference (mandatory)
   - Quality Attributes → Quality attributes mapping, Compute, Data stores
   - Success Criteria → Observability (what to measure)
   - Assumptions → Risks and assumptions
   - ADRs → Decisions section
   - Steering → informs all sections

   **For Business Design:**
   - Context → Problem framing, Current state
   - Intent → Intent statement
   - Motivation → Problem framing (urgency), Constraints
   - Quality Attributes → Constraints, Success model
   - Success Criteria → Success model, Acceptance criteria
   - Assumptions → Assumptions register, Risk register

4. **Validate completeness**:
   - Section 2 (Intent Reference) must be non-empty — HARD GATE
   - Every quality attribute (QA-*) should appear in the mapping table
   - Every steering ADR should be referenced in the Decisions section

5. **Write the output**:
   - Architecture: `.intent/architecture.md`
   - Business: `.intent/business-design.md`

6. **Write audit entry** and **update state.json**.

7. **Report**: Summary of what was produced, any unmapped quality attributes, readiness for `/intent.decompose`.

## Guidelines

- The design document is the BRIDGE between big idea and feature decomposition. It must be concrete enough that someone can decompose it into features.
- Every section should trace to the intent. If a section feels disconnected, it's either wrong or the intent needs updating.
- DO NOT decompose into features here — that's Phase 4.
- DO produce enough detail that Phase 4 can size and prioritise features correctly.
