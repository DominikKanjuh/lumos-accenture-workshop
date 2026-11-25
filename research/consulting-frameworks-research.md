# Consulting Frameworks Research: Accenture AI Workshop (2026-11-25)

How to make both cases read as one consulting engagement. Judges score **how we got to the answer and what we did for the client**, not only the code.

Source note: most framework write-ups are consultancy or vendor blogs. Weights and benchmarks from them are **examples, not validated standards**. Gartner reports are paywalled, so Gartner details come from summaries. Figures marked (unverified) came from secondary citations only.

---

## 0. TL;DR: the winning storyline

**One engagement, two deliverables.** WattWise asked: "Where can AI create real value?" (Case 2). We answered with a prioritized portfolio. Then we **proved the method on their own code**: the billing repo contains 3 open bugs, and each one maps to a value-chain pain point we scored.
- BUG-142: the batch run aborts on a meter-register rollover. Operations fails, customers go uninvoiced, and cash is delayed.
- BUG-151: the tiered tariff appears to charge the higher price on all consumption, not just the part above the allowance. The result is overcharging, complaints and regulatory or reputational risk.
- BUG-158: daily proration is off by one day. Base-fee revenue runs about 3% below plan **on every invoice**, which is silent revenue leakage.

Case 1 (the bug-fixing agent) is the **"no-regret quick win / lighthouse"** that comes out of the Case 2 prioritization. It is cheap, data is available (repo, wiki, tests), it is low regulatory risk (internal developer tooling with a human merge gate), and it shows value in days. It also sets up the AI operating model (human-in-the-loop, governance, KPIs) that the bigger bets need later (grid, trading).

Framing line: *"We didn't just tell you where AI creates value. We showed you, on your own billing code, in one day."*

---

## 1. Engagement structure & problem-solving toolkit

### 1.1 Phase models to borrow
| Model | Phases | Use for us |
|---|---|---|
| Classic consulting / Accenture-style | Discover/Assess → Define/Strategy → Design → Build/Pilot → Scale/Run | Engagement phase plan and roadmap |
| Double Diamond (UK Design Council, 2004/05; refreshed 2019) | Discover (diverge) → Define (converge) → Develop (diverge) → Deliver (converge) | Show *divergent* use-case ideation, then *convergent* scoring. For Case 1: explore the bug, define the root cause, develop candidate fixes, deliver the tested patch. |
| Hypothesis-driven + issue tree | Governing question → MECE branches → hypotheses → analyses to confirm or kill | Case 2 issue tree; Case 1 "root-cause hypotheses" the agent tests |
| Pyramid Principle / SCR(Q) (Minto, McKinsey) | Situation → Complication → (Question) → Resolution; answer first, grouped support | Deck storyline and action titles |
| As-is / To-be | Current process and pain → target process with AI → gap → roadmap | Case 1 bug lifecycle; Case 2 per top use case |

Accenture's own language, worth echoing to Accenture judges:
- "Lead with value". This is the first of Accenture's 5 gen AI imperatives. The other four: an AI-enabled secure digital core, reinventing talent and ways of working, closing the gap on responsible AI, and continuous reinvention.
- Accenture splits investments into **"no-regret" investments** (productivity) and **"strategic bets"** (new competitive advantage).
- Prioritize **business capabilities across the value chain**, not siloed use cases. Base it on business case, enterprise readiness and ROI.
- "Reinvention-ready digital core" and balancing **technical debt**. Recurring bugs are tech debt, which links straight to Case 1.

### 1.2 Issue tree (Case 2): ready to use
Governing question: *"Where and in what order should WattWise invest in AI to maximize value within 24 months, safely?"*
1. **Where is the value?** (by value-chain step: Generation · Grid (T&D) · Trading & Portfolio · Retail/Customer & Billing · Corporate/IT)
   - Revenue upside / cost reduction / risk reduction / customer experience
2. **Can we do it?** Data availability and quality · tech and skills · integration with legacy (billing, SCADA, ETRM) · change effort
3. **Should we do it?** Regulatory (EU AI Act, energy regulator, GDPR) · safety-critical exposure · reputational risk
4. **How fast and in what sequence?** Time-to-value · dependencies (data platform, governance) · reuse across use cases

