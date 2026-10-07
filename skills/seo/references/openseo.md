# OpenSEO: Shared Project Memory, Reports, Keywords and Crawler

Claude SEO is the only skill layer: it decides what to analyse and how. When the
OpenSEO MCP server is connected (tools named `mcp__openseo__<tool>`), OpenSEO is
the shared back end: project memory, saved reports, the tracked keyword list,
and the site crawler. Every OpenSEO tool below uses no credits except
`run_site_audit` with JavaScript rendering on hosted plans.

Search Console and GA4 stay on Claude SEO's own Google connection (its scripts
and gcloud sign-in); do not use OpenSEO's Google tools for them. Ahrefs calls
and the Ahrefs cache are covered in `ahrefs.md` in this directory.

## 0. Availability

If no `mcp__openseo__list_projects` tool is present, skip this whole file and
run the skill exactly as before (local files, WebSearch, the plugin's own
crawler). Never block on OpenSEO. If a call errors mid-run, finish the work
locally and say which OpenSEO step was skipped.

## 1. Project step (before work)

1. `mcp__openseo__list_projects` (no arguments). Pick the project whose `domain`
   matches the site being analysed (compare bare hostnames; `www.` and scheme
   do not matter). For keyword-only work, use the project the user names or the
   one for their own site.
2. No match: ask the user whether to create one. Only on a yes, call
   `mcp__openseo__create_project {"name": ..., "domain": ...}`. Without a
   project, skip steps 2 to 4 below and continue locally.
3. `mcp__openseo__get_project_context {"projectId": ...}`. Ground the work in
   it: business overview, current goal, positioning, writing preferences,
   competitors, key pages. Read the **research log** before buying research:
   if the same question was researched recently, reuse that and say so.
4. Before keyword research, also read `mcp__openseo__list_saved_keywords
   {"projectId": ..., "search"?: ..., "limit": 100}` (limit 50, 100 or 250).
   Before writing a report, read `mcp__openseo__list_reports {"projectId": ...}`.

## 2. Reports (after work)

Skills that produce a report also save it to the project. Keep writing the
local files the skill already writes; the OpenSEO copy is in addition.

1. `mcp__openseo__list_reports {"projectId": ...}`. If a report for the same job
   exists (same skill slug and subject), reuse its `reportId` so the save
   replaces it. A save whose title already exists without that id is refused.
2. `mcp__openseo__save_report` with:
   - `projectId`, and `reportId` when replacing
   - `title`: report type, subject when it is not the project's own site, and the
     full date, e.g. `Technical SEO Audit, Oct 7, 2026` or
     `Backlink Gap vs competitor.com, Oct 7, 2026` (max 120 characters; the
     same text as the HTML `<title>` and `<h1>`; never "SEO Report")
   - `summary`: Markdown under 2,500 characters: the verdict, the single top
     action, and the key numbers (score, counts, units spent)
   - `html`: one self-contained document ending in `</html>`. Inline CSS only;
     no external requests, images by URL, fonts or scripts. No backticks and no
     dollar-brace sequences anywhere. Aim under 80 KB (hard limit 500 KB).
   - `skill`: the slug of the running skill, e.g. `seo-audit`
3. Reply with the returned `url`, a one-line verdict and the top action. Do not
   share the report publicly (`set_report_sharing`) unless the user asks.

## 3. Keywords

Keyword research outputs (seo-cluster, seo-content-brief, seo-plan,
`/seo ahrefs volume|keywords|questions`) end by saving the keywords the user
chose or the plan targets:

- `mcp__openseo__save_keywords {"projectId": ..., "keywords": [...], "metrics": [...]}`,
  at most 100 per call; re-saving is a no-op.
- `metrics` rows: `keyword`, `searchVolume`, `keywordDifficulty` (0-100), `cpc`
  (USD), `intent` (`informational`, `commercial`, `transactional`,
  `navigational` or `unknown`). From Ahrefs: `volume` to `searchVolume`,
  `difficulty` to `keywordDifficulty`, `cpc` is in USD cents so divide by 100,
  and `intent` = the first true flag among transactional, commercial,
  informational, navigational in `intents`.
- `tags` (for example the cluster or page a keyword belongs to): ask the user
  first, as the tool requires. Default to no tags.

## 4. Crawler (seo-technical, seo-audit)

Use OpenSEO's crawler as the crawl source when available, instead of the
plugin's own link-following crawl:

1. `mcp__openseo__list_site_audits {"projectId": ...}`: note the newest
   completed audit for this URL (the comparison baseline).
2. `mcp__openseo__run_site_audit {"projectId": ..., "url": ..., "maxPages": 500}`.
   Leave `runLighthouse` false unless the user asked for Lighthouse;
   `renderJavaScript: true` only for client-rendered sites (slower, billed on
   hosted plans: say so first).
3. Poll `mcp__openseo__get_audit_status {"projectId": ..., "auditId": ...}`
   until it completes or fails; do other analysis meanwhile.
4. Read `mcp__openseo__get_audit_issues {"projectId": ..., "auditId": ...,
   "severity"?: "critical", "limit": 200}` (each issue has `how_to_fix`) and
   `mcp__openseo__get_audit_pages {..., "statusCode"?: 404, "urlContains"?: ...,
   "limit": 100}` for page-level data.
5. Compare with the baseline: `get_audit_issues` for the previous `auditId`;
   report new, fixed and persisting issues.

Keep the plugin's own fetch-based checks for what the crawler does not cover:
rendered HTML and SPA detection (`render_page.py`), security headers,
robots.txt and AI-crawler rules, schema validation, Core Web Vitals field data
(PSI/CrUX scripts), hreflang, and the agent-readiness checks. If the audit
fails or OpenSEO is absent, crawl with the plugin's own fetchers as before.

## 5. End of work

`mcp__openseo__update_project_context {"projectId": ..., "updates": [...]}`:

- Always: `{"appendResearchLog": {"summary": "<what was researched, key result, units spent, report url>"}}`
  (max 1,000 characters; the date is stamped by the server).
- Only for facts the user confirmed: `{"addCompetitors": [{"domain": ..., "name"?: ..., "notes"?: ...}]}`
  and `{"addKeyPages": [{"url": ..., "role"?: "hub|spoke|money|other", "topic"?: ...}]}`.
- Never rewrite the prose sections (business overview, goal, positioning,
  writing preferences) without the user's explicit go-ahead.
