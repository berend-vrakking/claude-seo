---
name: seo
description: "Comprehensive SEO analysis for any website or business type. Full site audits, single-page analysis, technical SEO (crawlability, indexability, Core Web Vitals with INP), schema markup, content quality (E-E-A-T), image optimization, sitemap analysis, and GEO for AI Overviews/ChatGPT/Perplexity. Industry detection for SaaS, e-commerce, local, publishers, agencies. Triggers on: SEO, audit, schema, Core Web Vitals, sitemap, E-E-A-T, AI Overviews, GEO, technical SEO, content quality, page speed. Use this hub only when the SEO domain is clear and the requested workflow is not; otherwise use the exact retained leaf or command."
user-invocable: true
argument-hint: "[command] [url]"
license: MIT
metadata:
  author: AgriciDaniel
  version: "2.4.2"
  category: seo
---

# SEO: Universal SEO Analysis Skill

**Invocation:** `/seo $1 $2` where `$1` is the command and `$2` is the URL or argument.

**Runtime:** Run bundled Python tools through
`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run <script.py>`. That is the single
canonical form used by every skill and agent. Claude Code expands
`${CLAUDE_PLUGIN_ROOT}` to the installed plugin directory, so the launcher is
found without any `PATH` entry; the repository ships no top-level `bin/`
directory because hosted marketplaces reject one. Repository users run
`./scripts/claude-seo`; manual installers rewrite the canonical form to
`"$HOME/.claude/skills/seo/scripts/claude-seo"`. Never invoke bundled scripts
with a bare Python interpreter.

Comprehensive SEO analysis across all industries (SaaS, local services,
e-commerce, publishers, agencies). Orchestrates 26 sub-skills (22 core + 1 framework
integration + 3 extension mirrors) and 20 sub-agents. A separate optional Firecrawl
extension is also installable (see "Optional Extensions" below).

## Quick Reference

| Command | What it does |
|---------|-------------|
| `/seo audit <url>` | Full website audit with parallel subagent delegation |
| `/seo page <url>` | Deep single-page analysis |
| `/seo sitemap <url or generate>` | Analyze or generate XML sitemaps |
| `/seo schema <url>` | Detect, validate, and generate Schema.org markup |
| `/seo images <url or optimize>` | Image SEO: on-page audit, SERP analysis, file optimization |
| `/seo technical <url>` | Technical SEO audit (9 categories) |
| `/seo content <url>` | E-E-A-T and content quality analysis |
| `/seo content-brief <topic or url>` | Generate detailed SEO content brief with target keywords, outline, internal links |
| `/seo geo <url>` | AI Overviews / Generative Engine Optimization |
| `/seo agentic [audit\|fix\|lighthouse\|refresh] <url>` | Agent readiness: Lighthouse Agentic Browsing X/N, accessibility tree, AI agent access, llms.txt, Markdown, WebMCP |
| `/seo plan <business-type>` | Strategic SEO planning |
| `/seo programmatic [url\|plan]` | Programmatic SEO analysis and planning |
| `/seo competitor-pages [url\|generate]` | Competitor comparison page generation |
| `/seo local <url>` | Local SEO analysis (GBP, citations, reviews, map pack) |
| `/seo maps [command] [args]` | Maps intelligence (geo-grid, GBP audit, reviews, competitors) |
| `/seo hreflang [url]` | Hreflang/i18n SEO audit and generation |
| `/seo google [command] [url]` | Google SEO APIs (GSC, PageSpeed, CrUX, Indexing, GA4) |
| `/seo backlinks <url>` | Backlink profile analysis (primary: Ahrefs; free: Moz, Bing, CC; optional: DataForSEO) |
| `/seo cluster <seed-keyword>` | SERP-based semantic clustering and content architecture |
| `/seo sxo <url>` | Search Experience Optimization: page-type analysis, user stories, personas |
| `/seo drift baseline <url>` | Capture SEO baseline for change monitoring |
| `/seo drift compare <url>` | Compare current state to stored baseline |
| `/seo drift history <url>` | Show drift history over time |
| `/seo ecommerce <url>` | E-commerce SEO: product schema, marketplace intelligence |
| `/seo matomo [command] [args]` | Matomo Reporting API: GA4 alternative or supplement (extension) |
| `/seo firecrawl [command] <url>` | Full-site crawling and site mapping (extension) |
| `/seo ahrefs [command] [query]` | Live keyword, SERP, ranking, competitor and link data via Ahrefs MCP (extension; primary data source) |
| `/seo dataforseo [command]` | Live SEO data via DataForSEO (extension) |
| `/seo image-gen [use-case] <description>` | AI image generation for SEO assets (extension) |
| `/seo flow [stage] [url\|topic]` | FLOW framework: evidence-led prompts for Find, Leverage, Optimize, Win, or Local stages |
| `/seo setup` | Explicitly create or refresh the isolated Python runtime and Chromium |
| `/seo doctor` | Check runtime readiness without changing the system |