### 1.3 Stakeholder map (assumed; validate with client)
| Stakeholder | Interest | Influence | What they need from us |
|---|---|---|---|
| CEO / Board | Growth, margin, transition story | High | 1-page answer, value at stake |
| CFO / Controlling | Revenue leakage (BUG-158!), ROI | High | Business case, payback |
| CIO / Head of Engineering | Dev productivity, tech debt, security | High | Agent architecture, governance, TCO |
| Billing operations | Batch stability (BUG-142) | Med | Fewer incidents, faster MTTR |
| Customer service | Complaints (BUG-151) | Med | Fewer billing calls |
| Grid / Trading heads | Forecast accuracy, asset uptime | High | Credible later-wave bets |
| Works council / developers | Job impact, trust in AI | Med | Human-in-the-loop, augmentation framing |
| Regulator / DPO / Legal | Compliance, fairness to customers | High (veto) | AI Act classification, audit trail |

---

## 2. AI use-case prioritization frameworks

### 2.1 Landscape
| Framework | Gist | Pros / cons |
|---|---|---|
| **Value vs Feasibility 2x2** | Quadrants: Quick Wins (high/high), Strategic Bets (high value, low feasibility), Fill-ins (low value, high feasibility), Money Pits / Deprioritize | Easy to read. Needs scoring underneath to avoid "gut feel". |
| **Gartner AI Use-Case Prism** | Business value (L/M/H) × feasibility (L/M/H). It is a 3×3 grid rotated 45°. Feasibility = technical (data/tech) + internal (people/process readiness) + external (customer/regulator readiness). Industry prisms exist (e.g. CSP, IT service desk). | Credible brand. The feasibility split is useful. |
| **Weighted scoring** | Score 1–5 on criteria × weights → total; then plot on the 2x2 | Transparent and defensible. Allows sensitivity analysis. |
| **Knock-out gates** | Pass/fail before scoring: usable data? owner? compliance? | Stops pretty-but-impossible ideas |
| RICE / ICE | Reach × Impact × Confidence / Effort | Product-style. Less fit for strategy, OK as a cross-check. |
| **BCG 10-20-70** | 10% algorithms, 20% tech and data, 70% people and processes | Use it in next steps to justify the change-management budget |
| Accenture no-regret vs strategic bets | Portfolio balance | Use it to label horizons |
| Horizon / portfolio (quick win → lighthouse → strategic bet) | Sequence by time and ambition | Roadmap storytelling |

Example weightings found:
- Ryz Labs: Value 30, Feasibility 20, Data 20, Risk 15, Adoption 15. Gate: no usable data means not in wave 1.
- Pertama: Impact 30, Feasibility 25, Strategic 20, Risk 15, Time 10.
- Okhrem: Value 25, Scale 15, Data readiness 15, Workflow fit 15, Time to evidence 10, Risk 10, Dependencies 5, Adoption 5.
- Simple: Value 50, Feasibility 30, Strategic fit 20.

### 2.2 TEMPLATE: our scoring matrix (recommended)
Two axes. Each axis is a weighted sum of 1–5 scores, so the 2x2 is not gut feel. Plus gates.

**Gates (pass/fail, before scoring)**
- G1 Data exists and is accessible (or can be within 3 months)
- G2 Clear business owner
- G3 Not prohibited or unmanageable under the EU AI Act / GDPR; safety-critical use only with human control

**VALUE axis (50% of total)**
| Criterion | Weight within axis | 1 = | 3 = | 5 = |
|---|---|---|---|---|
| Financial impact (EBIT: revenue up, cost down) | 40% | < €0.5M/yr | €1–5M/yr | > €10M/yr |
| Strategic fit (energy transition, customer, resilience) | 20% | unrelated | supports a goal | core to strategy |
| Customer / employee experience | 20% | none | noticeable | headline KPI (NPS, complaints) moves |
| Risk reduction (operational, regulatory, safety) | 20% | none | moderate | prevents major incidents or fines |

**FEASIBILITY axis (50% of total)**
| Criterion | Weight within axis | 1 = | 3 = | 5 = |
|---|---|---|---|---|
| Data readiness (availability, quality, labels) | 30% | doesn't exist | exists, messy | clean and accessible |
| Technical maturity (proven tech, integration effort) | 25% | research-grade | proven elsewhere, heavy integration | off-the-shelf, light integration |
| Time-to-value | 15% | > 18 months | 6–12 months | < 3 months |
| Regulatory / responsible-AI complexity (inverted) | 15% | high-risk, safety component | limited-risk, needs transparency | minimal risk, internal tool |
| Organizational readiness / change effort (inverted) | 15% | major process and role change | moderate | fits existing workflow |

