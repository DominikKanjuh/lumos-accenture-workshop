"""WikiGuard lint: proves the knowledge layer is in place and the code follows GUIDELINES.md.

Checks
  KIT  - AGENTS.md, GUIDELINES.md, skills, hooks present and wired; guard hook self-test
  INV  - every wiki page, data file and source module is registered and cross-referenced (no orphans); tickets <-> CHANGELOG
  MAP  - every wiki rule section is mapped, every mapped symbol/test exists, no orphan business code (K2)
  CODE - guideline rules on domain code: N1 float, N2 rounding, E1 built-in exceptions, docstrings/hints

Usage: python tools/wikiguard_lint.py --repo . [--strict]   (exit 1 on errors; --strict: warnings too)
"""
import argparse
import ast
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAIN = ["models", "meter", "tariff", "billing", "money"]
BUILTIN_EXC = {"Exception", "ValueError", "RuntimeError", "AssertionError", "KeyError", "TypeError"}
SKILLS = ["fix-bug", "drift-check", "wiki-sync"]


class Lint:
    def __init__(self) -> None:
        self.findings: list[tuple[str, str, str]] = []

    def err(self, area: str, msg: str) -> None:
        self.findings.append(("ERROR", area, msg))

    def warn(self, area: str, msg: str) -> None:
        self.findings.append(("WARN", area, msg))


def check_kit(repo: Path, lint: Lint) -> None:
    agents = repo / "AGENTS.md"
    if not agents.exists():
        lint.err("KIT", "AGENTS.md missing")
    elif "GUIDELINES.md" not in agents.read_text():
        lint.err("KIT", "AGENTS.md does not reference GUIDELINES.md")
    if not (repo / "GUIDELINES.md").exists():
        lint.err("KIT", "GUIDELINES.md missing")
    if (repo / "CLAUDE.md").exists() and "@AGENTS.md" not in (repo / "CLAUDE.md").read_text():
        lint.err("KIT", "CLAUDE.md exists without '@AGENTS.md': Claude Code would ignore AGENTS.md")
    for name in SKILLS:
        skill = repo / ".agents" / "skills" / name / "SKILL.md"
        if not skill.exists():
            lint.err("KIT", f"skill {name}: {skill.relative_to(repo)} missing")
            continue
        head = skill.read_text().split("---")[1] if skill.read_text().startswith("---") else ""
        if f"name: {name}" not in head or "description:" not in head:
            lint.err("KIT", f"skill {name}: frontmatter needs 'name: {name}' and 'description'")
        link = repo / ".claude" / "skills" / name / "SKILL.md"
        if not link.exists():
            lint.err("KIT", f"skill {name}: not visible to Claude Code (.claude/skills/{name} link missing)")
    settings = repo / ".claude" / "settings.json"
    hooks = json.loads(settings.read_text()).get("hooks", {}) if settings.exists() else {}
    if "guard.py\" pre" not in json.dumps(hooks.get("PreToolUse", [])).replace("\\", ""):
        lint.err("KIT", "PreToolUse guard hook not configured in .claude/settings.json")
    if "guard.py\" log" not in json.dumps(hooks.get("PostToolUse", [])).replace("\\", ""):
        lint.warn("KIT", "PostToolUse audit-log hook not configured")
    guard = repo / "tools" / "guard.py"
    if guard.exists():
        selftest_guard(repo, guard, lint)
    else:
        lint.err("KIT", "tools/guard.py missing")


def selftest_guard(repo: Path, guard: Path, lint: Lint) -> None:
    existing_test = next((repo / "tests").glob("test_*.py"), None)
    cases = [
        ("Write", {"file_path": str(repo / "wiki/Tariffs.md"), "content": "x"}, True),
        ("Write", {"file_path": str(repo / "wiki/Any-New-Page.md"), "content": "x"}, True),
        ("Edit", {"file_path": str(repo / "wiki/Home.md"), "old_string": "a", "new_string": "b"}, True),
        ("Write", {"file_path": str(repo / "wiki/_proposals/x.md"), "content": "x"}, False),
        ("Edit", {"file_path": str(repo / "wiki/Architecture.md"), "old_string": "a", "new_string": "b"}, False),
        ("Edit", {"file_path": str(repo / "data/readings.csv"), "old_string": "a", "new_string": "b"}, True),
        ("Edit", {"file_path": str(repo / "src/wattwise/meter.py"), "old_string": "a", "new_string": "b"}, False),
    ]
    if existing_test:
        cases.append(("Edit", {"file_path": str(existing_test), "old_string": "== 1", "new_string": "== 2"}, True))
    for tool, inp, should_block in cases:
        event = json.dumps({"tool_name": tool, "tool_input": inp, "cwd": str(repo)})
        rc = subprocess.run([sys.executable, str(guard), "selftest"], input=event, text=True,
                            capture_output=True).returncode
        if (rc == 2) != should_block:
            what = "block" if should_block else "allow"
            lint.err("KIT", f"guard self-test: should {what} {tool} {Path(inp['file_path']).relative_to(repo)}")


