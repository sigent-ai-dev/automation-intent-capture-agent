# Research: Voice Intent Elicitation

## R1: Strands Tool Registration Pattern for BidiAgent

**Decision**: Use the `@tool` decorator from `strands` to define elicitation tools as decorated Python functions, passed to `BidiAgent(tools=[...])` at creation time.

**Rationale**: The Strands SDK uses a simple decorator pattern — `@tool` extracts metadata from docstrings and type hints, generating JSON schema automatically. Tools are pure functions that receive parameters and return results. The BidiAgent handles tool invocation lifecycle (call → execute → return result to model) transparently.

**Key API**:
```python
from strands import tool

@tool
def update_intent(section: str, content: str) -> dict:
    """Update a section of the intent document."""
    # implementation
    return {"status": "success", "content": [{"text": "Updated"}]}

agent = BidiAgent(model=model, tools=[update_intent], system_prompt=prompt)
```

**Alternatives considered**:
- MCP tool server: Over-engineered for local filesystem tools. MCP is for cross-process tool serving.
- Custom tool protocol: Strands already provides everything needed.

## R2: Intent Document Format (intent-kit Compatibility)

**Decision**: Follow the exact template from `intent-kit/templates/intent-template.md` — frontmatter (Intent ID, Captured, Actor, Status) + sections (Context, Intent, Motivation, Quality Attributes, Success Criteria, Assumptions, Clarifications).

**Rationale**: The intent-kit CLI validates documents against this structure via `intent check`. Deviating would break downstream tooling.

**Format**:
```markdown
# Intent: [PROJECT NAME]

**Intent ID**: INT-NNN
**Captured**: YYYY-MM-DD
**Actor**: voice
**Status**: draft|confirmed

## Context
## Intent
## Motivation
## Quality Attributes
## Success Criteria
## Assumptions
## Clarifications
```

**Key constraints**:
- Intent section MUST be a single declarative sentence
- Quality Attributes tagged QA-NNN
- Success Criteria tagged SC-NNN
- Assumptions tagged ASM-NNN with confidence [high/medium/low]
- Clarifications have CLR-NNN with Prompt + Resolution (answer or OPEN)

## R3: Tool Design — Granular vs Monolithic

**Decision**: Four tools with focused responsibilities: `create_intent`, `update_intent_section`, `read_intent`, `finalise_intent`.

**Rationale**: Granular tools give the LLM clear affordances — it knows exactly when to create vs update vs read. A single monolithic `manage_intent(action, ...)` tool puts too much routing logic in the prompt. The LLM naturally calls `update_intent_section(section="motivation", content="...")` when the user explains why they're doing something.

**Tool signatures**:
- `create_intent(project_name: str, context: str, intent: str, motivation: str)` → creates new INT-NNN.md
- `update_intent_section(intent_id: str, section: str, content: str)` → updates one section
- `read_intent(intent_id: str)` → returns current document state (for read-back)
- `finalise_intent(intent_id: str)` → sets Status: confirmed, validates completeness

**Alternatives considered**:
- Single tool with action parameter: Poor LLM ergonomics — models perform better with distinct tool names.
- Section-per-tool (7 update tools): Too many tools clutters the tool list, confuses the model.

## R4: System Prompt Strategy for Elicitation Behaviour

**Decision**: Extend the BidiAgent system prompt with elicitation instructions that encode the "Propose, Don't Interrogate" principle. The prompt guides the agent to form interpretations and present them rather than asking questions.

**Rationale**: Constitution Principle II requires propose-and-correct, not interrogate. The system prompt is the primary lever for controlling agent behaviour during voice sessions. Instructions must be concise (Nova Sonic context budget) but directive.

**Prompt structure**:
1. Role: "You are capturing structured business intent through conversation"
2. Behaviour: "Form an interpretation of what the user wants and present it for correction"
3. Tool use: "Use create_intent when you have Context + Intent + Motivation. Use update_intent_section as you learn more."
4. Completion: "When mandatory fields are populated, summarise and ask for confirmation before calling finalise_intent"
5. Constraints: "Maximum 3 clarification questions. Record anything unresolved in Clarifications section."

**Alternatives considered**:
- Fine-tuned model: Not available for Nova Sonic, and prompt engineering achieves the goal.
- Separate orchestration layer: Over-engineered — the LLM with tools handles the flow naturally.

## R5: Filesystem Storage Strategy

**Decision**: Write to `.intent/` directory at project root. Files named `INT-NNN.md` with sequential numbering. Atomic writes via write-to-temp-then-rename.

**Rationale**: intent-kit expects documents in `.intent/`. Sequential naming avoids collisions. Atomic writes prevent partial documents if the process is interrupted during write.

**Implementation**:
- `mkdir -p .intent/` on first write
- Scan existing `INT-*.md` files to determine next number
- Write to `.intent/.INT-NNN.md.tmp` then `os.rename()` to final path
- On retry (FR-013), re-attempt the same atomic write

**Alternatives considered**:
- DynamoDB storage: Spec clarification ruled this out — filesystem is the source of truth.
- Non-atomic writes: Risk of partial documents on crash/disconnect.
