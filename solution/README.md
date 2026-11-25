# WikiGuard: one source of truth for WattWise

**Problem:** all 3 open bugs (BUG-142, BUG-151, BUG-158) are *knowledge drift*: the code silently diverged from the wiki rules while the 39 tests stayed green. Fixing bugs one at a time treats the symptom.
**Solution:** a tool-agnostic layer that makes wiki ↔ code ↔ tests ↔ data one connected, checked system, and AI agents that work inside it with guardrails and human approval.

## What's in the box (installs over the client repo)

| Layer | File | Role |
| --- | --- | --- |
| Agent instructions | `AGENTS.md` | Source-of-truth order, boundaries, workflows, company guidelines. Read natively by Claude Code (when no CLAUDE.md is present), Codex, Copilot, Cursor and Windsurf |
| Company guidelines | `GUIDELINES.md` | C/N/T/Q/E/K/P/A principles, each traced to an incident and an enforcing check |
| Skills (agentskills.io) | `.agents/skills/{fix-bug,drift-check,wiki-sync}` | Playbooks; symlinked into `.claude/skills/` for Claude Code |
| Reviewer | `.claude/agents/reviewer.md` | Fresh-context review against the Definition of Done |
| Guardrails | `tools/guard.py` + `.claude/settings.json` | Blocks edits to rule pages, `data/`, existing tests; audit log |
| Rule map | `tools/drift-check/rules.json` | Rule ID ↔ code ↔ tests ↔ examples, plus inventory of every wiki page and data file |
| Drift check | `tools/drift-check/drift_check.py` | Runs wiki worked examples against the code: IN SYNC / DRIFT / UNTESTED |
| Integrity lint | `tools/wikiguard_lint.py` | KIT wired up · INV no orphan wiki/data/module, schema drift · MAP registry complete · CODE guideline violations |
| Test gate | `tests/test_wikiguard.py` | Lint + drift + invariants (price continuity, inclusive days, rollover) inside `pytest` |
| CI | `.github/workflows/wikiguard.yml` | Same gate on every PR, drift report in the job summary |

## Run

```bash
./install.sh ../wattwise
cd ../wattwise
python tools/wikiguard_lint.py --repo .          # is the knowledge layer complete?
python tools/drift-check/drift_check.py --repo . # do wiki and code agree?
python -m pytest                                 # includes the WikiGuard gate
claude "/fix-bug BUG-142"                        # agent fix with human gate
```

## Verified results

| | Client code as-is | With the 3 fixes |
| --- | --- | --- |
| Drift check | 3 root-cause DRIFT (+2 inherited) | 0 DRIFT |
| pytest (39 original + 14 gate) | 13 failed, 40 passed | 1 failed (lint), 52 passed |
| Lint errors | 3 (E1: built-in exceptions in `tariff.py`) | 3 (same; a separate finding) |

Seeded tests: a new unregistered wiki page, an unregistered data file, a renamed CSV column and a stale module name in Architecture.md were each flagged by the lint.
