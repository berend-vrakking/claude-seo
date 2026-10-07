# Ahrefs Tool Catalog

Exact tools, parameters and `select` fields per task, checked against the
Ahrefs API v3 OpenAPI spec (2026-10-07). MCP tool = `mcp__ahrefs__` + the
name below. `*` = required. Call `mcp__ahrefs__doc` for any tool not listed or
when a field is rejected. Calling rules and cache handling:
`${CLAUDE_PLUGIN_ROOT}/skills/seo/references/ahrefs.md`.

## Keywords Explorer

| Tool | Parameters | Useful `select` fields |
|---|---|---|
| `keywords-explorer-overview` | `select*`, `country*`, `keywords` (comma list) or `keyword_list_id`, `target` + `mode` + `target_position` (`in_top10`, `in_top100`), `volume_monthly_date_from/_to`, `where`, `order_by`, `limit` | `keyword`, `volume`, `global_volume`, `difficulty`, `cpc`, `cps`, `clicks`, `traffic_potential`, `intents`, `parent_topic`, `parent_volume`, `serp_features`, `first_seen`, `volume_monthly_history` |
| `keywords-explorer-matching-terms` | `select*`, `country*`, `keywords`, `terms` (`all`, `questions`), `match_mode` (`terms`, `phrase`), `where`, `order_by`, `limit` | `keyword`, `volume`, `difficulty`, `cpc`, `traffic_potential`, `intents`, `parent_topic`, `serp_features` |
| `keywords-explorer-related-terms` | same, with `terms` (`all`, `also_rank_for`, `also_talk_about`) and `view_for` (`top_10`, `top_100`) | same as matching-terms |
| `keywords-explorer-search-suggestions` | `select*`, `country*`, `keywords`, `where`, `order_by`, `limit` | same as matching-terms |
| `keywords-explorer-volume-history` | `keyword*`, `country*`, `date_from`, `date_to` | rows: `date`, `volume` |
| `keywords-explorer-volume-by-country` | `keyword*`, `limit` | rows: `country`, `volume` |

`intents` is an object (informational, navigational, commercial, transactional,
branded, local). `difficulty` is 0-100.

## SERP Overview

| Tool | Parameters | Useful `select` fields |
|---|---|---|
| `serp-overview-serp-overview` | `select*`, `keyword*`, `country*`, `top_positions`, `type` (comma list of SERP feature types), `date` (`YYYY-MM-DDThh:mm:ss`) | `position`, `url`, `title`, `type`, `page_type`, `domain_rating`, `url_rating`, `backlinks`, `refdomains`, `keywords`, `traffic`, `value`, `top_keyword`, `top_keyword_volume`, `update_date` |

`type` values include `organic`, `snippet`, `image`, `image_th`, `video`,
`video_th`, `question`, `local_pack`, `news`, `shopping`, `discussion`,
`ai_overview`, `knowledge_panel`, `paid_top`. Organic only: filter on `organic`.

## Site Explorer: authority and links

| Tool | Parameters | Useful `select` fields |
|---|---|---|
| `site-explorer-domain-rating` | `target*`, `date*` | `domain_rating`, `ahrefs_rank` (fixed row) |
| `site-explorer-backlinks-stats` | `target*`, `date*`, `mode`, `protocol` | `live`, `all_time`, `live_refdomains`, `all_time_refdomains` (fixed row) |
| `site-explorer-refdomains` | `select*`, `target*`, `mode`, `history`, `where`, `order_by`, `limit` | `domain`, `domain_rating`, `traffic_domain`, `dofollow_links`, `links_to_target`, `new_links`, `lost_links`, `first_seen`, `last_seen`, `is_spam`, `is_root_domain` |
| `site-explorer-all-backlinks` | `select*`, `target*`, `mode`, `aggregation` (`similar_links`, `1_per_domain`, `all`), `history`, `where`, `order_by`, `limit` | `url_from`, `url_to`, `anchor`, `title`, `domain_rating_source`, `url_rating_source`, `traffic_domain`, `is_dofollow`, `is_nofollow`, `is_ugc`, `is_sponsored`, `is_spam`, `is_lost`, `is_new`, `first_seen`, `last_seen`, `lost_reason`, `languages` |
| `site-explorer-anchors` | `select*`, `target*`, `mode`, `history`, `where`, `order_by`, `limit` | `anchor`, `refdomains`, `refpages`, `links_to_target`, `dofollow_links`, `top_domain_rating`, `first_seen`, `last_seen`, `is_spam` |
| `site-explorer-broken-backlinks` | `select*`, `target*`, `mode`, `aggregation`, `where`, `order_by`, `limit` | `url_from`, `url_to`, `anchor`, `http_code_target`, `domain_rating_source`, `is_dofollow`, `first_seen` |
| `site-explorer-pages-by-backlinks` | `select*`, `target*`, `mode`, `history`, `where`, `order_by`, `limit` | `url_to`, `title_target`, `refdomains_target`, `links_to_target`, `dofollow_to_target`, `http_code_target`, `url_rating_target`, `top_domain_rating_source` |
| `site-explorer-linkeddomains` | `select*`, `target*`, `mode`, `where`, `order_by`, `limit` | `domain`, `domain_rating`, `links_from_target`, `dofollow_links`, `linked_pages` |

