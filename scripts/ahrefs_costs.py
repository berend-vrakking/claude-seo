#!/usr/bin/env python3
"""
Ahrefs API v3 / MCP unit estimation, approval, and budget tracking.

Ahrefs bills API units, not money. A request costs
    units = max(50, rows x per_row_cost)
where per_row_cost is the sum of the unique fields named in `select`, `where`
and `order_by`. Most fields cost 1 unit; the field costs below come from the
"(N units)" annotations in the Ahrefs OpenAPI spec (docs.ahrefs.com/openapi.json,
checked 2026-10-07). Some tools are free and some have a fixed cost.

Config: ~/.config/claude-seo/ahrefs-costs.json
Ledger: ~/.config/claude-seo/ahrefs-ledger.json
Set CLAUDE_SEO_CONFIG_DIR to point both somewhere else (used by the tests).

Usage:
    python ahrefs_costs.py estimate <tool> --rows N --select a,b [--where-fields x] [--order-by-fields y]
    python ahrefs_costs.py check <tool> --rows N --select a,b [--where-fields x] [--order-by-fields y]
    python ahrefs_costs.py log <tool> <units> [--note TEXT]
    python ahrefs_costs.py summary [--days N]
    python ahrefs_costs.py today
    python ahrefs_costs.py config [--mode always|threshold|none] [--threshold UNITS]
                                  [--daily-limit UNITS] [--plan lite|standard|advanced]
    python ahrefs_costs.py reset --confirm

<tool> is the MCP tool name (`site-explorer-organic-keywords`); a
`mcp__ahrefs__` prefix or an API path (`/site-explorer/organic-keywords`) is
accepted too. Output is always JSON.
"""

import argparse
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None

try:
    import msvcrt
except ImportError:
    msvcrt = None

CONFIG_DIR = Path(
    os.environ.get("CLAUDE_SEO_CONFIG_DIR") or Path.home() / ".config" / "claude-seo"
)
CONFIG_FILE = CONFIG_DIR / "ahrefs-costs.json"
LEDGER_FILE = CONFIG_DIR / "ahrefs-ledger.json"
LOCK_FILE = CONFIG_DIR / "ahrefs-ledger.lock"

MIN_UNITS = 50
DEFAULT_FIELD_UNITS = 1

# Fields the spec annotates with a cost above 1 unit (no field has two costs).
FIELD_UNITS = {
    **dict.fromkeys((
        "all_positions", "all_positions_prev", "all_time_refdomains", "class_c",
        "dofollow_refdomains", "live_refdomains", "refdomains", "refdomains_dofollow",
        "refdomains_nofollow", "refdomains_source", "refdomains_source_domain",
        "refdomains_target", "refdomains_target_domain", "referring_domains",
    ), 5),
    **dict.fromkeys((
        "ai_responses_chatgpt", "ai_responses_copilot", "ai_responses_gemini",
        "ai_responses_google_ai_mode", "ai_responses_google_ai_overviews",
        "ai_responses_grok", "ai_responses_perplexity", "difficulty", "global_volume",
        "intents", "keyword_difficulty", "keyword_difficulty_competitor",
        "keyword_difficulty_merged", "keyword_difficulty_prev",
        "keyword_difficulty_target", "linked_domain_traffic", "links", "org_cost",
        "org_traffic", "org_traffic_top_by_country", "paid_cost", "paid_traffic",
        "parent_volume", "range100_traffic", "range10k_plus_traffic", "range10k_traffic",
        "range1k_traffic", "range5k_traffic", "response", "sum_paid_traffic",
        "sum_paid_traffic_merged", "sum_paid_traffic_prev", "sum_traffic",
        "sum_traffic_merged", "sum_traffic_prev", "top_keyword_volume",
        "top_keyword_volume_prev", "total_search_volume", "traffic", "traffic_domain",
        "traffic_domain_source", "traffic_merged", "traffic_page", "traffic_potential",
        "traffic_prev", "traffic_source", "value", "value_merged", "value_prev", "volume",
        "volume_competitor", "volume_merged", "volume_monthly", "volume_prev",
        "volume_target",
    ), 10),
    **dict.fromkeys((
        "all_platforms", "chatgpt", "copilot", "gemini", "google_ai_mode",
        "google_ai_overviews", "google_ai_overviews_keywords", "grok", "perplexity",
    ), 15),
    "share_of_voice": 1,
}
# keywords-explorer-overview: 2 units per historical month (minimum 50 units).
HISTORY_FIELD = "volume_monthly_history"
HISTORY_UNITS_PER_MONTH = 2

