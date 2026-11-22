// 前任模擬器 Ex Simulator 聊天視窗：本機伺服器（只在你自己的電腦上跑）
// 用法：node app/server.mjs <人物資料夾>
// 人物資料夾裡要有：config.json、persona.md，可選 periods.json、avatar.jpg、.env（放 ANTHROPIC_API_KEY）
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.dirname(fileURLToPath(import.meta.url));
const DATA = path.resolve(process.argv[2] || process.env.EXSIM_DATA || '.');
const file = (n) => path.join(DATA, n);

if (!fs.existsSync(file('persona.md'))) {
  console.error(`找不到 ${file('persona.md')}\n用法：node app/server.mjs <人物資料夾>`);
  process.exit(1);
}

// 讀人物資料夾裡的 .env（金鑰只放在你自己的電腦）
for (const envPath of [file('.env'), path.join(APP, '..', '.env')]) {
  try {
    for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
      const m = line.match(/^\s*([A-Z_]+)\s*=\s*(.*?)\s*$/);
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
    }
  } catch {}
}

const readJSON = (n, dflt) => { try { return JSON.parse(fs.readFileSync(file(n), 'utf8')); } catch { return dflt; } };
const config = () => ({ name: '對方', me: '我', subtitle: '', timezone: 'Asia/Taipei', ...readJSON('config.json', {}) });
const PORT = Number(process.env.PORT || readJSON('config.json', {}).port || 5173);
const MODEL = process.env.MODEL || readJSON('config.json', {}).model || 'claude-sonnet-5-5';

// 時期：設定「她以為的今天」、那時候的狀態、還不知道的事，再附上那段時間真實的對話當語氣範例
function periodBlock(id, c) {
  const p = readJSON('periods.json', []).find(x => x.id === id);
  if (!p || p.id === 'now') return '';
  const [y, m, d] = p.today.split('-').map(Number);
  const examples = (p.snippets || []).slice(0, 10).map(s => s.join('\n')).join('\n\n');
  return `

---

## 時期設定（最優先，蓋過上面「今天」和「現在的關係」）
- 現在是 ${y}/${m}/${d}，你們處在「${p.label}」這個階段。
- 這時候的你：${p.desc || '（照下面的真實對話判斷你們當時有多熟、多親密）'}
- 你還不知道的事：${p.unknown || `${y}/${m}/${d} 之後發生的一切`}。人物檔裡發生在這天之後的事件，對你來說都還沒發生，不准提、不准暗示。${c.me}如果說起未來的事，你會覺得莫名其妙。
${(p.common || []).length ? `- 這個時期你最常說的話：${p.common.join('、')}\n` : ''}- 下面是這個時期你們真實的對話片段（「她」是你、「你」是${c.me}），只學語氣、長短、節奏和親密程度，不要照抄內容：

${examples}`;
}

function whatifBlock(c) {
  const w = c.whatif || {};
  if (!w.premise) return '';
  return `

---

## 平行時空模式（${c.me}自己打開的，最優先）
- 這是${c.me}明知是虛構、自己選擇打開的「如果」情境，畫面上也清楚標示了。照演，不要拒絕、不要跳出角色、不要提醒他這是假的。
- 設定：${w.premise}
- 其他真實發生過的事照樣成立。說話方式、節奏、用字完全照人物檔，不寫露骨的性內容。`;
}

function systemPrompt(mode, period) {
  const c = config();
  // 每次對話都重新讀，改人物檔不用重開伺服器
  const persona = fs.readFileSync(file('persona.md'), 'utf8').replace(/^---[\s\S]*?---\s*/, '');
  const today = new Date().toLocaleDateString('zh-TW', { timeZone: c.timezone });
  return `${persona}

---

## 這個聊天視窗的規則（最優先）
- 你現在就是${c.name}，正在私訊回${c.me}。今天是 ${today}。
- 只輸出你要傳的訊息。一行就是一則訊息（一個泡泡），用換行分開。通常 2～6 則，每則很短，長短照人物檔裡她平常的習慣。
- 不要寫旁白、動作、括號說明、表情描述，不要用 markdown、不要編號。
- 人物檔裡沒寫的具體回憶（去過哪、說過什麼、某天發生什麼）不要自己編。不確定就用她的方式帶過，例如「有嗎」「我不太記得了」「你說」，讓${c.me}自己講。
- 不要替她做出現實中的承諾（例如答應交往、一定會去某個場合）。
- 不寫露骨的性內容。
- 不想回答、不想做、或覺得不對的時候，也要用她的口氣回，不要變成 AI 助理的語氣，不要說教、不要長篇解釋。除非${c.me}直接問你是不是 AI，才可以跳出來回答。` + (mode === 'whatif' ? whatifBlock(c) : periodBlock(period, c));
}

