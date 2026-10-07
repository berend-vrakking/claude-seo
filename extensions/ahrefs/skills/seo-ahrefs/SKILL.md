---
name: seo-ahrefs
description: >
  Live SEO data via the Ahrefs MCP server: keyword research and keyword
  metrics (volume, difficulty, CPC, intent, traffic potential), SERP
  overviews, ranked keywords, top pages, organic competitors, backlinks,
  referring domains, anchors, broken links, history trends and bulk domain
  comparison, with a unit cost gate. Primary data source for keyword, SERP
  and link data. Use when user says "ahrefs", "keyword volume", "keyword
  difficulty", "ranked keywords", "referring domains", "backlink data",
  "competitor keywords", "SERP data", or "domain rating".
user-invocable: true
argument-hint: "[command] [query]"
license: MIT
compatibility: "Requires the Ahrefs MCP server (remote https://api.ahrefs.com/mcp/mcp, registered as `ahrefs`)"
metadata:
  author: AgriciDaniel
  version: "2.4.2"
  category: seo
---

# Ahrefs: Live SEO Data (Extension)

Live keyword, SERP, ranking, competitor and link data through the Ahrefs MCP
server. This is the Ahrefs counterpart of `seo-dataforseo` and the primary data
source the other skills call for keyword research, keyword metrics, SERPs,
backlinks, referring domains, competitors and ranked keywords.

Load `${CLAUDE_PLUGIN_ROOT}/skills/seo/references/ahrefs.md` before the first
call. It covers the availability check, parameter rules, unit cost model and
the cache layer every Ahrefs call follows. Load `references/tool-catalog.md`
for the exact tool, parameters and `select` fields per command.

## Prerequisites

The `ahrefs` MCP server must be connected. It is a remote HTTP server
(`https://api.ahrefs.com/mcp/mcp`, `Authorization: Bearer <MCP key>`), set up
in a project `.mcp.json` or by `extensions/ahrefs/install.sh`.

**Check availability first.** If no `mcp__ahrefs__*` tool is present in this
session, say that Ahrefs is not connected, point to
`extensions/ahrefs/docs/AHREFS-SETUP.md`, and offer the fallback: WebSearch for
SERPs and keyword ideas, `/seo backlinks` free sources for link data.

## Cost Guardrails

