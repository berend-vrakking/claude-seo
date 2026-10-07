# Ahrefs Cost Tiers

Units per request = `max(50, rows x per-row cost)`. Per-row cost = sum of the
unique fields across `select`, `where` and `order_by` (1 unit unless marked 5
or 10; see `${CLAUDE_PLUGIN_ROOT}/skills/seo/references/ahrefs.md`). Run
`ahrefs_costs.py estimate` for the exact number before a new pattern.

## Worked estimates (limit 100 unless noted)

| Command | Fields | Per row | Units |
|---|---|---|---|
| metrics | metrics + domain-rating + backlinks-stats, one row each | n/a | ~150 |
| volume (20 keywords) | keyword, volume, difficulty, cpc, traffic_potential, intents | 1+10+10+1+10+10 = 42 | 840 |
| keywords (ideas) | keyword, volume, difficulty | 21 | 2,100 |
| serp (top 10) | position, url, title, type, domain_rating, url_rating, page_type | 7 | 70 |
| serp with traffic | + traffic | 17 | 170 |
| organic | keyword, best_position, best_position_url, volume, sum_traffic | 23 | 2,300 |
| top-pages | url, sum_traffic, keywords, top_keyword, top_keyword_best_position | 14 | 1,400 |
| competitors (limit 20) | competitor_domain, keywords_common, keywords_competitor, share, domain_rating | 5 | 100 |
| refdomains | domain, domain_rating, dofollow_links, links_to_target, first_seen, last_seen, is_spam | 7 | 700 |
| refdomains + traffic | + traffic_domain | 17 | 1,700 |
| backlinks (1 per domain) | url_from, url_to, anchor, domain_rating_source, is_dofollow, first_seen, last_seen | 7 | 700 |
| anchors | anchor, refdomains, links_to_target, dofollow_links | 8 | 800 |
| batch (10 domains) | domain_rating, refdomains, org_traffic, org_keywords | 17 | 170 |
| content | fixed | n/a | 1,000 |

## Cheaper alternatives

- Need a count, not a list? Use the fixed-row tools (`backlinks-stats`,
  `metrics`, `domain-rating`): 50 units each.
- Comparing many domains: one `batch-analysis` call instead of N `metrics` calls.
- Sorting by a 10-unit field adds it to every row. Sort by a 1-unit proxy
  (`domain_rating`, `best_position`) when the order is only for triage.
- Drop `traffic_domain`, `traffic`, `value` and `*_prev` unless the answer
  needs them; they are the expensive columns.
- Questions about change over time: `mcp__openseo__ahrefs_history` (stored
  rows, free) before a second paid snapshot.
- Cached results cost nothing; repeat calls with identical arguments hit the
  cache when it is installed.

## Budget presets (`ahrefs_costs.py config`)

| Preset | `--threshold` | `--daily-limit` | Fits |
|---|---|---|---|
| Careful (default) | 2,500 | 25,000 | Lite plan, a few analyses a day |
| Working | 5,000 | 75,000 | Standard plan, regular audits |
| Open | 10,000 | 200,000 | Advanced plan, bulk research |

These are local guardrails, not Ahrefs limits. Check the real monthly
allowance with `subscription-info-limits-and-usage` and set `--plan` so the
gate warns when `limit` exceeds the plan's row cap.
