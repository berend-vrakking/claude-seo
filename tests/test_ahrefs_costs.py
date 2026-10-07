"""
Tests for scripts/ahrefs_costs.py: unit estimation, the approval gate, and
ledger integrity.

Ahrefs bills `max(50, rows x per-row cost)` units per request, where the
per-row cost sums the unique fields across select, where and order_by. Every
CLI test runs against an isolated CLAUDE_SEO_CONFIG_DIR, never the real
~/.config/claude-seo/ ledger.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO / "scripts" / "ahrefs_costs.py"
sys.path.insert(0, str(_REPO / "scripts"))

import ahrefs_costs as ac  # noqa: E402


def _run(config_dir: Path, *argv: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["CLAUDE_SEO_CONFIG_DIR"] = str(config_dir)
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *argv], capture_output=True, text=True, env=env,
    )


def _json(proc: subprocess.CompletedProcess) -> dict:
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


# ---------------------------------------------------------------------------
# estimation (pure)
# ---------------------------------------------------------------------------


def test_per_row_cost_sums_unique_fields_across_select_where_and_order_by() -> None:
    est = ac.estimate_units(
        "site-explorer-organic-keywords",
        rows=100,
        select="keyword,best_position,volume,sum_traffic",
        where_fields="volume",
        order_by_fields="sum_traffic:desc",
    )
    # keyword 1 + best_position 1 + volume 10 + sum_traffic 10; repeats count once.
    assert est["per_row_units"] == 22
    assert est["units"] == 2200


def test_minimum_charge_is_fifty_units() -> None:
    est = ac.estimate_units("site-explorer-domain-rating", rows=1, select="domain_rating")
    assert est["units"] == 50


def test_five_unit_fields_are_priced() -> None:
    est = ac.estimate_units("site-explorer-refdomains", rows=100, select="domain,refdomains")
    assert est["per_row_units"] == 6


@pytest.mark.parametrize("tool", [
    "rank-tracker-overview", "management-projects", "public-domain-rating-free",
    "subscription-info-limits-and-usage", "gsc-keywords", "web-analytics-stats", "doc",
    "site-audit-projects",
])
def test_free_tools_cost_nothing(tool: str) -> None:
    assert ac.estimate_units(tool, rows=500, select="volume")["units"] == 0


def test_fixed_cost_tools_ignore_rows() -> None:
    assert ac.estimate_units("site-audit-issues", rows=500)["units"] == 50
    assert ac.estimate_units("content-helper-topics")["units"] == 1000
    assert ac.estimate_units("content-helper-topics", target_url=True)["units"] == 1500


def test_volume_history_is_priced_per_month() -> None:
    est = ac.estimate_units(
        "keywords-explorer-overview", rows=1, select="keyword,volume_monthly_history",
        history_months=24,
    )
    assert est["per_row_units"] == 1 + 48


@pytest.mark.parametrize("name", [
    "mcp__ahrefs__site-explorer-top-pages", "/site-explorer/top-pages", "site-explorer-top-pages",
])
def test_tool_name_forms_normalize(name: str) -> None:
    assert ac.normalize_tool(name) == "site-explorer-top-pages"


def test_field_table_uses_only_the_spec_cost_tiers() -> None:
    # The spec annotates fields at 5, 10 or 15 units (share_of_voice: 1 per brand).
    for field, units in ac.FIELD_UNITS.items():
        assert field == field.strip().lower() and units in (1, 5, 10, 15), field


# ---------------------------------------------------------------------------
# approval gate (pure)
# ---------------------------------------------------------------------------


def _cfg(**kw):
    return {**ac.DEFAULT_CONFIG, **kw}


def test_small_call_is_approved() -> None:
    est = ac.estimate_units("keywords-explorer-overview", rows=10, select="keyword,volume")
    assert ac.decide(est, _cfg(), today_units=0)["status"] == "approved"


def test_call_above_threshold_needs_approval() -> None:
    est = ac.estimate_units("site-explorer-organic-keywords", rows=100,
                            select="keyword,volume,sum_traffic,keyword_difficulty")
    result = ac.decide(est, _cfg(threshold=2500), today_units=0)
    assert result["status"] == "needs_approval"
    assert result["approval_reason"] == "above_threshold"


def test_daily_limit_blocks() -> None:
    est = ac.estimate_units("site-explorer-refdomains", rows=100, select="domain,domain_rating")
    result = ac.decide(est, _cfg(daily_limit=1000), today_units=900)
    assert result["status"] == "blocked"
    assert result["reason"] == "daily_limit_exceeded"


def test_free_call_is_approved_even_at_the_daily_limit() -> None:
    est = ac.estimate_units("rank-tracker-overview", rows=100)
    assert ac.decide(est, _cfg(daily_limit=10), today_units=10)["status"] == "approved"


def test_warn_tool_always_needs_approval() -> None:
    est = ac.estimate_units("site-explorer-all-backlinks", rows=10, select="url_from")
    result = ac.decide(est, _cfg(mode="none"), today_units=0)
    assert result["approval_reason"] == "warn_tool"


def test_unknown_tool_needs_approval() -> None:
    est = ac.estimate_units("serp_organic_live_advanced", rows=10, select="url")
    result = ac.decide(est, _cfg(), today_units=0, known=ac.is_known_tool("serp_organic_live_advanced"))
    assert result["approval_reason"] == "unknown_tool"


def test_rows_above_the_plan_cap_warn() -> None:
    est = ac.estimate_units("site-explorer-top-pages", rows=250, select="url")
    result = ac.decide(est, _cfg(plan="lite"), today_units=0)
    assert any("plan cap of 100" in w for w in result["warnings"])
    assert "warnings" not in ac.decide(est, _cfg(plan="standard"), today_units=0)


# ---------------------------------------------------------------------------
# CLI and ledger
# ---------------------------------------------------------------------------


def test_cli_check_counts_logged_units(tmp_path: Path) -> None:
    _json(_run(tmp_path, "config", "--daily-limit", "1000"))
    _json(_run(tmp_path, "log", "site-explorer-metrics", "960", "--note", "metrics"))
    result = _json(_run(tmp_path, "check", "site-explorer-domain-rating", "--select", "domain_rating"))
    assert result["status"] == "blocked"
    assert _json(_run(tmp_path, "today"))["total_units"] == 960


def test_cli_estimate_reports_units(tmp_path: Path) -> None:
    result = _json(_run(tmp_path, "estimate", "mcp__ahrefs__keywords-explorer-overview",
                        "--rows", "20", "--select", "keyword,volume,difficulty,cpc"))
    assert result["tool"] == "keywords-explorer-overview"
    assert result["units"] == 20 * 22


def test_concurrent_logs_do_not_lose_entries(tmp_path: Path) -> None:
    calls = 16
    with ThreadPoolExecutor(max_workers=calls) as pool:
        results = list(pool.map(
            lambda i: _run(tmp_path, "log", "site-explorer-refdomains", "50", "--note", f"c{i}"),
            range(calls),
        ))
    assert all(r.returncode == 0 for r in results)
    entries = json.loads((tmp_path / "ahrefs-ledger.json").read_text())["entries"]
    assert len(entries) == calls


def test_corrupt_ledger_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "ahrefs-ledger.json").write_text("{not json")
    proc = _run(tmp_path, "check", "site-explorer-metrics")
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["status"] == "error"


def test_reset_requires_confirm(tmp_path: Path) -> None:
    _json(_run(tmp_path, "log", "site-explorer-metrics", "50"))
    assert _json(_run(tmp_path, "reset"))["status"] == "blocked"
    assert _json(_run(tmp_path, "reset", "--confirm"))["units_cleared"] == 50