Ahrefs bills API units: `max(50, rows x per-row cost)` per request, where
volume, traffic, difficulty and value fields cost 10 units per row and
referring-domain counts 5. **Before every paid call**, run:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run ahrefs_costs.py check <tool> --rows <limit> --select <fields> [--where-fields x] [--order-by-fields y]
```

- `approved`: proceed.
- `needs_approval`: show the unit estimate and today's usage; ask before calling.
- `blocked`: daily unit limit reached; do not call. Offer the fallback.

After a live call, log it: `... ahrefs_costs.py log <tool> <units>`. A result
served from the cache cost nothing; do not log it.

Unit management:
- `/seo ahrefs usage`: `mcp__ahrefs__subscription-info-limits-and-usage` (free): units used and left this month
- `/seo ahrefs costs today` / `costs summary`: `ahrefs_costs.py today` / `summary`
- `/seo ahrefs costs config --threshold 2500 --daily-limit 25000 --plan lite`

Keep `limit` at the plan cap or lower (Lite 100, Standard 250, Advanced 500)
and select only the fields the answer needs. Load `references/cost-tiers.md`
for worked estimates and cheaper alternatives per command.

## Quick Reference

| Command | Tool(s) |
|---------|---------|
| `/seo ahrefs metrics <domain>` | `site-explorer-metrics`, `site-explorer-domain-rating`, `site-explorer-backlinks-stats` |
| `/seo ahrefs volume <kw1,kw2,...>` | `keywords-explorer-overview` |
| `/seo ahrefs keywords <seed>` | `keywords-explorer-matching-terms`, `keywords-explorer-related-terms`, `keywords-explorer-search-suggestions` |
| `/seo ahrefs questions <seed>` | `keywords-explorer-matching-terms` with `terms=questions` |
| `/seo ahrefs trend <keyword>` | `keywords-explorer-volume-history`, `keywords-explorer-volume-by-country` |
| `/seo ahrefs serp <keyword>` | `serp-overview-serp-overview` |
| `/seo ahrefs organic <domain>` | `site-explorer-organic-keywords` (ranked keywords) |
| `/seo ahrefs top-pages <domain>` | `site-explorer-top-pages` |
| `/seo ahrefs competitors <domain>` | `site-explorer-organic-competitors` |
| `/seo ahrefs keyword-gap <domain> <competitor>` | `site-explorer-organic-keywords` for both |
| `/seo ahrefs backlinks <domain>` | `site-explorer-all-backlinks`, `site-explorer-anchors` |
| `/seo ahrefs refdomains <domain>` | `site-explorer-refdomains` |
| `/seo ahrefs link-gap <domain> <competitor>` | `site-explorer-refdomains` for both |
| `/seo ahrefs broken <domain>` | `site-explorer-broken-backlinks`, `site-explorer-pages-by-backlinks` |
| `/seo ahrefs history <domain>` | `mcp__openseo__ahrefs_history` first, else `site-explorer-metrics-history`, `site-explorer-refdomains-history`, `site-explorer-domain-rating-history` |
| `/seo ahrefs batch <domain1> <domain2> ...` | `batch-analysis-batch-analysis` |
| `/seo ahrefs content <keyword>` | `content-helper-topics` (1000 units; always ask first) |
| `/seo ahrefs usage` | `subscription-info-limits-and-usage` (free) |

Defaults: `country=us` unless the user or site says otherwise, `mode=subdomains`
for domains and `exact` for single URLs, `date` = today, `limit=100`.

## Commands

### metrics: domain overview
One row each from `site-explorer-metrics` (`org_traffic`, `org_keywords`,
`org_keywords_1_3`, `org_cost`), `site-explorer-domain-rating` (`domain_rating`,
`ahrefs_rank`) and `site-explorer-backlinks-stats` (`live`, `live_refdomains`).
About 150 units. Output a metric card with DR, referring domains, organic
keywords, traffic and traffic value.

### volume / keywords / questions / trend: keyword research
`keywords-explorer-overview` takes up to a comma-separated list of keywords per
call; batch instead of looping. Ideas come from `matching-terms` (`match_mode`
`terms` or `phrase`), `related-terms` (`also_rank_for`, `also_talk_about`) and
`search-suggestions`. Report volume, difficulty, CPC, traffic potential,
intent and parent topic; group ideas by parent topic.

### serp: SERP overview
`serp-overview-serp-overview` with `top_positions=10`. Report position, URL,
title, `type` (organic, snippet, video, image, ai_overview, local_pack...),
DR / UR and page type, plus the snapshot `update_date`. This is Ahrefs' stored
SERP, not a live fetch: if no positions come back, use WebSearch for that
keyword and label it.

### organic / top-pages / competitors / keyword-gap
`site-explorer-organic-keywords` ordered by `sum_traffic:desc` gives ranked
keywords with best position and URL; add `date_compared` for movers.
`site-explorer-top-pages` ranks pages by traffic. `site-explorer-organic-competitors`
lists domains sharing keywords. Keyword gap: pull the competitor's ranked
keywords, then the target's for the same set (`where` on `keyword`), and list
keywords where the competitor is in the top 10 and the target is absent or
below 20.

### backlinks / refdomains / link-gap / broken
`site-explorer-all-backlinks` with `aggregation=1_per_domain` and
`history=live` for one best link per domain; `site-explorer-anchors` for the
anchor distribution; `site-explorer-refdomains` for DR, dofollow links,
first/last seen and `is_spam`. Link gap: refdomains of the competitor minus
refdomains of the target. Broken: `site-explorer-broken-backlinks` plus
`site-explorer-pages-by-backlinks` filtered to non-200 `http_code_target`
(redirect candidates). For a scored backlink health report, hand the data to
`seo-backlinks`.

### history: what changed
Prefer stored rows: `mcp__openseo__ahrefs_history` (see the shared reference)
when the cache layer is present. Otherwise the `*-history` tools take
`date_from` (and `history_grouping`: daily, weekly or monthly).

### batch: compare many domains
`batch-analysis-batch-analysis` takes up to 100 `targets` (`{url, mode,
protocol}`) and a `select` array (`domain_rating`, `refdomains`, `org_traffic`,
`org_keywords`). Use it for competitor sets instead of one `metrics` call per domain.

## Cross-Skill Integration

| Skill | Uses |
|---|---|
| `seo-backlinks` | refdomains, anchors, all-backlinks, broken-backlinks, refdomains-history (primary source, confidence 1.00) |
| `seo-cluster` | serp-overview for SERP overlap, matching-terms / related-terms for expansion |
| `seo-sxo` | serp-overview for page-type analysis, keywords-explorer-overview for volume |
| `seo-content-brief`, `seo-content` | keywords-explorer-overview, matching-terms (questions), serp-overview, top-pages |
| `seo-plan` | organic-competitors, batch-analysis, organic-keywords, keywords-explorer |
| `seo-page` | organic-keywords (`mode=exact`), backlinks-stats for the URL |
| `seo-images` | serp-overview with `type=image,image_th` |
| `seo-ecommerce` | organic-keywords for the organic side of the gap analysis |
| `seo-audit` | spawns the `seo-ahrefs` agent for authority, rankings and competitor context |

## Error Handling

| Situation | Action |
|---|---|
| No `mcp__ahrefs__*` tools | Report "Ahrefs not connected", link the setup doc, use the fallback |
| Call denied with "Served from the Product Metrics Ahrefs cache" | Success. Use the attached result or `mcp__openseo__ahrefs_cached_result` |
| 401 / 403 | Key missing, revoked, or plan lacks API access. Do not retry |
| 429 | Rate limit (60/min). Wait, then retry once |
| 400 on a field | Wrong `select` / `where` name. Call `mcp__ahrefs__doc` for the tool and fix it |
| Empty result | Report "no data in Ahrefs for this target", not zero. Small sites and new keywords often have none |

## Output

Tables for comparisons, scores as XX/100 where defined, priorities Critical >
High > Medium > Low. Label every number "Ahrefs (live)" or "Ahrefs (cached,
fetched YYYY-MM-DD)" and give the country and date it describes.
