#!/usr/bin/env python3
"""把聊天軟體的匯出檔整理成同一種格式（JSON Lines），給後面的蒸餾步驟用。

支援：
  LINE       聊天記錄 .txt（中文、英文、日文介面皆可）
  Instagram  官方下載的 message_*.json
  Messenger  Facebook 下載的 message_*.json，或新版加密聊天下載的 .json
  WhatsApp   匯出聊天 .txt（iOS／Android 兩種格式）
  Telegram   Telegram Desktop 匯出的 result.json

用法：
  python3 parse.py --me "我的名字,我的另一個暱稱" -o chat.jsonl 檔案或資料夾 [...]
  python3 parse.py --list 檔案或資料夾 [...]      # 只列出每個檔案裡出現的名字

輸出每一行：{"t": "2025-06-26T23:04:00", "who": "me"|"them", "name": "...", "text": "...", "src": "LINE"}
只保留一對一聊天的文字訊息；貼圖、照片、通話、收回等不是文字的內容會被拿掉。
"""
import argparse, json, os, re, sys, datetime as dt
from pathlib import Path

# 不是文字內容的訊息（各平台、各語言）
NOISE = re.compile(
    r'^(\[(貼圖|照片|影片|圖片|檔案|語音訊息|語音|相簿|位置訊息|聯絡資訊|記事本|Sticker|Photo|Video|File|Voice message|Album|Location|Contact|スタンプ|写真|動画|ファイル|ボイスメッセージ)\]'
    r'|☎.*|.*(通話時間|未接來電|取消通話|Call time|Missed call|Canceled call|通話時間).*'
    r'|.*(已收回訊息|收回了訊息|unsent a message|メッセージの送信を取り消しました).*'
    r'|You sent an attachment\.?|.* sent an attachment\.?|.*傳送了附件。?'
    r'|Liked a message|.*對訊息按讚.*|Reacted .* to your message|.* reacted .* to your message'
    r'|<(Media omitted|已略過媒體|媒體已略過|附件已省略)>|(image|video|audio|sticker|GIF|document) omitted'
    r'|This message was deleted\.?|此訊息已刪除。?|你刪除了此訊息。?|You deleted this message\.?'
    r'|Messages and calls are end-to-end encrypted.*|訊息和通話已受端對端加密保護.*'
    r'|‎?<?附件：.*>?)$', re.I)


def clean(text):
    text = (text or '').replace('‎', '').replace('‏', '').strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1].replace('""', '"')
    return text.strip()


def fix_meta(s):
    """Meta（IG／Messenger）匯出的中文是亂碼（UTF-8 被當 latin-1），轉回來。"""
    if not isinstance(s, str):
        return s
    try:
        return s.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


# ---------------- LINE ----------------
LINE_DATE = re.compile(r'^(?:[A-Za-z]{3},\s*)?(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})\s*(?:[（(].*[)）]|[A-Za-z]+)?\s*$'
                       r'|^(?:[A-Za-z]{3},\s*)(\d{1,2})/(\d{1,2})/(\d{4})\s*$')
LINE_MSG = re.compile(r'^(上午|下午|午前|午後)?\s*(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?\t([^\t]*)\t(.*)$')


def parse_line(path):
    out, day, cur = [], None, None
    for raw in open(path, encoding='utf-8-sig', errors='replace').read().splitlines():
        line = raw.rstrip('\r')
        m = LINE_DATE.match(line.strip())
        if m:
            g = m.groups()
            if g[0]:
                day = dt.date(int(g[0]), int(g[1]), int(g[2]))
            else:
                day = dt.date(int(g[5]), int(g[3]), int(g[4]))
            cur = None
            continue
        m = LINE_MSG.match(line)
        if m and day:
            ap, hh, mm, ap2, name, text = m.groups()
            h = int(hh) % 12 if (ap or ap2) else int(hh)
            if ap in ('下午', '午後') or (ap2 or '').lower() == 'pm':
                h += 12
            if not name.strip():  # 系統訊息（加入、收回等）
                cur = None
                continue
            cur = {'t': dt.datetime.combine(day, dt.time(h % 24, int(mm))), 'name': name.strip(), 'text': text, 'src': 'LINE'}
            out.append(cur)
        elif cur is not None and line and not line.startswith('[LINE]') and not re.match(r'^(儲存日期|Saved on|保存日時)', line):
            cur['text'] += '\n' + line  # 多行訊息
    return out


