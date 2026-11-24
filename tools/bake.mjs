// 기본 화면(롯데월드타워 반경 5 km) 데이터를 미리 만들어 data.js 로 저장한다(window.TOWN3D_BAKED).
// 앱(index.html)을 헤드리스 브라우저로 열어 ?dump=1 로 받은 데이터를 그대로 기록하므로, 앱과 같은 변환 규칙을 쓴다.
// 1순위 Overpass(차로 수·신호등·3D 부품·노선색까지), 실패하면 벡터 타일(OpenFreeMap).
// 사용: npm i --no-save playwright && npx playwright install chromium && node tools/bake.mjs
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const ADDR = process.env.BAKE_ADDR || '롯데월드타워';
const RKM = process.env.BAKE_R || '5';
const OUT = process.env.BAKE_OUT || 'data.js';
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json' };

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p === '/') p = '/index.html';
  const f = path.join(ROOT, path.normalize(p));
  if (!f.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
  fs.readFile(f, (e, d) => {
    if (e) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream' });
    res.end(d);
  });
}).listen(8765);

const browser = await chromium.launch();
async function run(src, timeout) {
  const page = await browser.newPage();
  page.on('console', m => { if (m.type() === 'error') console.log('[page]', m.text()); });
  const url = `http://localhost:8765/index.html?addr=${encodeURIComponent(ADDR)}&r=${RKM}&dump=1&src=${src}`;
  console.log('open', url);
  await page.goto(url);
  await page.waitForFunction(() => window.__DUMP || window.__DUMPERR, null, { timeout, polling: 2000 });
  const [d, e] = await page.evaluate(() => [window.__DUMP || null, window.__DUMPERR || null]);
  await page.close();
  return [d, e];
}

let out = null, used = '';
for (const [src, t] of [['overpass', 15 * 60e3], ['tiles', 6 * 60e3]]) {
  try {
    const [d, e] = await run(src, t);
    if (d) { out = d; used = src; break; }
    console.log(src, 'failed:', e);
  } catch (e) { console.log(src, 'error:', e.message); }
}
await browser.close();
server.close();
if (!out) { console.error('no data'); process.exit(1); }
const D = JSON.parse(out);
D.baked = { at: new Date().toISOString(), src: used, addr: ADDR, r: +RKM };
fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, '/* 롯데월드타워 반경 5 km · © OpenStreetMap 기여자 (ODbL) · tools/bake.mjs 로 생성 */\nwindow.TOWN3D_BAKED=' + JSON.stringify(D) + ';\n');
console.log(`saved ${OUT} (${used}) buildings=${D.B.length} roads=${D.H.length} rail=${D.RLW.length} bytes=${fs.statSync(OUT).size}`);
