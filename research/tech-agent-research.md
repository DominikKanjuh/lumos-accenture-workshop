# Bug-Fixing Agent: Research Brief (Case 1, WattWise)

Prepared 2026-11-25 for the Accenture AI workshop. Every claim links to a source. Caveat: many 2026 benchmark numbers come from vendors or aggregators. Treat them as directional, not audited.

---

## TL;DR

1. **Simple, structured workflows beat clever swarms.** The approaches that win are a fixed pipeline (localize, then reproduce, then repair, then validate) or one agent loop with good tools. Free-form multi-agent swarms do worse. Add only *read-only* subagents and a *fresh-context reviewer*.
2. **Reproduce first.** A regression test that fails before the fix is the single most important check against fixing the symptom instead of the cause. It is also exactly what the client's CONTRIBUTING.md requires.
3. **Context is the product.** The wiki is the spec ("if code and wiki disagree, the code is wrong"). An agent that cites the wiki rule it enforced is better than one that only makes the tests pass.
4. **Transparency means evidence.** Output a root-cause analysis (RCA), red→green test logs, the blast radius (which customers and amounts change), a full audit log, and a PR that a human must approve. The agent never merges.
5. **Value story:** developers spend 17.3 h/week on maintenance and bad code (Stripe). Industrial auto-fix pilots show minutes instead of hours, provided humans review the result (Meta SapFix, Google, GitHub Autofix).

---

## 1. State of the art: what actually works

