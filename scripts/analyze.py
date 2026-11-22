#!/usr/bin/env python3
"""讀 chat.jsonl，給蒸餾用的三種資料。

  python3 analyze.py stats chat.jsonl
      每個月的訊息量、對方最常說的詞、常用表情、平均長度、回覆速度。用來決定時期怎麼切。

  python3 analyze.py sample chat.jsonl [--from 2025-06-01] [--to 2025-09-01] [-n 8] [--seed 1] [--grep 關鍵字]
      隨機抽幾段完整的來回對話（含前後文），給 Claude 讀，用來寫人物檔。

  python3 analyze.py periods chat.jsonl --split 2025-10-01,2025-12-01 [--labels 剛認識,升溫,現在] -o periods.json
      依切點把整段關係分成幾個時期，每個時期附上對方最常說的話、幾段真實對話當語氣範例。
      label／desc／unknown 留給 Claude 讀過樣本後填寫。
  python3 analyze.py periods chat.jsonl --auto 4 -o periods.json
      不知道怎麼切時，讓訊息量平均分成 N 段，當作起點。
"""
import argparse, collections, datetime as dt, json, random, re, sys

EMOJI = re.compile('[\U0001F300-\U0001F3FA\U0001F400-\U0001FAFF☀-☿♁♃-➿⭐❤]')  # 不含膚色、性別符號


def load(path):
    rows = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
    for r in rows:
        r['dt'] = dt.datetime.fromisoformat(r['t'])
    return rows


def in_range(rows, a=None, b=None):
    a = dt.datetime.fromisoformat(a) if a else None
    b = dt.datetime.fromisoformat(b) if b else None
    return [r for r in rows if (not a or r['dt'] >= a) and (not b or r['dt'] < b)]


def phrases(rows, k=30):
    """對方最常傳的短句（整則訊息），比斷詞更能看出口頭禪。"""
    c = collections.Counter(r['text'] for r in rows if r['who'] == 'them' and len(r['text']) <= 12)
    return [p for p, n in c.most_common(k) if n >= 3]


def stats(rows):
    by_month = collections.Counter((r['dt'].strftime('%Y-%m'), r['who']) for r in rows)
    months = sorted({m for m, _ in by_month})
    print('月份      對方    你')
    for m in months:
        print(f'{m}  {by_month[(m, "them")]:6d}  {by_month[(m, "me")]:6d}')
    them = [r for r in rows if r['who'] == 'them']
    if not them:
        return
    print(f'\n對方平均每則 {sum(len(r["text"]) for r in them) / len(them):.1f} 字')
    print('對方常說：' + '、'.join(phrases(rows, 40)))
    em = collections.Counter(e for r in them for e in EMOJI.findall(r['text']))
    print('對方常用表情：' + ' '.join(f'{e}{n}' for e, n in em.most_common(15)))
    # 回覆速度：對方回你的時間中位數（12 小時內才算）
    gaps = [(b['dt'] - a['dt']).total_seconds() / 60 for a, b in zip(rows, rows[1:])
            if a['who'] == 'me' and b['who'] == 'them' and (b['dt'] - a['dt']).total_seconds() < 43200]
    if gaps:
        gaps.sort()
        print(f'對方回你的時間（中位數）：{gaps[len(gaps) // 2]:.0f} 分鐘')
    hours = collections.Counter(r['dt'].hour for r in them)
    print('對方最常在這些時間傳訊息：' + '、'.join(f'{h}點' for h, _ in hours.most_common(5)))


def windows(rows, n, seed=0, grep=None, size=14):
    """抽 n 段對話：以對方的一則訊息為中心，前後各取幾則。"""
    rnd = random.Random(seed)
    idx = [i for i, r in enumerate(rows) if r['who'] == 'them' and (not grep or grep in r['text'])]
    rnd.shuffle(idx)
    picked, used = [], set()
    for i in idx:
        if len(picked) >= n:
            break
        a, b = max(0, i - size // 2), min(len(rows), i + size // 2)
        if any(j in used for j in range(a, b)):
            continue
        # 同一段要在 6 小時內，才是同一場對話
        seg = [r for r in rows[a:b] if abs((r['dt'] - rows[i]['dt']).total_seconds()) < 21600]
        if sum(1 for r in seg if r['who'] == 'them') < 3:
            continue
        used.update(range(a, b))
        picked.append(seg)
    picked.sort(key=lambda s: s[0]['dt'])
    return picked


def fmt(seg, them='她', me='我'):
    return [f"{r['dt']:%m/%d %H:%M} {them if r['who'] == 'them' else me}：{r['text']}" for r in seg]


def periods(rows, split, labels, out):
    cuts = [rows[0]['dt'].date().isoformat()] + split + [(rows[-1]['dt'] + dt.timedelta(days=1)).date().isoformat()]
    res = []
    for i, (a, b) in enumerate(zip(cuts, cuts[1:])):
        seg = in_range(rows, a, b)
        if not seg:
            continue
        last = i == len(cuts) - 2
        pid = 'now' if last else f'p{i + 1}'
        today = (dt.date.fromisoformat(b) - dt.timedelta(days=1)).isoformat()
        res.append({
            'id': pid,
            'label': labels[i] if i < len(labels) else ('現在' if last else f'時期{i + 1}'),
            'range': [a, b],
            'today': today,
            'desc': '',      # Claude 讀過這段的樣本後填：那時候的關係、她的狀態、說話方式
            'unknown': '',   # 這個時期的她還不知道的事（之後才發生的）
            'hint': '',      # 顯示在聊天畫面上的一句說明
            'common': phrases(seg, 20),
            'snippets': [fmt(w, '她', '你') for w in windows(seg, 10, seed=i)],
            'count': sum(1 for r in seg if r['who'] == 'them'),
        })
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for p in res:
        print(f"{p['id']}\t{p['label']}\t{p['range'][0]} ～ {p['range'][1]}\t對方 {p['count']} 則")
    print(f'→ {out}（desc／unknown／hint 還是空的，要讀樣本後補上）')


def auto_split(rows, n):
    """訊息量平均分成 n 段，切點對齊到月初。"""
    total = len(rows)
    cuts = []
    for k in range(1, n):
        d = rows[total * k // n]['dt'].date().replace(day=1)
        if d.isoformat() not in cuts and d > rows[0]['dt'].date():
            cuts.append(d.isoformat())
    return cuts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['stats', 'sample', 'periods'])
    ap.add_argument('chat')
    ap.add_argument('--from', dest='a')
    ap.add_argument('--to', dest='b')
    ap.add_argument('-n', type=int, default=8)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--grep')
    ap.add_argument('--split', default='')
    ap.add_argument('--auto', type=int)
    ap.add_argument('--labels', default='')
    ap.add_argument('-o', '--out', default='periods.json')
    a = ap.parse_args()
    rows = load(a.chat)
    if not rows:
        sys.exit('chat.jsonl 是空的')
    if a.cmd == 'stats':
        stats(in_range(rows, a.a, a.b))
    elif a.cmd == 'sample':
        for w in windows(in_range(rows, a.a, a.b), a.n, a.seed, a.grep):
            print('\n'.join(fmt(w)) + '\n---')
    else:
        split = [x for x in a.split.split(',') if x] or (auto_split(rows, a.auto) if a.auto else [])
        periods(rows, split, [x for x in a.labels.split(',') if x], a.out)


if __name__ == '__main__':
    main()
