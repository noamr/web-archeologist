#!/usr/bin/env node
/**
 * web-archeologist CLI: the non-interactive parts of the `web-archeologist`
 * skill, so an agent (or a human) can call one subcommand instead of having
 * the whole protocol in context.
 *
 * Every subcommand prints a single JSON document on stdout and exits 0 on
 * success, nonzero with `{"error": "..."}` on failure. Keep it that way --
 * callers pipe the output through `jq`.
 *
 * No npm deps: this is meant to run from a fresh clone with just Node >= 20.
 */

import { spawnSync } from 'node:child_process';
import { mkdirSync, existsSync, readdirSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, relative, resolve } from 'node:path';

const CACHE = process.env.WEB_ARCHEOLOGIST_CACHE
  || process.env.GEMINI_CACHE && join(process.env.GEMINI_CACHE, 'specs')
  || join(homedir(), '.cache', 'web-archeologist', 'specs');

// Domain -> { repo: "org/name", file?: filename inside the repo }. file is a
// hint for `resolve`; when absent, resolve greps *.bs and source.
const REPO_MAP = [
  { host: /^html\.spec\.whatwg\.org$/, repo: 'whatwg/html', file: 'source' },
  { host: /^dom\.spec\.whatwg\.org$/, repo: 'whatwg/dom', file: 'dom.bs' },
  { host: /^fetch\.spec\.whatwg\.org$/, repo: 'whatwg/fetch', file: 'fetch.bs' },
  { host: /^url\.spec\.whatwg\.org$/, repo: 'whatwg/url', file: 'url.bs' },
  { host: /^xhr\.spec\.whatwg\.org$/, repo: 'whatwg/xhr', file: 'xhr.bs' },
  { host: /^streams\.spec\.whatwg\.org$/, repo: 'whatwg/streams', file: 'index.bs' },
  { host: /^([a-z0-9-]+)\.spec\.whatwg\.org$/, repo: (m) => `whatwg/${m[1]}`, file: (m) => `${m[1]}.bs` },
  { host: /^drafts\.csswg\.org$/, repo: 'w3c/csswg-drafts' },
  { host: /^httpwg\.org$/, repo: 'httpwg/http-extensions' },
  { host: /^([a-z0-9-]+)\.github\.io$/, repo: (m, u) => inferWicg(m[1], u) },
];

function inferWicg(org, u) {
  // wicg.github.io/<name>/ -> WICG/<name>; same shape for most w3c github pages.
  const seg = u.pathname.split('/').filter(Boolean)[0];
  if (!seg) return `${org}/${org}`;
  const map = { wicg: 'WICG', w3c: 'w3c' };
  return `${map[org] ?? org}/${seg}`;
}

function die(msg, code = 1) {
  process.stdout.write(JSON.stringify({ error: msg }) + '\n');
  process.exit(code);
}

function ok(value) {
  process.stdout.write(JSON.stringify(value) + '\n');
}

function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', maxBuffer: 64 << 20, ...opts });
  if (r.error) throw r.error;
  return r;
}

async function cmdXref(args) {
  const term = args._[0];
  if (!term) die('xref <term>');
  const body = JSON.stringify({ keys: [{ term }] });
  const r = await fetch('https://respec.org/xref', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    signal: AbortSignal.timeout(15_000),
  });
  if (!r.ok) die(`respec.org/xref ${r.status}`);
  const j = await r.json();
  const hits = (j.result?.[0]?.[1] ?? []).map((h) => ({
    spec: h.spec ?? h.shortname,
    type: h.type,
    uri: h.uri,
    normative: h.normative,
  }));
  ok({ term, hits });
}

async function cmdMdn(args) {
  const q = args._.join(' ');
  if (!q) die('mdn <query>');
  const r = await fetch(`https://developer.mozilla.org/api/v1/search?q=${encodeURIComponent(q)}`, {
    signal: AbortSignal.timeout(15_000),
  });
  if (!r.ok) die(`mdn ${r.status}`);
  const j = await r.json();
  const docs = (j.documents ?? []).slice(0, args.limit ?? 5).map((d) => ({
    title: d.title,
    url: `https://developer.mozilla.org${d.mdn_url}`,
    summary: d.summary,
  }));
  ok({ query: q, docs });
}

