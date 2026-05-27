---
name: micu-api-usage-report
description: Generate Micu API quota usage reports by comparing token snapshots, validate that the Micu console data is fresh, and save weekly HTML/JSON reports for Codex and Claude Code token groups. Use when the user asks for Micu API usage, API额度使用报告, weekly API reports, token quota comparison, or automation of Micu API report generation.
---

# Micu API Usage Report

Use this skill for the user's Micu API quota reports. The report is a snapshot-to-snapshot comparison, not a natural-week usage-log sum.

## Core Rules

- Token identity is `name + group`.
- Group labels:
  - `vip_2` = Codex token
  - `vip_1_max_enterprise` = Claude Code token
- Period usage formula:
  - `added_quota = max(current.total - previous.total, 0)`
  - `period_usage = previous.remaining + added_quota - current.remaining`
- If `current.total < previous.total`, put the token in the anomaly section and exclude it from the normal ranking.
- New tokens may use `current.total - current.remaining` as provisional usage and must be marked as new.
- Missing tokens are anomalies and are not included in normal usage.
- Never treat a single snapshot's `total - remaining` as the normal period usage for matched tokens.

## Default Paths

- Snapshots: `/Users/luoji/Documents/micu_api_snapshots`
- Reports: `/Users/luoji/Documents/micu_api_reports`
- Legacy baseline HTML: `/Users/luoji/Documents/micu_api_usage_report_2026-05-18_to_2026-05-22.html`
- Micu token page: `https://www.micuapi.ai/console/token`
- Micu usage log page: `https://www.micuapi.ai/console/log`

## Standard Workflow

Run the bundled script:

```bash
node /Users/luoji/.codex/skills/micu-api-usage-report/scripts/micu_usage_report.js
```

The script will:

1. Find the latest previous snapshot before today as the baseline.
2. If no baseline exists, initialize one from the legacy HTML report.
3. Read the newest full Micu token API response from the Codex in-app browser Chromium cache.
4. Convert quota units to RMB using `quota / 500000`.
5. Validate freshness before producing a successful report.
6. Generate:
   - `YYYY-MM-DD_period_api_usage_report.html`
   - `YYYY-MM-DD_period_api_usage_comparison.json`
   - `YYYY-MM-DD_api_token_snapshot.json`

## Freshness Validation

The script must not silently publish stale data. A successful run requires a current full token response and at least one of:

- a token `last_used` date equal to today's date in `Asia/Shanghai`, or
- a same-day usage-log cache record if that support is added later.

If freshness fails, report failure and include the login/refresh link:

`https://www.micuapi.ai/console/token`

Do not save the stale token response as the next baseline on freshness failure.

## Automation Behavior

For weekly automation, run this skill every Thursday at 12:00 Asia/Shanghai. If the script succeeds, summarize the generated report path and top usage totals. If it fails freshness/login validation, tell the user to open the Micu token page, log in or refresh, then rerun the report.