# ---------------- Meta（IG／Messenger）----------------
def parse_meta(path, data):
    out = []
    if 'messages' in data and data['messages'] and 'senderName' in data['messages'][0]:
        # Messenger 新版加密聊天下載
        for m in data['messages']:
            if m.get('isUnsent') or not m.get('text'):
                continue
            out.append({'t': dt.datetime.fromtimestamp(m['timestamp'] / 1000), 'name': m['senderName'],
                        'text': m['text'], 'src': 'Messenger'})
        return out
    src = 'Instagram' if 'instagram' in str(data.get('thread_path', '')).lower() or 'instagram' in str(path).lower() \
        or 'magic_words' in data or any('is_geoblocked_for_viewer' in m for m in data.get('messages', [])[:50]) \
        or any('instagram.com' in str(m.get('share', {}).get('link', '')) for m in data.get('messages', [])[:200]) else 'Messenger'
    rows = data.get('messages', [])
    if len(rows) > 1 and rows[0].get('timestamp_ms', 0) > rows[-1].get('timestamp_ms', 0):
        rows = list(reversed(rows))  # Meta 匯出是新到舊，轉成舊到新，同一秒的訊息順序才會對
    for m in rows:
        if 'content' not in m or m.get('is_unsent'):
            continue
        if m.get('share') or m.get('photos') or m.get('videos') or m.get('audio_files') or m.get('sticker') or 'call_duration' in m:
            continue
        out.append({'t': dt.datetime.fromtimestamp(m['timestamp_ms'] / 1000), 'name': fix_meta(m['sender_name']),
                    'text': fix_meta(m['content']), 'src': src})
    return out


def meta_participants(data):
    p = data.get('participants', [])
    return [fix_meta(x['name'] if isinstance(x, dict) else x) for x in p]


# ---------------- Telegram ----------------
def tg_text(t):
    if isinstance(t, str):
        return t
    return ''.join(x if isinstance(x, str) else x.get('text', '') for x in t)


def parse_telegram(path, data):
    chats = data['chats']['list'] if 'chats' in data else [data]
    out = []
    for c in chats:
        if c.get('type') not in (None, 'personal_chat', 'bot_chat', 'saved_messages'):
            continue
        for m in c.get('messages', []):
            if m.get('type') != 'message' or m.get('media_type') or m.get('photo') or m.get('file'):
                continue
            text = tg_text(m.get('text', ''))
            if not text:
                continue
            out.append({'t': dt.datetime.fromisoformat(m['date']), 'name': m.get('from') or '', 'text': text, 'src': 'Telegram'})
    return out


# ---------------- WhatsApp ----------------
WA = [
    # iOS：[2025/1/2 下午11:52:01] 名字: 訊息　或　[02/01/2025, 23:52:01] 名字: 訊息
    re.compile(r'^‎?\[(\d{1,4})[/.\-](\d{1,2})[/.\-](\d{1,4}),?\s+(上午|下午|AM|PM|am|pm)?\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM|am|pm|上午|下午)?\]\s([^:]+):\s(.*)$'),
    # Android：02/01/2025, 23:52 - 名字: 訊息　或　2025/1/2 下午11:52 - 名字: 訊息
    re.compile(r'^‎?(\d{1,4})[/.\-](\d{1,2})[/.\-](\d{1,4}),?\s+(上午|下午|AM|PM|am|pm)?\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM|am|pm|上午|下午)?\s[-–]\s([^:]+):\s(.*)$'),
]


def parse_whatsapp(path):
    rows, cur = [], None
    for line in open(path, encoding='utf-8-sig', errors='replace').read().splitlines():
        m = None
        for r in WA:
            m = r.match(line)
            if m:
                break
        if m:
            cur = list(m.groups())
            rows.append(cur)
        elif cur is not None:
            cur[8] += '\n' + line
    # 判斷日期順序：年在前，或日/月在前
    firsts = [int(r[0]) for r in rows]
    seconds = [int(r[1]) for r in rows]
    ymd = any(f > 31 for f in firsts)
    dmy = not ymd and any(f > 12 for f in firsts)
    mdy = not ymd and not dmy and any(s > 12 for s in seconds)
    out = []
    for a, b, c, ap1, hh, mm, ap2, name, text in rows:
        a, b, c = int(a), int(b), int(c)
        if ymd:
            y, mo, d = a, b, c
        elif dmy or not mdy:
            d, mo, y = a, b, c
        else:
            mo, d, y = a, b, c
        if y < 100:
            y += 2000
        ap = (ap1 or ap2 or '').lower()
        h = int(hh)
        if ap in ('pm', '下午') and h < 12:
            h += 12
        if ap in ('am', '上午') and h == 12:
            h = 0
        out.append({'t': dt.datetime(y, mo, d, h, int(mm)), 'name': name.strip(), 'text': text, 'src': 'WhatsApp'})
    return out


