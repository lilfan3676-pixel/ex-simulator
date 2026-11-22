---
name: kite-chat
description: 把你和某個人的聊天紀錄（LINE、Instagram、Messenger、WhatsApp、Telegram 匯出檔）蒸餾成人物檔，再開一個像 IG 私訊的本機聊天網頁，讓「她」照以前的語氣回你；可以切換不同時期，也有「如果」平行時空模式。Use when the user wants to turn chat exports with a specific person into a persona and chat with it, mentions 蒸餾、人物檔、前任.skill、想跟他／她再聊一次, or wants to update an existing kite-chat persona.
user-invocable: true
---

# kite-chat：把聊天紀錄蒸餾成一個能聊天的人

這個 skill 會帶使用者走完：**匯出檔 → 整理 → 讀樣本 → 寫人物檔 → 分時期 → 開聊天網頁**。
所有資料都留在使用者自己的電腦；只有聊天時，人物檔和對話內容會送到 Claude API。

本 skill 的資料夾在載入時顯示的 Base directory（下面寫成 `$SKILL`）。腳本都在 `$SKILL/scripts/`，網頁在 `$SKILL/app/`。

## 開始前（每次都要做）

1. **確認是使用者本人參與的一對一聊天**。只能蒸餾「使用者和對方」之間的對話，不處理別人之間的聊天、群組。
2. 用一句話提醒：人物檔只放在自己電腦，不要上傳或分享出去；聊天網頁裡的不是真的對方。
3. 問清楚（用選擇題）：
   - 對方怎麼稱呼（顯示在聊天視窗的名字）、她怎麼叫使用者
   - 匯出檔放在哪裡（可以是資料夾）
   - 人物資料夾要放哪，預設 `~/kite-chat-data/<英文或拼音代稱>/`
   - 要不要「如果」平行時空模式（要的話，假設哪一天的哪件事不一樣）

各平台怎麼匯出，見 `$SKILL/docs/export.md`，使用者不知道時照著一步一步帶。

## 步驟 1：整理匯出檔

```bash
python3 $SKILL/scripts/parse.py --list <匯出檔或資料夾...>
```
看出現的名字，問使用者哪些是他自己（不同平台名字可能不同），然後：
```bash
python3 $SKILL/scripts/parse.py --me "名字1,名字2" -o <人物資料夾>/chat.jsonl <匯出檔或資料夾...>
```
- 只保留文字訊息；貼圖、照片、通話、收回會被拿掉。同一則訊息出現在兩個平台只留一份。
- 如果「對方」的則數是 0 或全部，代表 `--me` 沒對上，回頭用 `--list` 確認。

## 步驟 2：看整體輪廓

```bash
python3 $SKILL/scripts/analyze.py stats <人物資料夾>/chat.jsonl
```
得到每月訊息量、她的口頭禪、表情、平均長度、回覆速度、常聊的時段。
跟使用者確認關係的大轉折（開始熟、最熱、冷下來、吵架、說清楚），這會決定時期怎麼切。

## 步驟 3：讀樣本，寫人物檔

不要只看統計就寫。**每個月至少讀 2～3 段真實對話**：
```bash
python3 $SKILL/scripts/analyze.py sample <chat.jsonl> --from 2025-06-01 --to 2025-07-01 -n 3 --seed 1
python3 $SKILL/scripts/analyze.py sample <chat.jsonl> --grep 喜歡 -n 6     # 用關鍵字找重要時刻
```
重要時刻用關鍵字去找：喜歡、對不起、生氣、不要、在一起、朋友、想你、晚安、生日、分手、吵、哭。

照 `$SKILL/templates/persona.md` 寫 `<人物資料夾>/persona.md`：
- 每一條都分「（證據）」「（推論）」，回覆範例一律用原文。
- 寧可少寫也不要猜。不確定的細節（誰做了什麼、在哪裡、為什麼）**先問使用者**，不要自己補。
- 寫完把「時間線」和「Layer 0」唸給使用者聽，請他更正；更正記進 Correction Log。

## 步驟 4：分時期

照步驟 2 確認的轉折點切：
```bash
python3 $SKILL/scripts/analyze.py periods <chat.jsonl> --split 2025-10-01,2025-12-01,2026-03-01 --labels 剛認識,升溫,最熱,現在 -o <人物資料夾>/periods.json
```
不確定怎麼切時可以先用 `--auto 4`。最後一段 id 固定是 `now`。
然後讀每個時期的 `snippets`（已經附在 periods.json 裡），幫每個時期補上：
- `desc`：那時候你們多熟、她的狀態、說話方式跟現在差在哪（用「你」稱呼她來寫）
- `unknown`：這個時期的她還不知道的事（之後才發生的重要事件）
- `hint`：顯示在聊天畫面上的一句說明，例如「升溫：2025/11，她開始叫自己姐姐」

## 步驟 5：開聊天網頁

1. 複製 `$SKILL/templates/config.json` 到人物資料夾，填好 name、me、subtitle；不要「如果」模式就刪掉 whatif。
2. 頭貼：請使用者把照片放進人物資料夾，命名 `avatar.jpg`（或 .png／.webp）。
3. 金鑰：請使用者**自己**在人物資料夾建立 `.env`，寫一行 `ANTHROPIC_API_KEY=...`。不要叫他把金鑰貼在對話裡，也不要讀出來。
4. 啟動：
```bash
node $SKILL/app/server.mjs <人物資料夾>
```
打開 http://localhost:5173 。需要 Node.js 18 以上。

## 之後的更新

- 使用者說「她不會這樣講」「這件事不對」：改 persona.md，記進 Correction Log。改完不用重開伺服器。
- 有新的聊天紀錄：重跑步驟 1，再看新的部分補人物檔和時期。

## 不做的事

- 不蒸餾使用者沒參與的對話、不處理群組。
- 不幫忙把人物檔拿去冒充對方、傳訊息給真人或第三方。
- 不寫露骨的性內容。
- 使用者如果看起來很難過、走不出來，可以溫和地陪他聊，不要只催他繼續用。
