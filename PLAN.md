# Workshop Plan — WattWise (60 min)

Research inputs (in `research/`): `wattwise-analysis.md` (ground truth for the 3 bugs), `tech-agent-research.md`, `energy-usecases-research.md`, `consulting-frameworks-research.md`.

Deliverables: 2 separate pitches (deck + live demo) + markdown docs in repo.

---

## Case 1 — Bug Fixing Agent ("WattWise Fixer")

### Consulting storyline (SCR)
- **Situation:** WattWise devs lose time on recurring billing bugs; 3 open tickets.
- **Complication:** each bug costs money or trust — BUG-142 blocks the billing batch (cash), BUG-151 overcharges customers (~€97 incl. VAT across C-1002/C-1003, one case unreported), BUG-158 leaks ~3.3% of base-fee revenue on *every* invoice. The 39 existing tests are green and catch none of them.
- **Resolution:** a portable, human-in-the-loop agent that treats the wiki as the source of truth, reproduces the bug with a failing test, fixes it, proves it, and hands a reviewed PR to a human.

### Phases (what we "did for the client")
1. **Discover:** read the repo the way a new team member would: wiki, CONTRIBUTING, tests, tickets. Finding: the wiki is right, the code is wrong, and the tests don't cover these rules.
2. **Diagnose:** reproduce all 3 bugs and find each root cause (`meter.py:49`, `tariff.py:101`, `models.py:86`), plus who is affected.
3. **Design:** pick an agent architecture based on the research: a fixed pipeline beats a swarm (Agentless, mini-SWE-agent); reproduce-first; enforce guardrails with hooks; review with a fresh context.
4. **Build:** (below)
5. **Validate:** live demo on the tickets.
6. **Operate/scale:** autonomy ladder, KPIs, 8-week pilot, governance.

### Architecture: "universal" = tool-agnostic
- `AGENTS.md` (read natively by Codex, Copilot, Cursor and Gemini; `CLAUDE.md` → symlink). It holds the team rules: wiki beats code, never edit the wiki or existing tests, Conventional Commits, CHANGELOG, ticket status `Fixed (pending review)`.
- `.claude/skills/fix-bug/SKILL.md`: the playbook, also usable as a plain prompt by any agent:
  1. Triage → 2. Locate root cause and cite the wiki rule next to the code line → 3. Write a failing regression test using the wiki's worked examples → **human gate: approve the RCA** → 4. Minimal fix → 5. Full pytest + blast-radius re-bill (before/after per customer) → 6. Fresh-context reviewer checks against the Definition of Done → 7. Commit, CHANGELOG, ticket update, RCA report.
- Guardrails (Claude Code hooks): block edits to `wiki/`, `data/` and existing tests; log every tool call to `audit.log`.
- Runner: `claude -p "/fix-bug BUG-142"` (headless), or interactive for the demo.

### Build order (≈30 min)
| Min | Task |
| --- | --- |
| 0–10 | AGENTS.md + skill + hooks |
| 10–20 | Run agent on BUG-142 (easy, deterministic) → save RCA + diff |
| 20–30 | Run on BUG-151 (best business story; impact table) and BUG-158 if time |

### Demo (~7 min pitch)
Value framing (1 min) → architecture and guardrails (1) → live BUG-142: red test → wiki citation → fix → green → `run 2026-11` shows 5/5 (3) → BUG-151 impact table plus the guardrail blocking a test edit (1) → KPIs, pilot, next steps (1). Keep a pre-recorded run as backup.

KPIs: time per ticket, first-pass acceptance rate, escalation rate, reopen rate, € recovered.

---

## Case 2 — AI Strategy for WattWise Energy

### Storyline
"WattWise is a German household supplier and doesn't own the grid. Its value pool is retail: billing, service, churn, procurement. Its own code shows the problem: billing errors leak revenue and trust."

### Phases
1. **Discover:** map the value chain, look at the market context (14% switching rate in Germany, dynamic tariffs mandatory since 2025, only 5.5% smart meter coverage, EU AI Act high-risk rules moved to Dec 2027, NIS2, SAP's old utility billing system out of maintenance in 2027).
2. **Ideate:** long-list of about 45 use cases across 8 value-chain steps (in the research file) → short-list of about 12.
3. **Framework:** 3 pass/fail gates (legal/AI Act, data exists, strategic fit) → value score (€ impact, customer impact, strategic fit, scalability) vs feasibility score (data readiness, tech maturity, time-to-value, risk), weighted 50/50 on a 1/3/5 scale → 2x2 of quick wins, lighthouses, strategic bets and deprioritised. Add a sensitivity check showing the top 3 stay on top under different weights.
4. **Prioritise:**
   - **Quick wins:** AI that explains bill changes; agent assist for service; the AI bug-fixing agent (proven in Case 1).
   - **Lighthouse:** "Billing Guardian", pre-bill anomaly detection plus revenue-leakage recovery.
   - **Strategic bets:** a dynamic-tariff energy copilot that steers customer flexibility; churn prediction with next-best-action.
5. **Roadmap:** H1 (0–6 months) quick wins plus Billing Guardian pilot → H2 (6–12 months) scale service agents and churn → H3 (12–24 months) the flexibility copilot. Enablers: data platform, AI governance board, BCG's 10-20-70 rule (70% of the effort is people and process).
6. **Next steps:** for the top 3 use cases, an 8-week pilot each with an owner, KPIs and a budget range.

### Build order (≈30 min, in parallel with Case 1 if 2 people)
| Min | Task |
| --- | --- |
| 0–10 | Score the short-list in a matrix (markdown table) |
| 10–20 | 2x2 chart + roadmap |
| 20–30 | Deck: ~10 slides with action titles |

Deck: 1 title with the answer up front → 2 client situation → 3 value chain and where WattWise plays → 4 long-list → 5 framework and weights → 6 2x2 → 7 top 3 deep dive → 8 roadmap H1–H3 → 9 risks & governance (AI Act, GDPR) → 10 next steps and the decision we're asking for.

---

## Open decisions
1. Agent runtime: Claude Code + AGENTS.md/skill (recommended, ~10 min to build) vs a custom Claude Agent SDK script (more impressive, but risky in 1 hour).
2. Team split: who owns Case 1 and who owns Case 2?
3. Deck tool: Google Slides/PowerPoint by hand, or should I generate the slides?