Total = 0.5·Value + 0.5·Feasibility (both on a 1–5 scale). Quadrant cut-off is 3.0 on each axis (or the median of the portfolio).
Classification:
- V ≥ 3 and F ≥ 3: **Quick win / no-regret**
- V ≥ 3 and F < 3: **Strategic bet / lighthouse** (build foundations first)
- V < 3 and F ≥ 3: **Fill-in** (do opportunistically)
- V < 3 and F < 3: **Deprioritize**

**How to justify weights** (judges will ask):
1. **Anchored in the client goal.** The client asked for "real value", so value gets half the total and financial impact is the largest value item.
2. **Data readiness is the top feasibility item.** It is the most common reason AI pilots stall. Cite the McKinsey "pilots stuck" theme (unverified figure: 71%).
3. **Regulatory weight is meaningful in energy.** Critical infrastructure is listed in EU AI Act Annex III.
4. **Weights were agreed with the client** (in the workshop: "we'd validate these with your exec team via pairwise comparison / 100-point allocation").
5. **Sensitivity analysis.** Re-run with (a) value 70 / feasibility 30 and (b) equal criterion weights. Show that the **top 3 stay stable**, so the ranking is robust. If a use case flips, call it out as "depends on risk appetite". Even a small "rank stability" table is very convincing to judges.

### 2.3 Starter longlist: energy value chain (score these)
| # | Value-chain step | Use case | Likely quadrant (hypothesis) |
|---|---|---|---|
| 1 | Generation | Renewable (wind/PV) generation forecasting | Quick win / strategic |
| 2 | Generation | Predictive maintenance of plants and turbines | Strategic bet |
| 3 | Grid | Load / demand forecasting per feeder | Quick win |
| 4 | Grid | Predictive asset health (transformers, cables) and inspection by drone imagery | Strategic bet |
| 5 | Grid | Outage prediction and storm-crew dispatch optimization | Strategic bet (AI Act high-risk if a safety component) |
| 6 | Grid | DER / flexibility orchestration (EVs, heat pumps, batteries) | Strategic bet (long-term) |
| 7 | Trading | Short-term price forecasting and bidding optimization | Strategic bet / high value |
| 8 | Trading | Imbalance-cost reduction (forecast + position) | Quick win if data exists |
| 9 | Retail/Billing | **Meter-data validation and billing anomaly detection** (rollover, implausible jumps) | Quick win; evidenced by BUG-142 |
| 10 | Retail/Billing | **Invoice plausibility check before sending** (tariff rule engine + ML) | Quick win; evidenced by BUG-151/158 |
| 11 | Retail/Customer | Gen AI customer-service copilot / agent (billing questions, "explain my bill") | Quick win. McKinsey: billing and payments are 40–50% of utility calls. |
| 12 | Retail | Churn prediction and next-best-offer (e.g. heat-pump tariff) | Fill-in / quick win |
| 13 | Retail | Personalized energy-saving coach (smart-meter disaggregation) | Strategic / differentiator |
| 14 | Retail | Debt collection / payment-default prediction (watch fairness; credit scoring is Annex III high-risk) | Careful |
| 15 | Corporate/IT | **Autonomous bug-fixing / SDLC agent** (Case 1) | Quick win / lighthouse |
| 16 | Corporate | Regulatory-reporting and tariff-document gen AI assistant | Fill-in |
| 17 | Field service | Technician copilot (manuals, work orders) | Quick win |
| Creative | Cross | "Bill-shock early warning": predict a big jump and notify the customer mid-month | Differentiator |

Benchmarks (vendor claims, treat cautiously):
- AI trading: 8–15% margin improvement.
- Predictive maintenance: 25–40% less unplanned downtime.
- Billing revenue leakage: about 1–4% of revenue. About 17% of invoices need manual exception handling (ENGIE Impact).
- J.D. Power 2024: the biggest drop in utility customer satisfaction was in billing and payment (−11 points).

---

## 3. Roadmap & next steps (for the top use cases)

