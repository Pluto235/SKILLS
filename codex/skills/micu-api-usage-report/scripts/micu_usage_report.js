#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const os = require('os');
const zlib = require('zlib');

const CONFIG = {
  legacyReport: '/Users/luoji/Documents/micu_api_usage_report_2026-05-18_to_2026-05-22.html',
  snapshotDir: '/Users/luoji/Documents/micu_api_snapshots',
  reportDir: '/Users/luoji/Documents/micu_api_reports',
  browserCacheDir: path.join(os.homedir(), 'Library/Application Support/Codex/Partitions/codex-browser-app/Cache/Cache_Data'),
  tokenUrlHint: 'https://www.micuapi.ai/api/token/',
  loginUrl: 'https://www.micuapi.ai/console/token',
  timeZone: 'Asia/Shanghai',
  quotaDivisor: 500000,
};

const GROUP_KIND = {
  vip_2: 'Codex token',
  vip_1_max_enterprise: 'Claude Code token',
};

function pad(n) {
  return String(n).padStart(2, '0');
}

function zonedParts(date = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: CONFIG.timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date).reduce((acc, part) => {
    if (part.type !== 'literal') acc[part.type] = part.value;
    return acc;
  }, {});
  return parts;
}

function todayString() {
  const p = zonedParts();
  return `${p.year}-${p.month}-${p.day}`;
}

function nowString() {
  const p = zonedParts();
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}:${p.second}`;
}

function formatUnix(seconds) {
  if (!seconds) return '';
  const date = new Date(seconds * 1000);
  const p = zonedParts(date);
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}:${p.second}`;
}

