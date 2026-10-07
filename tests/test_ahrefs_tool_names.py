"""Every Ahrefs MCP tool a skill or agent names must exist in the Ahrefs API.

tests/fixtures/ahrefs_api_v3_tools.txt lists the Ahrefs MCP tool names: each
API v3 path from https://docs.ahrefs.com/openapi.json with `/` replaced by
`-`, plus `doc`. The DataForSEO port taught that skills naming tools the server
does not have send the model after tools that never exist (#317); this is the
same guard for Ahrefs. Refresh the fixture when Ahrefs adds or renames paths.

Also pins the seo-ahrefs agent permissions and the extension mirrors.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "ahrefs_api_v3_tools.txt"
FAMILIES = (
    "batch-analysis", "brand-radar", "content-helper", "gsc", "keywords-explorer",
    "management", "public", "rank-tracker", "serp-overview", "site-audit",
    "site-explorer", "social-media", "subscription-info", "web-analytics",
)
# A full MCP name, or a backticked bare tool name from a known family.
PREFIXED_RE = re.compile(r"mcp__ahrefs__([a-z0-9-]+)")
BARE_RE = re.compile(r"`((?:" + "|".join(FAMILIES) + r")-[a-z0-9-]*[a-z0-9])`")
# Names that match a family prefix but are not Ahrefs tools (seo-google report types).
NOT_AHREFS = {"gsc-performance"}
OPENSEO_AHREFS_TOOLS = (
    "mcp__openseo__ahrefs_cached_result",
    "mcp__openseo__ahrefs_cache_bypass",
    "mcp__openseo__ahrefs_history",
)
AGENTS = (ROOT / "agents" / "seo-ahrefs.md", ROOT / "extensions" / "ahrefs" / "agents" / "seo-ahrefs.md")


def _tools() -> set[str]:
    lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def _docs() -> list[Path]:
    return [*ROOT.glob("skills/**/*.md"), *ROOT.glob("agents/*.md"),
            *ROOT.glob("extensions/*/skills/**/*.md"), *ROOT.glob("extensions/*/agents/*.md"),
            *ROOT.glob("extensions/ahrefs/docs/*.md"), ROOT / "docs" / "COMMANDS.md"]


def test_fixture_has_every_api_path() -> None:
    assert len(_tools()) == 133


def test_every_referenced_ahrefs_tool_exists() -> None:
    tools = _tools()
    missing = []
    for path in _docs():
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for name in [*PREFIXED_RE.findall(line), *BARE_RE.findall(line)]:
                if name not in tools and name not in NOT_AHREFS:
                    missing.append(f"{path.relative_to(ROOT)}:{line_no}: {name}")
    assert not missing, "not Ahrefs API v3 tools:\n" + "\n".join(missing)


def test_seo_ahrefs_agent_grants_ahrefs_and_cache_tools_without_bash() -> None:
    for path in AGENTS:
        frontmatter = path.read_text(encoding="utf-8").split("---", 2)[1]
        tools_line = next(line for line in frontmatter.splitlines() if line.startswith("tools:"))
        assert "mcp__ahrefs__*" in tools_line
        for tool in OPENSEO_AHREFS_TOOLS:
            assert tool in tools_line, f"{path.name}: missing {tool}"
        assert "Bash" not in tools_line


def test_seo_ahrefs_agent_fails_closed_without_mcp() -> None:
    for path in AGENTS:
        text = path.read_text(encoding="utf-8")
        for phrase in ("fail closed", "Never inspect credential or",
                       "never bypass MCP with curl, raw HTTP, or another client"):
            assert phrase in text, f"{path.name}: missing {phrase!r}"


def test_seo_ahrefs_mirrors_are_identical() -> None:
    assert AGENTS[0].read_text(encoding="utf-8") == AGENTS[1].read_text(encoding="utf-8")
    core = ROOT / "skills" / "seo-ahrefs"
    mirror = ROOT / "extensions" / "ahrefs" / "skills" / "seo-ahrefs"
    core_files = sorted(p.relative_to(core) for p in core.rglob("*.md"))
    assert core_files == sorted(p.relative_to(mirror) for p in mirror.rglob("*.md"))
    for rel in core_files:
        assert (core / rel).read_text(encoding="utf-8") == (mirror / rel).read_text(encoding="utf-8"), rel


def test_agents_that_call_ahrefs_are_granted_it() -> None:
    """An agent whose body names an Ahrefs tool must list the server in tools:."""
    offenders = []
    for path in [*ROOT.glob("agents/*.md"), *ROOT.glob("extensions/*/agents/*.md")]:
        _, frontmatter, body = path.read_text(encoding="utf-8").split("---", 2)
        tools_line = next((line for line in frontmatter.splitlines() if line.startswith("tools:")), "")
        named = [*PREFIXED_RE.findall(body), *BARE_RE.findall(body)]
        if any(name not in NOT_AHREFS for name in named):
            if "mcp__ahrefs__*" not in tools_line:
                offenders.append(str(path.relative_to(ROOT)))
        for tool in OPENSEO_AHREFS_TOOLS:
            if tool in body and tool not in tools_line:
                offenders.append(f"{path.relative_to(ROOT)}: {tool}")
    assert not offenders, offenders