FREE_PREFIXES = (
    "rank-tracker-", "management-", "public-", "subscription-info-", "gsc-",
    "web-analytics-", "social-media-",
)
FREE_TOOLS = {"doc", "site-audit-projects"}
FIXED_UNITS = {
    "site-audit-issues": 50,
    "site-audit-page-content": 50,
    "site-audit-page-explorer": 50,
    "content-helper-topics": 1000,
}
CONTENT_HELPER_TARGET_URL_UNITS = 500

KNOWN_FAMILIES = (
    "batch-analysis-", "brand-radar-", "content-helper-", "keywords-explorer-",
    "serp-overview-", "site-audit-", "site-explorer-",
) + FREE_PREFIXES

# Rows per request by plan (Ahrefs API v3 limits).
PLAN_ROW_CAPS = {"lite": 100, "standard": 250, "advanced": 500}

# Always ask before these, whatever the mode: large exports or fixed big costs.
WARN_TOOLS = {"site-explorer-all-backlinks", "content-helper-topics", "batch-analysis-batch-analysis"}

DEFAULT_CONFIG = {
    "mode": "threshold",
    "threshold": 2500,
    "daily_limit": 25000,
    "plan": "lite",
    "warn_tools": sorted(WARN_TOOLS),
}

_TOOL_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class LedgerError(RuntimeError):
    """The ledger could not be read or written safely."""


def normalize_tool(name):
    """Return the MCP tool name for a tool name, mcp__ahrefs__ name, or API path."""
    tool = name.strip()
    if tool.startswith("mcp__"):
        tool = tool.rsplit("__", 1)[-1]
    if tool.startswith("/"):
        tool = tool.strip("/").replace("/", "-")
    return tool


def _fields(csv):
    """Field names from a comma list, dropping `:asc`/`:desc` and blanks."""
    out = []
    for part in (csv or "").split(","):
        name = part.strip().split(":", 1)[0].strip()
        if name and name not in out:
            out.append(name)
    return out


def estimate_units(tool, rows=1, select="", where_fields="", order_by_fields="",
                   history_months=12, target_url=False):
    """Estimate the units one request costs. Pure; no I/O."""
    tool = normalize_tool(tool)
    if tool in FREE_TOOLS or tool.startswith(FREE_PREFIXES):
        return {"tool": tool, "pricing": "free", "units": 0}
    if tool in FIXED_UNITS:
        units = FIXED_UNITS[tool]
        if tool == "content-helper-topics" and target_url:
            units += CONTENT_HELPER_TARGET_URL_UNITS
        return {"tool": tool, "pricing": "fixed", "units": units}

    fields = _fields(",".join((select or "", where_fields or "", order_by_fields or "")))
    breakdown = {}
    for field in fields:
        if field == HISTORY_FIELD:
            breakdown[field] = HISTORY_UNITS_PER_MONTH * max(1, history_months)
        else:
            breakdown[field] = FIELD_UNITS.get(field, DEFAULT_FIELD_UNITS)
    per_row = sum(breakdown.values()) or DEFAULT_FIELD_UNITS
    rows = max(1, int(rows))
    return {
        "tool": tool,
        "pricing": "per_row",
        "rows": rows,
        "fields": breakdown,
        "per_row_units": per_row,
        "units": max(MIN_UNITS, rows * per_row),
    }


def is_known_tool(tool):
    tool = normalize_tool(tool)
    return bool(_TOOL_RE.match(tool)) and (tool in FREE_TOOLS or tool.startswith(KNOWN_FAMILIES))


def _load_config():
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg.update(json.load(f))
    return cfg