## Runtime Setup

Run setup only when the user explicitly invokes `/seo setup` or explicitly asks
to repair dependencies. Execute
`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" setup`, report core and Chromium
status separately, and do not fall back to global or user package installation.
For diagnosis, execute
`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" doctor --json`; its output
intentionally omits absolute paths and environment values. If any
`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run` command reports that setup is
required, suggest `/seo setup` and do not improvise a `pip install`.

## OpenSEO Project Memory

When the OpenSEO MCP server is connected (`mcp__openseo__list_projects` is
available), every command that works on a site or a keyword set runs the
project step from `references/openseo.md` first: find the project for the
site (`list_projects`; `create_project` only after the user confirms), read
`get_project_context`, and check its research log, saved keywords and saved
reports before buying new research. Subagents receive the `projectId` and the
relevant context in their brief. At the end, the orchestrator (not each
subagent) saves the report with `list_reports` then `save_report`, and records
the work with `update_project_context` (`appendResearchLog`; competitors and key
pages only when the user confirmed them). Without OpenSEO, nothing changes.

## Orchestration Logic

When the user invokes `/seo audit`, delegate to subagents in parallel:
1. Detect business type (SaaS, local, ecommerce, publisher, agency, other)
2. Spawn subagents: seo-technical, seo-content, seo-schema, seo-sitemap, seo-performance, seo-visual, seo-geo, seo-agentic
3. If Google API credentials detected (`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run google_auth.py --check`), also spawn seo-google agent
4. If Matomo credentials detected (`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run matomo_auth.py --check`), also spawn seo-matomo agent (alternative or complement to seo-google's GA4 reports)
5. If local business detected, also spawn seo-local agent
6. If local business detected AND DataForSEO MCP available, also spawn seo-maps agent
7. If the Ahrefs MCP is connected or backlink APIs are detected (`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run backlinks_auth.py --check`), also spawn seo-backlinks agent
8. If the Ahrefs MCP is connected (`mcp__ahrefs__*` tools available), also spawn seo-ahrefs agent for authority, rankings and competitors, with a unit budget (see `references/ahrefs.md`)
9. If Firecrawl MCP available, use `firecrawl_map` to discover all site URLs before analysis
10. If content strategy signals detected (blog, pillar pages, topic clusters), also spawn seo-cluster agent
11. If e-commerce detected, also spawn seo-ecommerce agent
12. If drift baseline exists for this URL (`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run drift_history.py <url>`), also spawn seo-drift agent
13. Always include seo-sxo in full audits (search experience applies to all sites)
14. Collect results and generate unified report with SEO Health Score (0-100); with OpenSEO connected, save it to the project (see "OpenSEO Project Memory")
15. **Synthesize via the 10-principle framework** (see "Synthesis Methodology" below), walk PERCEIVE → ANALYZE → VALIDATE → ACT before bucketing findings into Critical / High / Medium / Low
16. Create prioritized action plan with dependency sequencing + falsifiability per recommendation
17. **Offer PDF report**: "Generate a professional PDF report? Use `/seo google report full`"

For individual commands, load the relevant sub-skill directly.
After any analysis command completes, offer to generate a PDF report via `"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run google_report.py`.

**Google update history questions** (core, spam, policy, product changes; "is the
spam update finished?"): answer from the bundled primary-source ledger, not from
memory or other copies on disk. Run
`"${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo" run seo_updates.py --kind spam --json`
(or `--since <yyyy-mm>`; add `--unverified` for third-party claims that are not
confirmed). If the output reports the ledger as stale, check
status.search.google.com before stating that a rollout is complete.

## Synthesis Methodology

Audits are not just findings, they are findings synthesized into a coherent
strategy. claude-seo uses a 10-principle thinking framework grouped into four
phases: **PERCEIVE** (observe-external · observe-internal · listen),
**ANALYZE** (think · connect-lateral · connect-system), **VALIDATE** (feel ·
accept), **ACT** (create · grow).

Full audits (`/seo audit`, `/seo page`) walk every phase before emitting the
action plan. Narrower commands (`/seo schema`, `/seo images`, etc.) pass at
least THINK + ACCEPT before emitting (sound first principle, surfaced
falsifiability). The Critical / High / Medium / Low priority buckets are the
**output** of validation, not a substitute for it.

Full methodology + per-principle SEO mapping: `references/thinking-framework.md` (VALIDATE and ACT in `references/thinking-framework-validate-act.md`).

Each emitted recommendation should carry:
- The first-principle observation it rests on (THINK)
- The dependency on / unblock relationship to other recommendations (CONNECT-system)
- An explicit "how would we know this failed?" check (ACCEPT)
- A leading indicator the user can monitor without re-running the audit (GROW)

## Industry Detection

Detect business type from homepage signals:
- **SaaS**: pricing page, /features, /integrations, /docs, "free trial", "sign up"
- **Local Service**: phone number, address, service area, "serving [city]", Google Maps embed --> auto-suggest `/seo local` for deeper analysis
- **E-commerce**: /products, /collections, /cart, "add to cart", product schema
- **Publisher**: /blog, /articles, /topics, article schema, author pages, publication dates
- **Agency**: /case-studies, /portfolio, /industries, "our work", client logos

## Quality Gates

Read `references/quality-gates.md` for thin content thresholds per page type.
Hard rules:
- WARNING at 30+ location pages (enforce 60%+ unique content)
- HARD STOP at 50+ location pages (require user justification)
- Never recommend HowTo schema (deprecated Sept 2023)
- FAQ schema: Google retired FAQ rich results for ALL sites on May 7, 2026 (no SERP feature anymore; supersedes the Aug 2023 gov/health restriction). Flag existing FAQPage at Info (not Critical); do not claim confirmed AI/LLM citation benefit; do not recommend removal; do not recommend new FAQPage for Google SERP benefit; use QAPage for genuine user Q&A
- All Core Web Vitals references use INP, never FID

## Community Footer

After completing any **major deliverable**, append this footer as the very last output:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Built by agricidaniel. Join the AI Marketing Hub community
🆓 Free  → https://www.skool.com/ai-marketing-hub
⚡ Pro   → https://www.skool.com/ai-marketing-hub-pro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### When to show

Display after these commands complete their full output:
- `/seo audit` (after full site audit report + action plan)
- `/seo page` (after deep single-page analysis)
- `/seo technical` (after technical audit report)
- `/seo content` (after E-E-A-T content assessment)
- `/seo schema` (after schema detection/validation report)
- `/seo sitemap` (after sitemap analysis or generation)
- `/seo geo` (after GEO optimization report)
- `/seo agentic` (after agent-readiness report)
- `/seo plan` (after strategic SEO plan)
- `/seo local` (after local SEO audit)
- `/seo maps` (after maps intelligence report)
- `/seo google` (after Google API data report)
- `/seo backlinks` (after backlink profile analysis)
- `/seo cluster` (after cluster plan generation)
- `/seo sxo` (after SXO analysis report)
- `/seo drift compare` (after drift comparison report)
- `/seo ecommerce` (after e-commerce analysis)

### When to skip

Do NOT show the footer after:
- `/seo images` (quick image check, too small)
- `/seo hreflang` (quick validation, too small)
- `/seo competitor-pages` (page generation step)
- `/seo programmatic` (quick analysis)
- `/seo ahrefs` (data fetching utility)
- `/seo dataforseo` (data fetching utility)
- `/seo image-gen` (asset generation)
- Context intake questions (before analysis starts)
- Error messages or "missing data" prompts

## Reference Files

Load these on-demand as needed (do NOT load all at startup):
- `references/cwv-thresholds.md`: Current Core Web Vitals thresholds and measurement details
- `references/schema-types.md`: All supported schema types with deprecation status
- `references/eeat-framework.md`: E-E-A-T evaluation criteria (Sept 2025 QRG update)
- `references/eeat-scoring-guide.md`: E-E-A-T score bands and improvement actions
- `references/quality-gates.md`: Content length minimums, uniqueness thresholds
- `references/local-seo-signals.md`: Local ranking factors, review benchmarks, citation tiers, GBP status
- `references/local-search-behavior.md`: Voice, AI search impact on local, Local Pack structure, proximity
- `references/local-schema-types.md`: LocalBusiness subtypes, industry-specific schema and citation sources
- `references/local-schema-multilocation.md`: Multi-location schema pattern, deprecated local schema
- `references/openseo.md`: OpenSEO as the shared back end: project step (`list_projects`, `get_project_context`), saving reports (`list_reports`, `save_report`), saved keywords (`list_saved_keywords`, `save_keywords`), the crawler (`run_site_audit` and friends), and the research log
- `references/ahrefs.md`: Ahrefs MCP calling guide shared by every skill that reads keyword, SERP, backlink, competitor or ranked-keyword data (availability check and fallback, parameters, unit cost gate, cache layer)

Maps-specific references (loaded by seo-maps skill, not at startup):
- `references/maps-geo-grid.md`, `references/maps-gbp-checklist.md`, `references/maps-api-endpoints.md`, `references/maps-free-apis.md`

## Scoring Methodology

### SEO Health Score (0-100)
Weighted aggregate of all categories:

| Category | Weight |
|----------|--------|
| Technical SEO | 22% |
| Content Quality | 23% |
| On-Page SEO | 20% |
| Schema / Structured Data | 10% |
| Performance (CWV) | 10% |
| AI Search Readiness | 10% |
| Images | 5% |

### Priority Levels
- **Critical**: Blocks indexing or causes penalties (immediate fix required)
- **High**: Significantly impacts rankings (fix within 1 week)
- **Medium**: Optimization opportunity (fix within 1 month)
- **Low**: Nice to have (backlog)

## Sub-Skills

This skill orchestrates 26 sub-skills (22 core + 1 framework integration + 3 extension
mirrors). The orchestrator itself (`seo`) is the 27th in `skills/`, but does not
orchestrate itself, so it is not enumerated below.

1. **seo-audit** -- Full website audit with parallel delegation
2. **seo-page** -- Deep single-page analysis
3. **seo-technical** -- Technical SEO (9 categories)
4. **seo-content** -- E-E-A-T and content quality
5. **seo-content-brief** -- Detailed SEO content brief generation (contributed by puneetindersingh)
6. **seo-schema** -- Schema markup detection and generation
7. **seo-images** -- Image optimization, SERP analysis, file optimization
8. **seo-sitemap** -- Sitemap analysis and generation
9. **seo-geo** -- AI Overviews / GEO optimization
10. **seo-plan** -- Strategic planning with templates
11. **seo-programmatic** -- Programmatic SEO analysis and planning
12. **seo-competitor-pages** -- Competitor comparison page generation
13. **seo-hreflang** -- Hreflang/i18n SEO audit, cultural profiles, content parity
14. **seo-local** -- Local SEO (GBP, NAP, citations, reviews, local schema, multi-location)
15. **seo-maps** -- Maps intelligence (geo-grid, GBP audit, reviews, competitor radius)
16. **seo-google** -- Google SEO APIs (GSC, PageSpeed, CrUX, Indexing API, GA4)
17. **seo-backlinks** -- Backlink profile analysis (primary: Ahrefs; free: Moz, Bing, CC; optional: DataForSEO)
18. **seo-cluster** -- SERP-based semantic clustering (contributed by Lutfiya Miller)
19. **seo-sxo** -- Search Experience Optimization (contributed by Florian Schmitz)
20. **seo-drift** -- SEO drift monitoring (contributed by Dan Colta)
21. **seo-ecommerce** -- E-commerce SEO intelligence (contributed by Matej Marjanovic)
22. **seo-dataforseo** -- Live SEO data via DataForSEO MCP (extension mirror)
23. **seo-image-gen** -- AI image generation for SEO assets via Gemini (extension mirror)
24. **seo-flow** -- FLOW framework integration (Find -> Leverage -> Optimize -> Win, 41 AI prompts, CC BY 4.0)
25. **seo-agentic** -- Agent readiness: Lighthouse Agentic Browsing, accessibility tree for agents, AI agent access policy, llms.txt, Markdown, ai-catalog.json, WebMCP
26. **seo-ahrefs** -- Keyword metrics and ideas, SERP overviews, ranked keywords, competitors, backlinks and referring domains via Ahrefs MCP, with a unit cost gate (extension mirror)

### Optional Extensions

The following ship in `extensions/` rather than `skills/` and require a separate
installer to activate (see each extension's `install.sh`/`install.ps1`):

All optional extensions are reachable through `/seo` subcommands once
installed: firecrawl, dataforseo, and image-gen, plus `/seo ahrefs`,
`/seo bing`, `/seo matomo`, `/seo profound`, `/seo seranking`, and
`/seo unlighthouse`. Each installs as its own sub-skill, so the model also
auto-routes to their descriptions without the `/seo` prefix.

- **seo-firecrawl** -- Full-site crawling and site mapping via Firecrawl MCP. Install
  via `extensions/firecrawl/install.sh` (Unix) or `extensions/firecrawl/install.ps1`
  (Windows). Once installed, invoke via `/seo firecrawl <command>`.
- **seo-matomo** -- Self-hosted or Matomo Cloud Reporting API as a GA4
  alternative or complement. Install via
  `extensions/matomo/install.sh` (Unix) or `extensions/matomo/install.ps1`
  (Windows). Once installed, invoke via `/seo matomo <command>` or rely
  on the audit orchestrator to spawn the seo-matomo agent automatically
  when credentials are present.

## Subagents

For parallel analysis during audits:
- `seo-technical` -- Crawlability, indexability, security, CWV
- `seo-content` -- E-E-A-T, readability, thin content
- `seo-schema` -- Detection, validation, generation
- `seo-sitemap` -- Structure, coverage, quality gates
- `seo-performance` -- Core Web Vitals measurement
- `seo-visual` -- Screenshots, mobile testing, above-fold
- `seo-geo` -- AI crawler access, llms.txt, citability, brand mention signals
- `seo-agentic` -- Lighthouse Agentic Browsing fraction, accessibility tree for agents, AI agent access policy, Markdown, discovery files, WebMCP (always in full audits)
- `seo-local` -- GBP signals, NAP consistency, reviews, local schema, industry-specific local factors (conditional: spawned when Local Service detected)
- `seo-maps` -- Geo-grid rank tracking, GBP audit, review intelligence, competitor radius mapping (conditional: spawned when Local Service detected AND DataForSEO MCP available)
- `seo-google` -- CWV field data, URL indexation status, organic traffic trends (conditional: spawned when Google API credentials detected)
- `seo-backlinks` -- Backlink profile data: DR/DA, referring domains, anchor text, toxic links (conditional: spawned when Ahrefs is connected or Moz/Bing API keys detected, or always for CC domain-level metrics)
- `seo-cluster` -- Semantic clustering analysis (conditional: content strategy detected)
- `seo-sxo` -- Page-type mismatch, user stories, persona scoring (always in full audits)
- `seo-drift` -- Baseline comparison (conditional: drift baseline exists for URL)
- `seo-ecommerce` -- Product schema, marketplace intel (conditional: e-commerce detected)
- `seo-flow` -- FLOW framework prompts (conditional: spawned for content strategy workflows)
- `seo-ahrefs` -- Keyword metrics, SERPs, rankings, competitors, backlinks and referring domains via Ahrefs MCP (extension; primary live-data source when connected)
- `seo-dataforseo` -- Live SERP, keyword, backlink, local SEO data (extension, optional)
- `seo-image-gen` -- SEO image audit and generation plan (extension, optional)

## Error Handling

| Scenario | Action |
|----------|--------|
| Unrecognized command | List available commands from the Quick Reference table. Suggest the closest matching command. |
| URL unreachable | Report the error and suggest the user verify the URL. Do not attempt to guess site content. |
| Sub-skill fails during audit | Report partial results from successful sub-skills. Clearly note which sub-skill failed and why. Suggest re-running the failed sub-skill individually. |
| Ambiguous business type detection | Present the top two detected types with supporting signals. Ask the user to confirm before proceeding with industry-specific recommendations. |