def check_map(repo: Path, lint: Lint) -> None:
    rules_path = repo / "tools" / "drift-check" / "rules.json"
    if not rules_path.exists():
        lint.err("MAP", "tools/drift-check/rules.json missing: no rule <-> code <-> test map")
        return
    spec = importlib.util.spec_from_file_location("drift_check", repo / "tools/drift-check/drift_check.py")
    drift = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drift)
    rep = drift.check(repo, json.loads(rules_path.read_text()))
    for p in rep["problems"]:
        lint.err("MAP", p)
    for s in rep["unmapped"]:
        lint.err("MAP", f"wiki section {s} has no entry in rules.json (K2)")
    for r in rep["results"]:
        if r["status"] == "NO EXAMPLE":
            lint.warn("MAP", f"{r['id']}: no executable example (Q1)")
    for r in rep["untested"]:
        lint.warn("MAP", f"{r}: rule has no test (Q1)")
    for s in rep["undocumented"]:
        lint.warn("MAP", f"{s}: code not mapped to any wiki rule (K2)")


def check_inventory(repo: Path, lint: Lint) -> None:
    """Every wiki page, data file and source module - old or new - must be registered and cross-referenced."""
    rules_path = repo / "tools" / "drift-check" / "rules.json"
    if not rules_path.exists():
        return
    registry = json.loads(rules_path.read_text())
    inv = registry.get("inventory", {})
    wiki_inv, data_inv = inv.get("wiki", {}), inv.get("data", {})
    src = repo / "src" / "wattwise"

    pages = {p.name for p in (repo / "wiki").glob("*.md")}
    for p in sorted(pages - set(wiki_inv)):
        lint.err("INV", f"wiki/{p} is not registered in rules.json inventory (new or orphan page)")
    for p in sorted(set(wiki_inv) - pages):
        lint.err("INV", f"inventory lists wiki/{p} but the file does not exist")
    for p, meta in wiki_inv.items():
        if meta.get("kind") == "rules" and p.removesuffix(".md") not in registry["wiki_pages"]:
            lint.err("INV", f"wiki/{p} is a rules page but is not checked for drift (wiki_pages)")
    home = repo / "wiki" / "Home.md"
    if home.exists():
        for p in sorted(pages - {"Home.md"}):
            if f"({p})" not in home.read_text():
                lint.err("INV", f"wiki/Home.md does not link {p}")

    modules = {p.stem for p in src.glob("*.py") if not p.stem.startswith("__")}
    arch = (repo / "wiki" / "Architecture.md").read_text() if (repo / "wiki/Architecture.md").exists() else ""
    for m in sorted(modules):
        if f"`{m}.py`" not in arch:
            lint.err("INV", f"src/wattwise/{m}.py is not described in wiki/Architecture.md")
    for m in sorted(set(re.findall(r"`(\w+)\.py`", arch)) - modules):
        lint.err("INV", f"wiki/Architecture.md describes {m}.py which does not exist")

    files = {p.name for p in (repo / "data").iterdir() if p.is_file() and not p.name.startswith(".")}
    for f in sorted(files - set(data_inv)):
        lint.err("INV", f"data/{f} is not registered in rules.json inventory")
    for f, meta in data_inv.items():
        path = repo / "data" / f
        if not path.exists():
            lint.err("INV", f"inventory lists data/{f} but the file does not exist")
            continue
        reader = src / f"{meta['read_by']}.py"
        if not reader.exists() or f not in reader.read_text():
            lint.err("INV", f"data/{f}: not read by {meta['read_by']}.py (unused or wrong owner)")
        for page in meta.get("documented_in", []):
            if f"data/{f}" not in (repo / "wiki" / page).read_text():
                lint.err("INV", f"data/{f}: not mentioned in wiki/{page}")
        if "csv_columns" in meta:
            header = path.read_text().splitlines()[0].split(",")
            if header != meta["csv_columns"]:
                lint.err("INV", f"data/{f}: columns {header} != registered {meta['csv_columns']} (schema drift)")
        if "json_keys" in meta:
            keys = sorted(json.loads(path.read_text()))
            if keys != sorted(meta["json_keys"]):
                lint.err("INV", f"data/{f}: keys {keys} != registered {meta['json_keys']} (schema drift)")