Cheap triage: `refdomains` sorted by `domain_rating:desc` with `history=live`.
`all-backlinks` with `aggregation=1_per_domain` gives one best link per domain.

## Site Explorer: organic search

| Tool | Parameters | Useful `select` fields |
|---|---|---|
| `site-explorer-metrics` | `target*`, `date*`, `mode`, `country`, `volume_mode`, `traffic_mode` | `org_traffic`, `org_keywords`, `org_keywords_1_3`, `org_cost`, `paid_traffic`, `paid_keywords` (fixed row) |
| `site-explorer-organic-keywords` | `select*`, `target*`, `date*`, `date_compared`, `country`, `mode`, `where`, `order_by`, `limit` | `keyword`, `best_position`, `best_position_url`, `best_position_kind`, `best_position_diff`, `volume`, `sum_traffic`, `keyword_difficulty`, `cpc`, `serp_features`, `is_informational`, `is_commercial`, `is_transactional`, `is_branded`, `last_update` |
| `site-explorer-top-pages` | `select*`, `target*`, `date*`, `date_compared`, `country`, `mode`, `where`, `order_by`, `limit` | `url`, `sum_traffic`, `traffic_diff`, `keywords`, `top_keyword`, `top_keyword_best_position`, `top_keyword_volume`, `value`, `referring_domains`, `page_type` |
| `site-explorer-organic-competitors` | `select*`, `target*`, `date*`, `country*`, `mode`, `where`, `order_by`, `limit` | `competitor_domain`, `competitor_url`, `domain_rating`, `keywords_common`, `keywords_competitor`, `keywords_target`, `share`, `traffic`, `value`, `pages` |
| `site-explorer-pages-by-traffic` | `target*`, `mode`, `country` | traffic-band page counts (fixed row) |

With `date_compared`, `*_prev` and `*_diff` fields show movement between dates.

## History (one row per period)

| Tool | Parameters | Rows |
|---|---|---|
| `site-explorer-metrics-history` | `target*`, `date_from*`, `date_to`, `history_grouping` (`daily`, `weekly`, `monthly`), `select` | `date`, `org_traffic`, `org_cost`, `paid_traffic` |
| `site-explorer-refdomains-history` | `target*`, `date_from*`, `date_to`, `history_grouping` | `date`, `refdomains` |
| `site-explorer-domain-rating-history` | `target*`, `date_from*`, `date_to`, `history_grouping` | `date`, `domain_rating` |
| `site-explorer-keywords-history` | `target*`, `date_from*`, `date_to`, `history_grouping`, `select` | `date`, `top3`, `top4_10`, `top11_20`, `top21_50`, `top51_plus` |

## Bulk and content

| Tool | Parameters | Notes |
|---|---|---|
| `batch-analysis-batch-analysis` | body: `select*` (array), `targets*` (array of `{url, mode, protocol}`, max 100), `country`, `order_by` | fields: `domain_rating`, `url_rating`, `refdomains`, `backlinks`, `org_traffic`, `org_keywords`, `org_cost`, `ahrefs_rank` |
| `content-helper-topics` | `keyword*`, `country*`, `top_competitors`, `target_url` | 1000 units (+500 with `target_url`); topics the ranking pages cover, with coverage scores |

## Free tools

| Tool | Use |
|---|---|
| `subscription-info-limits-and-usage` | Units used, limit and reset date |
| `rank-tracker-overview`, `rank-tracker-serp-overview`, `rank-tracker-competitors-*` | Positions from an Ahrefs Rank Tracker project |
| `management-projects`, `management-project-keywords`, `management-locations` | Rank Tracker project setup |
| `gsc-keywords`, `gsc-pages`, `gsc-performance-history`, `gsc-positions-history` | Search Console data connected in Ahrefs |
| `site-audit-projects` | Ahrefs Site Audit projects (issues and pages cost 50 units per call) |
| `public-domain-rating-free` | DR for any domain without plan units |
