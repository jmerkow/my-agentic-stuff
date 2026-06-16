# Procedure Checklist

Quick-reference for the orchestrator. Each box is a gate — don't skip ahead.

## Phase 1 — Discovery

- [ ] Scan target directory for source and config files
- [ ] Group files into functional groups by concern (≤1000 LOC each)
- [ ] Map import/dependency edges between groups
- [ ] Present group manifest to user for confirmation
- [ ] User confirms (or adjusts) groups before proceeding

## Phase 2 — Review

Per group (in dependency order):

- [ ] Read all files in the group
- [ ] Dispatch **Sub-agent A** (`eng-code-sub`) with review prompt + file contents
- [ ] Dispatch **Sub-agent B** (orchestrator's choice) with same prompt + contents
- [ ] Confirm both agents returned independently (no cross-contamination)
- [ ] Merge findings: tag agreements, uniques, and disagreements
- [ ] Write merged findings to `.eng/scratch/reviews/<group-slug>-review.md`
- [ ] Notify user the file is ready, then proceed to next group

## Phase 3 — Triage

- [ ] User fills in the response blockquote on each finding
- [ ] Answer any questions the user raises about findings — iterate until resolved
- [ ] Tag each finding heading with status emoji (✅ ⏳ ❌) once disposition is final
- [ ] Append `## Change Requests` section with one CR per accepted finding (or merged group)
- [ ] Cross-check CRs for interactions/conflicts (e.g., import added by one CR, removed by another)
- [ ] (Optional) Validate CRs with `eng-code-sub` — fix any UNCLEAR items
- [ ] Review is complete when all findings have a status tag and all CRs are CLEAR
