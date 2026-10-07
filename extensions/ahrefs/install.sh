#!/usr/bin/env bash
# Claude SEO: Ahrefs extension installer.
#
# Registers the official remote Ahrefs MCP server
# (https://api.ahrefs.com/mcp/mcp, Authorization: Bearer <MCP key>) in
# ~/.claude.json and copies the seo-ahrefs mirror skill and agent into
# ~/.claude/. Skip the MCP step if your project's .mcp.json already
# registers a server named "ahrefs": the skills only need the tools.
#
# Prereq: an Ahrefs MCP / API v3 key (Ahrefs account settings).
set -euo pipefail

main() {
    SKILL_DIR="${HOME}/.claude/skills"
    # MCP servers live in ~/.claude.json (the file `claude mcp add` writes).
    # NOT ~/.claude/settings.json - `mcpServers` is not a key Claude Code reads
    # there, so entries written to settings.json silently never load.
    MCP_CONFIG_JSON="${HOME}/.claude.json"

    echo "════════════════════════════════════════"
    echo "║   Claude SEO: Ahrefs extension       ║"
    echo "════════════════════════════════════════"

    command -v python3 >/dev/null 2>&1 || {
        echo "✗ Python 3 required."; exit 1;
    }

    if [ ! -d "${SKILL_DIR}/seo" ]; then
        echo "✗ claude-seo base plugin not installed."
        echo "  Install it first: curl -fsSL https://raw.githubusercontent.com/AgriciDaniel/claude-seo/main/install.sh | bash"
        exit 1
    fi

    # Locate this script's directory so the call works for both
    # `./install.sh` and `curl | bash` invocations.
    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" >/dev/null 2>&1 && pwd)"

    read -rsp "Ahrefs MCP key: " AHREFS_TOKEN
    echo
    if [ -z "${AHREFS_TOKEN}" ]; then
        echo "✗ No token provided."; exit 1;
    fi

    mkdir -p "${SKILL_DIR}/seo-ahrefs/references" "${HOME}/.claude/agents"
    cp "${SOURCE_DIR}/skills/seo-ahrefs/SKILL.md" "${SKILL_DIR}/seo-ahrefs/SKILL.md"
    cp "${SOURCE_DIR}/skills/seo-ahrefs/references/"*.md "${SKILL_DIR}/seo-ahrefs/references/"
    cp "${SOURCE_DIR}/agents/seo-ahrefs.md" "${HOME}/.claude/agents/seo-ahrefs.md"
    echo "✓ Installed skill: ${SKILL_DIR}/seo-ahrefs/"
    echo "✓ Installed agent: ${HOME}/.claude/agents/seo-ahrefs.md"

    # Merge MCP config into ~/.claude.json atomically.
    mkdir -p "$(dirname "${MCP_CONFIG_JSON}")"
    CLAUDE_SEO_SECRET="${AHREFS_TOKEN}" python3 - "${MCP_CONFIG_JSON}" <<'PY'
import json
import os
import sys
import tempfile

# The token arrives in the environment, not argv: argv is visible to other
# local users through ps, the environment is not.
path, token = sys.argv[1], os.environ["CLAUDE_SEO_SECRET"]
data = {}
if os.path.exists(path):
    try:
        with open(path) as fh:
            data = json.load(fh)
    except json.JSONDecodeError:
        sys.exit(f"✗ {path} is not valid JSON. Nothing was changed; fix it and rerun.")
data.setdefault("mcpServers", {})["ahrefs"] = {
    "type": "http",
    "url": "https://api.ahrefs.com/mcp/mcp",
    "headers": {"Authorization": f"Bearer {token}"},
}
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".",
                          prefix=".settings.", suffix=".json")
try:
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
except Exception:
    if os.path.exists(tmp):
        os.unlink(tmp)
    raise
print(f"✓ Wrote mcpServers.ahrefs to {path}")
PY

    echo
    echo "Done. Open a new Claude Code session and run:"
    echo "  /seo ahrefs metrics example.com"
    echo
    echo "Full docs: extensions/ahrefs/docs/AHREFS-SETUP.md"
}

main "$@"