### 3.1 TEMPLATE: engagement phase plan
| Phase | Weeks | Activities | Deliverables | Gate |
|---|---|---|---|---|
| 0. Mobilize | 0–1 | Sponsor, scope, stakeholder interviews | Charter, stakeholder map | Sponsor sign-off |
| 1. Discover / Assess | 1–3 | Value-chain walkthrough, pain points, data and tech inventory, AI maturity check | As-is, longlist (15–25 use cases) | Longlist agreed |
| 2. Define / Prioritize | 3–5 | Gates, weighted scoring, sensitivity, exec workshop on weights | Prioritized portfolio, 2x2, business cases for top 3–5 | Portfolio approved |
| 3. Design | 5–7 | To-be process, solution architecture, data needs, risk and AI Act classification, KPIs | Pilot charters | Go / no-go per pilot |
| 4. Pilot (MVP) | 7–19 | 8–12 week pilots with baseline vs treatment, human-in-the-loop | Pilot results vs KPIs | Scale decision on evidence |
| 5. Scale / Run | 19+ | Industrialize (MLOps/LLMOps), operating model, CoE, change and training | Scaled solution, value tracking | Quarterly portfolio re-score |

### 3.2 Horizons (portfolio story)
- **H1 (0–3 months), no-regret quick wins:** bug-fixing agent, invoice plausibility checker, customer-service copilot for billing questions.
- **H2 (3–12 months), lighthouses:** load/renewable forecasting, predictive asset health. These need a data platform.
- **H3 (12–24+ months), strategic bets:** trading optimization, DER/flexibility orchestration, outage prediction. Watch AI Act high-risk status.

### 3.3 Enablers / operating model (the "70%" of 10-20-70)
- **AI CoE / hub-and-spoke:** a central platform, governance and skills team. Domain owners own the use cases. BCG's "Client Zero" model has domain experts owning AI workflows.
- **Governance & responsible AI:** use-case intake, risk classification, model cards and audit trail, and human oversight. Align with the NIST AI RMF and the OWASP Agentic AI Top 10 for agents.
- **EU AI Act:** Annex III point 2 makes AI used as a **safety component in the supply of electricity/gas/heating** high-risk. Credit scoring of natural persons is also Annex III. Billing helpers and developer tools are typically minimal or limited risk. Timeline: Annex III obligations were originally due 2 Aug 2026. Reports say they are postponed to **2 Dec 2027** via the Digital Omnibus. State it as "check final adoption".
- **Data foundation:** smart-meter data, asset data and market data in one governed platform.
- **Change management:** training, communication, works-council involvement, framing AI as augmentation.
- **Value tracking:** KPI baseline before the pilot, benefits realized per quarter.

### 3.4 KPI examples per top use case
| Use case | KPI |
|---|---|
| Bug-fixing agent | MTTR, % bugs auto-fixed and accepted, reviewer minutes per fix, escaped defects / change-fail rate |
| Invoice plausibility | % invoices flagged, false-positive rate, corrected invoices, leakage recovered (€) |
| CS copilot | Average handle time, first-contact resolution, billing call volume, CSAT |
| Forecasting | MAPE, imbalance cost (€) |
| Predictive maintenance | Unplanned downtime, SAIDI/SAIFI, maintenance cost |

---

## 4. Framing Case 1 (bug-fixing agent) consulting-style

### 4.1 SCR
- **Situation:** WattWise bills households monthly from an in-house Python billing app with a wiki, tests and coding conventions.
- **Complication:** recurring bugs reach production, and existing tests didn't catch them. In one week there were 3 tickets touching operations (batch abort), customers (overcharging complaint) and finance (about 3% base-fee shortfall). Developers lose time. Industry data says about 42% of developer time goes to maintenance, technical debt and bad code (Stripe Developer Coefficient 2018: 17.3 of 41.1 hours/week).
- **Resolution:** an agent that reads the ticket, uses the repo context (wiki rules, code, conventions, tests) and forms root-cause hypotheses. It reproduces the bug with a failing test first, fixes it, runs the full suite, and opens a **reviewable PR with a reasoning trace**. A human approves the merge.

