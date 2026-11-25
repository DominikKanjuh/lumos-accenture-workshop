#!/usr/bin/env python3
"""Wiki-vs-code drift checker for WattWise (stdlib only).

Reads the business rules (one per wiki heading) and their worked examples from
wiki/*.md, runs each example against the code, and reports per rule whether the
code still does what the wiki says. See README.md.
"""

import argparse
import ast
import json
import re
import sys
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent


# --- wiki parsing --------------------------------------------------------------

def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_sections(page, text):
    """One section per heading. ID = '<Page>#<heading-slug>'.

    A section spans its sub-headings. Headings starting with 'Example' are worked
    examples of the parent rule, not rules themselves.
    """
    lines, heads, fence = text.splitlines(), [], False
    for i, line in enumerate(lines):
        fence ^= line.startswith("```")
        m = not fence and re.match(r"(#{1,3}) (.+)", line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    sections = {}
    for n, (i, level, title) in enumerate(heads):
        if title.startswith("Example"):
            continue
        end = next((j for j, lv, _ in heads[n + 1:] if lv <= level), len(lines))
        own_end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        if not "".join(lines[i + 1:own_end]).strip():
            continue  # heading without own content (e.g. page title)
        body = "\n".join(lines[i + 1:end])
        own = "\n".join(lines[i + 1:own_end])
        sections[f"{page}#{slug(title)}"] = {"title": title, "body": body, "own": own, "page_text": text}
    return sections


def norm_cell(cell):
    cell = cell.replace("**", "").replace("`", "").strip()
    cell = re.sub(r"\s*EUR$", "", cell)
    return cell.replace(",", "") if re.fullmatch(r"[\d,]+(\.\d+)?", cell) else cell


def tables(body):
    """All markdown tables in a section as lists of {header: cell} dicts."""
    found, block = [], []
    for line in body.splitlines() + [""]:
        if line.strip().startswith("|"):
            block.append([norm_cell(c) for c in line.strip().strip("|").split("|")])
        elif block:
            header, rows = block[0], [r for r in block[2:]]
            found.append([dict(zip(header, r)) for r in rows])
            block = []
    return found


def wiki_says(body):
    """The first sentence containing bold text, i.e. the rule's key statement."""
    prose, code, fence = [], [], False
    for line in body.splitlines():
        fence ^= line.startswith("```")
        if line.startswith("```"):
            continue
        (code if fence else prose).append(line.strip().lstrip("- "))
    prose = [p for p in prose if not p.startswith(("|", "#"))]
    text = " ".join(" ".join(prose).split()) or next((c for c in code if c), "")
    sentences = re.split(r"(?<=[.:])\s+(?=[A-Z*])", text)
    pick = next((s for s in sentences if "**" in s), sentences[0] if sentences else "")
    pick = pick.replace("**", "").replace("`", "")
    return pick if len(pick) <= 110 else pick[:107] + "..."


# --- example execution ---------------------------------------------------------

def namespace(src):
    """Wiki vocabulary -> code. Small helpers so examples read like the wiki."""
    sys.dont_write_bytecode = True  # leave the client repo untouched
    sys.path.insert(0, str(src))
    from wattwise import billing, errors, meter as meter_mod, models, money, service, tariff

    D, iso = Decimal, date.fromisoformat

    def meter(digits, meter_id="M-1"):
        return models.Meter(meter_id, digits)

    def r(value, on, meter_id="M-1"):
        return models.MeterReading(meter_id, iso(on), value)

    def consumption(digits, opening, closing, days=30):
        start = date(2026, 11, 1)
        return meter_mod.consumption_kwh(meter(digits), models.MeterReading("M-1", start, opening),
                                         models.MeterReading("M-1", start + timedelta(days), closing))

    def days(label):
        start, end = label.split(" to ")
        return models.BillingPeriod(iso(start), iso(end)).days

    def invoice(code, month, kwh):
        p = service.month_period(month)
        cust = models.Customer("C-1", "Test", "M-1", code)
        return billing.create_invoice(cust, tariff.get_tariff(code), meter(6), p,
                                      r(100000, p.start.isoformat()),
                                      r(100000 + kwh, (p.end + timedelta(1)).isoformat()))

    def label_key(label):
        return re.sub(r"\s*\(.*\)|\s*\d+%", "", label).strip()

    def amount(inv, label):
        parts = {label_key(l.description): l.amount for l in inv.lines}
        parts.update(Net=inv.net, VAT=inv.vat, Total=inv.gross)
        return parts[label_key(label)]

    def vat_on_net(inv):
        return inv.net == sum(l.amount for l in inv.lines) and \
            inv.vat == money.round_eur(inv.net * D("0.19")) and inv.gross == inv.net + inv.vat

    def max_step(code, upto=1500):
        t = tariff.get_tariff(code)
        return max(tariff.energy_charge(t, n + 1) - tariff.energy_charge(t, n) for n in range(upto))

    def tiers_well_formed():
        return all(t.tiers[-1].up_to_kwh is None and
                   [x.up_to_kwh for x in t.tiers[:-1]] == sorted(x.up_to_kwh for x in t.tiers[:-1])
                   for t in tariff.TARIFFS.values())

    ns = {k: v for k, v in locals().items() if callable(v) and not k.startswith("_")}
    for mod in (models, meter_mod, tariff, billing, money, service, errors):
        ns.update({k: v for k, v in vars(mod).items() if not k.startswith("_") and k != "meter"})
    ns.update(meter=meter, D=D)
    return ns


def fill(template, row):
    return re.sub(r"\{([^{}]+)\}", lambda m: row[m.group(1)], template)


def expand(example, section):
    """Turn a registry example into concrete (call, expected, source) triples."""
    if "table" not in example:
        quote = example.get("wiki_quote")
        grounded = quote and quote in section["page_text"]
        src = "wiki" if grounded else ("NOT IN WIKI" if quote else "registry")
        return [(example["call"], example["expect"], src)]
    rows = tables(section["body"])[example["table"]]
    where = example.get("where", {})
    rows = [row for row in rows if all(row.get(k) == v for k, v in where.items())]
    return [(fill(example["call"], row), fill(example["expect"], row), "wiki table") for row in rows]


def run(call, ns):
    try:
        return eval(call, dict(ns))  # registry is trusted, repo-local config
    except Exception as exc:  # noqa: BLE001 - a raise is a valid outcome
        return f"raises {type(exc).__name__}: {exc}"


def same(actual, expected):
    if expected.startswith("raises "):
        return str(actual).startswith(expected + ":")
    try:
        return Decimal(str(actual)) == Decimal(expected)
    except InvalidOperation:
        return str(actual) == expected


# --- code & test inventory -----------------------------------------------------

def code_symbols(src, modules):
    """Public functions, methods/properties and UPPER_CASE constants per module."""
    found = set()
    for mod in modules:
        tree = ast.parse((src / "wattwise" / f"{mod}.py").read_text())
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                found.add(f"{mod}.{node.name}")
            elif isinstance(node, ast.ClassDef):
                found |= {f"{mod}.{node.name}.{f.name}" for f in node.body
                          if isinstance(f, ast.FunctionDef) and not f.name.startswith("_")}
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                found |= {f"{mod}.{t.id}" for t in targets
                          if isinstance(t, ast.Name) and t.id.isupper()}
    return found


def test_names(tests_dir):
    return {f"{p.name}::{n.name}" for p in sorted(tests_dir.glob("test_*.py"))
            for n in ast.walk(ast.parse(p.read_text()))
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}


# --- main ----------------------------------------------------------------------

def check(repo, registry):
    sections = {}
    for page in registry["wiki_pages"]:
        sections.update(parse_sections(page, (repo / "wiki" / f"{page}.md").read_text()))
    ns = namespace(repo / "src")
    symbols, tests = code_symbols(repo / "src", registry["code_scope"]), test_names(repo / "tests")
    results, problems, drifted = [], [], set()
    for rid, rule in registry["rules"].items():
        if rid not in sections:
            problems.append(f"registry rule `{rid}` has no matching wiki heading")
            continue
        problems += [f"`{rid}`: code symbol `{s}` not found" for s in rule["code"] if s not in symbols]
        problems += [f"`{rid}`: test `{t}` not found" for t in rule["tests"] if t not in tests]
        checks = []
        for ex in rule["examples"]:
            for call, expected, src in expand(ex, sections[rid]):
                actual = run(call, ns)
                checks.append((call, expected, actual, same(actual, expected), src))
                if src == "NOT IN WIKI":
                    problems.append(f"`{rid}`: example quote for `{call}` no longer in wiki")
        failed = [c for c in checks if not c[3]]
        via = [d for d in rule.get("depends_on", []) if d in drifted]
        drifted |= {rid} if failed else set()
        status = "DRIFT" if failed else "NO EXAMPLE" if not checks else \
            "UNTESTED" if not rule["tests"] else "IN SYNC"
        results.append(dict(id=rid, status=status, says=wiki_says(sections[rid]["own"]),
                            code=rule["code"], tests=rule["tests"], checks=checks, failed=failed,
                            via=via))
    referenced = {s for r in registry["rules"].values() for s in r["code"]}
    return dict(results=results, problems=problems,
                unmapped=sorted(set(sections) - set(registry["rules"])),
                undocumented=sorted(symbols - referenced),
                untested=[r["id"] for r in results if not r["tests"]])


def code_does(res):
    if res["failed"]:
        call, exp, act, _, _ = res["failed"][0]
        more = f" (+{len(res['failed']) - 1} more)" if len(res["failed"]) > 1 else ""
        return f"{call} -> {act}  [wiki: {exp}]{more}"
    return f"matches {len(res['checks'])}/{len(res['checks'])} examples"


def print_report(rep):
    for res in rep["results"]:
        ok = len(res["checks"]) - len(res["failed"])
        via = f"   <- inherited from {', '.join(res['via'])}" if res["status"] == "DRIFT" and res["via"] else ""
        print(f"[{res['status']:<10}] {res['id']}   ({ok}/{len(res['checks'])} examples){via}")
        print(f"    wiki says : {res['says']}")
        print(f"    code      : {', '.join(res['code'])}")
        for call, exp, act, passed, src in res["checks"]:
            if not passed:
                print(f"    DRIFT     : {call}\n                wiki: {exp}   code: {act}   ({src})")
        print(f"    tests     : {', '.join(t.split('::')[1] for t in res['tests']) or 'NONE'}\n")
    counts = {s: sum(r["status"] == s for r in rep["results"]) for s in
              ("IN SYNC", "DRIFT", "UNTESTED", "NO EXAMPLE")}
    roots = [r["id"] for r in rep["results"] if r["status"] == "DRIFT" and not r["via"]]
    print("Summary: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
    print(f"Root-cause DRIFT ({len(roots)})          : {', '.join(roots)}")
    print(f"Wiki rules without tests      : {', '.join(rep['untested']) or '-'}")
    print(f"Wiki sections not in registry : {', '.join(rep['unmapped']) or '-'}")
    print(f"UNDOCUMENTED code (no rule)   : {', '.join(rep['undocumented']) or '-'}")
    for p in rep["problems"]:
        print(f"REGISTRY PROBLEM: {p}")


def markdown(rep):
    esc = lambda s: str(s).replace("|", "\\|")
    out = ["# Wiki/code drift report", "",
           "| Rule | Status | Wiki says | Code does | Tests |", "| --- | --- | --- | --- | --- |"]
    out += [f"| `{r['id']}` | **{r['status']}**{' (via ' + ', '.join(r['via']) + ')' if r['status'] == 'DRIFT' and r['via'] else ''} | {esc(r['says'])} | `{esc(code_does(r))}` | "
            f"{len(r['tests']) or 'none'} |" for r in rep["results"]]
    out += ["", "## Failing examples", ""]
    out += [f"- `{r['id']}`: `{c[0]}` wiki **{c[1]}**, code **{c[2]}** ({c[4]})"
            for r in rep["results"] for c in r["failed"]] or ["- none"]
    out += ["", "## Coverage", "",
            "**Wiki rules without tests:** " + (", ".join(f"`{x}`" for x in rep["untested"]) or "none"),
            "", "**Wiki sections not in registry:** " + (", ".join(f"`{x}`" for x in rep["unmapped"]) or "none"),
            "", "**UNDOCUMENTED code (not referenced by any wiki rule):** "
            + (", ".join(f"`{x}`" for x in rep["undocumented"]) or "none")]
    if rep["problems"]:
        out += ["", "## Registry problems", ""] + [f"- {p}" for p in rep["problems"]]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default="wattwise", help="path to the wattwise repo")
    ap.add_argument("--rules", default=HERE / "rules.json", type=Path)
    ap.add_argument("--out", default=HERE / "drift-report.md", type=Path)
    args = ap.parse_args()
    rep = check(Path(args.repo).resolve(), json.loads(args.rules.read_text()))
    print_report(rep)
    args.out.write_text(markdown(rep))
    print(f"\nMarkdown report: {args.out}")
    sys.exit(1 if any(r["status"] == "DRIFT" for r in rep["results"]) or rep["problems"] else 0)


if __name__ == "__main__":
    main()
