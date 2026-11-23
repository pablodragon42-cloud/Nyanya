// usage: node render.js <startFrame> <endFrame> <out.mp4|dir> [--png]
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const ROOT = __dirname, FPS = 30;
const types = { '.js': 'text/javascript', '.html': 'text/html', '.ttf': 'font/ttf' };
const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); r.end(d); }); });
(async () => {
  const [a, b, out] = process.argv.slice(2); const s = +a, e = +b; const stills = process.argv.includes('--png');
  await new Promise(r => srv.listen(0, r)); const port = srv.address().port;
  const br = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const pg = await br.newPage({ viewport: { width: 1920, height: 1080 } });
  pg.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.error('[page]', m.text().slice(0, 300)); });
  await pg.goto(`http://127.0.0.1:${port}/index.html`);
  await pg.waitForFunction(() => window.READY || window.ERR, null, { timeout: 600000 });
  const err = await pg.evaluate(() => window.ERR); if (err) { console.error(err); process.exit(1); }
  let ff;
  if (!stills) {
    ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  } else fs.mkdirSync(out, { recursive: true });
  const t0 = Date.now();
  const list = process.argv.find(x => x.startsWith('--frames=')); const frames = list ? list.slice(9).split(',').map(Number) : null;
  const seq = frames || Array.from({ length: e - s }, (_, i) => s + i);
  for (const f of seq) {
    const url = await pg.evaluate(t => window.renderFrame(t), f / FPS);
    const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    if (stills) fs.writeFileSync(path.join(out, `f${String(f).padStart(5, '0')}.jpg`), buf);
    else if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 30 === 0) console.error(`frame ${f} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  if (ff) { ff.stdin.end(); await new Promise(r => ff.on('close', r)); }
  await br.close(); srv.close();
})();
