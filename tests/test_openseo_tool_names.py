"""OpenSEO MCP tools named by skills and agents must exist, and be granted.

OpenSEO is the shared back end (project memory, reports, saved keywords,
crawler) behind the Claude SEO skills. tests/fixtures/openseo_mcp_tools.txt
lists the tool names the OpenSEO MCP server registers; refresh it when
OpenSEO adds or renames a tool.

Search Console and GA4 stay on Claude SEO's own Google connection, so no
skill or agent may route them through OpenSEO's Google tools.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "openseo_mcp_tools.txt"
# A trailing `_*` is a family wildcard in prose, not a tool name.
TOOL_RE = re.compile(r"mcp__openseo__([a-z_]+[a-z])(?![a-z_*])")
GOOGLE_VIA_OPENSEO = re.compile(
    r"mcp__openseo__(?:get_search_console_\w+|inspect_urls|get_search_opportunities|get_google_analytics_\w+)"
)


def _tools() -> set[str]:
    lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def _docs() -> list[Path]:
    return [*ROOT.glob("skills/**/*.md"), *ROOT.glob("agents/*.md"),
            *ROOT.glob("extensions/*/skills/**/*.md"), *ROOT.glob("extensions/*/agents/*.md"),
            *ROOT.glob("extensions/*/docs/*.md"), ROOT / "README.md"]


def test_every_referenced_openseo_tool_exists() -> None:
    tools = _tools()
    missing = [
        f"{path.relative_to(ROOT)}:{n}: {name}"
        for path in _docs()
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        for name in TOOL_RE.findall(line)
        if name not in tools
    ]
    assert not missing, "not OpenSEO tools:\n" + "\n".join(missing)


def test_google_data_does_not_route_through_openseo() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{n}"
        for path in _docs()
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if GOOGLE_VIA_OPENSEO.search(line)
    ]
    assert not offenders, offenders


def test_agents_are_granted_the_openseo_tools_they_name() -> None:
    offenders = []
    for path in [*ROOT.glob("agents/*.md"), *ROOT.glob("extensions/*/agents/*.md")]:
        _, frontmatter, body = path.read_text(encoding="utf-8").split("---", 2)
        tools_line = next((line for line in frontmatter.splitlines() if line.startswith("tools:")), "")
        for name in sorted(set(TOOL_RE.findall(body))):
            if f"mcp__openseo__{name}" not in tools_line:
                offenders.append(f"{path.relative_to(ROOT)}: mcp__openseo__{name}")
    assert not offenders, offenders


def test_shared_reference_keeps_the_fallback_rule() -> None:
    text = (ROOT / "skills" / "seo" / "references" / "openseo.md").read_text(encoding="utf-8")
    assert "skip this whole file" in text
    assert "Never block on OpenSEO" in text
