import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve('.');
const source = path.join(root, 'src');
const read = relative => fs.readFileSync(path.join(source, relative), 'utf8');

test('auth credentials are neither hard-coded nor read from persistent Web Storage', () => {
  const auth = read('noetaris/state/AuthContext.jsx');
  const signIn = read('noetaris/pages/public/LiveSignIn.jsx');
  assert.doesNotMatch(auth, /sessionStorage|localStorage/);
  assert.doesNotMatch(signIn, /sessionStorage|localStorage/);
  assert.doesNotMatch(auth, /(?:NSAI_(?:API|ADMIN)_TOKEN)\s*=\s*["'][^"']{24,}["']/);
});

test('profile sign-out uses canonical server logout and only leaves after confirmation', () => {
  const profile = read('noetaris/components/ProfileDropdown.jsx');
  const auth = read('noetaris/state/AuthContext.jsx');
  assert.match(profile, /const\s+\{\s*logout\s*,\s*identity\s*\}\s*=\s*useAuth\(\)/);
  assert.match(profile, /if\s*\(!await\s+logout\(\)\)/);
  assert.match(profile, /nav\('\/login'\)/);
  assert.match(auth, /return\s+true;\s*\}\s*catch\s*\(error\)\s*\{[\s\S]*?return\s+false;/);
  assert.doesNotMatch(profile, /sessionStorage|localStorage/);
});

