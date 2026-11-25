# Knowledge Drift: Research & Recommended Design

Context: the WattWise billing repo. All 3 bugs (BUG-142 meter rollover, BUG-151 tiered brackets, BUG-158 inclusive day count) are **knowledge drift**: the code moved away from the wiki and the 39 tests stayed green. CONTRIBUTING.md says "if code and wiki disagree, the code is wrong". Thesis: there is no single source of truth that both the wiki and the code are checked against. We want an AI loop that writes and maintains the wiki in sync with the code, detects drift in both directions, and fixes bugs grounded in the wiki.

Research date: 2026-11-25. Statements marked (2nd-hand) come from secondary coverage I could not check against the primary source.

---

## 1. Landscape: tools & products

### A. AI wiki generators (code → docs; mostly one-shot, read-only)
| Tool | What it does | Relevance / weakness |
| --- | --- | --- |
| **DeepWiki / Devin Wiki** (Cognition) | Generates a wiki and a Q&A chat for any GitHub repo. You can steer it with `.devin/wiki.json` (`repo_notes`, `pages`; max 30 pages). | Generated **from code**. If the code is wrong, the wiki faithfully documents the bug. It hallucinates (see §3). https://docs.devin.ai/work-with-devin/deepwiki |
| **Google Code Wiki** (Nov 13 2025, Gemini) | Wiki per repo, regenerated after each change. Hyperlinks go from concepts to the exact files and functions. Diagrams and a chat agent. Public preview; the private-repo Gemini CLI extension is still on a waitlist (2nd-hand). | "Always up to date" means up to date **with the code**, not with business intent. https://developers.googleblog.com/introducing-code-wiki-accelerating-your-code-understanding/ |
| **RepoAgent** (Tsinghua/Siemens, EMNLP'24 demo) | Repo-level docs in 3 stages: global structure analysis, generation, **update hooked into Git**. | Early example of "maintain, not just generate". https://arxiv.org/abs/2402.16667 · https://github.com/OpenBMB/RepoAgent |
| **DocAgent** (Meta, ACL'25) | Multi-agent Reader/Searcher/Writer/**Verifier**/Orchestrator. Works in topological dependency order over the AST. Evaluated on Completeness, Helpfulness, **Truthfulness**. | The Verifier role and the truthfulness metric are worth copying. https://arxiv.org/abs/2504.08725 · https://github.com/facebookresearch/DocAgent |
| **CodeWiki** (FSoft, ACL'26 Findings) | Hierarchical decomposition, recursive agents, diagrams. **CodeWikiBench** scores generated docs with rubrics **derived from the official human docs**. ~68.8% score; DeepWiki ~65 on re-run. | Even the best systems recover only about two thirds of what the human docs say. Human-owned docs remain the reference. https://arxiv.org/abs/2510.24428 · https://github.com/FSoft-AI4Code/CodeWikiBench |
| **Karpathy "LLM Wiki"** (gist, Apr 2026) | "Idea file": raw sources (immutable) → LLM-owned markdown wiki → schema file (e.g. CLAUDE.md). Three operations: **ingest, query, lint**. Lint finds "contradictions between pages", "stale claims that newer sources have superseded", orphans, missing cross-refs. "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase." 5k+ stars in 2 weeks (2nd-hand). | Closest conceptual match. Our twist: treat **code as one more source** and lint wiki ↔ code contradictions. https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f |

### B. Docs that stay synced with code (continuous documentation)
| Tool | Mechanism |
| --- | --- |
| **Swimm** | "Code-coupled docs": markdown in the repo that references snippets, tokens and paths. A patented **Auto-sync** analyzes each PR diff and auto-updates trivial changes (renames). On significant changes the **CI check fails** with "docs likely out of date", and a human clicks "Approve Auto-sync". https://swimm.io/blog/keeping-internal-docs-up-to-date-always-with-the-swimm-github-app · https://devm.io/continuous-delivery/documentation-toledano-176995 |
| **Mintlify Autopilot** (beta, Oct 2026) | Background agent. When code merges it reads the diff, finds the affected doc sections and **opens a docs PR tagged for review**; also runs a daily quality check. Optional auto-merge. https://www.mintlify.com/docs/autopilot · https://thedocsreport.com/mintlify-autopilot-pull-requests-2026/ |
| **DeepDocs, gh-aw daily doc updater, Copilot automations, dosu + claude-code-action** | Same pattern: code change → agent → reviewable docs PR, never a direct commit to main. Overview: https://www.augmentcode.com/guides/self-updating-documentation-docs-agents-sync · https://www.agentpatterns.ai/workflows/continuous-documentation/ |
| **OSS drift detectors** | `jbrockSTL/doc-drift` (GitHub Action, LLM flags stale docs per PR, optionally fails the build): https://github.com/jbrockSTL/doc-drift · `custodex` (`cdx check` exits non-zero on drift; pluggable LLM backend incl. Claude Code CLI; logs every verdict for human review): https://github.com/JuanSync7/custodex · `docdrift` (stdlib, deterministic first, LLM only for uncertain cases): https://github.com/Ashutosh-Kumar03/docdrift · `ooli/DocGuard` (AST diff + local LLM): https://github.com/Nobody-KnowsBetter/ooli · `DocSync` (AST diff gating + RAG + LLM judge, never auto-merges): https://github.com/SahilMudgil/DocSync · Claude skill `doc-drift-detector`: https://github.com/borghei/Claude-Skills/blob/main/engineering/doc-drift-detector/SKILL.md |

**Gap in the market:** nearly every tool checks **signatures, flags, renamed symbols and API surface**, and only in the **code → docs** direction. None checks **business semantics** (for example, "tiers are marginal like tax brackets"), and none handles **docs → code**, where the docs are the truth and the code is the bug. Augment's "living specs" and Focused Labs mention two-way sync, but only as a concept: https://www.augmentcode.com/guides/living-specs-vs-static-specs · https://dev.to/focused_dot_io/documentation-drift-breaks-coding-agents-focused-labs-3bkp

### C. Executable specifications / living documentation (docs → code, deterministic)
- **Specification by Example** (Gojko Adzic, 2011). Its chapter on "Living documentation" makes the point that specs with concrete examples, **automatically validated**, never go stale. Its patterns include "automating validation without changing specifications". https://www.manning.com/books/specification-by-example · https://en.wikipedia.org/wiki/Specification_by_example
- **Concordion / FitNesse / Cucumber-Gherkin / pytest-bdd**. Human-readable specs (HTML, wiki tables, Given/When/Then) are instrumented to run as tests. FitNesse is literally a wiki whose tables execute. That is exactly the shape of the WattWise wiki tables.
- **doctest / Sybil / pytest-markdown-docs**. `pytest --doctest-glob="*.md"` runs `>>>` examples embedded in markdown. Sybil and pytest-markdown-docs run fenced code blocks.
- **Vale** (prose linter in CI, used by Grafana and GitLab). It enforces style and terminology but does not catch semantic drift. Useful for a glossary rule (e.g., always "billable days"). https://grafana.com/docs/writers-toolkit/review/lint-prose/

### D. Spec-driven development (SDD) and agent memory
- **GitHub spec-kit**: constitution → specify → plan → tasks → implement → **converge** (`/speckit-converge` compares code against spec/plan/constitution and is read-only). The constitution plays the role of our CONTRIBUTING.md. https://github.com/github/spec-kit
- **AWS Kiro**: `.kiro/specs/` (requirements.md in **EARS**: "WHEN … THE SYSTEM SHALL …", design.md, tasks.md), **steering files** (product/tech/structure.md), **agent hooks** (on file save or tool use → run an agent prompt). Can generate property-based tests from EARS requirements. https://kiro.dev/docs/specs/ · https://kiro.dev/docs/hooks/
- **Tessl**: "spec-as-source", `// GENERATED FROM SPEC - DO NOT EDIT`. Same spec produced different code across runs. Now pivoting to a skills/registry platform.
- **Böckeler (Thoughtworks, martinfowler.com)**: three levels, **spec-first → spec-anchored → spec-as-source**. Most tools only deliver spec-first. Kiro turned a small bug into 4 user stories and 16 acceptance criteria. "I'd rather review code than all these markdown files." Warns of a repeat of the model-driven-development failure. https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
  - **Positioning for us:** WattWise already has a human spec (the wiki). We need **spec-anchored**: keep the wiki and code continuously reconciled. No SDD ceremony, no regeneration.
- **ADRs** (Architecture Decision Records) keep the "why" that AI docs lose (§3). Wiki rules already carry ticket references (FEAT-064), which work as lightweight ADR anchors.
- **AGENTS.md / CLAUDE.md / Cursor rules / Kiro steering**: persistent context files. Necessary, but they **block nothing on their own**. Enforcement needs tests, hooks or CI.

---

## 2. Patterns to adopt

1. **Stable rule IDs = bidirectional traceability.** Give each wiki rule an anchor such as `RULE-METER-ROLLOVER`. Code cites it (`# implements RULE-METER-ROLLOVER`) and tests carry `@pytest.mark.rule("RULE-METER-ROLLOVER")`. A collection-time hook fails if a test cites an unknown ID or a rule has **no test**. Regulated-software precedent: `jamb` (IEC 62304, `@pytest.mark.requirement("SRS001")`, generates a trace matrix): https://github.com/vanandrew/jamb · general recipe (Pass / Fail / Stale / Gap verdicts): https://getautonoma.com/blog/requirements-traceability-matrix
2. **Compile wiki examples into tests (golden examples).** The worked examples in the WattWise wiki *already* match the sample data exactly: 247 kWh Basic → 113.03, Comfort 260 → 78.44, HeatPump 1220 → 337.18, rollover 99870→95 = 225, 30-day base fee 9.76. Parse those tables and blocks into parametrized pytest cases. This turns the wiki into FitNesse/Concordion-style living documentation in about 40 lines of code.
3. **Deterministic first, LLM second** (the docdrift/DocSync/ooli pattern). Executable examples catch hard drift for free. The LLM only judges prose rules that have no example, such as "one extra kWh must never make the bill jump".
4. **Drift is a CI check, not a dashboard.** Swimm fails the PR. Mintlify and custodex open PRs. Make `drift-check` a required check.
5. **Two-direction proposals plus a human "which side is truth" gate.** When drift is detected, the agent classifies it as either (a) **code is wrong**, opening a code-fix PR with a regression test (the default per CONTRIBUTING.md), or (b) **wiki is stale** (an intentional change, e.g. FEAT-064 moving the base fee to per-day), opening a wiki PR for **product-owner sign-off**. It never edits a business rule unilaterally. That matches CONTRIBUTING's "raise it in the PR, do not change it yourself".
6. **Verifier role + fresh context** (DocAgent). A second pass checks every generated doc claim against code and line references, and every code fix against the wiki citation.
7. **Keep the "why".** Wiki-generation prompts must preserve rationale ("so customers who move mid-month only pay for supplied days"; "marketing promises…") and ticket refs. Do not just restate the code.
8. **LLM-wiki lint loop** (Karpathy). Periodically lint for contradictions between wiki pages, between wiki and code, orphan rules, and rules without examples.

---

## 3. Evidence

### Cost of outdated docs / knowledge loss
- **GitHub Open Source Survey 2017**: "incomplete or outdated documentation is a pervasive problem, observed by **93%** of respondents", yet **60%** rarely or never contribute docs. (Quoted in Tan et al., EMSE: https://arxiv.org/abs/2212.01479; original: https://opensourcesurvey.org/2017/)
- **GitHub Octoverse 2021**: "developers see about **50% productivity boost** with easy-to-source documentation" (survey of 12k devs + 4M repos; 2nd-hand quotes). https://www.infoq.com/news/2021/11/github-octoverse-2021 · https://swimm.io/blog/documentation-game-changer
- **Stack Overflow Dev Survey 2022**: **68%** hit a knowledge silo at least weekly; **63%** spend >30 min a day searching for answers; for a 50-dev team that is **333–651 h/week lost**. 2023: 63% still >30 min a day. https://stackoverflow.blog/2022/06/22/asked-and-answered-the-results-for-the-2022-developer-survey-are-here/ · https://survey.stackoverflow.co/2023/
- **Wen et al. 2019** (1,500 Java systems): only **13–20%** of code changes trigger comment updates, so docs drift by default. https://www.inf.usi.ch/lanza/Downloads/Wen2019a.pdf
- **Code-comment inconsistency → bugs**: iComment (Linux/Mozilla) found outdated comments that caused real bugs. A 2024 study links inconsistency to bug introduction: https://arxiv.org/abs/2409.10781
- **Hu et al. ICSE'22** (720 practitioners): **74%** want tools that check comment/code consistency. https://xin-xia.github.io/publication/icse224.pdf
- WattWise itself: 3 drift bugs, all passing CI. In the client's own numbers: billing batch blocked, ~€97 overcharge, ~3.3% base-fee revenue leak on every invoice (see `wattwise-analysis.md`).

### Practitioner criticism of AI docs (design constraints)
- **Hallucination / confident wrongness**: an HN maintainer on DeepWiki: "It's so wrong in every section I saw." https://news.ycombinator.com/item?id=45884860 · "very subtly incorrect … likely to boomerang on you only a month or so later"; it hallucinates when names no longer match behaviour: https://news.ycombinator.com/item?id=45011615 · An OpenWrt maintainer received "bug" reports based on DeepWiki errors: https://forum.openwrt.org/t/important-consideration-deepwiki-ai-generated-docs-may-contain-inaccuracies/249471
- **Docs generated from code inherit the code's bugs**: the core argument against code → docs-only tools. On WattWise, DeepWiki would document cumulative-tier pricing as "the rule".
- **Restating the code / losing the why**: "If the comments can be generated from the code, then they are just restating what the code is doing." https://news.ycombinator.com/item?id=36044663 · "Summaries keep the rule and drop the 'because'": https://news.ycombinator.com/item?id=50331998 · "I hate when the AI edits and removes my 'why' comments": https://news.ycombinator.com/item?id=49646940
- **Feedback-loop risk**: users stop reaching curated docs, and LLMs train on wrong generated docs. https://news.ycombinator.com/item?id=45884169
- **Counter-evidence**: "documentation is MUCH more up to date since using LLMs" https://news.ycombinator.com/item?id=50438318
- **SDD overhead**: too many markdown files and false control (Böckeler, above).

**Design implications:** (1) never let generated docs overwrite human business rules; (2) ground every claim in a code line *and* a wiki rule; (3) prefer executable checks over LLM opinion; (4) human approval decides which side is truth; (5) keep rationale and ticket references.

---

## 4. Recommended minimal design (~30 min build): "WikiGuard" (spec-anchored)

**Pitch line:** *"Your wiki already contains the answers. We made it executable, traceable and self-maintaining, so the next bug fails CI instead of reaching a customer's invoice."*

### Components
1. **Rule anchors in the wiki (5 min, the agent does it).** Add `<!-- rule: RULE-TARIFF-MARGINAL -->` style IDs above each business rule and worked example in `Tariffs.md`, `Meter-Readings.md` and `Billing-Rules.md`. Add a `wiki/Rules-Index.md` (Karpathy-style index) listing rule → page → implementing function → tests. Wording of business rules is not changed, so no PO sign-off is needed.
2. **`tests/test_wiki_examples.py`, executable wiki (10 min).** Parse the markdown worked-example tables and blocks. Hand-coded regex is fine: tier tables with a bold total row, `→ 225 kWh`, `→ 9.76 EUR`, the full-example invoice. Generate parametrized pytest cases marked `@pytest.mark.rule(...)`. Run it and **the golden examples go red, exposing all 3 bugs** (expected ~5: base fee, full example, Comfort, HeatPump, rollover; not yet run). Until now the suite was 39 green.
3. **`conftest.py` traceability gate (5 min).** Register the `rule` marker. At collection, fail on unknown rule IDs. Print a coverage matrix (rule → tests → status) and flag rules with no test as **GAP**.
4. **`/drift-check` agent skill (both directions) (5 min, a prompt file).** Inputs: wiki page, mapped code (from Rules-Index), red test output. Output: a drift report per rule with verdict `CODE_WRONG` | `WIKI_STALE` | `AMBIGUOUS`, citing the wiki line and the code line.
   - `CODE_WRONG` (default per CONTRIBUTING) → hand off to the existing `/fix-bug` skill (Case 1): minimal fix, wiki tests go green.
   - `WIKI_STALE` → draft a wiki PR containing the "why" and ticket ref, **flagged for product-owner sign-off**. Never auto-merged.
   - Prose-only rules (no example) → LLM judge plus a proposed new worked example to add, which shrinks the LLM's role over time.
5. **Guardrails / CI (5 min).** A Claude Code hook blocks agent edits to business-rule text in `wiki/` (anchors and index only). `audit.log`. A one-line GitHub Action: `pytest` (includes the wiki examples + trace gate) → on failure, run `claude -p "/drift-check"` and comment the report on the PR.

### Demo script (~4 min)
1. "39 green tests, 3 customers overcharged." Show the wiki example table next to the code.
2. Run `pytest tests/test_wiki_examples.py` → red, each labelled with a RULE ID. Show the trace matrix with GAPs.
3. `/drift-check` → report: 3× `CODE_WRONG` with wiki↔code citations, plus 1× `WIKI_STALE` candidate (illustrate it with a deliberately changed doc, or show FEAT-064 as the history example).
4. `/fix-bug BUG-151` → green. Reverse direction: change a wiki number in a branch and the gate flags code ≠ wiki, which proves it works both ways.
5. Close with KPIs: % rules with executable examples, drift MTTD (minutes vs. a customer complaint), # GAPs, wiki PR acceptance rate.

### Why this wins with judges
- Directly answers "no unified source of truth": the **wiki becomes the test oracle** and both sides are continuously reconciled.
- **Deterministic core, AI on the edges**, which answers the hallucination criticism head-on.
- Covers a gap commercial tools leave open (Swimm, Mintlify, DeepWiki are code → docs, syntactic): **semantic business-rule drift, both directions, with human truth arbitration**.
- Scales via a maturity path: anchors → executable examples → CI gate → agent PRs → Karpathy-style lint and auto-generated wiki for undocumented modules (with a Verifier).
- Fits the regulatory direction for energy billing: an auditable rule ↔ code ↔ test trace matrix, as in IEC 62304 practice.

### Risks / honest caveats
- Regex parsing of the wiki is brittle. Mitigation: a fenced `example` block convention for new rules.
- Telling `WIKI_STALE` apart from `CODE_WRONG` needs intent. That is why it is a human gate, not automated.
- Several figures above are secondary quotes (marked). The 2017 GitHub survey and the Octoverse 2021 figures were not checked against the primary pages.
