# 前任模擬器 Ex Simulator

> *「聊天紀錄留下來的不只是文字，是那個人說話的樣子：她的口頭禪、她回你的速度、她怎麼把在乎藏在一句『哼』後面。」*

**如果還有話沒說完，就再聊一次吧。**

![License](https://img.shields.io/badge/License-MIT-yellow) ![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Node.js](https://img.shields.io/badge/Node.js-18%2B-339933) ![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97757) ![Platforms](https://img.shields.io/badge/LINE_%7C_IG_%7C_Messenger_%7C_WhatsApp_%7C_Telegram-supported-brightgreen)

把你和某個人的聊天紀錄，蒸餾成一個會照「她」的語氣回你的聊天視窗。

- **支援 LINE、Instagram、Messenger、WhatsApp、Telegram** 的官方匯出檔，可以多個平台合在一起（例如前半段在 IG、後半段在 LINE）。
- **像 IG 私訊的聊天網頁**：她的頭貼、已讀、正在輸入、一句一個泡泡，會等你連傳完才回。
- **切換時期**：剛認識、最熱、冷下來……每個時期的她只知道那時候以前的事，語氣也照那時候的真實對話。
- **「如果」平行時空**：假設某一天的某件事沒有發生，她會怎麼跟你聊。畫面上會清楚標示這不是真的。
- **全部在你自己的電腦上跑**。人物檔和聊天紀錄不會上傳到任何地方，只有聊天時會送給 Claude API 產生回覆。

這是一個 [Claude Code](https://claude.com/claude-code) skill：Claude 會讀你們的真實對話、跟你確認細節，寫出人物檔，不是用一個固定的 prompt 套。

> 文中的「她」只是方便稱呼，對方是誰都可以用。

---

## 使用前請先讀

- **只用在你自己參與的一對一對話**。對方沒有同意被做成聊天機器人，所以人物檔、聊天紀錄都只留在自己電腦，**不要上傳、分享或公開**，也不要拿來冒充對方或傳訊息給任何人。
- 聊天視窗裡的不是她。它只是用你們過去的對話學來的語氣，會說錯、會說出她不會說的話。
- 如果你在一段很難放下的關係裡，這個工具可能讓你更難放下。累了就關掉，跟真實的朋友聊聊。
- 聊天時，人物檔和對話內容會送到 Anthropic 的 API，適用 [Anthropic 的隱私政策](https://www.anthropic.com/legal/privacy)。

---

## 一、準備工具（第一次才需要）

| 需要的東西 | 用途 | 怎麼確認有沒有裝 | 沒有的話 |
|---|---|---|---|
| Claude Code | 讀聊天紀錄、寫人物檔 | 終端機輸入 `claude --version` | 照 [官方說明](https://docs.claude.com/en/docs/claude-code/setup) 安裝，或用 Claude 桌面 App 的 Code 分頁 |
| Python 3.9 以上 | 整理匯出檔 | `python3 --version` | [python.org](https://www.python.org/downloads/) 下載安裝 |
| Node.js 18 以上 | 聊天網頁 | `node --version` | [nodejs.org](https://nodejs.org/) 下載 LTS 版 |
| Anthropic API 金鑰 | 聊天網頁產生回覆 | — | 見下面 |

**申請 API 金鑰**：到 [console.anthropic.com](https://console.anthropic.com/) 登入 → Billing 儲值 → API Keys → Create Key，複製下來先存在安全的地方（之後只會用在第三步）。建議在 Limits 設一個每月用量上限。

> Windows 使用者：下面的 `python3` 改成 `python`，`~` 是你的使用者資料夾（例如 `C:\Users\你的名字`）。

## 二、安裝

```bash
git clone https://github.com/lilfan3676-pixel/ex-simulator ~/.claude/skills/ex-simulator
```

想先看看聊天網頁長怎樣？專案裡附了一個虛構的範例人物「小安」：

```bash
cd ~/.claude/skills/ex-simulator
echo "ANTHROPIC_API_KEY=你的金鑰" > .env      # 也可以用文字編輯器建立這個檔案
node app/server.mjs examples/demo
```
打開瀏覽器到 http://localhost:5173 就能跟小安聊。看完在終端機按 `Ctrl + C` 關掉。

## 三、匯出聊天紀錄

照 [docs/export.md](docs/export.md) 從各個 App 匯出你們的聊天，**全部放進同一個資料夾**，例如 `~/Downloads/chats/`。

- Instagram 和 Messenger 的匯出要等幾小時到幾天，可以先申請。
- 不同平台都有的話全部放進去，會自動合併、去掉重複。

## 四、蒸餾人物檔

開啟 Claude Code，輸入：

```
/ex-simulator
```

或直接說「用前任模擬器幫我把跟 ○○ 的聊天紀錄做成人物檔，匯出檔在 ~/Downloads/chats」。

Claude 會依序：

1. **問你幾件事**：她的名字、她怎麼叫你、匯出檔在哪、要不要「如果」平行時空模式。
2. **請你指認哪些名字是你自己**（每個平台的名字可能不一樣）。
3. **看整體輪廓**：每個月聊多少、她的口頭禪和表情、回覆速度，請你確認關係的幾個轉折點。
4. **讀真實對話、寫人物檔**：每個月都會抽幾段來讀。不確定的細節會問你，不會自己亂編。
5. **把時間線和她的個性唸給你聽，請你更正**。這一步最重要，錯的地方直接說。
6. **分時期**：照你們的轉折點切成幾段，每段寫清楚那時候的她是什麼樣子。

全部會存在人物資料夾，預設是 `~/ex-simulator-data/<代稱>/`：

```
~/ex-simulator-data/her/
  chat.jsonl      整理好的聊天紀錄
  persona.md      人物檔（最重要，Claude 幫你寫、你來改）
  periods.json    時期設定
  config.json     名字、副標、平行時空設定
  avatar.jpg      頭貼（你自己放）
  .env            API 金鑰（你自己放）
```

聊天量大的話，這一步可能要聊上一陣子，值得慢慢來：人物檔寫得越準，聊起來越像她。

## 五、開始聊天

1. **放頭貼**（可省略）：把她的照片放進人物資料夾，改名成 `avatar.jpg`（`.png`、`.webp` 也可以）。沒放的話會顯示名字的最後一個字。
2. **放金鑰**：在人物資料夾建立一個叫 `.env` 的檔案，內容只有一行：
   ```
   ANTHROPIC_API_KEY=你的金鑰
   ```
   金鑰不要貼在 Claude Code 的對話裡。
3. **啟動**：
   ```bash
   node ~/.claude/skills/ex-simulator/app/server.mjs ~/ex-simulator-data/her
   ```
4. 打開 http://localhost:5173 。聊完在終端機按 `Ctrl + C` 關掉。

### 聊天畫面怎麼用

- **上方的按鈕**切換時期（例如 剛認識／最熱／現在）。每個時期的對話分開保存，互不影響。
- **「如果」**是平行時空模式，畫面會變紫色並標示「這不是真的她」。
- 你可以連傳好幾則，她會等你停下來再一起回。
- 右上角 **⋯** 清除目前這個時期的對話，重新開始。
- 對話只存在你這台電腦的瀏覽器裡；換瀏覽器或清除瀏覽資料就會不見。

## 六、之後怎麼調整

| 想做的事 | 怎麼做 |
|---|---|
| 她講話不像她、說錯事 | 在 Claude Code 說「用前任模擬器，她不會這樣講，應該是……」，或直接打開 `persona.md` 改。改完不用重開，下一則就生效。 |
| 有新的聊天紀錄 | 重新匯出放進資料夾，跟 Claude 說「用前任模擬器更新人物檔」。 |
| 改名字、副標、平行時空設定 | 打開人物資料夾的 `config.json` 改。 |
| 換模型 | `config.json` 的 `"model"`，預設 `claude-sonnet-5-5`。要更像但比較貴可以換 `claude-opus-5-5`。 |
| 同時開兩個人物 | 第二個加上不同的埠號：`PORT=5174 node .../server.mjs ~/ex-simulator-data/另一個人` |
| 刪掉所有資料 | 刪除整個人物資料夾，再到聊天畫面按 ⋯ 清除各時期的對話。 |

**費用**：每一則回覆都會把整份人物檔一起送出，人物檔越長、聊越多就越貴。可以在 Anthropic 後台看用量、設上限。

## 七、常見問題

| 看到的狀況 | 原因和解法 |
|---|---|
| `看不出是哪個平台的匯出檔` | 檔案不是官方匯出格式，或匯出時選成 HTML。Instagram／Messenger 要選 **JSON**；LINE 要用「傳送聊天記錄」產生的 .txt。 |
| 整理完「對方 0 則」或「你 0 則」 | 你自己的名字沒指認對。先跑 `python3 scripts/parse.py --list 匯出資料夾` 看出現哪些名字。 |
| `略過群組聊天` | 只支援一對一聊天。 |
| 聊天畫面出現「還沒設定 ANTHROPIC_API_KEY」 | `.env` 沒放在人物資料夾，或檔名多了 `.txt`（Windows／Mac 文字編輯器常自動加副檔名）。 |
| 出現 `credit balance is too low` | API 帳戶餘額不足，到 console.anthropic.com 儲值。 |
| `EADDRINUSE` | 5173 埠已經被佔用（可能已經開著一個），關掉另一個或換埠號：`PORT=5174 node ...`。 |
| 找不到 `persona.md` | 啟動指令最後的資料夾路徑打錯，要指到人物資料夾本身。 |
| 她一直編出沒發生過的事 | 在人物檔的時間線和記憶片段補上正確的事，並請她「不確定就說不記得」（人物檔範本裡已經有這條規則）。 |

---

## 進階：不透過 Claude Code 手動跑

```bash
cd ~/.claude/skills/ex-simulator

# 1. 整理匯出檔（先用 --list 看你自己的名字是哪個）
python3 scripts/parse.py --list ~/Downloads/chats
python3 scripts/parse.py --me "我的名字,我的IG名稱" -o ~/ex-simulator-data/her/chat.jsonl ~/Downloads/chats

# 2. 看統計、抽對話樣本
python3 scripts/analyze.py stats ~/ex-simulator-data/her/chat.jsonl
python3 scripts/analyze.py sample ~/ex-simulator-data/her/chat.jsonl --from 2025-06-01 --to 2025-07-01 -n 5
python3 scripts/analyze.py sample ~/ex-simulator-data/her/chat.jsonl --grep 喜歡 -n 6

# 3. 分時期（再自己補上每個時期的 desc、unknown、hint）
python3 scripts/analyze.py periods ~/ex-simulator-data/her/chat.jsonl --split 2025-10-01,2026-01-01 --labels 剛認識,最熱,現在 -o ~/ex-simulator-data/her/periods.json

# 4. 照 templates/persona.md、templates/config.json 寫好人物檔和設定，放頭貼和 .env，然後
node app/server.mjs ~/ex-simulator-data/her
```

測試解析程式：`python3 tests/test_parse.py`（用 `examples/` 裡虛構的小安和阿傑的對話檢查五種格式）。

---

## English

**Ex Simulator (前任模擬器)** turns your chat history with one person (LINE / Instagram / Messenger / WhatsApp / Telegram exports) into a persona file, then runs a local Instagram-DM-style chat page where "she" replies in her own voice. You can switch between periods of the relationship (she only knows what happened up to then) and an optional, clearly labelled "what if" mode.

**Quick start**

1. Requirements: Claude Code, Python 3.9+, Node.js 18+, an Anthropic API key.
2. `git clone https://github.com/lilfan3676-pixel/ex-simulator ~/.claude/skills/ex-simulator`
3. Export your chats (see [docs/export.md](docs/export.md)) into one folder.
4. In Claude Code, run `/ex-simulator`. Claude parses the exports, reads real conversations, drafts `persona.md` and `periods.json`, and asks you to correct them.
5. Put `avatar.jpg` and a `.env` file containing `ANTHROPIC_API_KEY=...` in the persona folder, then run `node ~/.claude/skills/ex-simulator/app/server.mjs ~/ex-simulator-data/<name>` and open http://localhost:5173.

Try the bundled fictional demo first: create `.env` in the project folder and run `node app/server.mjs examples/demo`.

Only use it on conversations you took part in, keep the persona private, and never use it to impersonate the real person. Everything stays on your machine except the chat requests sent to the Claude API. MIT licensed.
