# AGENTS.md, Agent Skills, and Claude Code: research notes

Date: 2026-11-25. Legend: **[V]** = checked against official docs or primary source during this research. **[3P]** = third-party sources only (blogs, guides, GitHub issues). **[UNVERIFIED]** = conflicting or unconfirmed.

---

## 1. AGENTS.md standard

**What it is** [V] (https://agents.md)
- Plain Markdown, no required fields or schema. A "README for agents": build/test commands, conventions, boundaries.
- **Nested files:** agents read the nearest AGENTS.md in the directory tree. FAQ: "The closest AGENTS.md to the edited file wins; explicit user chat prompts override everything."
- **Migration tip from the FAQ:** rename the existing file to AGENTS.md and symlink the old name to it.
- **Stewardship** [V]: OpenAI released it in Aug 2025. On 2025-12-09 the Linux Foundation formed the **Agentic AI Foundation (AAIF)**, with MCP (Anthropic), goose (Block) and AGENTS.md (OpenAI) as its founding projects. agents.md now says it is "stewarded by the Agentic AI Foundation under the Linux Foundation."
  - https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation
  - https://aaif.io/news/linux-foundation-announces-formation-of-aaif
  - Adoption figure of "60k+ repos" at launch: [3P] (WorkOS blog).

### Native support matrix (late 2026)

| Tool | Reads AGENTS.md natively? | Nested? | Notes / config | Status |
|---|---|---|---|---|
| **Claude Code** | **Yes, since v2.1.277**, but only if there is **no** CLAUDE.md / .claude/CLAUDE.md / CLAUDE.local.md in the cwd or any ancestor (default mode `claude-md-or-agents-md`) | Yes (ancestors at start; subdir loaded when a file there is Read) | See section 3.1. Does NOT read `AGENTS.override.md`, `AGENTS.local.md`, or anything under `.agents/` | [V] code.claude.com/docs/en/memory |
| **OpenAI Codex** (CLI/IDE/cloud) | Yes (originator) | Yes. Walks from the git root down to the cwd; one file per dir; precedence `AGENTS.override.md` > `AGENTS.md` > `project_doc_fallback_filenames`; concatenated root-first; `project_doc_max_bytes` default 32 KiB; global `~/.codex/AGENTS.md` | `~/.codex/config.toml`: `project_doc_fallback_filenames = ["TEAM_GUIDE.md"]`, `project_doc_max_bytes = 65536` | [3P]. Consistent across many guides and a docs mirror (codex-docs.com); the official page could not be fetched |
| **GitHub Copilot coding agent** (cloud) | Yes, since 2025-08-28 | Yes (`**/AGENTS.md`); also reads `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, `CLAUDE.md`, `GEMINI.md` | Copilot code review reads AGENTS.md. VS Code local agent uses `chat.useAgentsMdFile` / `chat.useNestedAgentsMdFiles` (nested is buggy per issue reports) | [V] https://github.blog/changelog/2025-08-28-copilot-coding-agent-now-supports-agents-md-custom-instructions/ , https://docs.github.com/en/copilot/reference/custom-instructions-support |
| **Cursor** | Yes (IDE + CLI) | Yes in the IDE; nested files combine, more specific wins. [3P]: CLI reads the root file only | AGENTS.md has no frontmatter, so it always applies. Use `.cursor/rules/*.mdc` for glob-scoped rules. Also reads CLAUDE.md | [V] https://cursor.com/docs/rules (via search summary) |
| **Gemini CLI** | **No, not by default** (default is GEMINI.md). Opt in with config | Hierarchical once configured | `.gemini/settings.json`: `{"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}}` | [V] https://geminicli.com/docs/cli/gemini-md.md |
| **Windsurf** (Cascade; now Cognition/Devin) | Yes | Yes. Root file = always-on rule; a subdir file = glob rule scoped to that dir. Both `AGENTS.md` and `agents.md` work | Same rules engine as `.windsurf/rules/` / `.devin/rules/` | [V] docs.windsurf.com/windsurf/cascade/agents-md (via search). [UNVERIFIED]: docs may now redirect to docs.devin.ai |
| **Aider** | **No, opt-in only** | No | `.aider.conf.yml`: `read: AGENTS.md` (or `aider --read AGENTS.md`) | [V] agents.md FAQ. Some guides wrongly say "native" |
| **Jules** (Google) | Yes (repo root) | [UNVERIFIED] | jules.google docs: it "will also refer to agents.md" for environment setup | [3P]/partial |
| **Zed** | Yes, but **first match wins and nothing is merged**. Order: `.rules`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | No | A stale `.cursorrules` hides AGENTS.md. Personal file: `~/.config/zed/AGENTS.md` | [3P] (GitHub discussion zed-industries/zed#63908 quotes the docs) |
| Others listed on agents.md | Factory, Amp, goose, opencode, Warp, VS Code, Devin, Junie, RooCode, Kilo Code, Augment, etc. | varies | | [V] listed on agents.md, not individually checked |

**Implication for WattWise:** use one root `AGENTS.md` as the single source of truth and **do not add a CLAUDE.md**, so Claude Code reads AGENTS.md natively. If Claude-specific content is needed, add a CLAUDE.md that contains `@AGENTS.md` and then the extra lines (works on every Claude Code version). Remove any `.rules` or `.cursorrules` files, which would shadow AGENTS.md in Zed. Add `.gemini/settings.json` and `.aider.conf.yml` shims for those tools.

---

## 2. Agent Skills open standard (SKILL.md)

**Spec** [V] https://agentskills.io/specification.md. Originally developed by Anthropic and released as an open standard. Repo: https://github.com/agentskills/agentskills
- A skill is a folder `skill-name/SKILL.md`, with optional `scripts/`, `references/`, `assets/`.
- **Frontmatter (spec allows exactly 6 fields):**

| Field | Req | Constraint |
|---|---|---|
| `name` | yes | 1–64 chars, `[a-z0-9-]`, no leading/trailing or double hyphen, **must match the folder name** |
| `description` | yes | 1–1024 chars. Say what it does and when to use it, with trigger keywords |
| `license` | no | short |
| `compatibility` | no | ≤500 chars, environment requirements |
| `metadata` | no | string→string map |
| `allowed-tools` | no | space-separated, **experimental** (e.g. `Bash(git:*) Read`) |

- Progressive disclosure: the name and description load at startup (~100 tokens). The body loads on activation; keep it under 5000 tokens / 500 lines. Keep references one level deep.
- Validate with `skills-ref validate ./my-skill`.

Minimal portable skill:
```markdown
---
name: wiki-drift-check
description: Compare wiki/ pages against the code they describe and report or fix knowledge drift. Use when code under src/ changes, before merging, or when asked to sync or update docs.
---
# Steps
1. ...
```

### Skill folder support by tool

| Tool | Project paths | User paths | Status |
|---|---|---|---|
| **Claude Code** | `.claude/skills/<name>/SKILL.md` (plus nested `<subdir>/.claude/skills`). **Does NOT read `.agents/skills/`** | `~/.claude/skills/` | [V] skills docs. Open feature requests: anthropics/claude-code#31005 (main, ~443 👍), #16345 (closed as dup), #107421 (v2.1.318 still does not read it) |
| **OpenAI Codex** | `.agents/skills/` (scans from the cwd up to the repo root; [3P] also `.codex/skills`) | `~/.agents/skills`, `/etc/codex/skills` | [3P] |
| **GitHub Copilot** (cloud agent, CLI, VS Code) | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.copilot/skills/` | [V] https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills (shows .github/skills). `.agents/skills` [V] via Microsoft VS docs |
| **Cursor** (2.4+) | `.cursor/skills/`, `.agents/skills/`, plus compatibility reads of `.claude/skills/` and `.codex/skills/` | home equivalents | [V] https://cursor.com/docs/skills , https://cursor.com/changelog/2-4 |
| **Gemini CLI** | `.gemini/skills/` or alias `.agents/skills/` (workspace must be trusted) | `~/.gemini/skills/` or `~/.agents/skills/` | [V] https://geminicli.com/docs/cli/creating-skills/ |
| OpenCode | `.agents/skills` | | [3P] |

**Portable layout recommendation:** keep the canonical copy in `.agents/skills/<name>/` and add a **per-skill** symlink `.claude/skills/<name> -> ../../.agents/skills/<name>`. Claude Code supports symlinked skill folders [V]. Do not symlink the whole `.claude/skills` dir; [3P] issue #20820 says Claude writes internal files there. Alternatively, keep the canonical copy in `.claude/skills/`, which Copilot and Cursor read anyway; only Codex and Gemini would then need `.agents/skills`. **Use only the 6 spec fields** in frontmatter. Claude Code extensions (`disable-model-invocation`, `argument-hint`, `context: fork`, `paths`, …) cause a hard error when uploaded to claude.ai or the Skills API: `Unexpected key(s) in SKILL.md frontmatter` [V].

---

## 3. Claude Code specifics [V] (code.claude.com/docs)

### 3.1 AGENTS.md loading (https://code.claude.com/docs/en/memory#agents-md)

| Repo has | Claude reads |
|---|---|
| AGENTS.md, no CLAUDE.md/CLAUDE.local.md in cwd or above | AGENTS.md |
| AGENTS.md + CLAUDE.md | CLAUDE.md only |
| CLAUDE.md containing `@AGENTS.md` | both (via import) |

- Requires **v2.1.277+**. It is implemented by the built-in plugin `cc-plugin-agents-md@builtin` (named `agents-md@builtin` before v2.1.285).
- `~/.claude/CLAUDE.md`, managed CLAUDE.md, and `.claude/rules/` do **not** suppress AGENTS.md.
- Unavailable in these cases: versions before 2.1.277, the plugin disabled, sometimes the first session after an upgrade, and (before 2.1.281) Bedrock or telemetry-off sessions.
- `InstructionsLoaded` hooks don't fire for a natively loaded AGENTS.md.
- Load both files (user or managed settings only; ignored in project settings):
```json
{ "pluginConfigs": { "cc-plugin-agents-md@builtin": { "options": { "instructionFiles": "claude-md-and-agents-md" } } } }
```
- Fallback that works on all versions (CLAUDE.md):
```markdown
@AGENTS.md

## Claude Code
Use plan mode for changes under `src/billing/`.
```
  A symlink (`ln -s AGENTS.md CLAUDE.md`) also works, but the Edit and Write tools refuse to write through a symlink.
- Size guidance: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." Use path-scoped `.claude/rules/*.md` (frontmatter `paths:`) for part-of-repo rules.

### 3.2 Skills and slash commands (https://code.claude.com/docs/en/skills)
- **"Custom commands have been merged into skills."** `.claude/commands/foo.md` still works (same frontmatter except `name` and `paths`). A skill at `.claude/skills/foo/SKILL.md` is invoked as `/foo`, and a skill wins over a command with the same name.
- Claude-only frontmatter: `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation` (manual `/name` only), `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context: fork`, `agent`, `background`, `hooks`, `paths`, `shell`.
- Combined description and when_to_use are truncated at 1,536 chars in the listing.

### 3.3 Subagents: `.claude/agents/*.md` (https://code.claude.com/docs/en/sub-agents)
Required fields: `name` (≤256 chars, no `:`) and `description`. Optional fields: `tools`, `disallowedTools`, `model` (`sonnet|opus|haiku|fable|inherit|<full id>`), `permissionMode` (`default|acceptEdits|auto|dontAsk|bypassPermissions|plan`), `maxTurns`, `skills` (preloads full skill content), `mcpServers`, `hooks`, `memory` (`user|project|local`), `background`, `omitClaudeMd`, `effort`, `isolation: worktree`, `color`, `initialPrompt`.
```markdown
---
name: wiki-auditor
description: Read-only auditor that compares wiki/ against src/ and reports drift. Use after code changes or before release.
tools: Read, Grep, Glob, Bash
model: sonnet
permissionMode: plan
skills: [wiki-drift-check]
---
You audit documentation drift. Never edit files; output a table of claim → code location → status.
```
Subagents are Claude-only. For portability, put the logic in a skill and keep the subagent as a thin wrapper.

### 3.4 Hooks: block edits to paths (https://code.claude.com/docs/en/hooks)
`.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|NotebookEdit",
        "hooks": [
          { "type": "command", "command": "\"${CLAUDE_PROJECT_DIR}\"/.claude/hooks/protect-paths.sh" }
        ]
      }
    ]
  }
}
```
`.claude/hooks/protect-paths.sh` (stdin JSON has `tool_name` and `tool_input.file_path`, which is an absolute path):
```bash
#!/usr/bin/env bash
f=$(jq -r '.tool_input.file_path // empty')
case "$f" in
  */tests/fixtures/*|*/issues/*|*/.env*)
    echo "Blocked: $f is read-only for agents (see AGENTS.md > Boundaries)" >&2
    exit 2 ;;