function money(n) {
  return `¥${Number(n || 0).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function roundMoney(n) {
  return Math.round(Number(n || 0) * 100) / 100;
}

function keyOf(row) {
  return `${row.name}::${row.group}`;
}

function writeJson(file, data) {
  fs.writeFileSync(file, `${JSON.stringify(data, null, 2)}\n`);
}

function loadJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function parseOldHtmlSnapshot(file) {
  const html = fs.readFileSync(file, 'utf8');
  const rowRe = /<tr>\s*<td>(.*?)<\/td>\s*<td><span class="tag">(.*?)<\/span><\/td>\s*<td class="right">(.*?)<\/td>\s*<td class="right">¥([\d.]+) \/ ¥([\d.]+)<\/td>[\s\S]*?<td>(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})<\/td>/g;
  return [...html.matchAll(rowRe)].map((m) => ({
    name: stripTags(m[1]),
    group: stripTags(m[2]),
    kind: GROUP_KIND[stripTags(m[2])] || 'Other token',
    ratio: stripTags(m[3]),
    remaining: Number(m[4]),
    total: Number(m[5]),
    last_used: m[6],
  }));
}

function stripTags(value) {
  return String(value || '').replace(/<[^>]*>/g, '').trim();
}

function ensureBaseline() {
  fs.mkdirSync(CONFIG.snapshotDir, { recursive: true });
  fs.mkdirSync(CONFIG.reportDir, { recursive: true });
  const files = listSnapshotFiles().filter((file) => snapshotDate(file) < todayString());
  if (files.length) return files[files.length - 1];

  if (!fs.existsSync(CONFIG.legacyReport)) {
    throw new Error(`No previous snapshot found and legacy baseline HTML is missing: ${CONFIG.legacyReport}`);
  }

  const baselineFile = path.join(CONFIG.snapshotDir, '2026-05-22_api_token_snapshot.json');
  if (!fs.existsSync(baselineFile)) {
    writeJson(baselineFile, {
      captured_at: '2026-05-22',
      source: CONFIG.legacyReport,
      identity: 'name+group',
      tokens: parseOldHtmlSnapshot(CONFIG.legacyReport),
    });
  }
  return baselineFile;
}

function listSnapshotFiles() {
  if (!fs.existsSync(CONFIG.snapshotDir)) return [];
  return fs.readdirSync(CONFIG.snapshotDir)
    .filter((name) => /^\d{4}-\d{2}-\d{2}_api_token_snapshot\.json$/.test(name))
    .sort()
    .map((name) => path.join(CONFIG.snapshotDir, name));
}

function snapshotDate(file) {
  return path.basename(file).slice(0, 10);
}

function findGzipJsonPayloads(buffer) {
  const payloads = [];
  for (let start = 0; start < buffer.length - 2; start += 1) {
    if (buffer[start] !== 0x1f || buffer[start + 1] !== 0x8b || buffer[start + 2] !== 0x08) continue;
    for (let end = buffer.length; end > start; end -= 1) {
      try {
        const text = zlib.gunzipSync(buffer.subarray(start, end)).toString('utf8');
        if (text.trim().startsWith('{')) payloads.push({ start, end, text });
        break;
      } catch (_) {
        // Chromium cache files often contain trailing metadata after gzip payloads.
      }
    }
  }
  return payloads;
}

function findLatestTokenCacheResponse() {
  if (!fs.existsSync(CONFIG.browserCacheDir)) {
    throw new Error(`Browser cache directory not found: ${CONFIG.browserCacheDir}`);
  }

  const candidates = [];
  for (const name of fs.readdirSync(CONFIG.browserCacheDir)) {
    const file = path.join(CONFIG.browserCacheDir, name);
    let stat;
    try {
      stat = fs.statSync(file);
      if (!stat.isFile()) continue;
      const buffer = fs.readFileSync(file);
      if (!buffer.includes(Buffer.from(CONFIG.tokenUrlHint))) continue;
      for (const payload of findGzipJsonPayloads(buffer)) {
        let json;
        try {
          json = JSON.parse(payload.text);
        } catch (_) {
          continue;
        }
        const data = json.data;
        if (!data || !Array.isArray(data.items) || typeof data.total !== 'number') continue;
        if (data.items.length < data.total) continue;
        candidates.push({ file, name, stat, json, data });
      }
    } catch (_) {
      // Ignore cache files that disappear or cannot be decoded.
    }
  }

  candidates.sort((a, b) => b.stat.mtimeMs - a.stat.mtimeMs);
  if (!candidates.length) {
    throw new Error(`No full token API cache response found. Open and refresh ${CONFIG.loginUrl}, then rerun.`);
  }
  return candidates[0];
}

function snapshotFromTokenResponse(candidate) {
  const tokens = candidate.data.items.map((item) => {
    const remaining = roundMoney(item.remain_quota / CONFIG.quotaDivisor);
    const total = roundMoney((item.remain_quota + item.used_quota) / CONFIG.quotaDivisor);
    return {
      name: item.name,
      group: item.group,
      kind: GROUP_KIND[item.group] || 'Other token',
      ratio: item.group === 'vip_1_max_enterprise' ? '1.5x' : item.group === 'vip_2' ? '0.35x' : '',
      remaining,
      total,
      last_used: formatUnix(item.accessed_time),
    };
  });

  return {
    captured_at: nowString(),
    source: `Codex browser cache ${CONFIG.tokenUrlHint}?p=1&size=100; contains all ${candidate.data.total} tokens`,
    page_sources: [{
      page: candidate.data.page,
      page_size: candidate.data.page_size,
      total: candidate.data.total,
      count: candidate.data.items.length,
      file: path.basename(candidate.file),
      cache_mtime: candidate.stat.mtime.toISOString(),
    }],
    identity: 'name+group',
    tokens,
  };
}

function validateFreshness(snapshot) {
  const today = todayString();
  const todayTokens = snapshot.tokens.filter((token) => String(token.last_used || '').startsWith(today));
  return {
    ok: todayTokens.length > 0,
    today,
    reason: todayTokens.length > 0
      ? `${todayTokens.length} token(s) have last_used on ${today}.`
      : `No token last_used date matches ${today}; cache/page data may be stale.`,
    today_tokens: todayTokens.map((token) => ({
      name: token.name,
      group: token.group,
      last_used: token.last_used,
    })),
  };
}

function compareSnapshots(previous, current) {
  const prevMap = new Map(previous.tokens.map((row) => [keyOf(row), row]));
  const curMap = new Map(current.tokens.map((row) => [keyOf(row), row]));
  const normal = [];
  const anomalies = [];

  for (const cur of current.tokens) {
    const prev = prevMap.get(keyOf(cur));
    if (!prev) {
      const usage = Math.max(cur.total - cur.remaining, 0);
      normal.push({
        status: 'new',
        name: cur.name,
        group: cur.group,
        kind: GROUP_KIND[cur.group] || cur.kind || 'Other token',
        ratio: cur.ratio,
        previous_remaining: null,
        previous_total: null,
        current_remaining: cur.remaining,
        current_total: cur.total,
        added_quota: cur.total,
        period_usage: roundMoney(usage),
        last_used: cur.last_used,
        note: '新出现 token，缺少上期基线，本期消耗暂按本次总额 - 本次剩余估算。',
      });
      continue;
    }

    if (cur.total < prev.total) {
      anomalies.push({
        status: 'quota_decreased',
        name: cur.name,
        group: cur.group,
        kind: GROUP_KIND[cur.group] || cur.kind || 'Other token',
        previous_remaining: prev.remaining,
        previous_total: prev.total,
        current_remaining: cur.remaining,
        current_total: cur.total,
        note: '本次总额度小于上次总额度，可能发生额度减少、重置或 token 迁移，未计入正常消耗排行。',
      });
      continue;
    }

    const added = Math.max(cur.total - prev.total, 0);
    const usage = Math.max(prev.remaining + added - cur.remaining, 0);
    normal.push({
      status: 'matched',
      name: cur.name,
      group: cur.group,
      kind: GROUP_KIND[cur.group] || cur.kind || 'Other token',
      ratio: cur.ratio,
      previous_remaining: prev.remaining,
      previous_total: prev.total,
      current_remaining: cur.remaining,
      current_total: cur.total,
      added_quota: roundMoney(added),
      period_usage: roundMoney(usage),
      last_used: cur.last_used,
    });
  }

  for (const prev of previous.tokens) {
    if (!curMap.has(keyOf(prev))) {
      anomalies.push({
        status: 'missing_current',
        name: prev.name,
        group: prev.group,
        kind: GROUP_KIND[prev.group] || prev.kind || 'Other token',
        previous_remaining: prev.remaining,
        previous_total: prev.total,
        current_remaining: null,
        current_total: null,
        note: '上次报告存在，本次 Token Management 未见，未计入正常消耗排行。',
      });
    }
  }

  normal.sort((a, b) => b.period_usage - a.period_usage);
  return { normal, anomalies };
}

function renderReport(previous, current, comparison, freshness) {
  const codexTotal = comparison.normal
    .filter((row) => row.group === 'vip_2')
    .reduce((sum, row) => sum + row.period_usage, 0);
  const claudeTotal = comparison.normal
    .filter((row) => row.group === 'vip_1_max_enterprise')
    .reduce((sum, row) => sum + row.period_usage, 0);
  const total = comparison.normal.reduce((sum, row) => sum + row.period_usage, 0);
  const top = comparison.normal[0];

  const rows = comparison.normal.map((row) => {
    const barWidth = total > 0 ? Math.max((row.period_usage / total) * 100, row.period_usage > 0 ? 2 : 0) : 0;
    return `
          <tr>
            <td>${escapeHtml(row.name)}</td>
            <td><span class="tag">${escapeHtml(row.group)}</span></td>
            <td>${escapeHtml(row.kind)}</td>
            <td class="right">${money(row.period_usage)}</td>
            <td class="right">${money(row.added_quota)}</td>
            <td class="right">${row.previous_remaining == null ? '-' : money(row.previous_remaining)}</td>
            <td class="right">${money(row.current_remaining)}</td>
            <td>${escapeHtml(row.last_used || '-')}</td>
            <td><div class="bar"><span style="width:${barWidth.toFixed(2)}%"></span></div></td>
          </tr>`;
  }).join('');

  const anomalyRows = comparison.anomalies.length === 0
    ? '<p class="small">未发现额度减少、消失 token 或其他需确认项目。</p>'
    : `<table>
        <thead>
          <tr>
            <th>Token/API 名称</th>
            <th>分组</th>
            <th>状态</th>
            <th class="right">上次剩余/总额</th>
            <th class="right">本次剩余/总额</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          ${comparison.anomalies.map((row) => `
          <tr>
            <td>${escapeHtml(row.name)}</td>
            <td><span class="tag">${escapeHtml(row.group)}</span></td>
            <td>${escapeHtml(row.status)}</td>
            <td class="right">${row.previous_remaining == null ? '-' : `${money(row.previous_remaining)} / ${money(row.previous_total)}`}</td>
            <td class="right">${row.current_remaining == null ? '-' : `${money(row.current_remaining)} / ${money(row.current_total)}`}</td>
            <td>${escapeHtml(row.note)}</td>
          </tr>`).join('')}
        </tbody>
      </table>`;

  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>本期对比 API 额度使用报告</title>
  <style>
    :root { --ink:#111827; --muted:#64748b; --line:#d7dee8; --paper:#f7f9fc; --panel:#fff; --blue:#2563eb; --orange:#ea580c; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; color:var(--ink); background:var(--paper); line-height:1.55; }
    .page { width:min(1180px, calc(100vw - 40px)); margin:0 auto; padding:36px 0 56px; }
    header { display:grid; grid-template-columns:1fr auto; gap:24px; align-items:end; padding-bottom:22px; border-bottom:2px solid var(--ink); }
    h1 { margin:0; font-size:34px; line-height:1.12; letter-spacing:0; }
    h2 { margin:0 0 14px; font-size:20px; letter-spacing:0; }
    section { margin-top:28px; }
    .subtitle, .small, .stamp { color:var(--muted); }
    .stamp { text-align:right; font-size:13px; white-space:nowrap; }
    .callout { border-left:4px solid var(--orange); background:#fff7ed; padding:14px 16px; border-radius:8px; color:#7c2d12; }
    .metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
    .metric { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }
    .metric .label { color:var(--muted); font-size:13px; }
    .metric .value { margin-top:6px; font-size:28px; font-weight:760; line-height:1.15; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
    .metric .note { margin-top:8px; color:var(--muted); font-size:12px; }
    table { width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; font-size:13px; }
    th, td { padding:10px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:middle; font-variant-numeric:tabular-nums; }
    th { background:#eef3fa; color:#243244; font-weight:700; white-space:nowrap; }
    tr:last-child td { border-bottom:0; }
    .right { text-align:right; }
    .tag { display:inline-block; padding:2px 8px; border-radius:999px; background:#e0ecff; color:#1d4ed8; font-size:12px; white-space:nowrap; }
    .bar { height:8px; width:100%; background:#e5e7eb; border-radius:999px; overflow:hidden; }
    .bar > span { display:block; height:100%; background:var(--blue); border-radius:inherit; }
    @media (max-width:820px) { header { grid-template-columns:1fr; } .stamp { text-align:left; } .metrics { grid-template-columns:repeat(2,minmax(0,1fr)); } }
  </style>
</head>
<body>
  <main class="page">
    <header>
      <div>
        <h1>本期对比 API 额度使用报告</h1>
        <div class="subtitle">基线：${escapeHtml(previous.captured_at)} 上一次报告快照；当前：${escapeHtml(current.captured_at)} Token Management 快照</div>
      </div>
      <div class="stamp">数据来源：www.micuapi.ai 控制台<br>生成时间：${escapeHtml(current.captured_at)}</div>
    </header>

    <section>
      <div class="callout">
        <strong>数据说明：</strong>本报告按两次额度快照对比计算本期消耗，不使用单次快照的“总额 - 剩余”作为本期用量。公式：本期消耗 = 上次剩余 + max(本次总额 - 上次总额, 0) - 本次剩余。若总额度减少，则列入异常区，不计入正常排行。新鲜度校验：${escapeHtml(freshness.reason)}
      </div>
    </section>

    <section>
      <h2>总览</h2>
      <div class="metrics">
        <div class="metric"><div class="label">本期总消耗</div><div class="value">${money(total)}</div><div class="note">正常匹配及新增 token 合计</div></div>
        <div class="metric"><div class="label">消耗最高 Token</div><div class="value">${top ? escapeHtml(top.name) : '-'}</div><div class="note">${top ? `${escapeHtml(top.group)} / ${money(top.period_usage)}` : '-'}</div></div>
        <div class="metric"><div class="label">Codex token 消耗</div><div class="value">${money(codexTotal)}</div><div class="note">vip_2 分组合计</div></div>
        <div class="metric"><div class="label">Claude Code token 消耗</div><div class="value">${money(claudeTotal)}</div><div class="note">vip_1_max_enterprise 分组合计</div></div>
      </div>
    </section>

    <section>
      <h2>每个 API / Token 本期消耗</h2>
      <p class="small">按本期消耗金额从大到小排序；vip_2 分组为 Codex token，vip_1_max_enterprise 分组为 Claude Code token。</p>
      <table>
        <thead>
          <tr>
            <th>Token/API 名称</th>
            <th>分组</th>
            <th>类型</th>
            <th class="right">本期消耗</th>
            <th class="right">期间加额</th>
            <th class="right">上次剩余</th>
            <th class="right">本次剩余</th>
            <th>最近使用</th>
            <th>消耗占比</th>
          </tr>
        </thead>
        <tbody>${rows}
        </tbody>
      </table>
    </section>

    <section>
      <h2>异常与需确认</h2>
      ${anomalyRows}
    </section>
  </main>
</body>
</html>`;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));
}

