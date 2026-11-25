# WikiGuard: Storyline

**Team:** Vlada, Zeynep, Dominik, Mykyta

## 1. Hook

WattWise gave us their code and three bug tickets. We could have fixed three bugs. Instead we asked: _why do these bugs exist at all?_

## 2. Insight

- All 3 bugs are the same problem: **knowledge drift**. The wiki says one thing, the code does another.
- The 39 existing tests were **all green** and caught none of them.
- The cost is real: a billing run that crashed (BUG-142), customers overcharged ~€97 (BUG-151), base-fee revenue leaking ~3% on every invoice (BUG-158).

> The problem isn't bugs. It's that there's no single source of truth.

## 3. How we worked (consulting approach)

1. **Discover:** read the repo like a new hire (wiki, conventions, tests, tickets).
2. **Diagnose:** reproduced all 3 bugs by hand and traced each to a wiki rule the code breaks.
3. **Research:** parallel AI research agents scanned GitHub, Hacker News, papers and tools (Swimm, DeepWiki, SWE-agent, …). Gap found: existing tools generate docs _from_ code, so they document the bug as the rule.
4. **Design → Build → Validate:** below.

## 4. What we built: a universal agent toolkit

| Piece                        | What it does                                                                                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **AGENTS.md**                | One instruction file every major coding agent reads (Claude Code, Codex, Copilot, Cursor). Wiki = truth, hard boundaries, company guidelines. |
| **Skills**                   | Portable playbooks: `fix-bug`, `drift-check`, `wiki-sync`.                                                                                    |
| **Drift check**              | Runs the wiki's worked examples against the code → _in sync / drift / untested_.                                                              |
| **Integrity lint + CI gate** | No orphans: every wiki page, data file, module and ticket must be linked and consistent.                                                      |
| **Guardrails**               | Hooks block edits to rules, data and existing tests; every agent action is logged.                                                            |
| **Human in the loop**        | Agent proposes with a root-cause report; a fresh-context reviewer checks; humans approve.                                                     |

## 5. Proof

- Before: drift check flags **all 3 bugs**.
- We ran the agent headless on each ticket: **3 bugs fixed in ~8 minutes**, each with a failing-first test, wiki citation, CHANGELOG entry and RCA report.
- After: **0 drift**, all 5 customers invoiced, 62 of 63 tests pass.
- Guardrails verified live: an agent told to edit a wiki rule, overwrite data and weaken a test was blocked all 3 times, and each attempt was logged.
- **New finding nobody reported:** the one remaining failure is our lint catching `tariff.py` raising Python built-in errors (`ValueError`, `AssertionError`) instead of the team's domain exceptions. That breaks their own CONTRIBUTING rule, and no ticket or test had noticed. The system finds problems, not just fixes known ones.
- Bonus findings: an unreported overcharge (C-1003, October) and €5.04 of base-fee underbilling on issued invoices, both flagged for a finance decision.

## 6. Why it matters

- **Universal:** plain Markdown and Python, works with any agent and any repo.
- **Prevents, not just fixes:** drift is caught in CI before it reaches a customer.
- **Trustworthy:** deterministic checks first, AI second, human approval always.

## 7. Next steps

Pilot on one real WattWise team for 8 weeks → measure time-to-fix, drift caught pre-release and fix acceptance rate → roll out across repos.