esac
exit 0
```
**Exit-code semantics** [V]:
- `0`: success. Any JSON on stdout is applied. With no output, the normal permission flow continues.
- `2`: **blocking**. For PreToolUse the tool call is blocked and stderr is shown to Claude as the reason.
- Any other code (including `1`): **non-blocking** error and the action proceeds. The docs: "If your hook is meant to enforce a policy, use `exit 2`." A non-0/2 exit also overrides printed JSON.
- JSON alternative (exit 0): `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`. Values are `allow|deny|ask|defer` (`defer` only with `-p`). Precedence across hooks: deny > defer > ask > allow. Old top-level `decision: approve|block` is deprecated for PreToolUse.
- An optional per-hook `"if": "Edit(*.ts)"` narrows by permission-rule syntax.
- **Simpler alternative without a script:** permission deny rules in `.claude/settings.json`, for example `{"permissions":{"deny":["Edit(/tests/fixtures/**)","Edit(/issues/**)"]}}`. Use `Edit(...)` to cover Write too; a `Write(path)` rule isn't matched [V permissions docs].
- Caveat [V]: `claude -p` without `--bare` runs project hooks even in untrusted folders.

### 3.5 Headless (https://code.claude.com/docs/en/headless)
```bash
claude -p "Fix issue issues/BUG-003.md; ground the fix in wiki/" \
  --allowedTools "Read,Edit,Bash(pytest:*)" --output-format json