function parseSpecUrl(url) {
  const u = new URL(url);
  for (const m of REPO_MAP) {
    const mh = u.host.match(m.host);
    if (!mh) continue;
    const repo = typeof m.repo === 'function' ? m.repo(mh, u) : m.repo;
    const file = typeof m.file === 'function' ? m.file(mh, u) : m.file;
    return { repo, file, fragment: u.hash.slice(1), url };
  }
  return null;
}

function ensureClone(repo, { deepen } = {}) {
  mkdirSync(CACHE, { recursive: true });
  const dir = join(CACHE, repo.replace('/', '--'));
  if (!existsSync(join(dir, '.git'))) {
    const r = run('git', ['clone', '--depth', '1000', `https://github.com/${repo}.git`, dir]);
    if (r.status !== 0) throw new Error(`clone ${repo}: ${r.stderr.trim()}`);
  }
  if (deepen) {
    const r = run('git', ['-C', dir, 'fetch', '--unshallow'], { stdio: 'pipe' });
    // --unshallow fails with "not shallow" once done; ignore that.
    if (r.status !== 0 && !/not shallow/i.test(r.stderr)) {
      throw new Error(`unshallow ${repo}: ${r.stderr.trim()}`);
    }
  }
  return dir;
}

// Given a cloned spec repo, find the file and line where `fragment` is defined.
// Heuristics mirror the skill: <dfn id|data-x=fragment> with common prefixes,
// then multi-line <dfn ...>data-x="fragment", then propdef `Name: fragment`.
function locateFragment(dir, file, fragment) {
  const candidateFiles = file ? [file] : scanBsFiles(dir);
  // Attribute quotes are optional in Bikeshed sources (`id=foo`), and the
  // fragment often has one of these implicit prefixes. Grep's ERE has no
  // non-capturing groups or lookaheads, so the terminator is a character
  // class -- enough to keep `main-fetch` from also matching
  // `concept-main-fetch-foo`.
  const end = `["'> \\t]`;
  const prefix = `(concept-|rel-|attr-|dom-)?`;
  const esc = escapeRe(fragment);
  const needles = [
    `<dfn[^>]*[ \\t](id|data-x)=["']?${prefix}${esc}${end}`,
    `data-x=["']?${esc}${end}`,
    `^[ \\t]*Name:[ \\t]*${esc}[ \\t]*$`,
  ];
  for (const f of candidateFiles) {
    const path = join(dir, f);
    if (!existsSync(path)) continue;
    const r = run('grep', ['-nE', needles.join('|'), path]);
    if (r.status === 0) {
      const first = r.stdout.split('\n', 1)[0];
      const [line, ...rest] = first.split(':');
      return { file: f, line: Number(line), match: rest.join(':').trim() };
    }
  }
  return null;
}

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function scanBsFiles(dir) {
  const out = [];
  const walk = (d) => {
    for (const e of readdirSync(d, { withFileTypes: true })) {
      if (e.name.startsWith('.')) continue;
      const p = join(d, e.name);
      if (e.isDirectory()) { walk(p); continue; }
      if (/\.bs$|^source$|^index\.bs$/.test(e.name)) out.push(relative(dir, p));
    }
  };
  walk(dir);
  return out;
}

async function cmdResolve(args) {
  const url = args._[0];
  if (!url) die('resolve <spec-url>');
  const p = parseSpecUrl(url);
  if (!p) die(`no repo mapping for ${new URL(url).host}`);
  if (!p.fragment) die(`url has no #fragment`);
  const dir = ensureClone(p.repo);
  const hit = locateFragment(dir, p.file, p.fragment);
  if (!hit) die(`no dfn found for #${p.fragment} in ${p.repo}/${p.file ?? '(any .bs)'}`);
  ok({ repo: p.repo, dir, fragment: p.fragment, file: hit.file, line: hit.line, match: hit.match });
}