test('fixture-backed floating assistant is unavailable in live mode', () => {
  const assistant = read('noetaris/components/FloatingAssistant.jsx');
  assert.match(assistant, /if\s*\(mode\s*!==\s*["']demo["']\)/);
  assert.match(assistant, /data-testid=["']floating-live-workspace-unavailable["']/);
  assert.match(assistant, /<DemoFloatingAssistant\s*\/>/);
});

test('live shell does not expose fixture notifications, placeholder links, or false readiness', () => {
  const shell = read('noetaris/layout/AppShell.jsx');
  const operations = read('noetaris/pages/app/OperationsPages.jsx');
  assert.match(shell, /const liveNavDomains = \[/);
  assert.match(shell, /mode === "demo" \? navDomains : liveNavDomains/);
  assert.match(shell, /mode === "demo" \? notifications\.length : null/);
  assert.match(shell, /Notifications unavailable/);
  assert.doesNotMatch(shell, /OPERATOR READY|\/app\/documents\/doc-1/);
  assert.match(operations, /LIVE FEED UNAVAILABLE/);
  assert.match(operations, /No sample notifications are shown/);
});

test('fixture-backed operational routes are explicitly unavailable in live mode', () => {
  const app = fs.readFileSync(path.join(source, 'App.jsx'), 'utf8');
  assert.match(app, /function PreviewOnlyFeature\(\{ name, children \}\)/);
  assert.match(app, /if \(mode !== "live"\) return children/);
  for (const route of [
    'templates', 'agents', 'evaluations',
    'agents/new', 'agents/:id', 'evidence',
    'workflows', 'workflows/new', 'workflows/:id/edit', 'workflows/:id/versions',
    'executions', 'executions/:id', 'demo-controls',
  ]) {
    const routeBlock = app.match(new RegExp(`<Route path="${route.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')}"[^\\n]+`));
    assert.ok(routeBlock, `Missing route ${route}`);
    assert.match(routeBlock[0], /PreviewOnlyFeature/, `Live-mode fixture boundary missing for ${route}`);
  }
});

test('research search reports failures and does not invent evidence precision or source filters', () => {
  const research = read('noetaris/pages/app/ResearchPage.jsx');
  assert.match(research, /setSearchError\(error\.message/);
  assert.match(research, /Unable to load sources:/);
  assert.match(research, /Candidate excerpts/);
  assert.match(research, /not verified answers, exhaustive coverage, or engineering determinations/);
  assert.match(research, /Search results are not filtered to this list/);
  assert.match(research, /Review status not supplied/);
  assert.match(research, /Locator: \{locator \|\| 'Not supplied'\}/);
  assert.doesNotMatch(research, /Exact Geometry|verified provenance|line:1|setSelectedDoc/);
  assert.doesNotMatch(research, /console\.error/);
});

test('application shell respects the operating system reduced-motion preference', () => {
  const shell = read('noetaris/layout/AppShell.jsx');
  assert.match(shell, /matchMedia\?\.\('\(prefers-reduced-motion: reduce\)'\)/);
  assert.match(shell, /dataset\.reduceMotion = media\?\.matches \? 'true' : 'false'/);
  assert.match(shell, /media\?\.addEventListener\('change', update\)/);
  assert.doesNotMatch(shell, /dataset\.reduceMotion = 'false'/);
});

test('command-center telemetry has no fabricated count or model-readiness defaults', () => {
  const dashboard = read('noetaris/pages/app/CommandCenter.jsx');
  assert.doesNotMatch(dashboard, /docCount:\s*20|claimCount:\s*20|conflictsCount:\s*1|verifiedCount:\s*9/);
  assert.doesNotMatch(dashboard, /modelData\?\.status\s*===\s*['"]ready['"]\s*\|\|\s*true/);
  assert.match(dashboard, /conflict_analysis_complete/);
  assert.match(dashboard, /"Unavailable"/);
});

test('public brand casing and claims match the preview deployment state', () => {
  const logo = read('noetaris/brand/Logo.jsx');
  const header = read('noetaris/layout/PublicHeader.jsx');
  const landing = read('noetaris/pages/public/LandingPage.jsx');
  const marketing = read('noetaris/pages/public/MarketingPages.jsx');
  const audit = fs.readFileSync(path.join(root, 'scripts/audit-pages.mjs'), 'utf8');
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.match(logo, /Noetaris <span/);
  assert.match(header, /hidden xl:flex/);
  assert.match(header, /className="xl:hidden n-btn-ghost/);
  assert.match(landing, /RESEARCH CANDIDATE/);
  assert.match(landing, /designed around your sources/);
  assert.doesNotMatch(landing, /grounded in your sources/);
  assert.doesNotMatch(landing, /LIVE PLATFORM|24 orchestrated|Routed · policy aware|Enterprise Ready/);
  assert.doesNotMatch(landing + marketing, /NOETARIS/);
  assert.match(landing, /Public deployment and private-user content admission remain pending/);
  assert.match(landing, /Check Access/);
  assert.match(marketing, /Release admission is denied/);
  assert.match(marketing, /AMD hosted Gemma is selected; automatic dispatch, voice and Evolus remain incomplete/);
  assert.doesNotMatch(marketing, /50 verified routes|Full OAuth|What runs today|Data residency/);
  assert.match(audit, /Refusing to overwrite existing audit evidence/);
  assert.match(audit, /protectedRoutesGated/);
  assert.match(audit, /responsiveOverflow/);
  assert.match(audit, /authReady/);
  assert.match(audit, /providerControlsSafe/);
  assert.match(audit, /loginResponsive/);
  assert.match(audit, /loginOverflow\.length/);
  assert.match(html, /<title>Noetaris CoGen \| Engineering Intelligence<\/title>/);
});

test('preview login avoids unsupported trust claims and skips hidden WebGL on mobile', () => {
  const login = read('noetaris/pages/public/LoginPage.jsx');
  assert.match(login, /matchMedia\("\(min-width: 1024px\)"\)/);
  assert.match(login, /\{showHeroScene && \(/);
  assert.doesNotMatch(login, /Identity-scoped sources|Exact citation geometry|Walk into a governed workspace/);
  assert.doesNotMatch(login, /Every source, model and workflow is scoped to your identity/);
  assert.match(login, /does not authenticate source access or certify isolation/);
  assert.match(login, /Google sign-in unavailable/);
  assert.match(login, /GitHub sign-in unavailable/);
  assert.match(login, /useState\(""\)/);
});

test('live sign-in uses Noetaris branding and does not imply private content is admitted', () => {
  const liveSignIn = read('noetaris/pages/public/LiveSignIn.jsx');
  const audit = fs.readFileSync(path.join(root, 'scripts/audit-pages.mjs'), 'utf8');
  assert.match(liveSignIn, /Sign in to Noetaris/);
  assert.match(liveSignIn, /Private document access remains unavailable until separately admitted/);
  assert.doesNotMatch(liveSignIn, /Sign in to NSAI|verifies identity and resource permissions/);
  assert.match(audit, /loginText\.includes\('Sign in to Noetaris'\)/);
  assert.doesNotMatch(audit, /loginText\.includes\('Sign in to NSAI'\)/);
});

test('the public asset bundle contains no saved bearer credential marker or literal credential assignment', () => {
  const assets = path.join(root, 'dist/assets');
  assert.ok(fs.existsSync(assets), 'Production bundle missing; build must run before credential scanner.');
  for (const entry of fs.readdirSync(assets, { withFileTypes: true })) {
    if (!entry.isFile() || !/\.(?:js|css|html)$/.test(entry.name)) continue;
    const content = fs.readFileSync(path.join(assets, entry.name), 'utf8');
    assert.doesNotMatch(content, /noetaris\.bearer/, `Persisted bearer marker leaked in ${entry.name}`);
    assert.doesNotMatch(content, /NSAI_API_TOKEN/, `API token identifier leaked in ${entry.name}`);
    assert.doesNotMatch(content, /(?:TOKEN|BEARER)\s*[=:]\s*["'][A-Za-z0-9_-]{32,}["']/, `Possible hard-coded credential leaked in ${entry.name}`);
  }
});
