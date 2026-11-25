#!/usr/bin/env bash
# Install the WikiGuard overlay into a client repo: ./install.sh ../wattwise
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DST="$(cd "${1:?usage: install.sh <repo>}" && pwd)"

cp "$SRC/AGENTS.md" "$SRC/GUIDELINES.md" "$DST/"
mkdir -p "$DST/.agents" "$DST/.claude/skills" "$DST/.claude/agents" "$DST/.github/workflows" "$DST/tools/drift-check" "$DST/reports" "$DST/wiki/_proposals"
cp -R "$SRC/.agents/skills" "$DST/.agents/"
cp "$SRC/.claude/settings.json" "$DST/.claude/"
cp "$SRC/.claude/agents/"*.md "$DST/.claude/agents/"
cp "$SRC/.github/workflows/wikiguard.yml" "$DST/.github/workflows/"
cp "$SRC/tools/guard.py" "$SRC/tools/wikiguard_lint.py" "$DST/tools/"
cp "$SRC/tools/drift-check/drift_check.py" "$SRC/tools/drift-check/rules.json" "$SRC/tools/drift-check/README.md" "$DST/tools/drift-check/"
cp "$SRC/tools/test_wikiguard.py" "$DST/tests/"
for s in "$SRC"/.agents/skills/*/; do
  n="$(basename "$s")"; ln -sfn "../../.agents/skills/$n" "$DST/.claude/skills/$n"
done
echo "Installed into $DST. Try: python tools/drift-check/drift_check.py --repo ."
