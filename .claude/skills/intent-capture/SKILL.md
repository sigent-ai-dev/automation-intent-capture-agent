---
name: "intent-capture"
description: "Capture structured business intent from a big idea description — Phase 1 of IDD."
argument-hint: "Describe the big idea you want to capture"
compatibility: "Requires .intent/ directory (run intent init first)"
metadata:
  author: "intent-kit"
  source: "templates/commands/capture.md"
user-invocable: true
disable-model-invocation: false
---


## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

`/intent.capture` is Phase 1 of IDD. It turns a big idea (which may be vague, detailed, or anywhere between) into the seven-section intent format through collaborative elicitation.

### Interaction Philosophy

This command uses a **Propose-and-Steer** approach with Socratic escalation:

1. **Lead with interpretation** — form your best understanding of the intent and present it. Don't interrogate from a blank slate.
2. **One exchange at a time** — each response from the user reshapes your understanding.
3. **The user can challenge the direction** — "wrong angle", "too narrow", "that's a feature not an intent" are all valid responses.
4. **Silence means consent** — if you propose something and the user doesn't object, it's accepted.
5. **Stop when aligned** — don't ask questions for the sake of completeness. If you can write a valid intent document, do it.

### Execution Flow

**Step 1: Assess input quality.**

Read the user's input and classify:

- **Rich input** (paragraph+ with clear outcomes, context, motivation): Skip to Step 3 — you have enough to draft the full intent.
- **Moderate input** (sentence or two with some context): Go to Step 2 with a single focused proposal.
- **Vague input** (a few words, no clear outcome): Go to Step 2 with interpretation + 1-2 probing questions.
- **Empty input**: ERROR "No idea description provided. Describe the big idea you want to capture."
- **File path**: Read the file and classify its content as above.

**Step 2: Propose interpretation (Approach A — Propose-and-Steer).**

Present your interpretation of the big idea in this format:

```
Here's my read of what you're describing:

**The big idea**: [your one-sentence interpretation of the intent — the outcome, not the approach]

**What I think is driving this**: [your inference of motivation — why now?]

**Success would look like**: [2-3 observable outcomes you infer]

**What I'm assuming**: [1-2 key assumptions you're making]

[If there's genuine ambiguity that blocks you from drafting:]
**One thing I need to understand**: [single focused question — NOT a batch]

Am I reading this right, or should I adjust my understanding?
```

Rules for Step 2:
- Maximum 1 question. If you can infer the answer, state your assumption instead.
- Your question should be framed as "Am I right that X?" not "What is X?" — propose, don't interrogate.
- If the user says "yes" or confirms, move to Step 3.
- If the user corrects, incorporate the correction and either move to Step 3 (if you now have enough) or present a revised interpretation.
- If the user says "wrong direction" or challenges the framing, **escalate to Socratic mode**: reflect back what they said, probe gently ("Tell me more about what's driving this"), and guide them toward articulating the intent. Maximum 3 conversational exchanges before attempting Step 3 again.
- Never present more than 3 proposal rounds total — if alignment isn't reached, proceed with best understanding and mark gaps as CLR-NNN items.

**Step 3: Draft the seven sections.**

Using your (now validated) understanding, structure the intent into seven sections:

**Context**: Environmental facts, constraints, prior art. If the user mentions existing systems, regulatory requirements, team structure, or organisational context — it goes here. DO NOT put solution ideas here.

**Intent**: Distill the big idea into a SINGLE declarative sentence. Rules:
- Must be falsifiable (you can verify if the shipped system satisfies it)
- Must be a single sentence (≤ 3 sentence boundaries)
- Must describe the OUTCOME, not the approach
- If you cannot distill to one sentence, propose your best attempt and ask if it captures the core

**Motivation**: Urgency, timing, cost of inaction. WHY NOW, not why at all.

**Quality Attributes**: NFRs. Tag each QA-NNN. If the user didn't mention NFRs, infer reasonable ones from the domain and mark as assumed. Common categories: latency, throughput, availability, data residency, security posture, compliance, scalability.

**Success Criteria**: Observable outcomes. Tag each SC-NNN. Each must be testable. Maximum 7. If more exist, the intent is too broad — propose splitting.

**Assumptions**: Beliefs not yet verified. Tag confidence (high/medium/low). Common sources: technology, team capability, data availability, timeline.

**Clarifications**: Gaps or ambiguities. Each gets CLR-NNN. Mark OPEN if genuinely unclear and would affect architecture. Maximum 5 OPEN. More than 5 means the intent needs more discovery.

**Step 4: Present the draft for confirmation.**

Show the complete intent document and ask:

```
Here's the captured intent. Review it — I'll adjust anything that doesn't match your thinking.

[full intent document]

Does this capture what you're trying to do? Flag anything that feels off — especially the Intent sentence and Success Criteria, since everything downstream traces to those.
```

If the user confirms: proceed to Step 5.
If the user corrects: incorporate and re-present only the changed sections.

**Step 5: Validate.**

- `context` is non-empty
- `intent` is a single declarative sentence
- `motivation` is non-empty
- `success_criteria` has at least 1 item
- No more than 5 OPEN clarifications
- No more than 7 success criteria

**Step 6: Write outputs.**

Create `.intent/` directory if it doesn't exist.

Write `.intent/intent.md` using the template structure.

Write audit entry to `.intent/audit.md`:
```markdown
## [ISO 8601 timestamp] — Intent captured

**Actor**: [user/agent]
**Phase**: capture
**Outcome**: [complete | incomplete — N validation errors]
**Intent summary**: [the single sentence]
```

Update `.intent/state.json`:
```json
{
  "current_phase": "capture",
  "phases": { "capture": { "complete": true, "completed_at": "<timestamp>" } }
}
```

**Step 7: Report completion.**

Show the intent summary, any open clarifications, and readiness for `/intent.steer`.

## Guidelines

- This is a BIG IDEA capture, not a feature specification. If the user describes something that sounds like a single user story, say so: "This sounds like a feature rather than an intent. Is there a larger initiative it belongs to?"
- Make informed guesses for Quality Attributes and Assumptions — document them clearly so the user can correct.
- The intent sentence is the most important output. Spend effort getting it right.
- DO NOT make architectural decisions. That's Phase 2.
- DO NOT decompose into features. That's Phase 4.
- If the user provides a document/file path, read it and synthesise — don't just copy sections verbatim.
- **Correction is the high-value signal** — when the user redirects, that tells you more than their original input. Capture it, acknowledge it visibly, adjust.
- **Show your reasoning** — "I'm interpreting 'organisations' as multi-tenancy because..." lets the user correct the inference, not just the conclusion.