# ---------------- 判斷格式 ----------------
def load_file(path):
    p = Path(path)
    if p.suffix.lower() == '.json':
        data = json.load(open(p, encoding='utf-8'))
        if isinstance(data, dict) and ('chats' in data or data.get('type') in ('personal_chat', 'private_group', 'private_supergroup', 'bot_chat', 'saved_messages')):
            return parse_telegram(p, data), []
        if isinstance(data, dict) and 'messages' in data:
            if len(meta_participants(data)) > 2:
                print(f'略過群組聊天：{p.name}（只支援一對一）', file=sys.stderr)
                return [], []
            return parse_meta(p, data), meta_participants(data)
        print(f'看不懂這個 JSON：{p.name}', file=sys.stderr)
        return [], []
    head = open(p, encoding='utf-8-sig', errors='replace').read(4000)
    if head.startswith('[LINE]') or re.search(r'^\d{1,2}:\d{2}\t|^(上午|下午)\d', head, re.M):
        return parse_line(p), []
    if any(r.search(head) for r in [re.compile(x.pattern.replace('^', '(?m)^', 1)) for x in WA]):
        return parse_whatsapp(p), []
    print(f'看不出是哪個平台的匯出檔：{p.name}', file=sys.stderr)
    return [], []


def expand(paths):
    for x in paths:
        p = Path(x)
        if p.is_dir():
            for f in sorted(p.rglob('*')):
                if f.suffix.lower() in ('.txt', '.json') and f.is_file():
                    yield f
        else:
            yield p


def main():
    ap = argparse.ArgumentParser(description='把聊天匯出檔整理成 chat.jsonl')
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--me', default='', help='你自己在各個匯出檔裡的名字，用逗號分開')
    ap.add_argument('-o', '--out', default='chat.jsonl')
    ap.add_argument('--list', action='store_true', help='只列出出現的名字和則數，不輸出')
    a = ap.parse_args()

    msgs = []
    for f in expand(a.paths):
        rows, _ = load_file(f)
        msgs += rows
    names = {}
    for m in msgs:
        names.setdefault((m['src'], m['name']), 0)
        names[(m['src'], m['name'])] += 1
    if a.list or not a.me:
        print('出現的名字（平台／名字／則數）：')
        for (src, n), c in sorted(names.items(), key=lambda x: -x[1]):
            print(f'  {src}\t{n}\t{c}')
        if not a.me:
            print('\n請用 --me 指定哪些名字是你自己，例如：--me "小明,Ming Chen"', file=sys.stderr)
        return
    me = {x.strip() for x in a.me.split(',') if x.strip()}
    # 每個平台裡，除了你以外講最多話的人就是對方；其他名字（例如 Meta AI、群組旁人）不算
    main = {}
    for (src, n), c in names.items():
        if n not in me and n and c > main.get(src, ('', 0))[1]:
            main[src] = (n, c)
    dropped = {(src, n): c for (src, n), c in names.items() if n not in me and main.get(src, ('',))[0] != n}
    if dropped:
        print('這些名字不是你也不是對方，已略過：' + '、'.join(f'{n}（{src} {c} 則）' for (src, n), c in dropped.items()), file=sys.stderr)
    msgs = [m for m in msgs if m['name'] in me or main.get(m['src'], ('',))[0] == m['name']]
    out, seen = [], set()
    msgs.sort(key=lambda m: m['t'])
    for m in msgs:
        text = clean(m['text'])
        if not text or NOISE.match(text):
            continue
        key = (m['t'].strftime('%Y%m%d%H%M'), text)  # 同一則訊息出現在兩個來源時只留一份
        if key in seen:
            continue
        seen.add(key)
        out.append({'t': m['t'].isoformat(timespec='seconds'), 'who': 'me' if m['name'] in me else 'them',
                    'name': m['name'], 'text': text, 'src': m['src']})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8') as fh:
        for m in out:
            fh.write(json.dumps(m, ensure_ascii=False) + '\n')
    them = sum(1 for m in out if m['who'] == 'them')
    print(f'完成：{len(out)} 則文字訊息（對方 {them} 則、你 {len(out) - them} 則）→ {a.out}')
    if out:
        print(f'時間範圍：{out[0]["t"][:10]} ～ {out[-1]["t"][:10]}')
    if them == 0 or them == len(out):
        print('注意：看起來 --me 的名字沒有對上，請先用 --list 確認名字。', file=sys.stderr)


if __name__ == '__main__':
    main()
