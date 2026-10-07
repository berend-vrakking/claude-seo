---
name: seo-plan
description: >
  Strategic SEO planning for new or existing websites. Industry-specific
  templates, competitive analysis, content strategy, and implementation
  roadmap. Use when user says "SEO plan", "SEO strategy", "SEO planning",
  "content strategy", "keyword strategy", "content calendar",
  "site architecture", or "SEO roadmap".
user-invocable: true
argument-hint: "[business-type]"
license: MIT
metadata:
  author: AgriciDaniel
  version: "2.4.2"
  category: seo
---

# Strategic SEO Planning

## Process

### 1. Discovery
- Business type, target audience, competitors, goals
- Current site assessment (if exists)
- Budget and timeline constraints
- Key performance indicators (KPIs)

### 2. Competitive Analysis
- Identify top 5 competitors
- Analyze their content strategy, schema usage, technical setup
- Identify keyword gaps and content opportunities
- Assess their E-E-A-T signals
- Estimate their domain authority

### 3. Architecture Design
- Load industry template from `assets/` directory
- Design URL hierarchy and content pillars
- Plan internal linking strategy
- Sitemap structure with quality gates applied
- Information architecture for user journeys

### 4. Content Strategy
- Content gaps vs competitors
- Page types and estimated counts
- Blog/resource topics and publishing cadence
- E-E-A-T building plan (author bios, credentials, experience signals)
- Content calendar with priorities

### 5. Technical Foundation
- Hosting and performance requirements
- Schema markup plan per page type
- Core Web Vitals baseline targets
- AI search readiness requirements
- Mobile-first considerations

### 6. Implementation Roadmap (4 phases)

#### Phase 1: Foundation (weeks 1-4)
- Technical setup and infrastructure
- Core pages (home, about, contact, main services)
- Essential schema implementation
- Analytics and tracking setup

#### Phase 2: Expansion (weeks 5-12)
- Content creation for primary pages
- Blog launch with initial posts
- Internal linking structure
- Local SEO setup (if applicable)

#### Phase 3: Scale (weeks 13-24)
- Advanced content development
- Link building and outreach
- GEO optimization
- Performance optimization

#### Phase 4: Authority (months 7-12)
- Thought leadership content
- PR and media mentions
- Advanced schema implementation
- Continuous optimization

## Industry Templates

Load from `assets/` directory:
- `saas.md`: SaaS/software companies
- `local-service.md`: Local service businesses
- `ecommerce.md`: E-commerce stores
- `publisher.md`: Content publishers/media
- `agency.md`: Agencies and consultancies
- `generic.md`: General business template

## Output

### Deliverables
- `SEO-STRATEGY.md`: Complete strategic plan
- `COMPETITOR-ANALYSIS.md`: Competitive insights
- `CONTENT-CALENDAR.md`: Content roadmap
- `IMPLEMENTATION-ROADMAP.md`: Phased action plan
- `SITE-STRUCTURE.md`: URL hierarchy and architecture

### KPI Targets
| Metric | Baseline | 3 Month | 6 Month | 12 Month |
|--------|----------|---------|---------|----------|
| Organic Traffic | ... | ... | ... | ... |
| Keyword Rankings | ... | ... | ... | ... |
| Domain Authority | ... | ... | ... | ... |
| Indexed Pages | ... | ... | ... | ... |
| Core Web Vitals | ... | ... | ... | ... |

### Success Criteria
- Clear, measurable goals per phase
- Resource requirements defined
- Dependencies identified
- Risk mitigation strategies

## Ahrefs Integration (Optional, primary data source)

If `mcp__ahrefs__*` tools are available (rules: `${CLAUDE_PLUGIN_ROOT}/skills/seo/references/ahrefs.md`), use `mcp__ahrefs__site-explorer-organic-competitors` for the real competitor set, `mcp__ahrefs__batch-analysis-batch-analysis` (`domain_rating`, `refdomains`, `org_traffic`, `org_keywords`) to size the site against them in one call, `mcp__ahrefs__site-explorer-organic-keywords` and `mcp__ahrefs__site-explorer-top-pages` for keyword and content gaps, and `mcp__ahrefs__keywords-explorer-overview` / `mcp__ahrefs__keywords-explorer-matching-terms` for keyword research. Gate each call with `ahrefs_costs.py check`. Without Ahrefs, plan from WebSearch and the site itself and mark traffic and volume figures as not measured.

## DataForSEO Integration (Optional)

With DataForSEO but no Ahrefs, use `dataforseo_labs_google_competitors_domain` and `dataforseo_labs_google_domain_intersection` for real competitive intelligence, `dataforseo_labs_bulk_traffic_estimation` for traffic estimates, `kw_data_google_ads_search_volume` and `dataforseo_labs_bulk_keyword_difficulty` for keyword research, and `business_data_business_listings_search` for local business data.

## Saved Keywords (OpenSEO, Optional)

With OpenSEO connected (rules: `${CLAUDE_PLUGIN_ROOT}/skills/seo/references/openseo.md`, section 3):

1. Before research, read `mcp__openseo__list_saved_keywords` (filter with
   `search` on the seed) and the project's research log. Reuse what is there
   instead of buying the same metrics again.
2. After the user accepts the result, save the target keywords of the plan's first phases with
   `mcp__openseo__save_keywords` (up to 100 per call, with `metrics` mapped
   from Ahrefs: volume, difficulty, CPC in USD, intent). Ask before adding tags.
3. Then offer to track them: add them to the site's Ahrefs Rank Tracker
   project with `mcp__ahrefs__management-project-keywords` only after the user
   confirms (it changes their Ahrefs project and may count against keyword limits).

Without OpenSEO, skip this section.

## OpenSEO Project and Report (Optional)

When the OpenSEO MCP server is connected (`mcp__openseo__list_projects` is
available), follow `${CLAUDE_PLUGIN_ROOT}/skills/seo/references/openseo.md`: run the project step
before analysis (find the project, read `get_project_context` and its research
log), then, once the report is final, call `mcp__openseo__list_reports` and
`mcp__openseo__save_report` with `skill: "seo-plan"`, a title such as
`SEO Strategy Plan, Oct 7, 2026`, and a summary carrying the verdict, the goal, the phase-1 priorities, and the competitors used.
Pass the `reportId` of an existing report for the same subject to replace it.
Keep writing the local output files as well. Finish with
`update_project_context` (`appendResearchLog`). When run as a subagent of
`/seo audit`, skip the save: the orchestrator saves one report.
Without OpenSEO, skip this section.

## Error Handling

| Scenario | Action |
|----------|--------|
| Unrecognized business type | Fall back to `generic.md` template. Inform user that no industry-specific template was found and proceed with the general business template. |
| No website URL provided | Proceed with new-site planning mode. Skip current site assessment and competitive gap analysis that require a live URL. |
| Industry template not found | Check `assets/` directory for available templates. If the requested template file is missing, use `generic.md` and note the missing template in output. |
