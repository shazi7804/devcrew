# SITREP — the shape of every report

> Every message that ends a turn — orchestrator → CEO, worker → CEO, role →
> orchestrator — opens with this block. Adapted from
> [joshuaboys/SITREP](https://github.com/joshuaboys/SITREP) (MIT).
>
> Why a fixed shape: the CEO decides from these messages, often several windows
> at once. A long chronological report buries the one line they have to act on,
> and a missed ask is the same as an ask never made. A fixed shape puts that line
> in the same place every time.

## The block

```
SITUATION  <one line: where things stand — the takeaway, not the history>
ACTION     <what was done this turn — one line each, max 3>
STATUS     DONE | IN PROGRESS | BLOCKED | FAIL — <one clause>
NEXT       CEO：<numbered asks the CEO can answer by number>  | 無
           我：<what this session does next, with no input>
```

The block is written in the CEO's language; the four field names stay English
so a parser (and the eye) can find them.

## Rules

- **STATUS is one of four words.** `BLOCKED` means *waiting on someone* — name
  who. `FAIL` means a gate or sensor went red.
- **`DONE` means it runs on the real thing.** Work whose live evidence is missing
  is never `DONE` and never "green": it is `BLOCKED — 未接真服務：<what is
  missing, who provides it>`. Say what is not live in SITUATION, before the CEO
  has to ask. Fake-backed tests passing is not a status.
- **NEXT always has a `CEO：` line.** When nothing is needed it says `無` — the
  CEO must be able to skip a message by reading one line. Every ask is numbered,
  starts with a verb, and offers the answers (`① 接受 ② 砍掉 ③ 先擱著`). A
  load-bearing ask adds your pick and its downside on one line.
- **Code names get plain words on first use** — `N1（首屏大小上限）`, not `N1`.
- **Numbers stay exact.** Never round a status or drop the condition it holds
  under.
- **Unknown is a status, not a guess.** Write `未查` / `查不到定論`; never
  "should be fine".
- **Detail goes in a file; the message carries its path.** No narration of how
  you got there, no process notes, no lessons — state goes to TASKS.md,
  lessons to memory.
- **A correction is one line**, in SITUATION or ACTION, never a paragraph.
- **Below the block, only what the CEO asked for.** If they asked a question,
  answer it in ≤3 lines under the block. Otherwise stop.

Judgment roles still end with their verdict YAML (`verdicts.template.md`): the
SITREP goes on top for the reader, the YAML at the bottom for the parser.

## Examples

**Orchestrator → CEO, asks pending**
```
SITUATION  瓶頸是簽核：已簽 8 / 草稿 8 / 沒需求 8
ACTION     專案規則檔 併行 2→10 改完，跨廠審查 APPROVE
           派出 iOS 截圖、字型、金流、Sentry
STATUS     BLOCKED — 等 CEO 簽核
NEXT       CEO：① 批 8 張草稿卡
                ② commit 專案規則檔
                ③ 重簽 css-scope（architect 要補一條需求）
                ④ 商標：自查／律師／擱著
           我：iOS 截圖回來後補 css-scope 視覺驗收
```

**Orchestrator → CEO, nothing needed**
```
SITUATION  css-scope 實作完成，測試 2386→2445 全綠
ACTION     派 auditor（14 檔超過門檻）、派 iOS build＋截圖
STATUS     IN PROGRESS
NEXT       CEO：無
           我：截圖回來補視覺驗收 → 綠了請你簽
```

**A decision with a trade-off**
```
SITUATION  推播卡會碰到已簽的 ADR-1：Android 推播一定經過 Google
ACTION     查過，沒有繞過 FCM 的路
STATUS     BLOCKED — 等 CEO 決定
NEXT       CEO：① 接受（改 ADR-1）② 砍 Android 推播 ③ 先擱著
                推 ①，缺點：Google 進信任邊界，不再完全自架
           我：等你決定前不動推播卡
```

**Worker / role → orchestrator** (the orchestrator digests it; it is not relayed to the CEO)
```
SITUATION  css-scope R1 視覺驗收
ACTION     14 台模擬器裝 app＋修前修後截圖
STATUS     DONE — 證據 /abs/path/.aidlc/features/css-scope/shots/
NEXT       CEO：無
           我：claim 已釋放
```
