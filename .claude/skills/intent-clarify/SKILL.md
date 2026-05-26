---
name: "intent-clarify"
description: "Identify and resolve under-specified areas in the captured intent."
argument-hint: "Optional: specific section to clarify"
compatibility: "Requires .intent/ directory (run intent init first)"
metadata:
  author: "intent-kit"
  source: "templates/commands/clarify.md"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

## Outline

`/intent.clarify` identifies gaps, ambiguities, or under-specified areas in the current intent document and presents structured clarification questions.

### Execution Flow

1. **Load** `.intent/intent.md` and `.intent/state.json`.

2. **Analyze** each section for:
   - Vague language ("should work well", "fast enough", "secure")
   - Missing quantification in Quality Attributes
   - Untestable Success Criteria
   - Low-confidence Assumptions that could invalidate the intent
   - Implicit assumptions not captured in the Assumptions section
   - Scope ambiguity (what's in vs out)

3. **Generate** up to 5 clarification questions, each in this format:

   ```markdown
   ### CLR-[NNN]

   **Section**: [which section of intent.md]
   **Issue**: [what's unclear or under-specified]

   **Question**: [specific, answerable question]

   **Suggested answers**:
   | Option | Answer | Implications |
   |--------|--------|--------------|
   | A | [answer] | [what this means for the project] |
   | B | [answer] | [what this means] |
   | C | [answer] | [what this means] |
   ```

4. **Wait** for user responses.

5. **Update** `.intent/intent.md` with resolved clarifications.

6. **Write audit entry** for each resolution.

## Guidelines

- Maximum 5 questions per invocation — prioritise by impact on downstream phases.
- Prioritisation order: scope > architecture impact > security/compliance > user experience > implementation detail.
- Only ask about things that would change the design document or decomposition. Don't ask about implementation details.
- If all clarifications are resolved and the intent validates, report readiness for the next phase.