async function cmdBlame(args) {
  const url = args._[0];
  if (!url) die('blame <spec-url>');
  const p = parseSpecUrl(url);
  if (!p) die(`no repo mapping for ${new URL(url).host}`);
  const dir = ensureClone(p.repo, { deepen: true });
  const hit = locateFragment(dir, p.file, p.fragment);
  if (!hit) die(`no dfn found for #${p.fragment}`);

  // Fast pickaxe: last touch and earliest touch of this line's content.
  const blame = run('git', ['-C', dir, 'blame', '-L', `${hit.line},${hit.line}`,
    '--porcelain', hit.file]);
  const lastSha = blame.stdout.split(/\s+/)[0];
  const lineContent = blame.stdout.split('\n').find((l) => l.startsWith('\t'))?.slice(1) ?? hit.match;

  // Earliest commit that introduced that exact text in that file.
  const pickaxe = run('git', ['-C', dir, 'log', '-S', lineContent, '--oneline', '--reverse',
    '--', hit.file]);
  const firstLine = pickaxe.stdout.split('\n').filter(Boolean)[0] ?? '';
  const firstSha = firstLine.split(' ', 1)[0];

  const commitInfo = (sha) => {
    if (!sha) return null;
    const r = run('git', ['-C', dir, 'show', '-s', '--format=%H%n%an%n%aI%n%s%n%b', sha]);
    const [h, an, ai, subject, ...bodyLines] = r.stdout.split('\n');
    return { sha: h, author: an, date: ai, subject, body: bodyLines.join('\n').trim() };
  };

  ok({
    repo: p.repo,
    fragment: p.fragment,
    file: hit.file,
    line: hit.line,
    last: commitInfo(lastSha),
    first: commitInfo(firstSha),
  });
}

async function cmdIrc(args) {
  const term = args._.join(' ');
  if (!term) die('irc <term>');
  const dir = ensureClone('KrijnHoetmer/irc-logs');
  const r = run('grep', ['-rniE', term, join(dir, 'whatwg')]);
  const matches = r.stdout.split('\n').filter(Boolean).slice(0, args.limit ?? 50)
    .map((l) => {
      const idx = l.indexOf(':');
      const idx2 = l.indexOf(':', idx + 1);
      return { path: relative(dir, l.slice(0, idx)), line: Number(l.slice(idx + 1, idx2)), text: l.slice(idx2 + 1) };
    });
  ok({ term, count: matches.length, matches });
}

function cmdRepo(args) {
  const url = args._[0];
  if (!url) die('repo <spec-url>');
  const p = parseSpecUrl(url);
  if (!p) die(`no repo mapping for ${new URL(url).host}`);
  ok(p);
}

function parseArgs(argv) {
  const out = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const eq = a.indexOf('=');
      if (eq > 0) out[a.slice(2, eq)] = a.slice(eq + 1);
      else if (argv[i + 1] && !argv[i + 1].startsWith('-')) out[a.slice(2)] = argv[++i];
      else out[a.slice(2)] = true;
    } else {
      out._.push(a);
    }
  }
  if (out.limit) out.limit = Number(out.limit);
  return out;
}

const USAGE = `web-archeologist <cmd> [args]

  xref <term>           Look up a term through respec.org/xref.
  mdn <query>           Top MDN docs for a query.
  resolve <spec-url>    Find file + line of a #fragment's <dfn> in its repo.
  blame <spec-url>      resolve + earliest/latest commits for that line.
  irc <term>            grep WHATWG IRC logs for a term.
  repo <spec-url>       Print the (repo, file, fragment) mapping.

Cache: ${CACHE} (set WEB_ARCHEOLOGIST_CACHE to override).
Output: one JSON document on stdout; errors go there too as {"error": ...}.`;

async function main() {
  const [, , cmd, ...rest] = process.argv;
  if (!cmd || cmd === '-h' || cmd === '--help') { console.error(USAGE); process.exit(cmd ? 0 : 2); }
  const args = parseArgs(rest);
  const handlers = {
    xref: cmdXref, mdn: cmdMdn, resolve: cmdResolve, blame: cmdBlame,
    irc: cmdIrc, repo: cmdRepo,
  };
  const h = handlers[cmd];
  if (!h) die(`unknown command: ${cmd}`);
  try { await h(args); }
  catch (e) { die(e.message || String(e)); }
}

main();