### 4.2 Business case (illustrative, label assumptions)
- Value levers: (1) developer hours saved per bug; (2) lower MTTR, so revenue and cash aren't delayed (BUG-142: invoices blocked); (3) avoided leakage (BUG-158: about 3% of base-fee revenue per month until fixed); (4) avoided complaints, rebilling and regulatory exposure (BUG-151).
- Simple formula: `Annual value = bugs/yr × (hrs saved/bug × loaded €/hr) + Σ(leakage €/day × days of MTTR reduction) + avoided rebilling/complaint cost`
- **TCO:** LLM API cost per run (cents to a few € per bug), engineering to build and maintain, reviewer time, governance overhead.
- Present it as an **illustrative calculation with explicit assumptions**, for example "assume 40 billing bugs/yr, 6 h saved each, €80/h ≈ €19k direct savings plus leakage". The leakage line usually dominates. That is the "so what" for the CFO.

### 4.3 Pilot design
- Scope: one repository (billing), low/medium-severity bugs first, read-only production access, sandbox CI.
- Design: historical replay (closed tickets with known fixes) **plus** live shadow mode (the agent proposes, the human fixes in parallel), then assisted mode.
- Duration: 8 weeks. Success criteria are set **before** the start.
- Expectation setting: real-world AI PR acceptance rates are reported at about 27–35% (Linear data: 32.7% vs 84.4% for human PRs). Acceptance rate alone is a weak KPI. Pair it with quality and review-effort metrics.

### 4.4 KPIs (agent)
- **Outcome:** MTTR (DORA), change-fail rate / escaped defects, rework rate
- **Agent quality:** % tickets with correct root cause identified, % fixes passing the full test suite, PR acceptance rate (context only)
- **Effort:** Mean Human Intervention Time (reviewer minutes per fix). ΔT = manual baseline − (agent time + review time).
- **Trust:** % of reasoning traces rated "clear" by reviewers; no policy violations

### 4.5 Human-in-the-loop operating model & governance
- Autonomy ladder: L0 suggest → L1 draft PR → L2 auto-merge for trivial, well-tested classes only (later, by evidence).
- Guardrails:
  - Never commit to main.
  - Restricted tools and paths.
  - Tests must go red→green (a reproducing test is mandatory).
  - Follow CONTRIBUTING / conventions; diff size limits.
  - Secrets isolation, audit log of every tool call.
- Escalation: if the ticket conflicts with the wiki/spec (e.g. "expected" behavior is ambiguous), the agent **stops and asks the human** instead of guessing. This is a strong demo moment.
- **Impact analysis:** the agent also reports *which customers and invoices were affected* (BUG-151: "if this affects more customers, we need to know so we can issue corrected invoices"). That is the business value beyond the code.
- RACI: Agent = drafts fix · Developer = reviews and merges (Accountable) · Tech lead = owns guardrails · Billing ops / Finance = informed of customer impact.

### 4.6 Rollout plan
Pilot (billing repo) → expand to other internal apps → integrate with ticketing (Jira) and CI → CoE owns the agent platform → reuse it for other SDLC agents (test generation, code review). Re-score in the portfolio quarterly.

---

## 5. Winning the pitch

### 5.1 What judges reward (synthesis)
- **Answer first** (Pyramid). Slide 1 states the recommendation. Spend at most 2 slides restating the case.
- **Action titles** that tell the story when read in sequence. Synthesize between sections.
- **Problem → hypothesis → solution** flow, MECE buckets, quantified where possible, assumptions stated explicitly.
- **Honest limitations** beat a "perfect" story. Judges value candor about risks and barriers.
- **Map content to the scoring criteria.** Make each criterion visibly "ticked" (e.g. a slide titled "Transparent reasoning & human review").
- **The demo beats slides.** A working rough build scores above a polished description. Show one complete user journey. Have a **recorded backup video**; never debug live.
- Design: 2–3 colors plus 1 accent, one font, white space, no animations.
- Q&A: list the likely questions and prepare backup slides (weights? why not trading first? AI Act? cost? what if the agent is wrong?).
- Rehearse at least twice and time it.

### 5.2 Time allocation
- 5-minute slot: problem 0:45 · approach/method 1:00 · demo or result 2:00 · next steps / value 1:00 · close 0:15.
- 10-minute slot (both cases): opener and storyline 1:00 · Case 2 strategy 4:00 · Case 1 as proof (demo) 4:00 · roadmap and ask 1:00.
- Extend the demo and next steps, not the intro.