function usageSummary(comparison) {
  const total = comparison.normal.reduce((sum, row) => sum + row.period_usage, 0);
  const codex = comparison.normal.filter((row) => row.group === 'vip_2').reduce((sum, row) => sum + row.period_usage, 0);
  const claude = comparison.normal.filter((row) => row.group === 'vip_1_max_enterprise').reduce((sum, row) => sum + row.period_usage, 0);
  return {
    total_usage: roundMoney(total),
    codex_usage: roundMoney(codex),
    claude_code_usage: roundMoney(claude),
    top_token: comparison.normal[0] || null,
  };
}

function main() {
  const date = todayString();
  fs.mkdirSync(CONFIG.snapshotDir, { recursive: true });
  fs.mkdirSync(CONFIG.reportDir, { recursive: true });

  const previousSnapshotFile = ensureBaseline();
  const previous = loadJson(previousSnapshotFile);

  let current;
  let freshness;
  try {
    const candidate = findLatestTokenCacheResponse();
    current = snapshotFromTokenResponse(candidate);
    freshness = validateFreshness(current);
    if (!freshness.ok) {
      const failureFile = path.join(CONFIG.reportDir, `${date}_period_api_usage_failure.json`);
      writeJson(failureFile, {
        ok: false,
        reason: freshness.reason,
        login_url: CONFIG.loginUrl,
        current,
        previous_snapshot_file: previousSnapshotFile,
        generated_at: nowString(),
      });
      console.error(JSON.stringify({
        ok: false,
        reason: freshness.reason,
        loginUrl: CONFIG.loginUrl,
        failureFile,
      }, null, 2));
      process.exitCode = 2;
      return;
    }
  } catch (error) {
    const failureFile = path.join(CONFIG.reportDir, `${date}_period_api_usage_failure.json`);
    writeJson(failureFile, {
      ok: false,
      reason: error.message,
      login_url: CONFIG.loginUrl,
      previous_snapshot_file: previousSnapshotFile,
      generated_at: nowString(),
    });
    console.error(JSON.stringify({
      ok: false,
      reason: error.message,
      loginUrl: CONFIG.loginUrl,
      failureFile,
    }, null, 2));
    process.exitCode = 2;
    return;
  }

  const currentSnapshotFile = path.join(CONFIG.snapshotDir, `${date}_api_token_snapshot.json`);
  const comparison = compareSnapshots(previous, current);
  const reportHtml = renderReport(previous, current, comparison, freshness);
  const outReport = path.join(CONFIG.reportDir, `${date}_period_api_usage_report.html`);
  const outComparison = path.join(CONFIG.reportDir, `${date}_period_api_usage_comparison.json`);

  writeJson(currentSnapshotFile, current);
  fs.writeFileSync(outReport, reportHtml);
  writeJson(outComparison, { previous, current, comparison, freshness, summary: usageSummary(comparison) });

  console.log(JSON.stringify({
    ok: true,
    previousSnapshotFile,
    currentSnapshotFile,
    outReport,
    outComparison,
    freshness,
    summary: usageSummary(comparison),
    normalRows: comparison.normal.length,
    anomalies: comparison.anomalies.length,
  }, null, 2));
}

main();
