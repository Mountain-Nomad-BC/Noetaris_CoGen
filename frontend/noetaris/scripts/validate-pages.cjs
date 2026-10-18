/* Route inventory and production bundle guard. This is static validation, not browser certification. */
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const app = fs.readFileSync(path.join(root, 'src/App.jsx'), 'utf8');
const html = fs.readFileSync(path.join(root, 'dist/index.html'), 'utf8');
const routePatterns = [...app.matchAll(/<Route\s+path="([^"]+)"/g)].map(match => match[1]);
const routes = [...new Set([...routePatterns.filter(route => route.startsWith('/') && route !== '*' && route !== '/auth/callback'), '/app', ...routePatterns.filter(route => !route.startsWith('/') && route !== '' && route !== '*').map(route => `/app/${route}`)])];
const missing = [];
const authContext = fs.readFileSync(path.join(root, 'src/noetaris/state/AuthContext.jsx'), 'utf8');
const signIn = fs.readFileSync(path.join(root, 'src/noetaris/pages/public/LiveSignIn.jsx'), 'utf8');
if (/sessionStorage|localStorage/.test(authContext)) missing.push('Bearer credentials must not be read from or persisted to Web Storage.');
if (/sessionStorage|localStorage/.test(signIn)) missing.push('Live sign-in must not persist user credentials.');
for (const route of routes) {
  const href = route.startsWith('/') ? route : `/app/${route}`;
  if (!html.includes('assets/') || !fs.readdirSync(path.join(root, 'dist/assets')).length) missing.push(`No built asset payload for route ${href}`);
}
const references = [...html.matchAll(/(?:src|href)="(\/assets\/[^\"]+)"/g)].map(match => match[1]);
for (const asset of references) if (!fs.existsSync(path.join(root, 'dist', asset.slice(1)))) missing.push(`Missing referenced bundle ${asset}`);
if (!routes.includes('/app') || !routes.includes('/app/library') || !routes.includes('/app/chat') || !routes.includes('/app/settings')) missing.push('Required application route missing');
const bundledScripts = [...html.matchAll(/(?:src|href)="(\/assets\/[^\"]+\.js)"/g)].map(match => match[1]);
const bannedBundleMarkers = [/noetaris\.bearer/, /NSAI_API_TOKEN/, /(?:TOKEN|BEARER)\s*[=:]\s*["'][A-Za-z0-9_-]{32,}["']/];
for (const marker of bannedBundleMarkers) for (const asset of bundledScripts) {
  const content = fs.readFileSync(path.join(root, 'dist', asset.slice(1)), 'utf8');
  if (marker.test(content)) missing.push(`Credential persistence or hard-coded token assignment detected in ${asset}`);
}
const result = { status: missing.length ? 'FAIL' : 'PASS', explicitRoutes: routes.length, builtAssetFiles: fs.readdirSync(path.join(root, 'dist/assets')).length, htmlAssetReferences: references.length, checks: { credentialFreeBundle: missing.every(error => !error.includes('embedded secret') && !error.includes('Credential persistence')) }, errors: missing };
console.log(JSON.stringify(result, null, 2));
if (missing.length) process.exitCode = 1;
