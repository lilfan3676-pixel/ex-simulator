#!/usr/bin/env python3
"""確認五種平台的假匯出檔都能讀出同一段對話。執行：python3 tests/test_parse.py"""
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
import make_examples as mk

mk.EX.mkdir(exist_ok=True)
mk.line_txt(); mk.meta_json('instagram'); mk.meta_json('messenger'); mk.whatsapp_txt(); mk.telegram_json()

EXPECT = [(t, w, x) for t, w, x in mk.CONVO if not x.startswith('[')]
ok = True
for f in ['line_zh.txt', 'instagram_message_1.json', 'messenger_message_1.json',
          'whatsapp_ios.txt', 'whatsapp_android.txt', 'telegram_result.json']:
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / 'chat.jsonl'
        r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'parse.py'), '--me', mk.ME, '-o', str(out),
                            str(mk.EX / f)], capture_output=True, text=True)
        rows = [json.loads(l) for l in out.read_text(encoding='utf-8').splitlines()] if out.exists() else []
    got = [(r_['t'][:16].replace('T', ' '), r_['who'], r_['text']) for r_ in rows]
    if got == EXPECT:
        print(f'通過  {f}')
    else:
        ok = False
        print(f'失敗  {f}\n  {r.stdout}{r.stderr}')
        for a, b in zip(got + [None] * len(EXPECT), EXPECT):
            if a != b:
                print('   得到', a, '\n   應為', b)
                break
sys.exit(0 if ok else 1)