def _save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def _lock(handle, exclusive):
    """Advisory lock, blocking. Never runs unlocked (see dataforseo_costs.py)."""
    if fcntl is not None:
        fcntl.flock(handle, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
    elif msvcrt is not None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
    else:
        raise LedgerError("No file-locking primitive available; refusing to touch the ledger.")


def _unlock(handle):
    if fcntl is not None:
        fcntl.flock(handle, fcntl.LOCK_UN)
    elif msvcrt is not None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _read_ledger():
    if not LEDGER_FILE.exists():
        return {"entries": []}
    try:
        with open(LEDGER_FILE, encoding="utf-8") as f:
            ledger = json.load(f)
    except json.JSONDecodeError as exc:
        raise LedgerError(
            f"Unit ledger {LEDGER_FILE} is not valid JSON ({exc}). Refusing to continue "
            "from zero, which would under-report usage. Repair or remove it."
        ) from exc
    if not isinstance(ledger, dict) or not isinstance(ledger.get("entries"), list):
        raise LedgerError(f"Unit ledger {LEDGER_FILE} has no 'entries' list. Repair or remove it.")
    return ledger


def _write_ledger(ledger):
    fd, tmp_path = tempfile.mkstemp(dir=str(CONFIG_DIR), prefix=".ahrefs-ledger.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, LEDGER_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


@contextmanager
def _locked_ledger(write=False):
    """One lock across the whole read-modify-write, held on a separate .lock file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, "a+") as lock_handle:
        _lock(lock_handle, exclusive=write)
        try:
            ledger = _read_ledger()
            yield ledger
            if write:
                _write_ledger(ledger)
        finally:
            _unlock(lock_handle)


def _today_str():
    return datetime.now().strftime("%Y-%m-%d")


def _today_units(ledger):
    today = _today_str()
    return sum(e["units"] for e in ledger["entries"] if e["timestamp"].startswith(today))


def _estimate_from_args(args):
    return estimate_units(
        args.tool, rows=args.rows, select=args.select, where_fields=args.where_fields,
        order_by_fields=args.order_by_fields, history_months=args.history_months,
        target_url=args.target_url,
    )


def decide(est, cfg, today_units, known=True):
    """Return the check result for an estimate. Pure; no I/O."""
    units = est["units"]
    daily_limit = cfg.get("daily_limit", DEFAULT_CONFIG["daily_limit"])
    cap = PLAN_ROW_CAPS.get(str(cfg.get("plan", "lite")).lower())
    result = dict(est)
    result.update({
        "today_units": today_units,
        "daily_limit_units": daily_limit,
        "daily_remaining_units": daily_limit - today_units,
    })
    warnings = []
    if cap and est.get("rows", 0) > cap:
        warnings.append(
            f"rows {est['rows']} exceed the {cfg.get('plan')} plan cap of {cap} per request; "
            f"set limit={cap} or page with offset"
        )
    if warnings:
        result["warnings"] = warnings

    if units == 0:
        result["status"] = "approved"
        return result
    if today_units + units > daily_limit:
        result.update({
            "status": "blocked",
            "reason": "daily_limit_exceeded",
            "message": (
                f"Daily Ahrefs limit of {daily_limit} units would be exceeded "
                f"(today {today_units}, this call {units})."
            ),
        })
        return result

    reason = None
    if not known:
        reason = "unknown_tool"
    elif est["tool"] in cfg.get("warn_tools", WARN_TOOLS):
        reason = "warn_tool"
    elif cfg.get("mode") == "always":
        reason = "mode_always"
    elif cfg.get("mode", "threshold") == "threshold" and units >= cfg.get("threshold", 2500):
        reason = "above_threshold"
    if reason:
        result.update({
            "status": "needs_approval",
            "approval_reason": reason,
            "message": (
                f"This Ahrefs call costs about {units} units. Today: "
                f"{today_units}/{daily_limit}. Reason: {reason}. Proceed?"
            ),
        })
    else:
        result["status"] = "approved"
    return result


def cmd_estimate(args):
    est = _estimate_from_args(args)
    est["status"] = "estimated"
    if not is_known_tool(args.tool):
        est["warning"] = f"'{est['tool']}' is not a known Ahrefs tool family; check the name with doc."
    json.dump(est, sys.stdout, indent=2)


def cmd_check(args):
    with _locked_ledger() as ledger:
        today = _today_units(ledger)
    result = decide(_estimate_from_args(args), _load_config(), today, known=is_known_tool(args.tool))
    json.dump(result, sys.stdout, indent=2)


def cmd_log(args):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": normalize_tool(args.tool),
        "units": args.units,
    }
    if args.note:
        entry["note"] = args.note
    with _locked_ledger(write=True) as ledger:
        ledger["entries"].append(entry)
        today = _today_units(ledger)
    json.dump({"status": "logged", "entry": entry, "today_units": today}, sys.stdout, indent=2)


def cmd_summary(args):
    with _locked_ledger() as ledger:
        entries = list(ledger["entries"])
    cutoff = (datetime.now() - timedelta(days=args.days)).isoformat()
    recent = [e for e in entries if e["timestamp"] >= cutoff]
    by_day = {}
    for e in recent:
        day = by_day.setdefault(e["timestamp"][:10], {"units": 0, "calls": 0})
        day["units"] += e["units"]
        day["calls"] += 1
    json.dump({
        "status": "summary",
        "period_days": args.days,
        "daily_totals": dict(sorted(by_day.items())),
        "total_units": sum(e["units"] for e in recent),
        "total_calls": len(recent),
    }, sys.stdout, indent=2)


def cmd_today(args):
    with _locked_ledger() as ledger:
        entries = [e for e in ledger["entries"] if e["timestamp"].startswith(_today_str())]
    cfg = _load_config()
    by_tool = {}
    for e in entries:
        row = by_tool.setdefault(e["tool"], {"units": 0, "calls": 0})
        row["units"] += e["units"]
        row["calls"] += 1
    total = sum(e["units"] for e in entries)
    json.dump({
        "status": "today",
        "date": _today_str(),
        "total_units": total,
        "daily_limit_units": cfg["daily_limit"],
        "remaining_units": cfg["daily_limit"] - total,
        "calls": len(entries),
        "by_tool": by_tool,
    }, sys.stdout, indent=2)


def cmd_config(args):
    cfg = _load_config()
    changed = False
    for key in ("mode", "threshold", "daily_limit", "plan"):
        value = getattr(args, key)
        if value is not None:
            cfg[key] = value
            changed = True
    if changed:
        _save_config(cfg)
    json.dump({"status": "updated" if changed else "current", "config": cfg}, sys.stdout, indent=2)


def cmd_reset(args):
    if not args.confirm:
        json.dump({"status": "blocked", "message": "Reset requires --confirm."}, sys.stdout, indent=2)
        return
    today = _today_str()
    with _locked_ledger(write=True) as ledger:
        removed = [e for e in ledger["entries"] if e["timestamp"].startswith(today)]
        ledger["entries"] = [e for e in ledger["entries"] if not e["timestamp"].startswith(today)]
        ledger["entries"].append({
            "timestamp": datetime.now().isoformat(),
            "tool": "_audit_reset",
            "units": 0,
            "note": f"Reset cleared {len(removed)} entries totaling {sum(e['units'] for e in removed)} units",
        })
    json.dump({
        "status": "reset",
        "date": today,
        "entries_removed": len(removed),
        "units_cleared": sum(e["units"] for e in removed),
    }, sys.stdout, indent=2)


def _add_estimate_args(parser):
    parser.add_argument("tool", help="Ahrefs MCP tool name, e.g. site-explorer-organic-keywords")
    parser.add_argument("--rows", type=int, default=1, help="Rows requested (the limit parameter)")
    parser.add_argument("--select", default="", help="Comma-separated select fields")
    parser.add_argument("--where-fields", default="", dest="where_fields",
                        help="Comma-separated fields used in where")
    parser.add_argument("--order-by-fields", default="", dest="order_by_fields",
                        help="Comma-separated order_by fields (:asc/:desc allowed)")
    parser.add_argument("--history-months", type=int, default=12, dest="history_months",
                        help="Months requested for volume_monthly_history")
    parser.add_argument("--target-url", action="store_true", dest="target_url",
                        help="content-helper-topics: a target_url is scored (+500 units)")


def main():
    parser = argparse.ArgumentParser(description="Ahrefs API unit estimation and budget tracking")
    sub = parser.add_subparsers(dest="command", required=True)

    _add_estimate_args(sub.add_parser("estimate", help="Estimate units for one request"))
    _add_estimate_args(sub.add_parser("check", help="Check whether a request may run"))

    p_log = sub.add_parser("log", help="Log the units a live call consumed")
    p_log.add_argument("tool")
    p_log.add_argument("units", type=int)
    p_log.add_argument("--note")

    p_sum = sub.add_parser("summary", help="Units used over recent days")
    p_sum.add_argument("--days", type=int, default=7)

    sub.add_parser("today", help="Units used today")

    p_cfg = sub.add_parser("config", help="View or update configuration")
    p_cfg.add_argument("--mode", choices=["always", "threshold", "none"])
    p_cfg.add_argument("--threshold", type=int, help="Units per call that need approval")
    p_cfg.add_argument("--daily-limit", type=int, dest="daily_limit", help="Units per day")
    p_cfg.add_argument("--plan", choices=sorted(PLAN_ROW_CAPS), help="Ahrefs plan (row cap)")

    p_reset = sub.add_parser("reset", help="Clear today's ledger entries")
    p_reset.add_argument("--confirm", action="store_true")

    args = parser.parse_args()
    dispatch = {
        "estimate": cmd_estimate, "check": cmd_check, "log": cmd_log, "summary": cmd_summary,
        "today": cmd_today, "config": cmd_config, "reset": cmd_reset,
    }
    try:
        dispatch[args.command](args)
    except LedgerError as exc:
        json.dump({"status": "error", "message": str(exc)}, sys.stdout, indent=2)
        sys.exit(1)


if __name__ == "__main__":
    main()