def check_changelog(repo: Path, lint: Lint) -> None:
    """K5: tickets and CHANGELOG agree - every fixed ticket is logged, every logged ticket exists and is fixed."""
    changelog, issues = repo / "CHANGELOG.md", repo / "issues"
    if not changelog.exists():
        lint.err("INV", "CHANGELOG.md missing")
        return
    text = changelog.read_text()
    if "## Unreleased" not in text:
        lint.err("INV", "CHANGELOG.md has no '## Unreleased' section")
        return
    unreleased = text.split("## Unreleased", 1)[1].split("\n## ", 1)[0]
    logged = set(re.findall(r"\b(BUG-\d+)\b", unreleased))
    tickets = {}
    for f in issues.glob("BUG-*.md") if issues.exists() else []:
        status = re.search(r"\|\s*Status\s*\|\s*([^|]+)\|", f.read_text())
        tickets[f.name.split("-")[0] + "-" + f.name.split("-")[1]] = status.group(1).strip() if status else ""
    for tid, status in sorted(tickets.items()):
        if status.lower().startswith("fixed") and tid not in logged:
            lint.err("INV", f"{tid} is '{status}' but has no CHANGELOG line under Unreleased (K5)")
    for tid in sorted(logged):
        if tid not in tickets:
            lint.err("INV", f"CHANGELOG mentions {tid} but issues/ has no such ticket (K5)")
        elif tickets[tid].lower().startswith("open"):
            lint.err("INV", f"CHANGELOG lists {tid} but the ticket is still '{tickets[tid]}' (K5)")
    for line in unreleased.splitlines():
        if line.startswith("- ") and not re.search(r"\((BUG|FEAT)-\d+\)", line):
            lint.warn("INV", f"CHANGELOG line without ticket id: {line[:60]}")


def check_guidelines(repo: Path, lint: Lint) -> None:
    """Every company guideline ID in GUIDELINES.md must be stated in AGENTS.md (and vice versa)."""
    g, a = repo / "GUIDELINES.md", repo / "AGENTS.md"
    if not (g.exists() and a.exists()):
        return
    ids = set(re.findall(r"^\| ([A-Z]\d+) \|", g.read_text(), re.M))
    in_agents = set(re.findall(r"\b([CNTQEKPA]\d+)\b", a.read_text()))
    for i in sorted(ids - in_agents):
        lint.err("KIT", f"guideline {i} from GUIDELINES.md missing in AGENTS.md")
    for i in sorted(in_agents - ids):
        lint.err("KIT", f"AGENTS.md cites guideline {i} that GUIDELINES.md does not define")


def check_code(repo: Path, lint: Lint) -> None:
    for mod in DOMAIN:
        path = repo / "src" / "wattwise" / f"{mod}.py"
        if not path.exists():
            continue
        tree = ast.parse(path.read_text())
        loc = lambda n: f"{path.relative_to(repo)}:{n.lineno}"  # noqa: E731
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                lint.err("CODE", f"{loc(node)} float literal (N1)")
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
                if name == "float":
                    lint.err("CODE", f"{loc(node)} float() (N1)")
                if name in {"round", "quantize"} and mod != "money":
                    lint.err("CODE", f"{loc(node)} {name}() outside money.round_eur (N2)")
            if isinstance(node, ast.Raise) and node.exc is not None:
                exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
                if isinstance(exc, ast.Name) and exc.id in BUILTIN_EXC:
                    lint.err("CODE", f"{loc(node)} raises built-in {exc.id}; use wattwise.errors (E1)")
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                doc = ast.get_docstring(node)
                if not doc:
                    lint.warn("CODE", f"{loc(node)} {node.name}: missing docstring")
                if isinstance(node, ast.FunctionDef):
                    params = [a for a in node.args.args if a.arg not in ("self", "cls")]
                    if node.returns is None or any(a.annotation is None for a in params):
                        lint.warn("CODE", f"{loc(node)} {node.name}: missing type hints")
                    raises = any(isinstance(n, ast.Raise) for n in ast.walk(node))
                    if doc and len(params) > 0 and "Args:" not in doc and "\n" in doc:
                        lint.warn("CODE", f"{loc(node)} {node.name}: docstring lacks 'Args:'")
                    if doc and raises and "Raises:" not in doc:
                        lint.warn("CODE", f"{loc(node)} {node.name}: raises but docstring lacks 'Raises:'")
    pyproject = repo / "pyproject.toml"
    if pyproject.exists() and "dependencies = []" not in pyproject.read_text():
        lint.warn("CODE", "pyproject.toml declares runtime dependencies; approval required (P3)")


def run(repo: Path) -> Lint:
    lint = Lint()
    check_kit(repo, lint)
    check_guidelines(repo, lint)
    check_inventory(repo, lint)
    check_changelog(repo, lint)
    check_map(repo, lint)
    check_code(repo, lint)
    return lint


def main() -> None:
    ap = argparse.ArgumentParser(description="WikiGuard lint")
    ap.add_argument("--repo", default=".", type=Path)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()
    lint = run(args.repo.resolve())
    for level, area, msg in sorted(lint.findings, key=lambda f: (f[0] != "ERROR", f[1])):
        print(f"{level:5} {area:4} {msg}")
    errors = sum(f[0] == "ERROR" for f in lint.findings)
    warns = len(lint.findings) - errors
    print(f"\n{errors} error(s), {warns} warning(s)")
    sys.exit(1 if errors or (args.strict and warns) else 0)


if __name__ == "__main__":
    main()
