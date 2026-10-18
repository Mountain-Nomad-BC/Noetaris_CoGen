/* Fail-fast frontend source and recovered CSS verification. This is NOT a browser/E2E test. */
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const postcss = require('postcss');
const root = path.resolve(__dirname, '..', 'src');
const errors = [];
let sourceFiles = 0, localImports = 0, cssFiles = 0;
const imported = new Set();
function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    if (fs.statSync(p).isDirectory()) { walk(p); continue; }
    if (/\.css$/.test(name)) {
      cssFiles++;
      try { postcss.parse(fs.readFileSync(p, 'utf8'), { from: p }); }
      catch (e) { errors.push(`Bad CSS ${p}: ${e.message}`); }
    }
    const isScript = /\.(js|jsx)$/.test(name);
    if (isScript) sourceFiles++;
    if (!isScript) continue;
    const code = fs.readFileSync(p, 'utf8');
    const syntax = ts.createSourceFile(p, code, ts.ScriptTarget.Latest, true, name.endsWith('.jsx') ? ts.ScriptKind.JSX : ts.ScriptKind.JS);
    for (const problem of syntax.parseDiagnostics) errors.push(`${p}: ${ts.flattenDiagnosticMessageText(problem.messageText, ' ')}`);
    for (const found of code.matchAll(/(?:\bimport\s+(?:[\s\S]*?\s+from\s+)?|\bimport\s*\()\s*["']([^"']+)["']/g)) {
      const dep = found[1];
      if (!dep.startsWith('./') && !dep.startsWith('../') && !dep.startsWith('@/')) continue;
      localImports++;
      let dest = dep.startsWith('@/') ? path.join(root, dep.slice(2)) : path.resolve(path.dirname(p), dep);
      if (!['', '.js', '.jsx', '.json', '.css', '/index.js', '/index.jsx'].some(ext => fs.existsSync(dest + ext))) errors.push(`Missing import ${p}: ${dep}`);
      imported.add(dest);
    }
  }
}
walk(root);
for (const f of ['index.css', 'App.css']) {
  if (fs.readFileSync(path.join(root, f), 'utf8').includes('___CSS_LOADER_EXPORT___')) errors.push(`Webpack loader text remains in ${f}`);
}
if (fs.readFileSync(path.join(root, 'index.css'), 'utf8').includes(String.raw`\\`)) errors.push('Recovered CSS contains doubled selector escapes');
const app = fs.readFileSync(path.join(root, 'App.jsx'), 'utf8');
const authContext = fs.readFileSync(path.join(root, 'noetaris/state/AuthContext.jsx'), 'utf8');
const login = fs.readFileSync(path.join(root, 'noetaris/pages/public/LiveSignIn.jsx'), 'utf8');
if (/sessionStorage|localStorage/.test(authContext) || /sessionStorage|localStorage/.test(login)) errors.push('The live sign-in flow persists bearer credentials in Web Storage.');
if (/\b(?:NSAI_API_TOKEN|NSAI_ADMIN_TOKEN)\s*=\s*["'][^"']{24,}["']/.test(authContext + login)) errors.push('Embedded API credential assignment found in live auth source.');
const assetDir = path.join(root, '..', 'dist', 'assets');
for (const name of fs.existsSync(assetDir) ? fs.readdirSync(assetDir).filter(file => /\.js$/.test(file)) : []) {
  const bundle = fs.readFileSync(path.join(assetDir, name), 'utf8');
  if (/noetaris\.bearer|(?:NSAI_(?:API|ADMIN)_TOKEN)\s*=\s*["'][^"']{24,}["']/.test(bundle)) errors.push(`Persisted bearer marker or hard-coded API credential found in production JavaScript bundle ${name}.`);
}
for (const pathName of ['/app/chat', 'documents/:id', 'workflows/new', 'knowledge', 'library', 'demo-controls']) {
  if (!app.includes(pathName.replace('/app/',''))) errors.push(`Route not detected: ${pathName}`);
}
console.log(JSON.stringify({ sourceFiles, cssFiles, localImports, errors: errors.length }, null, 2));
if (errors.length) { console.error(errors.join('\n')); process.exitCode = 1; }