### 5.3 Common mistakes
- Use-case laundry list with no framework.
- Framework with no justification of weights.
- 2x2 with no numbers behind it.
- No "so what" or next steps.
- Tech-only demo with no business impact.
- Ignoring regulation and change.
- Too many slides.
- Live demo failure with no backup.
- Agent shown as a black box with no reasoning trace and no human gate.

### 5.4 TEMPLATE: deck outline, Case 2 (AI Strategy), about 8–10 slides
1. **Title + answer:** "Start AI where the money leaks: 3 no-regret billing & service plays now, grid and trading bets on a 24-month path."
2. **Situation & complication (SCR):** energy transition, cost pressure, customer satisfaction falling in billing; AI pilots often stall before production.
3. **Our approach:** Double Diamond / phase graphic (Discover → Define → Prioritize → Roadmap) and the issue tree.
4. **Use-case longlist on the value chain:** Generation · Grid · Trading · Retail/Billing · Corporate (15–20 cases; flag the creative ones).
5. **Framework:** gates, value and feasibility criteria with weights, and *why* these weights.
6. **Prioritization result:** 2x2 / Gartner-style prism with numbered bubbles, plus the top-5 table.
7. **Robustness:** sensitivity analysis shows the top 3 are stable under different weightings.
8. **Deep dive on the top 3:** value at stake, data, risk, KPI (one row each).
9. **Roadmap:** H1/H2/H3 Gantt, plus enablers (data platform, CoE, governance, AI Act, change: the 70%).
10. **Next steps & ask:** 30/60/90 days, pilot charters, decision needed from the client. **Bridge to Case 1:** "We've already started: here's the first quick win, live."

### 5.5 TEMPLATE: deck outline, Case 1 (Bug-Fixing Agent), about 6–8 slides
1. **Title + answer:** "An agent that fixes billing bugs in minutes, and a human still decides."
2. **The pain in your repo:** 3 tickets mapped to ops, customer and finance impact (€ and customer counts if derivable).
3. **How the agent works:** architecture with ticket → context retrieval (wiki, code, conventions, tests) → hypotheses → reproducing test → fix → test suite → PR + reasoning report → human review.
4. **Live demo / video:** one bug end to end (prefer BUG-142 or BUG-151 for drama). Show the reasoning trace and the red→green test.
5. **Results:** all 3 bugs (root cause, fix, tests added, affected customers), plus honest limitations.
6. **Human-in-the-loop & governance:** autonomy ladder, guardrails, audit log, escalation when the spec is ambiguous.
7. **Business case & KPIs:** illustrative ROI, MTTR, acceptance, reviewer minutes.
8. **Rollout:** pilot → scale → CoE, and where it sits in the Case 2 portfolio (quick win).

---

## 6. Linking both cases: narrative devices
- **"Client zero" evidence:** the only artifacts the client gave us (repo + briefs) already show 3 billing defects. That is concrete proof that Retail/Billing is a real pain point, so it scores high on value in the Case 2 matrix.
- **Use the scoring matrix on Case 1 itself:** show the bug agent scored as a quick win (e.g. V 3.4 / F 4.4). This shows that the framework *chose* Case 1 and that Case 1 wasn't bolted on.
- **Second quick win that comes from Case 1:** the bugs reveal a missing control. Turn it into a use case, the "invoice plausibility / meter-anomaly guard" (AI and rules check invoices before sending). This is a creative idea derived from the client's own evidence.
- **Operating model rehearsal:** the human-in-the-loop, audit trail and KPIs built for the agent are the same governance needed later for high-risk grid AI. "Start safe, earn autonomy."
- **One storyline:** Situation (energy provider under pressure) → Complication (AI hype, but where is real value, and money leaks even in billing) → Resolution (prioritized portfolio + quick win already delivered + roadmap).

---

## Sources
Frameworks / prioritization
- https://digital.compunnel.com/blog/ai-use-case-prioritisation
- https://umbrex.com/resources/frameworks/supply-chain-frameworks/ai-use-case-prioritization-framework/
- https://www.ryzlabs.com/templates/ai-use-case-prioritization-matrix
- https://paul-okhrem.com/ai-use-case-prioritization-framework/
- https://wizr.ai/blog/ai-use-case-prioritization-framework/
- https://www.pertamapartners.com/insights/ai-use-case-prioritization-framework
- https://www.gartner.com/en/documents/4773731 (Use-Case Prism CSP) · https://www.gartner.com/en/documents/4813531 (IT service desk)
- https://medium.com/@atabarezz/%EF%B8%8F-cut-through-the-hype-4a9017a423c7 (Gartner Prism explained)
- https://www.bcg.com/featured-insights/the-leaders-guide-to-transforming-with-ai (10-20-70)
- https://www.bcg.com/publications/2026/the-formula-for-agentic-ai-value
- https://www.bcg.com/publications/2026/bcg-ai-transformation-client-zero

