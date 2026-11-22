# 前任模擬器 Ex Simulator

把你和某個人的聊天紀錄，蒸餾成一個會照「她」的語氣回你的聊天視窗。

- **支援 LINE、Instagram、Messenger、WhatsApp、Telegram** 的官方匯出檔，可以多個平台合在一起（例如前半段在 IG、後半段在 LINE）。
- **像 IG 私訊的聊天網頁**：她的頭貼、已讀、正在輸入、一句一個泡泡，會等你連傳完才回。
- **切換時期**：剛認識、最熱、冷下來……每個時期的她只知道那時候以前的事，語氣也照那時候的真實對話。
- **「如果」平行時空**：假設某一天的某件事沒有發生，她會怎麼跟你聊。畫面上會清楚標示這不是真的。
- **全部在你自己的電腦上跑**。人物檔和聊天紀錄不會上傳到任何地方，只有聊天時會送給 Claude API 產生回覆。

這是一個 [Claude Code](https://claude.com/claude-code) skill：Claude 會讀你們的真實對話、跟你確認細節，寫出人物檔，不是用一個固定的 prompt 套。

## 需要

- Claude Code（用來蒸餾人物檔）
- Python 3.9 以上（整理匯出檔，不用另外裝套件）
- Node.js 18 以上（聊天網頁）
- Anthropic API 金鑰（聊天網頁產生回覆用，按用量計費）

## 安裝

```bash
git clone https://github.com/<你的帳號>/ex-simulator ~/.claude/skills/ex-simulator
```

然後在 Claude Code 裡說：「用前任模擬器幫我把跟 ○○ 的聊天紀錄做成人物檔」，或直接輸入 `/ex-simulator`。
Claude 會一步一步帶你：匯出 → 整理 → 寫人物檔 → 分時期 → 開聊天網頁。各平台怎麼匯出見 [docs/export.md](docs/export.md)。

## 自己手動跑

```bash
# 1. 整理匯出檔（先用 --list 看你自己的名字是哪個）
python3 scripts/parse.py --list ~/Downloads/line.txt ~/Downloads/instagram_inbox/
python3 scripts/parse.py --me "我的名字,我的IG名稱" -o ~/ex-simulator-data/her/chat.jsonl ~/Downloads/line.txt ~/Downloads/instagram_inbox/

# 2. 看統計、抽對話樣本
python3 scripts/analyze.py stats ~/ex-simulator-data/her/chat.jsonl
python3 scripts/analyze.py sample ~/ex-simulator-data/her/chat.jsonl --from 2025-06-01 --to 2025-07-01 -n 5

# 3. 分時期（之後要補上每個時期的說明）
python3 scripts/analyze.py periods ~/ex-simulator-data/her/chat.jsonl --split 2025-10-01,2026-01-01 --labels 剛認識,最熱,現在 -o ~/ex-simulator-data/her/periods.json

# 4. 照 templates/ 寫好 persona.md 和 config.json，放頭貼 avatar.jpg，
#    在人物資料夾建立 .env 寫入 ANTHROPIC_API_KEY=...，然後
node app/server.mjs ~/ex-simulator-data/her
# 打開 http://localhost:5173
```

人物資料夾長這樣：

```
~/ex-simulator-data/her/
  chat.jsonl      整理好的聊天紀錄
  persona.md      人物檔（最重要，Claude 幫你寫、你來改）
  periods.json    時期設定（可省略）
  config.json     名字、平行時空設定
  avatar.jpg      頭貼（可省略）
  .env            ANTHROPIC_API_KEY=...
```

## 請先讀這段

- **只用在你自己參與的對話**。對方沒有同意被做成聊天機器人，所以人物檔、聊天紀錄都只留在自己電腦，**不要上傳、分享或公開**，也不要拿來冒充對方或傳訊息給任何人。
- 聊天視窗裡的不是她。它只是用你們過去的對話學來的語氣，會說錯、會說出她不會說的話。
- 如果你在一段很難放下的關係裡，這個工具可能讓你更難放下。累了就關掉，跟真實的朋友聊聊。
- 聊天時，人物檔和對話內容會送到 Anthropic 的 API，適用 [Anthropic 的隱私政策](https://www.anthropic.com/legal/privacy)。

## 測試

```bash
python3 tests/test_parse.py    # 用 examples/ 裡的假對話檢查五種格式
```
`examples/` 裡的對話是虛構的（小安和阿傑），不是真人。

---

## English

**Ex Simulator (前任模擬器)** turns your chat history with one person (LINE / Instagram / Messenger / WhatsApp / Telegram exports) into a persona file, then runs a local Instagram-DM-style chat page where "she" replies in her own voice. You can switch between periods of the relationship (she only knows what happened up to then) and an optional clearly-labelled "what if" mode.

It is a Claude Code skill: clone it into `~/.claude/skills/ex-simulator`, then ask Claude Code to build a persona from your exports. Everything stays on your machine except the chat requests sent to the Claude API.

Only use it on conversations you took part in, keep the persona private, and never use it to impersonate the real person. MIT licensed.
