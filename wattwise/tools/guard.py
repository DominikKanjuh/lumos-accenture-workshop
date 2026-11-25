"""Agent guardrail hook: enforces AGENTS.md boundaries and writes an audit log.

Claude Code hook: reads the tool call as JSON on stdin. Exit 2 = block (stderr is shown to the agent).
Usage: `guard.py pre` (PreToolUse on Edit|Write) and `guard.py log` (PostToolUse, all tools).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Deny by default: every wiki page (incl. new ones) is source of truth. Agents may only write
# proposals and the mechanics pages that describe the code.
WIKI_WRITABLE = {"wiki/Architecture.md", "wiki/Glossary.md"}


def rel(path: str, cwd: str) -> str:
    try:
        return Path(path).resolve().relative_to(Path(cwd).resolve()).as_posix()
    except ValueError:
        return path


def check(event: dict) -> str | None:
    inp = event.get("tool_input", {})
    path = rel(inp.get("file_path", ""), event.get("cwd", "."))
    if path.startswith("wiki/") and path not in WIKI_WRITABLE and not path.startswith("wiki/_proposals/"):
        return f"{path} is source of truth (owned by the product owner). Write a proposal to wiki/_proposals/ instead."
    if path.startswith("data/"):
        return "data/ is read-only: the meter readings are correct. Fix the code."
    if path.startswith("issues/") and event.get("tool_name") == "Write":
        return "Do not rewrite tickets; only edit the status line."
    if path.startswith("tests/") and Path(inp.get("file_path", "")).exists():
        old, new = inp.get("old_string"), inp.get("new_string")
        if old is None:
            return "Do not overwrite an existing test file. Add tests with an additive Edit or a new file."
        if not (new.startswith(old) or new.endswith(old)):
            return "Existing tests must not be changed or weakened. Only append new tests."
    return None


def log(event: dict, blocked: str | None = None) -> None:
    inp = {k: (v[:500] + "…" if isinstance(v, str) and len(v) > 500 else v)
           for k, v in (event.get("tool_input") or {}).items()}
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "tool": event.get("tool_name"), "input": inp}
    if blocked:
        entry["blocked"] = blocked
    reports = Path(event.get("cwd", ".")) / "reports"
    if reports.is_dir():
        with open(reports / "agent-audit.log", "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
    event = json.load(sys.stdin)
    if mode == "log":
        log(event)
        return
    reason = check(event)
    if reason:
        if mode != "selftest":
            log(event, blocked=reason)
        print(f"BLOCKED by guard: {reason}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
