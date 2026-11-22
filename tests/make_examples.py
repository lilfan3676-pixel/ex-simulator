#!/usr/bin/env python3
"""用一段虛構的對話（小安和阿傑，都不是真人）產生五種平台的假匯出檔，放在 examples/。
測試時用來確認每種格式都能讀對。"""
import json, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / 'examples'

# (時間, 誰, 內容)；'them' 是小安，'me' 是阿傑
CONVO = [
    ('2025-03-01 21:05', 'me', '欸你上次推薦的那家咖啡廳'),
    ('2025-03-01 21:05', 'me', '我今天去了'),
    ('2025-03-01 21:07', 'them', '真的假的'),
    ('2025-03-01 21:07', 'them', '好喝吧哈哈哈'),
    ('2025-03-01 21:08', 'them', '[STICKER]'),
    ('2025-03-01 21:10', 'me', '肉桂捲超好吃\n但是排隊排了半小時'),
    ('2025-03-01 21:12', 'them', '下次早一點去啊笨蛋'),
    ('2025-03-02 09:30', 'them', '早安'),
    ('2025-03-02 09:31', 'them', '[PHOTO]'),
    ('2025-03-02 12:15', 'me', '早安 剛起床'),
    ('2025-03-02 12:16', 'them', '睡到中午 好爽喔'),
    ('2025-03-15 23:40', 'them', '你睡了嗎'),
    ('2025-03-15 23:41', 'me', '還沒啊怎麼了'),
    ('2025-03-15 23:45', 'them', '沒事 只是突然想聊天'),
]
THEM, ME = '小安', '阿傑'


def ts(s):
    return dt.datetime.strptime(s, '%Y-%m-%d %H:%M')


def line_txt():
    out = [f'[LINE] 與{THEM}的聊天記錄', '儲存日期： 2025/04/01 10:00', '']
    day = None
    wd = '一二三四五六日'
    for t, w, x in CONVO:
        d = ts(t)
        if d.date() != day:
            day = d.date()
            out += ['', f'{d:%Y/%m/%d}（{wd[d.weekday()]}）']
        ap = '上午' if d.hour < 12 else '下午'
        h = d.hour % 12 or 12
        text = {'[STICKER]': '[貼圖]', '[PHOTO]': '[照片]'}.get(x, x)
        if '\n' in text:
            text = '"' + text + '"'
        out.append(f'{ap}{h:02d}:{d.minute:02d}\t{THEM if w == "them" else ME}\t{text}')
    (EX / 'line_zh.txt').write_text('\n'.join(out) + '\n', encoding='utf-8')


def meta_json(kind):
    msgs = []
    for t, w, x in reversed(CONVO):  # Meta 匯出是新到舊
        name = THEM if w == 'them' else ME
        m = {'sender_name': name.encode('utf-8').decode('latin-1'), 'timestamp_ms': int(ts(t).timestamp() * 1000)}
        if x == '[STICKER]':
            m['sticker'] = {'uri': 'x.png'}
        elif x == '[PHOTO]':
            m['photos'] = [{'uri': 'p.jpg'}]
        else:
            m['content'] = x.encode('utf-8').decode('latin-1')
        msgs.append(m)
    data = {'participants': [{'name': THEM.encode('utf-8').decode('latin-1')}, {'name': ME.encode('utf-8').decode('latin-1')}],
            'messages': msgs, 'title': THEM.encode('utf-8').decode('latin-1'),
            'thread_path': f'inbox/{kind}_example'}
    (EX / f'{kind}_message_1.json').write_text(json.dumps(data, ensure_ascii=True, indent=1), encoding='utf-8')


def whatsapp_txt():
    out = []
    for t, w, x in CONVO:
        d = ts(t)
        text = {'[STICKER]': 'sticker omitted', '[PHOTO]': 'image omitted'}.get(x, x)
        out.append(f'[{d:%d/%m/%Y}, {d:%H:%M:%S}] {THEM if w == "them" else ME}: {text}')
    (EX / 'whatsapp_ios.txt').write_text('\n'.join(out) + '\n', encoding='utf-8')
    out = []
    for t, w, x in CONVO:
        d = ts(t)
        h = d.hour % 12 or 12
        text = {'[STICKER]': '<Media omitted>', '[PHOTO]': '<Media omitted>'}.get(x, x)
        out.append(f'{d.month}/{d.day}/{d:%y}, {h}:{d:%M} {"AM" if d.hour < 12 else "PM"} - {THEM if w == "them" else ME}: {text}')
    (EX / 'whatsapp_android.txt').write_text('\n'.join(out) + '\n', encoding='utf-8')


def telegram_json():
    msgs = []
    for i, (t, w, x) in enumerate(CONVO):
        m = {'id': i + 1, 'type': 'message', 'date': ts(t).isoformat(), 'from': THEM if w == 'them' else ME}
        if x == '[STICKER]':
            m.update(media_type='sticker', file='s.webp', text='')
        elif x == '[PHOTO]':
            m.update(photo='p.jpg', text='')
        else:
            m['text'] = x if i != 6 else ['下次早一點去啊', {'type': 'bold', 'text': '笨蛋'}]
        msgs.append(m)
    data = {'name': THEM, 'type': 'personal_chat', 'id': 1, 'messages': msgs}
    (EX / 'telegram_result.json').write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    EX.mkdir(exist_ok=True)
    line_txt(); meta_json('instagram'); meta_json('messenger'); whatsapp_txt(); telegram_json()
    print('examples/ 已產生')