Accenture
- https://www.accenture.com/content/dam/accenture/final/accenture-com/document-2/Accenture-Reinvention-in-the-age-of-generative-AI-Report.pdf (5 imperatives, no-regret vs strategic bets)
- https://www.accenture.com/content/dam/accenture/final/industry/cross-industry/document/Making-Reinvention-Real-With-GenAI-TL.pdf (Sempra utility case)
- https://agici.it/wp-content/uploads/2024/05/Accenture-2024_GENERATIVE-AI-FOR-UTILITIES-REINVENTION.pdf (Gen AI for utilities)
- https://www.accenture.com/en/insights/technology/building-reinvention-ready-digital-core
- https://newsroom.accenture.com/news/2024/new-accenture-research-finds-that-companies-with-ai-led-processes-outperform-peers

Energy / McKinsey / billing
- https://www.mckinsey.com/industries/electric-power-and-natural-gas/our-insights/how-utilities-can-rewire-customer-operations-with-agentic-ai (billing and payments 40–50% of calls)
- https://thinking.inc/en/industry-service/energy-ai-use-cases/ (value-chain split, benchmark claims)
- https://genta.dev/resources/revenue-leakage-utility-billing-ai · https://www.bynry.com/blog/reduce-billing-errors-revenue-leakage-water-utility
- https://martinai.ca/blog/meter-to-cash-billing-accuracy

Regulation
- https://artificialintelligenceact.eu/high-level-summary/
- https://ai-act-service-desk.ec.europa.eu/en/ai-act/annex-3
- https://www.bakerbotts.com/thought-leadership/publications/2026/march/the-eu-ai-act
- https://www.wirtek.com/blog/when-is-energy-and-industrial-ai-high-risk-under-the-ai-act
- https://arxiv.org/pdf/2408.01121

Dev productivity / agent KPIs
- https://codeant.ai/blogs/ai-code-review-rollout-kpis
- https://exemplary.ai/enterprise/blog/ai-pilot-task-completion-metrics
- https://smartym.pro/articles/corporate-coding-assistants-selection-infrastructure-kpis/
- https://davidandgoliath.ai/daily-ai-briefing/linear-ai-coding-agents-triple-output-review-bottleneck
- https://baeseokjae.github.io/posts/ai-coding-accepted-code-quality-2026/
- https://www.arxiv.org/pdf/2602.08915
- https://codescene.com/hubfs/calculate-business-costs-of-technical-debt.pdf (Stripe Developer Coefficient figures)
- https://www.pymnts.com/personnel/2018/stripe-survey-software-developers-engineers/

Structure / storytelling / pitching
- https://en.wikipedia.org/wiki/Double_Diamond_(design_process_model)
- https://deckary.com/blog/pyramid-principle-consulting · https://inslidr.com/scr-framework/ · https://www.roadtooffer.com/blog/scqa-framework
- https://www.hackingthecaseinterview.com/pages/case-competitions
- https://managementconsulted.com/how-to-win-a-case-competition/
- https://medium.com/@rmaryerson/cut-to-the-case-how-to-win-your-next-case-competition-1d80c222e778
- https://casebuzz.in/case-competition-presentation-tips/
- https://www.unswbsoc.com/publications/what-are-case-competitions
- https://www.slideteam.net/blog/top-20-case-competition-samples-with-templates-and-examples
- https://angelhack.com/blog/10-tips-to-help-you-rock-your-next-hackathon-demo/
- https://reskilll.com/blogs/hackathon-demo-presentation-tips-pitch-3-minutes-win-2026/
- https://hacktribe.co/blog/how-to-build-a-hackathon-pitch-deck-practical-5-minute-structure

Not covered: Reddit r/consulting / HN threads (not searched; time-boxed). The original Gartner and Stripe PDFs were not read; figures come from secondary summaries.
