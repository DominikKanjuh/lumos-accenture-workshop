---
name: drift-check
description: Detect and triage knowledge drift between the wiki business rules and the code. Runs the deterministic checker, then classifies each finding and routes it to the right owner. Use before releases, on every PR, or when asked whether code and docs agree.
---

# drift-check

## 1. Run the deterministic check (no LLM judgement yet)
```bash
python tools/drift-check/drift_check.py --repo . --out reports/drift-report.md
```
Statuses: `IN SYNC`, `DRIFT` (wiki example ≠ code result), `UNTESTED` (rule has no test), `NO EXAMPLE`, plus wiki sections missing from the registry and `UNDOCUMENTED` code.

## 2. Triage each finding into exactly one bucket
| Bucket | Meaning | Action |
| --- | --- | --- |
| **Code wrong** | Wiki rule is clear, code contradicts it | Open or link a ticket in `issues/`, hand to `fix-bug` |
| **Wiki stale** | Code reflects an approved change the wiki missed (check CHANGELOG / git log) | Draft `wiki/_proposals/<rule-id>.md` for PO sign-off |
| **Ambiguous** | Cannot tell which side is right | Escalate to a human with both readings; do not guess |
| **Untested** | Rule correct in code but unprotected | Hand to `wiki-sync` to turn its wiki examples into tests |
| **Undocumented** | Code with business meaning but no wiki rule | Hand to `wiki-sync` to draft documentation |

Inherited drift (`depends_on` in `rules.json`) is resolved by its root rule. Don't open duplicate tickets.

## 3. Report
Write `reports/drift-triage.md`: one table row per finding (rule id, status, bucket, evidence, owner, next step) and a one-paragraph summary for the product owner and tech lead. Include the € impact when a DRIFT affects invoices.