# structured: --output-format json --json-schema '<schema>'  -> .structured_output
# --bare: skips hooks/skills/subagents/plugins/MCP/auto-memory/CLAUDE.md (recommended for scripts; planned future default for -p)
```
Note: `--bare` also skips your skills and project instructions. For this project, run *without* `--bare` so AGENTS.md and the skills load, or pass them explicitly.

### 3.6 GitHub Action (https://code.claude.com/docs/en/github-actions, https://github.com/anthropics/claude-code-action)
Quick setup: run `/install-github-app` in Claude Code (github.com only). Minimal `@claude` workflow:
```yaml
name: Claude Code
on:
  issue_comment: { types: [created] }
  pull_request_review_comment: { types: [created] }
jobs:
  claude:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    permissions: { contents: write, pull-requests: write, issues: write, id-token: write, actions: read }
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 1 }
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # automation mode: prompt: "/wiki-drift-check"   claude_args: '--allowedTools "Read,Edit,Bash(pytest:*)"'
```
With `prompt:`, the action runs on any event, including `schedule` and `pull_request`. Tools must be granted through `claude_args --allowedTools` or the skill's `allowed-tools`. Use `claude_code_oauth_token` instead for subscription auth. A drift check on PRs could be `on: pull_request` with `paths: ['src/**']`.

---

## 4. Best practices and evidence

### Exemplary real AGENTS.md files (fetched 2026-11-25)
1. **openai/openai-agents-python** (~106 lines): authority/workflow rules, a **skill-routing table** pointing at `.agents/skills/<name>/SKILL.md`, review rules, security. Closest model for our "AGENTS.md + skills" design. https://github.com/openai/openai-agents-python/blob/main/AGENTS.md
2. **astral-sh/uv** (~49 lines): terse ALWAYS/NEVER/PREFER bullets that point to CONTRIBUTING.md for commands instead of duplicating them. https://github.com/astral-sh/uv/blob/main/AGENTS.md
3. **pydantic/pydantic-ai** (~177 lines). https://github.com/pydantic/pydantic-ai/blob/main/AGENTS.md
4. **temporalio/sdk-python** (~137 lines; Python SDK). https://github.com/temporalio/sdk-python/blob/main/AGENTS.md
5. **apache/airflow** (~254 lines; large monorepo, longer than ideal). https://github.com/apache/airflow/blob/main/AGENTS.md
(getsentry/sentry and vercel/next.js have them too, but they are longer.)

### What to include and what to avoid
- GitHub analysis of 2,500+ agents.md files (https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) [V]. It covers six areas: **commands (early, with exact flags), testing, project structure, code style (show a real example), git workflow, boundaries** (always / ask first / never). Name the exact stack and versions. Avoid vagueness ("helpful assistant"). Grow the file when the agent makes mistakes.
- Claude docs [V]: under 200 lines, specific and verifiable instructions, no contradictions. Imports don't reduce context cost.
- Avoid: repository overviews and directory tours (see the ETH study below), content duplicated from README/CONTRIBUTING (link instead), generic advice the model already follows, and auto-generated `/init` dumps left unedited.

### Evidence on effectiveness
- **Gloaguen et al., ETH Zurich, "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?"** arXiv:2602.11988 (v1 Feb 2026, v3 Sep 2026; ICLR'26 workshop) [V abstract]. Context files "do not generally improve task success rates, while increasing inference cost by over 20%". Instructions *are* followed well, but **repository overviews are not helpful**. Files are "useful for specifying non-standard coding practices". In v1, developer-written files beat LLM-generated ones; LLM-generated files cut success by 0.5–2% [3P summary of v1 numbers]. https://arxiv.org/abs/2602.11988
- **"On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents"** arXiv:2601.20404 [V abstract]. 10 repos, 124 PRs: AGENTS.md is associated with **−28.6% median runtime** and **−16.6% output tokens**, with comparable completion. https://arxiv.org/abs/2601.20404
- **"Do They Do as They Are Told?"** arXiv:2611.13709 (Nov 2026) [V abstract]. Agents follow context-file instructions "more often than not", but adherence is **bimodal**: some instruction types are always followed and others never. This argues for **enforcement beyond the file** (hooks, CI, tests). https://arxiv.org/abs/2611.13709
- Also cited but not read: arXiv:2602.14690 (configuring agentic tools), arXiv:2605.10039 (factorial study of file-structure variables) [UNVERIFIED findings].

**Takeaway for WattWise:** keep AGENTS.md short (well under 200 lines). Focus it on commands, non-obvious domain rules (billing rules live in wiki/, so link to them rather than restating), and boundaries. Put procedures (bug fix, drift check) in skills, which load on demand. Enforce hard boundaries with hooks, permission rules and CI, not with prose alone. Measure on the issues/ bug set with and without the setup, as the ETH paper recommends.

---

## Unverified / caveats summary
- Codex discovery details (override file, 32 KiB limit, `.agents/skills`): only third-party sources and a docs mirror. The official OpenAI page was not fetched; it may have moved to learn.chatgpt.com.
- Zed priority order: from a GitHub discussion quoting the docs; zed.dev itself was not fetched.
- Jules nested support: unknown.
- Windsurf docs may now live at docs.devin.ai, with `.devin/` paths preferred.
- Cursor CLI reading the root file only: third-party.
- Claude Code `.agents/skills`: confirmed NOT supported per the docs ("anything under a `.agents/` directory" is not read). Track anthropics/claude-code#31005.
