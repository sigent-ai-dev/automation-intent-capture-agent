---
name: "speckit-roadmap"
description: "Generate and maintain project-level roadmap showing sprint timeline, feature dependencies, and overall progress."
argument-hint: "Optional: 'view' to display existing roadmap"
compatibility: "Requires spec-kit project with sprints/ directory"
metadata:
  author: "github-spec-kit"
  source: "spec-kit/templates/commands/roadmap.md"
user-invocable: true
disable-model-invocation: false
---


# Roadmap Command

You are creating and maintaining a **project-level roadmap** that provides visibility across sprints, tracks dependencies, and shows overall project progress.

## Purpose

Generate a roadmap that shows:
1. Project vision and goals
2. Current sprint status
3. Upcoming sprints (planned)
4. Completed sprints (archived)
5. Feature backlog
6. Dependencies and blockers
7. Milestones and success metrics

## Input

**Arguments**: $ARGUMENTS

- No arguments: Generate or update the roadmap
- `view`: Display existing roadmap

## Process

### Step 1: Gather Project Context

1. **Read constitution**:
   - Extract project vision from `memory/constitution.md`
   - Identify core principles and goals

2. **Scan sprint archives**:
   - List all directories in `sprints/archive/`
   - For each sprint, read `summary.md`
   - Extract: sprint number, name, dates, features, status

3. **Check active sprint**:
   - Read `sprints/active/sprint.md` if exists
   - Extract: current sprint info, features, progress

4. **Scan feature specs**:
   - List all features in `specs/`
   - Identify: completed, in-progress, planned
   - Extract dependencies from plan.md files

### Step 2: Analyze Sprint History

1. **For each completed sprint**:
   - Sprint number and name
   - Duration and dates
   - Features completed
   - Key outcomes
   - Status

2. **Calculate project metrics**:
   - Total sprints completed
   - Total features delivered
   - Average velocity (if tracked)
   - Completion trends

### Step 3: Identify Current State

1. **Active sprint**:
   - Sprint number and name
   - Duration and dates
   - Current progress (% complete)
   - Features in progress
   - Blockers or risks

2. **If no active sprint**:
   - Show: "No active sprint"
   - Suggest: "Use `/speckit-sprint start` to begin next sprint"

### Step 4: Plan Future Sprints

1. **Analyze feature backlog**:
   - List features not yet in any sprint
   - Group by priority (P1, P2, P3)
   - Identify dependencies

2. **Suggest upcoming sprints**:
   - Based on feature priorities
   - Consider dependencies
   - Estimate 2-3 future sprints

3. **Tentative sprint planning**:
   - Sprint N+1: High-priority features
   - Sprint N+2: Medium-priority features
   - Sprint N+3: Lower-priority features

### Step 5: Map Dependencies

1. **Scan feature specs**:
   - Look for dependency mentions in plan.md
   - Check for "depends on" or "blocked by" statements

2. **Create dependency map**:
   - Feature X depends on Feature Y
   - External dependencies (APIs, services, approvals)

3. **Identify blockers**:
   - Features blocked by dependencies
   - External blockers (vendor, approval, etc.)

### Step 6: Define Milestones

1. **Extract from sprints**:
   - Major deliverables from sprint summaries
   - Key achievements and outcomes

2. **Project milestones**:
   - MVP milestone (first usable version)
   - Beta milestone (feature complete)
   - GA milestone (production ready)
   - Future milestones

3. **Milestone dates**:
   - Based on sprint timeline
   - Include target dates

### Step 7: Generate Roadmap Document

1. **Fill sections**:

   **Vision**:
   - High-level project vision
   - What are we building and why?

   **Current Sprint**:
   - Sprint number, name, dates
   - Progress and status
   - Features in progress

   **Upcoming Sprints**:
   - Sprint N+1: Name, dates, planned features
   - Sprint N+2: Name, dates, planned features
   - Sprint N+3: Name, dates, planned features

   **Completed Sprints**:
   - Table of completed sprints
   - Sprint number, name, duration, features, status

   **Feature Backlog**:
   - High priority (P1)
   - Medium priority (P2)
   - Low priority (P3)

   **Dependencies & Blockers**:
   - Internal dependencies
   - External dependencies
   - Current blockers

   **Milestones**:
   - Milestone name, date, description
   - Status (upcoming, achieved)

   **Success Metrics**:
   - Key metrics for project success
   - Current status vs targets

2. **Save to**: `sprints/roadmap.md`

### Step 8: Generate Visual Timeline (Optional)

Create ASCII timeline:
```
Project Timeline
================

Sprint 001 [========] Complete (Oct 1-15)
Sprint 002 [========] Complete (Oct 16-31)
Sprint 003 [====----] In Progress (Nov 1-15)
Sprint 004 [--------] Planned (Nov 16-30)
           ^
           Today
```

### Step 9: Output Summary

Display summary with:
- Location of roadmap file
- Number of completed sprints
- Current sprint info
- Number of upcoming planned sprints
- Feature backlog count
- Active blockers count
- Milestone status

## Integration with Other Commands

### `/speckit-sprint start` Integration
- Update roadmap when new sprint starts
- Move sprint from "Upcoming" to "Current"

### `/speckit-archive` Integration
- Update roadmap when sprint completes
- Move sprint from "Current" to "Completed"

### `/speckit-specify` Integration
- Add new features to backlog
- Update feature counts

## Notes

- Roadmap is living document - update regularly
- Roadmap shows high-level view, not detailed specs
- Use roadmap for stakeholder communication
- Update after each sprint completion
- Review and adjust upcoming sprints as needed
