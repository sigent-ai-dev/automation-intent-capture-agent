---
name: "speckit-dora"
description: "Generate weekly DORA metrics snapshot from GitHub data."
argument-hint: ""
compatibility: "Requires GitHub repo with gh CLI"
metadata:
  author: "speckit-extras"
  source: "speckit-extras/extension/commands/speckit.dora.md"
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

`/speckit.dora` computes the four DORA-2018 metrics from GitHub API data and produces a Markdown report. It provides visibility into delivery health without external tooling.

### Inputs

- `[<start>..<end>]` (optional) — explicit ISO-8601 date window. Defaults to last 7 days.
- `--dry-run` — render to stdout, don't write file.
- `--output <path>` — override output path.

### Execution Flow

**Step 1 — Determine window.**

- Parse date range from arguments, or default to `7 days ago..today`
- Identify the repo from `gh repo view --json nameWithOwner`

**Step 2 — Fetch data via `gh` CLI.**

```bash
# Merged PRs in window
gh pr list --state merged --search "merged:>=<start> merged:<=<end>" --json number,title,mergedAt,headRefName,commits,createdAt --limit 500

# Workflow runs (deployments) in window
gh run list --workflow <deploy-workflow> --status completed --json conclusion,createdAt,updatedAt --limit 500

# Revert PRs (for CFR)
gh pr list --state merged --search "merged:>=<start> merged:<=<end> revert in:title" --json number,mergedAt
```

If the repo doesn't have a deploy workflow, fall back to merged-to-main PRs as the deployment proxy.

**Step 3 — Compute metrics.**

**Deployment Frequency (DF):**
- Count: successful deploy runs (or merged PRs) in window
- Rate: count / active days in window
- Band: Elite (multiple/day) | High (1/day–1/week) | Medium (1/week–1/month) | Low (<1/month)

**Lead Time for Changes (LT):**
- For each merged PR: time from first commit on branch to merge timestamp
- Metric: median across all PRs in window
- Band: Elite (<1 day) | High (1 day–1 week) | Medium (1 week–1 month) | Low (>1 month)

**Change Failure Rate (CFR):**
- Failures: deploy runs with `conclusion: failure` OR revert PRs merged within 24h of a deploy
- Rate: failures / total deploys
- Band: Elite (0-5%) | High (5-10%) | Medium (10-15%) | Low (>15%)

**Mean Time to Restore (MTTR):**
- For each failure: time from failure to next successful deploy
- Metric: median across failures in window
- Band: Elite (<1 hour) | High (<1 day) | Medium (<1 week) | Low (>1 week)

**Step 4 — Compare with prior window.**

If a previous report exists at `doc/reports/`, load its metrics and compute deltas:
- ↑ improved, ↓ degraded, → unchanged

**Step 5 — Render report.**

```markdown
# DORA Report: <start> → <end>

**Repository**: <owner/repo>
**Generated**: <timestamp>
**Window**: <N> calendar days, <M> active days

## Metrics

| Metric | Value | Band | Prior | Δ |
|--------|-------|------|-------|---|
| Deployment Frequency | 22.3/day | Elite | 13.5/day | ↑ |
| Lead Time for Changes | 17 min (median) | Elite | 8 min | → |
| Change Failure Rate | 40.4% | Medium | 33.3% | ↓ |
| Mean Time to Restore | 27 min | High | 1h 36m | ↑ |

## Detail

### Deployment Frequency
- Total merges: <N>
- Active days: <M>
- Peak: <day> (<count>)

### Lead Time
- Median: <time>
- p90: <time>
- Fastest: PR #<N> (<time>)
- Slowest: PR #<N> (<time>)

### Change Failure Rate
- Total deploys: <N>
- Failures: <M>
- Reverts: [list PR numbers]

### Mean Time to Restore
- Median: <time>
- Incidents: [list with duration]

## Notes

[Any observations — e.g., "CFR is high due to intentional smoke-test reverts, not production incidents"]
```

**Step 6 — Write output.**

- Default: `doc/reports/YYYY-MM-DD-weekly-dora.md`
- Update `doc/README.md` § Delivery Reports table (if section exists)
- If `--dry-run`: stdout only

**Step 7 — Report completion** with metrics summary and path to file.

## Guidelines

- Use `gh` CLI exclusively — no direct API calls. This keeps auth simple.
- If workflow data isn't available (no CI), degrade gracefully: use merged PRs as deployment proxy, note the limitation in the report.
- DORA bands follow the 2022 State of DevOps Report definitions.
- The Notes section is for human annotation — the command should leave it as a placeholder for the operator to fill in context (e.g., "reverts were intentional quality signals, not defects").