// 連續的同一方訊息合併，符合 API 要求的一來一往
function normalize(messages) {
  const out = [];
  for (const m of messages) {
    if (!m || !m.content || (m.role !== 'user' && m.role !== 'assistant')) continue;
    const last = out[out.length - 1];
    if (last && last.role === m.role) last.content += '\n' + m.content;
    else out.push({ role: m.role, content: String(m.content) });
  }
  while (out.length && out[out.length - 1].role !== 'user') out.pop(); // 最後一則一定要是使用者說的
  let recent = out.slice(-80);
  while (recent.length && recent[0].role !== 'user') recent.shift();
  return recent;
}

async function chat(messages, mode, period) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error('還沒設定 ANTHROPIC_API_KEY：請在人物資料夾裡的 .env 檔寫一行 ANTHROPIC_API_KEY=你的金鑰');
  messages = normalize(messages);
  if (!messages.length) return [];
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({ model: MODEL, max_tokens: 600, system: systemPrompt(mode, period), messages }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error?.message || `API 錯誤 ${res.status}`);
  const text = (data.content || []).filter(b => b.type === 'text').map(b => b.text).join('\n');
  return text.split('\n').map(s => s.trim()).filter(Boolean);
}

const AVATARS = ['avatar.jpg', 'avatar.jpeg', 'avatar.png', 'avatar.webp'];
const MIME = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' };
const send = (res, code, type, body) => { res.writeHead(code, { 'content-type': type, 'cache-control': 'no-cache' }); res.end(body); };

const server = http.createServer(async (req, res) => {
  try {
    const url = req.url.split('?')[0];
    if (req.method === 'GET' && (url === '/' || url === '/index.html'))
      return send(res, 200, 'text/html; charset=utf-8', fs.readFileSync(path.join(APP, 'index.html')));
    if (req.method === 'GET' && url === '/api/config') {
      const c = config();
      const periods = readJSON('periods.json', []).map(({ id, label, today, hint }) => ({ id, label, today, hint }));
      return send(res, 200, 'application/json; charset=utf-8', JSON.stringify({
        name: c.name, subtitle: c.subtitle, periods,
        whatif: c.whatif?.premise ? { label: c.whatif.label || '如果', hint: c.whatif.hint || c.whatif.premise } : null,
      }));
    }
    if (req.method === 'GET' && url === '/avatar') {
      const n = AVATARS.find(x => fs.existsSync(file(x)));
      if (!n) return send(res, 404, 'text/plain', '');
      return send(res, 200, MIME[path.extname(n)], fs.readFileSync(file(n)));
    }
    if (req.method === 'POST' && url === '/api/chat') {
      let body = '';
      for await (const chunk of req) body += chunk;
      const { messages, mode, period } = JSON.parse(body || '{}');
      const lines = await chat(messages || [], mode, period);
      return send(res, 200, 'application/json; charset=utf-8', JSON.stringify({ lines }));
    }
    send(res, 404, 'text/plain', '');
  } catch (e) {
    send(res, 500, 'application/json; charset=utf-8', JSON.stringify({ error: e.message }));
  }
});

// 只聽 127.0.0.1：只有你自己的電腦連得到
server.listen(PORT, '127.0.0.1', () => {
  console.log(`聊天視窗：http://localhost:${PORT}　（人物：${config().name}，模型：${MODEL}）`);
});