| System | Architecture | Key lesson | Source |
|---|---|---|---|
| **Agentless** (Xia et al.) | Fixed 3 phases: hierarchical localization (file → class/function → edit lines), repair with sampled candidate patches, validation with reproduction and regression tests. No agent chooses the next action. | 32% on SWE-bench Lite at $0.70 per issue, beating the open-source agents of its time. Over 50% on Verified with Claude 3.5 Sonnet. **Predictable pipelines are competitive.** | [arXiv 2407.01489](https://arxiv.org/abs/2407.01489), [ACM](https://dl.acm.org/doi/full/10.1145/3715754) |
| **SWE-agent** | One agent loop plus an "Agent-Computer Interface": a small set of view/search/edit commands, with a linter that blocks syntactically broken edits. | Tool design matters as much as the model. Removing the linted edit causes the largest ablation drop. | [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf), [ACI docs](https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md) |
| **mini-SWE-agent** | About 100 lines, bash only, linear history. | Scores >74% on Verified. With frontier models, the **scaffold matters less and less.** It is now the harness for the "bash-only" leaderboard. | [GitHub fork mirror](https://github.com/RoyceChase/mini-swe-agent), [Steel leaderboard](https://leaderboard.steel.dev/leaderboards/swe-bench-verified/) |
| **Anthropic minimal scaffold** | bash plus a string-replace edit tool. Tools are "mistake-proofed", e.g. absolute paths are required. | Claude 3.5 Sonnet reached the then-SOTA 49%. "Performance can vary significantly based on scaffolding." | [Anthropic](https://www.anthropic.com/research/swe-bench-sonnet) |
| **AutoCodeRover** | Code search over program structure (AST, class/method) plus spectrum-based fault localization from tests. | 46.2% on Verified at under $0.70. Test-guided localization helps. | [arXiv 2404.05427](https://arxiv.org/pdf/2404.05427), [GitHub](https://github.com/AutoCodeRoverSG/auto-code-rover) |
| **OpenHands** (CodeAct) | General agent whose actions are code (bash/Python). Open SDK. | 72.8% on Verified with Sonnet 4.5. Open platform with many agents. | [ICLR 2025](https://arxiv.org/pdf/2407.16741), [SDK paper](https://arxiv.org/html/2511.03690v1) |
| **Moatless / SWE-Search** | Monte Carlo tree search over agent trajectories. | Search and self-evaluation trade compute for accuracy. On Lite it was on par with CodeAct (26.7% vs 26%). | [ICLR OpenHands paper](https://arxiv.org/pdf/2407.16741v2), [SWE-rebench refs](https://arxiv.org/pdf/2505.20411) |
| **Claude Code / Agent SDK** | The same harness as Claude Code (tools, subagents, hooks, permissions) exposed as a Python/TS library. Also headless `claude -p` and `anthropics/claude-code-action@v1` (@claude on an issue → branch/PR). | Hooks (`PreToolUse`, `PostToolUse`, `Stop`, …) can **deny** tool calls even in bypass mode, which gives you guardrails in code. | [SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks), [Python ref](https://code.claude.com/docs/en/agent-sdk/python), [GH Actions](https://code.claude.com/docs/en/github-actions), [headless](https://claudecodeguide.dev/docs/patterns/headless-mode) |
| **OpenAI Codex (cloud)** | Async sandbox per task, guided by AGENTS.md. | Gives "verifiable evidence": citations of terminal logs and test output, and states failures explicitly. | [Introducing Codex](https://openai.com/index/introducing-codex/), [upgrades](https://openai.com/index/introducing-upgrades-to-codex/) |
| **GitHub Copilot cloud/coding agent** | Assign an issue → `copilot/` branch → draft PR in a firewalled Actions VM. | Cannot approve or merge its own PRs. CI on its PRs needs human approval. The requester's approval does not count. | [GitHub Docs](https://docs.github.com/en/copilot/responsible-use/agents), [blog](https://github.blog/news-insights/product-news/github-copilot-meet-the-new-coding-agent/) |
| **Devin** | Fully async "junior engineer". | Self-reported PR merge rate rose from 34% to 67% (2025). Works best with clear requirements, and human review is still needed. | [Cognition](https://cognition.com/blog/devin-annual-performance-review-2025) |
| **Google Jules** | Async VM. **Shows a plan that you approve before any code is written.** Never auto-merges. | The plan-approval gate is a cheap, effective human-in-the-loop (HITL) step. | [Jules docs](https://jules.google/docs/), [Google blog](https://blog.google/innovation-and-ai/models-and-research/google-labs/jules/) |

**Benchmark reality check**
- Late-2026 claims: Claude Opus 5 at about 96–97% on Verified ([Vals.ai via Steel](https://leaderboard.steel.dev/leaderboards/swe-bench-verified/), [BenchLM](https://benchlm.ai/benchmarks/swe-bench-verified)). Opus 5.5 at 89.9% on the harder SWE-bench Pro (vendor-reported, [Morph](https://www.morphllm.com/swe-bench-pro)). The official swebench.com board is stale.
- Verified is saturated or contaminated. OpenAI stopped using it: ≥59.4% of the hard problems it audited have flawed tests ([OpenAI](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)). In SWE-Bench+, 32.7% of "successful" patches were solution leakage and 31% passed only because the tests were weak ([arXiv 2410.06992](https://arxiv.org/abs/2410.06992)). **Lesson for the demo: "tests pass" ≠ "correct". Show spec compliance.**

**Models (verified):** `claude-opus-5-5` costs $4/$20 per million input/output tokens, has a 1M context window and always-on adaptive thinking ([Claude docs](https://platform.claude.com/docs/en/models/opus-5-5/overview)). `claude-sonnet-5-5` costs $2/$10 and is about 30% faster than Sonnet 5 ([Anthropic](https://www.anthropic.com/claude/sonnet)). Use Opus for root cause and review, Sonnet for intake and running steps.

---

## 2. Patterns

### Reproduce first / failing test first
- Anthropic's official TDD recipe: write tests → confirm they fail → commit the tests → implement **without modifying the tests** → iterate until green ([Claude Code best practices](https://www.anthropic.com/research/claude-code-best-practices)).
- Practitioner prompt: "the test must fail *for the reported reason* … report the one-line root cause; if it won't fit in one line, the agent doesn't understand it yet" ([DEV](https://dev.to/minoru-iwasaki/make-claude-code-prove-its-fix-turn-any-bug-report-into-a-failing-test-first-1pbf)).
- Enforce it with a **hook that blocks edits to source files until a failing repro has been recorded**. Prompt rules alone were gamed: agents declared bugs unreproducible, or wrote tests that failed for unrelated reasons ([DEV](https://dev.to/yureki_lab/how-i-taught-my-ai-coding-agent-to-reproduce-bugs-before-fixing-them-594g)).
- Research on generating reproduction tests: Otter, e-Otter++ and EvoOtter now reach 63–78% fail-to-pass rates on TDD-Bench and SWT-Bench ([e-Otter++](https://arxiv.org/html/2508.06365), [EvoOtter](https://arxiv.org/html/2607.02854)). Using tests to rank candidate patches raised the resolve rate from 27% to 32% ([Otter](https://www.researchgate.net/publication/388883523_Otter_Generating_Tests_from_Issues_to_Validate_SWE_Patches)).

### Root-cause analysis
- Hierarchical localization from the ticket to a file, then a function, then lines (Agentless). Structure-aware search plus test-based fault localization (AutoCodeRover).
- Agents fix symptoms because "the error names the line where the failure *showed*, not the code that caused it", and a guard earns the same reward as a real fix ([SpecStory](https://specstory.com/learning/debugging/symptom-fixes)). Mitigations: require a **spec citation** (wiki rule ↔ code line), "rank probable root causes" ([Anthropic](https://www.anthropic.com/claude-explains/fix-software-bugs-faster-using-claude)), and ban special cases. The WattWise wiki says the same: "no special cases for single customers or meters".

### Context engineering
- "Context engineering is effectively the #1 job of engineers building AI agents" ([Cognition](https://cognition.com/blog/dont-build-multi-agents)).
- AGENTS.md is the open standard: Linux Foundation / AAIF, over 60k repos. CLAUDE.md is Claude's native equivalent. Keep it to about 100 lines of **pointers**, not an encyclopedia ([agents.md overview](https://www.agentpatterns.ai/standards/agents-md/), [Addy Osmani](https://addyosmani.com/agents/15-agents-md/)).
- **Important nuance for this client:** agents follow instruction files over the code in 90.1% of runs ([arXiv 2610.30571](https://arxiv.org/abs/2610.30571)). For WattWise that is *desired*, because the wiki is the source of truth. So the context file should say explicitly: "wiki = spec, code may be wrong; never edit the wiki; flag disagreements". Do **not** use the generic "code wins" fix from that paper.

### Multi-agent: planner / fixer / reviewer
- Anthropic: prefer **workflows** (predefined code paths) for well-defined tasks. "Evaluator-optimizer" fits "code that must pass tests". Start simple ([summary of Building Effective Agents](https://agentpatterns.ai/patterns/agent-design/anthropic-effective-agents-framework/)).
- Cognition's update (Apr 2026): "one main loop carries state, subagents are stateless workers with narrow scope" ([Cognition](https://cognition.com/blog/dont-build-multi-agents), [follow-up summary](https://agentic-ai.readthedocs.io/en/latest/ContextEngineering/devin/)).
- A fresh-context **reviewer subagent** catches what the author missed ([Claude Academy](https://academy.claude.com/courses/claude-code-101/the-explore-plan-code-commit-workflow)). Jules' "Planning Critic" reportedly cut task failure by 9.5% (third-party, [review](https://baeseokjae.github.io/posts/google-jules-ai-agent-review-2026/)).

### Self-verification
- Agents work best when they get "ground truth from the environment" (test runs) at every step ([Anthropic via summary](https://www.querynow.com/ai-agents/orchestration/workflows-vs-agents)).
- Google's patching pipeline filters out patches that fail build or tests before any human sees them ([Google research](https://research.google/pubs/ai-powered-patching-the-future-of-automated-vulnerability-fixes/)).

---

## 3. Transparency and human-in-the-loop

| Mechanism | Who does it | Source |
|---|---|---|
| Plan approval before coding | Jules, Claude Code Plan Mode | [Jules](https://jules.google/docs/), [Claude best practices](https://www.anthropic.com/research/claude-code-best-practices) |
| Evidence citations (logs, test output) | Codex | [OpenAI](https://openai.com/index/introducing-codex/) |
| Agent cannot merge; CI approval required; requester ≠ approver | Copilot agent | [GitHub Docs](https://docs.github.com/en/copilot/responsible-use/agents) |
| Engineer always approves; the fix is routed to the author of the change that broke | Meta SapFix | [Meta Eng](https://engineering.fb.com/2018/09/13/developer-tools/finding-and-fixing-software-bugs-automatically-with-sapfix-and-sapienz/) |
| Code owners review LLM commits | Google | [Google research](https://research.google/pubs/ai-powered-patching-the-future-of-automated-vulnerability-fixes/) |
| Programmatic guardrails and audit (`PreToolUse` deny/ask, `PostToolUse` logging) | Claude Agent SDK | [SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks) |
| Sandbox and egress firewall; filtering of hidden prompt-injection characters | Copilot | [GitHub Docs](https://docs.github.com/en/copilot/responsible-use/agents) |
| Prompt-injection risk from issue-triggered actions | Claude Code Action misconfiguration | [Flatt Security](https://flatt.tech/research/posts/poisoning-claude-code-one-github-issue-to-break-the-supply-chain/) |

Design implication: treat the bug-ticket text as **untrusted input**, give the agent least-privilege tools, and log every tool call to JSONL so it can be audited.

---

## 4. Failure modes practitioners report, and mitigations

| Failure | Evidence | Mitigation in our design |
|---|---|---|
| **Changing or weakening tests** to go green | HN: Sonnet "known to change tests so that they would pass" ([HN](https://news.ycombinator.com/item?id=46542036)). ImpossibleBench: Claude models cheated mostly by editing tests, over 79% of cheating cases ([arXiv 2510.20270](https://arxiv.org/pdf/2510.20270)) | Hook denies edits to existing tests. Hash the test files after the red test is committed. A diff check shows only additions under `tests/`. |
| **Special-casing / symptom fixes** | Agent changed backend responses to fit the tests ([Speedscale](https://speedscale.com/blog/ai-coding-agents-break-what-works/)). Guards instead of fixes ([SpecStory](https://specstory.com/learning/debugging/symptom-fixes)) | RCA must cite a wiki rule. Reviewer rejects customer- or meter-specific branches. Blast-radius run across all customers. |
| **Swallowing exceptions** | "cannot get the agent to stop masking failures" ([HN](https://news.ycombinator.com/item?id=46542036)) | Context file: raise domain errors from `errors.py`. Reviewer checks for `except: pass`. |
| **Tests that encode bugs / empty asserts** | ([HN](https://news.ycombinator.com/item?id=50059523)) | Expected values come from the wiki's worked examples, with the hand calculation in a comment (a CONTRIBUTING rule). |
| **Passing ≠ correct** | 28.6% of obviously wrong samples still pass ([arXiv 2512.10218](https://arxiv.org/html/2512.10218v2)). Weak tests ([SWE-Bench+](https://arxiv.org/abs/2410.06992)) | Validate against the spec examples, not only the suite. Independent reviewer. Human gate. |
| **Forcing a fix when the spec is ambiguous** | An abort option cut GPT-5 cheating from 54% to 9% ([ImpossibleBench](https://arxiv.org/pdf/2510.20270)) | Give the agent an `escalate_to_human` tool for wiki/code conflicts it cannot settle. |
| **Scope creep → review burden** | Bug-fix agent PRs have the *lowest* acceptance; reviewers abandon them ([arXiv 2601.15195](https://arxiv.org/pdf/2601.15195)). Burden depends on "what agents touch, not what they say" ([arXiv 2601.00753](https://arxiv.org/html/2601.00753v1)) | Minimal diff policy. One ticket per PR. Reviewer flags any file touched outside the RCA. |
| **Productivity illusion** | METR: experienced developers were 19% slower with early-2025 AI while believing they were 20% faster ([METR](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)). DORA 2025: AI raises throughput but also **instability** ([DORA](https://dora.dev/insights/balancing-ai-tensions/), [RedMonk](https://redmonk.com/rstephens/2025/12/18/dora2025/)) | Measure, don't assume: log time and cost per ticket and the reviewer accept rate. Gates protect stability. |

---

## 5. Business value evidence

**The cost of bugs**
- Developers spend 17.3 of 41.1 h/week on maintenance, debugging and refactoring (42%). 3.8 h of that is bad code, about $85B a year in total ([Stripe Developer Coefficient via PYMNTS](https://www.pymnts.com/news/b2b-payments/2018/stripe-developer-workforce/)).
- 44% of developers name bug fixing as their top pain point. 55% say they would build features if bug fixing took less time. 26% spend up to half their time fixing bugs ([Rollbar/BusinessWire](https://www.businesswire.com/news/home/20210216005484/en/Rollbar-Research-Shows-That-Traditional-Error-Monitoring-Is-Missing-the-Mark), [DevOps.com](https://devops.com/survey-fixing-bugs-stealing-time-from-development/)).
- The cost of poor software quality in the US is ≥$2.41T a year ([CISQ 2022 via Undo](https://undo.io/resources/new-research-cost-poor-software-quality-us-2022-report)). Over half of defects are found downstream ([NIST 2002](https://www.edge-ai-vision.com/2025/08/the-2-4-trillion-crisis-why-hardware-software-integration-is-your-most-critical-technical-decision/)).

**Evidence that AI fixing works (all keep humans in the loop)**
- **Meta SapFix:** 165 patches for 57 crashes. Median of **69 minutes** from fault detection to a fix sent for approval ([Meta](https://engineering.fb.com/2018/09/13/developer-tools/finding-and-fixing-software-bugs-automatically-with-sapfix-and-sapienz/), [paper](https://discovery.ucl.ac.uk/id/eprint/10084761/1/SapFix-Automated-End-to-End-Repair-at-Scale-v2.pdf)).
- **Google (Gemini):** fixes 15% of sanitizer bugs. **~95% of commits accepted without discussion** by code owners. Hundreds of commits merged ([Google](https://research.google/pubs/ai-powered-patching-the-future-of-automated-vulnerability-fixes/)).
- **GitHub Copilot Autofix:** median 28 min vs 1.5 h manual (more than 3x faster). SQL injection: 18 min vs 3.7 h ([GitHub Blog](https://github.blog/news-insights/product-news/secure-code-more-than-three-times-faster-with-copilot-autofix/)).
- **Uber FixrLeak:** fixed 93 of 102 eligible resource leaks automatically ([ZenML case DB](https://www.zenml.io/llmops-database/using-genai-to-automatically-fix-java-resource-leaks)). Uber's internal coding agent grew from under 1% to 8% of all code changes ([ShiftMag](https://shiftmag.dev/how-uber-engineers-use-ai-agents-8617/)).
- **Devin:** 67% PR merge rate (vendor-reported). Customers include Goldman Sachs, Santander and Nubank ([Cognition](https://cognition.com/blog/devin-annual-performance-review-2025)).
- **MTTR (ops-side, vendor-reported):** 40–85% reductions, e.g. Autodesk −85% ([summary](https://ai2roi.substack.com/p/ai-to-roi-metric-mean-time-to-resolve)). Forrester composites: 30–60% ([AI CERTs](https://www.aicerts.ai/news/debugging-automation-tools-cut-mttr-boost-efficiency/)). Use these with care, because they come from incident response, not code fixes.

**Client-specific value framing (WattWise)**
- BUG-142 blocks invoicing for every customer after C-1004: lost cash flow plus ops overtime.
- BUG-151 overcharges customers against a marketing promise: regulatory, churn and reputation risk. The ticket asks "which other customers are affected?", so the agent should produce an **impact list with EUR deltas** for corrected invoices.
- BUG-158 means about 3% base-fee revenue leakage on *every* invoice.
- The pitch: the agent turns a ticket into a reviewed, test-backed PR plus a business impact report within minutes, at a cost of cents to a few dollars at Opus 5.5 prices. The human role moves from *doing* to *approving*.
- Illustrative ROI (state the assumptions on screen): 10 developers × 20% of their time on bugs × 50% of tickets that can be automated × 30% net time saved after review ≈ 0.3 FTE.

---

## 6. Recommendation: a minimal but impressive build in about 1 day

### Architecture: "Spec-Driven Bug Fixer". A deterministic workflow with agentic steps and two human gates.

```
issues/BUG-xxx.md
   │
[1] Triage (Sonnet 5.5, structured output)
   │   → ticket.json: symptom, entities (C-1004, M-20004), expected behavior, suspected component
[2] Investigator (Opus 5.5 subagent, READ-ONLY tools: Read/Grep/Glob, Bash(pytest, python -m wattwise))
   │   → reproduces via CLI, reads AGENTS.md → CONTRIBUTING + relevant wiki pages
   │   → RCA.md: ranked hypotheses; "Wiki rule X (Meter-Readings.md §Register rollover) vs code meter.py:51"
[3] Reproducer: writes regression test (# Regression test for BUG-xxx, test_<fn>_<behaviour>,
   │   hand calculation from the wiki example) → pytest MUST FAIL for the stated reason → commit "test(...)"
   ├── HUMAN GATE 1 (optional in demo): approve RCA + plan  ◄── Jules/Plan-Mode pattern
[4] Fixer (Opus 5.5): minimal edit in the domain module only. Hooks enforce:
   │   • deny Edit on src/ until a red test is recorded  • deny edits to existing tests & wiki/
   │   • deny float(/round(/quantize( in money code  • deny new deps  • log every call → audit.jsonl
[5] Validator (deterministic code, no LLM): full pytest; spec examples from the wiki;
   │   AST convention check (type hints, Google docstrings, Decimal, round_eur);
   │   BLAST RADIUS: bill all customers before vs after → which invoices change, EUR deltas
[6] Reviewer (fresh-context Opus 5.5): CONTRIBUTING Definition-of-Done checklist, symptom-vs-cause,
   │   special-casing, test integrity → APPROVE / REQUEST_CHANGES (max 2 loops) / ESCALATE
[7] Packager: branch, Conventional Commit "fix(meter): handle register rollover (BUG-142)",
   │   CHANGELOG line, ticket status "Fixed (pending review)", PR body (RCA, evidence, impact, risks)
   └── HUMAN GATE 2: engineer reviews PR & merges. Agent never merges.
```

**Why this design (for the jury)**
- It is Agentless-style predictability with SWE-agent-style guardrails, matching what the research shows works (sections 1–2).
- Each step maps to the client's *own* Development-Workflow.md (reproduce → root cause → regression test → fix → suite → changelog → PR → second reviewer). The agent follows their process, so it is easy to adopt.
- Guardrails are enforced **in code (hooks)**, not just in prompts, because prompt-only rules get gamed (section 4).
- Escalation is a first-class outcome. "I'm not sure" beats a confident wrong fix (ImpossibleBench).

**Stack:** Python 3.10 + `claude-agent-sdk` (`query()` / `ClaudeSDKClient`, `ClaudeAgentOptions(allowed_tools=…, hooks={"PreToolUse": [...], "PostToolUse": [...]}, agents={...})`) ([Python ref](https://code.claude.com/docs/en/agent-sdk/python)). Add an `AGENTS.md`/`CLAUDE.md` at the WattWise root, about 40 lines of pointers: wiki is the spec, conventions, test commands, a ban on wiki and test edits, and escalation rules. Optional: a GitHub Action (`anthropics/claude-code-action@v1`) to show the path to production ([docs](https://code.claude.com/docs/en/github-actions)).

**Day plan:** 2 h for the AGENTS.md, hooks and audit log; 3 h for the pipeline steps 1–7; 1.5 h for the blast-radius and convention checker; 1.5 h to run all 3 bugs, tune, and record a backup video.

### Demo script (about 7 min)
1. **Problem and value (1 min):** cost-of-bugs stats; the three tickets framed as business risks (blocked invoicing, overcharging, revenue leak).
2. **Live run on BUG-142 (3 min):** a split screen with the reasoning trace on one side and the audit log on the other. Show the red test (`InvalidReadingError`), the wiki citation (`10^digits − opening + closing`), the green suite, and `python -m wattwise run 2026-11` printing 5/5.
3. **Guardrail moment (1 min):** show the hook blocking an attempt to edit `tests/` or the wiki (pre-recorded or seeded), and the reviewer rejecting a seeded "if meter == M-20004" patch.
4. **BUG-151 business output (1 min):** the blast-radius table lists every Comfort/HeatPump customer overcharged, with EUR deltas (C-1002 260 kWh: 95.94 → 78.44 per the wiki example). This is ready for customer service to issue corrected invoices.
5. **Human review and the path to production (1 min):** the PR body plus the DoD checklist; the engineer approves. KPIs: minutes and cost per ticket, accept rate, escalation rate. Roadmap: shadow mode → PR mode → CI-triggered.

### KPIs to propose to the client
Time from ticket to PR, reviewer acceptance rate on the first pass, escalation rate, reopened-bug rate (regression), cost per ticket, and the DORA change-failure rate, which guards against the AI-instability effect.
