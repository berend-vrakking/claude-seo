# Ahrefs extension setup

Connects the official remote Ahrefs MCP server
(`https://api.ahrefs.com/mcp/mcp`) so the `seo-ahrefs` skill, the
`seo-ahrefs` agent and the ported skills (backlinks, cluster, SXO, content
brief, content, plan, page, images, audit) read live Ahrefs data. Ahrefs is
the primary source for keyword research, keyword metrics, SERPs, backlinks,
referring domains, competitors and ranked keywords. Without it those skills
fall back to WebSearch and the free backlink sources.

The server must be registered under the name `ahrefs`, so its tools appear as
`mcp__ahrefs__<tool>` (API v3 path with `/` replaced by `-`, e.g.
`mcp__ahrefs__site-explorer-organic-keywords`).

## Option A: project config (recommended for teams)

If your project already registers the server in `.mcp.json`, nothing else is
needed. The entry looks like this; keep the key in an environment variable,
not in the file:

```json
{
  "mcpServers": {
    "ahrefs": {
      "type": "http",
      "url": "https://api.ahrefs.com/mcp/mcp",
      "headers": { "Authorization": "Bearer ${AHREFS_MCP_KEY}" }
    }
  }
}
```

The plugin's own `skills/seo-ahrefs/` and `agents/seo-ahrefs.md` ship with
claude-seo, so plugin installs need no extension installer either.

## Option B: user config (installer)

```bash
./extensions/ahrefs/install.sh        # Linux / macOS
.\extensions\ahrefs\install.ps1       # Windows PowerShell
```

The installer:

1. Prompts for your Ahrefs MCP key (input is hidden).
2. Copies `skills/seo-ahrefs/` (with `references/`) into
   `~/.claude/skills/seo-ahrefs/` and `agents/seo-ahrefs.md` into
   `~/.claude/agents/` for manual (non-plugin) installs.
3. Atomically writes `mcpServers.ahrefs` into `~/.claude.json` as a remote
   HTTP server with an `Authorization: Bearer <key>` header. The file is
   `chmod 0o600` after the merge on Linux / macOS. The key travels through
   the environment, never the command line.

No Node.js is needed: the server is remote.

## Verify

Open a new Claude Code session, check that `mcp__ahrefs__*` tools are listed
(`/mcp`), then:

```
/seo ahrefs usage                 # free: units used and left this month
/seo ahrefs metrics example.com
```

## Units and cost gate

Ahrefs bills API units per request: `max(50, rows x per-row cost)`, where the
per-row cost sums the fields requested in `select`, `where` and `order_by`
(most fields 1 unit; volume, traffic, difficulty and value fields 10;
referring-domain counts 5). Rank Tracker, GSC, Management, Public and
subscription-info tools are free. Row caps per request: Lite 100, Standard
250, Advanced 500. Rate limit: 60 requests per minute.

Every skill runs the gate before a paid call:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run ahrefs_costs.py check site-explorer-refdomains --rows 100 --select domain,domain_rating
"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run ahrefs_costs.py config --threshold 2500 --daily-limit 25000 --plan lite
"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run ahrefs_costs.py today
```

Config and ledger live in `~/.config/claude-seo/ahrefs-costs.json` and
`ahrefs-ledger.json`. Worked estimates: `skills/seo-ahrefs/references/cost-tiers.md`.

## Product Metrics cache layer (optional)

If Claude Code hooks route Ahrefs calls through the OpenSEO cache, a call may
be denied with "Served from the Product Metrics Ahrefs cache". Skills treat
that as success and read the result from the hook context or
`mcp__openseo__ahrefs_cached_result`. See
`skills/seo/references/ahrefs.md` section 4.

## Rotate the key

Re-run the installer (Option B) or update the environment variable (Option A).

## Uninstall

```bash
./extensions/ahrefs/uninstall.sh    # removes the skill, the agent and the MCP entry
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| No `mcp__ahrefs__*` tools in `/mcp` | Server not registered as `ahrefs`, or session started before the change | Check the server name; start a new session |
| 401 / 403 on every call | Key missing, revoked, or the plan lacks API access | Create a new key in Ahrefs account settings; re-run the installer |
| 400 naming a field | `select` / `where` field not valid for that tool | Call `mcp__ahrefs__doc` for the tool; see `references/tool-catalog.md` |
| 429 | More than 60 requests per minute | Wait a minute; batch keywords and domains |
| Calls held by seo-cockpit | The companion plugin asks before paid MCP calls | Choose "run once" or "allow until reload" |
