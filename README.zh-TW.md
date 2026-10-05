# devcrew

[English](README.md) · **繁體中文**

**一個 agent 背後，是一整支 AI 軟體團隊。** 你是 CEO：你帶來想法，在幾個關卡簽核。
其餘的事由 `orchestrator` 處理。它把你的想法寫成一份簽過的合約，把每個階段交給專門的
agent，並拿你簽過的內容檢查每一個結果，最後交付到正式環境。

同一份原始碼可以安裝到 **KiroCrew**、**Mission Control** 或 **Claude Code**。
換一台新機器，clone 這個 repo，你的 agent 就會把團隊重建起來。

## 安裝

你不需要執行安裝程式。你的 coding agent 讀 `AGENTS.md`，然後把團隊裝進它自己。

**1. Clone 這個 repo**

```bash
git clone https://github.com/shazi7804/devcrew
cd devcrew
```

**2. 在這個資料夾打開你的 coding agent**（Claude Code、KiroCrew 或 Mission
Control），貼上這段：

> Read `AGENTS.md` in this repo and install devcrew into whichever coding-agent
> host you are running in. Detect the host, translate the neutral `framework/`
> source with the matching guide in `hosts/`, generate the agent + skill files,
> verify them, and tell me how to switch to the `orchestrator` agent.

**3. 看它回報什麼。** agent 會回報四件事：

- 它偵測到哪個 host，
- 它產生了哪些 agent 檔和 skill，
- 哪些外部 skill 裝好了、哪些找不到（見[原生技能](#原生技能)），
- 怎麼切換到 `orchestrator`。

在 Claude Code 上，它還會安裝多 session 治理的 hooks，並實際做競爭測試，證明只有
一個 session 會成為 orchestrator。

| Host | 會產生什麼 | 怎麼切換 |
|---|---|---|
| Claude Code | `.claude/agents/*.md`、`.claude/skills/`、`CLAUDE.md` 的一段、`.claude/settings.json` 裡的 hooks | 不用切換：第一個 session 會被選為 orchestrator，之後開的視窗是 worker |
| KiroCrew | `~/.kiro/agents/<role>.json` | 在 dashboard 的 agent 切換器選 **orchestrator** |
| Mission Control | `<DATA_DIR>/agents.json` 裡的角色 + `skills-library.json` | 建一張 `assignedTo: "orchestrator"` 的任務 |

換新機器時，重新 clone 並重做第 2 步。repo 才是唯一的真實來源；安裝出來的檔案都是
產生物，不要手動修改。

## 裝好之後，直接用自然的方式跟 `orchestrator` 說話

沒有指令要學。你是 CEO：想要什麼就直接說，像跟人說話一樣。

> 我想要一個咖啡訂閱的 landing page，要有註冊流程和 Stripe 結帳。

> 客戶說大報表的匯出按鈕很慢，修一下。

> 做一個記帳 App，iOS 和 Android 都要，可以拍收據自動辨識金額。

orchestrator 只會問會改變設計的那幾個問題，把你的意思寫下來，請你簽核。之後它只會在
🔴 關卡回來找你。它每則訊息都是四行的 **SITREP**，看 `CEO：` 那一行就知道有沒有事在
等你。

## 架構

```
                        ┌──────────┐
                        │   CEO    │  idea in · 🔴 sign-offs · final merge
                        └────┬─────┘
                             │ talks only to
                             ▼
┌───────────────────────────────────────────────────────────────────────┐
│ orchestrator (PM): dispatches roles, verifies gates, keeps the ledger │
└──┬────────────────────────────────────────────────────────────────────┘
   │ hands each role a FILE PATH (a contract), never a paraphrase
   ▼
 PHASE       ROLE(S)                   PRODUCES                  GATE
 ─────       ───────                   ────────                  ────
 0   Intent  orchestrator              requirements.md 🔒        🔴 CEO
 0.5 Market  analyst (commercial)      GO / PIVOT / NO-GO        🔴 CEO
 1   Arch.   architect                 design.md + ADRs
                                       standards.md 🔒           🔴 CEO
 2   Design  designer (if UI)          design system + prototype
                                       (award-grade loop)        🔴 CEO
 3   Build   frontend ∥ backend        code + PRs + tests        tests green
 4   Verify  qa ∥ security ∥ auditor*  three verdicts            all pass
 5   Deploy  devops (if service)       running system + smoke    smoke green
 6   Release release (if shipped)      signed artifact → users   🔴 CEO
 ∞   Evolve  proposal → qa ∥ reviewer  signed proposal + PR      🔴 CEO merge

 🔒 = hash-locked. Every later gate re-checks the hash. A change without a new
      signature is drift, and drift halts the run.
 *  = auditor runs only on a large diff (> 1000 changed lines or > 20 files).
 ∥  = dispatched in parallel. Each role has its own context and none reads
      another's verdict.

 LOOPS
   A  fix       a gate fails ──▶ back to the phase that owns the fix (never P0)
                3 attempts, up to 5 while failures keep dropping, then 🔴 CEO
   B  reflect   every task ends with a 3-line retro ──▶ framework/memory/
   C  evolve    a retro suggests a framework change ──▶ signed proposal
                requirements 🔴 ──▶ PR ──▶ CI ──▶ qa ∥ reviewer (another
                model vendor, no team memory) ──▶ 🔴 CEO merge

 ONE SOURCE, THREE HOSTS
   framework/ ──▶ hosts/kirocrew.md        ~/.kiro/agents/*.json
              ──▶ hosts/mission-control.md agents.json + skills-library.json
              ──▶ hosts/claude-code.md     .claude/agents/*.md + hooks
```

完整的架構請看 [ARCHITECTURE.md](ARCHITECTURE.md)：harness 分層、迴圈上限、合約關係圖、
三種狀態，以及多 session 治理。具約束力的規則在
[framework/skills/aidlc/SKILL.md](framework/skills/aidlc/SKILL.md)。

## 團隊

每個角色都有自己的頁面（英文）：它做什麼、接收什麼、交出什麼、必須通過的關卡，以及它
拒絕做的事。

| Agent | 角色 | 階段 | 一句話 |
|---|---|---|---|
| [orchestrator](docs/agents/orchestrator.md) | Orchestrator + PM | 全部 | 對齊意圖、派工給各角色、判定每個關卡 |
| [analyst](docs/agents/analyst.md) | 市場分析 | 0.5 | 判斷這個想法值不值得做：GO / PIVOT / NO-GO |
| [architect](docs/agents/architect.md) | 架構師 | 1 | 透過跨廠商的模型議會選技術棧；寫 ADR 和 `standards.md` |
| [designer](docs/agents/designer.md) | 設計（UI/UX） | 2 | 設計系統 + 2–3 個原型，反覆迭代到得獎水準 |
| [frontend](docs/agents/frontend.md) | 前端研發 | 3 | 用設計 token，照簽過的原型精準實作 |
| [backend](docs/agents/backend.md) | 後端研發 | 3 | 服務、API 與資料層，預設就是安全的 |
| [qa](docs/agents/qa.md) | QA | 4 | 用證據確認每一條簽過的需求都達成 |
| [security](docs/agents/security.md) | 資安 | 4 | 威脅模型、依賴與密鑰掃描、身分驗證／授權審查 |
| [auditor](docs/agents/auditor.md) | 效率稽核 | 4* | 抓出冗餘、該重用沒重用、運行成本；唯讀 |
| [devops](docs/agents/devops.md) | DevOps / SRE | 5 | 部署到 `standards.md` 定義的環境，並跑冒煙測試 |
| [release](docs/agents/release.md) | 發佈管理 | 6 | 版本、簽章、發佈管道、分階段上線、回滾 |
| [reviewer](docs/agents/reviewer.md) | 框架審查 | ∞ | 審查 devcrew 自身的變更；不同廠商的模型、不掛團隊記憶 |

## 原生技能

Skill 是角色按需載入的作業程序。有些隨這個 repo 附帶；其餘來自 host 或第三方，由
`AGENTS.md` 安裝或對應。缺少的話，安裝程序會直接告訴你，而不是自己捏造一個。

| Skill | 使用者 | 來源 |
|---|---|---|
| `aidlc` | 所有角色 | 本 repo：[framework/skills/aidlc](framework/skills/aidlc/SKILL.md)（協作協定與合約範本） |
| `mobile-build` | frontend | 本 repo：[framework/skills/mobile-build](framework/skills/mobile-build/SKILL.md) |
| `mobile-verify` | qa、security | 本 repo：[framework/skills/mobile-verify](framework/skills/mobile-verify/SKILL.md) |
| `mobile-release` | release | 本 repo：[framework/skills/mobile-release](framework/skills/mobile-release/SKILL.md) |
| `impeccable` | designer | [impeccable.style](https://impeccable.style/) · [pbakaus/impeccable](https://github.com/pbakaus/impeccable)（Apache-2.0）：設計評論、稽核、反「AI 感」偵測器 |
| `llm-council` | orchestrator、architect | host skill：跨廠商的對抗式模型議會 |
| `frontend-design-workflow` | orchestrator、designer、frontend | host skill：原型優先的 UI 流程 |
| `web-preview` · `web-verify` | designer、frontend、qa、devops、release | host skill：在瀏覽器中展示並驗證頁面 |
| `deploy-web` · `artifact-deploy` | orchestrator、devops、release | host skill：靜態網站與產出物部署 |
| `goal-conductor` | orchestrator | host skill：長時間目標追蹤 |
| `image-authoring` · `widgets` | analyst | host skill：市場分析用的圖表 |

SITREP 回報格式改編自 [joshuaboys/SITREP](https://github.com/joshuaboys/SITREP)（MIT）。

## 實際看看

### 一次執行長什麼樣子

1. **你說你要什麼。** 例如：*「我想要一個咖啡訂閱的 landing page。」*
2. **orchestrator 只問會改變設計的問題**，然後寫出 `requirements.md` 請你簽核（🔴 關卡）。
3. **它依照範圍派出需要的角色**，一次一個關卡：architect，有 UI 就接 designer，再來
   frontend ∥ backend，然後 qa ∥ security（大型 diff 再加 auditor），要上線或發佈時
   再接 devops 和 release。
4. **它只在 🔴 關卡或完成時回來找你。** 每則回報都是同樣的四行區塊，所以你需要處理的
   那一行永遠在同一個位置：

```
SITUATION  <一行：現在的狀況>
ACTION     <這一輪做了什麼，最多 3 行>
STATUS     DONE | IN PROGRESS | BLOCKED | FAIL — <一句話>
NEXT       CEO：<有編號的請求，你回編號就好>  | 無
           我：<它接下來不需要你輸入就會做的事>
```

回覆編號即可（`1 ①`）。這個區塊填好的範例在
[contracts/sitrep.template.md](framework/skills/aidlc/contracts/sitrep.template.md)。
每個關卡都會留下檔案（`requirements.md`、`design.md`、`design-scorecard.md`、verdict
YAML），你可以打開任何一個自己檢查證據。

### 自己驗證這套機制

以下是在這個 repo 上實際執行的指令，以及它們印出的輸出（只在註明處有刪減）。你也可以
自己跑。

**團隊原始碼沒有寫到任何 host 的工具，也沒有寫死任何機器的資訊**（第 9 條不變條件）：

```console
$ python3 tools/check_neutral.py --self-test
self-test ok
$ python3 tools/check_neutral.py
neutral: ok
```

**同時打開 32 個 Claude Code 視窗，只有一個會成為 orchestrator。** 以下是
[hosts/claude-code.md](hosts/claude-code.md) § *Multi-session governance* (4) 的競爭
測試腳本，在一個拋棄式目錄上以 `B=framework/tools/boot.py` 執行的輸出：

```console
       1
       1
empty stdin exit=0
```

第一個 `1` 是同一瞬間啟動的 32 個 session 中，成為 orchestrator 的數量。第二個是 20 個
session 同時搶一個過期鎖時，搶到的數量。最後一行表示格式錯誤的 hook 輸入不會卡住
session。

**designer 的反「AI 感」檢查。** 這是對一個刻意做得很制式的 hero 區塊（Inter 字體、紫色
漸層、灰色文字）執行 `impeccable detect` 的結果。designer 會一直迭代到它什麼都沒回報為止：

```console
$ npx impeccable detect index.html
  [gray-on-color] text #999999 on bg gradient(#6366f1, #a855f7)
  [low-contrast] 1.4:1 (need 4.5:1) — text #999999 on #a855f7
  [overused-font] Primary font: inter
  [ai-color-palette] Purple/violet accent colors detected

4 anti-patterns found.
$ echo $?
2
```

（有刪減：第一行被掃描檔案的路徑，以及每個發現項目後面那一行修正建議。）

## 文件

| 讀這份 | 用途 |
|---|---|
| [docs/agents/](#團隊) | 每個角色一頁：做什麼、它的關卡、它拒絕做的事 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 一頁看完整個系統：分層、流程、迴圈、合約、狀態 |
| [framework/skills/aidlc/SKILL.md](framework/skills/aidlc/SKILL.md) | 具約束力的協定：階段、關卡、範圍路由、規模門檻 |
| [framework/skills/aidlc/contracts/](framework/skills/aidlc/contracts/) | 範本：requirements、design、standards、verdicts、SITREP |
| [framework/session-governance.md](framework/session-governance.md) | 開了多個 session 時，如何選出唯一的 orchestrator |
| [hosts/](hosts/) | 安裝指南：KiroCrew、Mission Control、Claude Code |
| [AGENTS.md](AGENTS.md) | 給 AI 的啟動檔，以及十條設計不變條件 |
| [CHANGELOG.md](CHANGELOG.md) | 每個版本改了什麼、為什麼改 |

## Repo 結構

| 路徑 | 是什麼 |
|---|---|
| `AGENTS.md` | AI 在全新 clone 上讀來安裝自己的啟動檔 |
| `framework/agents/` | 12 個角色的 prompt：每個 agent 的真實來源 |
| `framework/skills/aidlc/` | AIDLC 協定，加上合約範本（requirements、design、standards、verdicts、SITREP） |
| `framework/skills/mobile-*` | 行動 App 的建置／驗證／發佈程序 |
| `framework/memory/` | 團隊共享記憶：lessons、ADR、回顧 |
| `framework/session-governance.md` + `framework/tools/boot.py` | 開了多個視窗時，決定哪個 session 是 orchestrator |
| `hosts/` | 每個 host 一份轉接指南 |
| `docs/agents/` | 每個角色的說明文件（本 README 有連結） |
| `proposals/` | 每次修改 devcrew 自身時簽過的需求 |
| `tools/` + `.github/workflows/` | CI 檢查：中立性、連結與角色檔、圖表對齊 |

## 原則

1. **簽過的意圖至高無上。** 每個關卡都拿它來檢查。
2. **角色是獨立的 agent，共用一份記憶。** 各自獨立的 context 讓對抗式審查是真的；共享
   記憶讓經驗在團隊中傳承。
3. **關鍵決策要經過跨廠商的模型議會**，不是單一模型說了算。
4. **自我演進有關卡。** 框架的變更也從它自己簽過的需求開始，跟產品變更一樣。它只能以
   PR 的形式進來，通過 CI、依照那份需求的 QA、以及另一家模型廠商的 reviewer，最後由
   CEO 合併。沒有 agent 能合併自己的變更。
5. **技術選型永遠跟上現況。** Architect 在選擇之前會先搜尋當下的技術現況。
6. **部署拓撲依專案而定。** 它在 `standards.md` 裡與 CEO 一起定義；框架從不預設任何雲。
7. **浪費就是關卡失敗。** 測試通過不代表程式碼值得那個體積。大型 diff 由 Auditor 依照
   `standards.md` 裡的預算檢查。
8. **不為了讓東西通過而放寬任何關卡。** 放寬核准關卡、安全控制、權限邊界或觸發條件，
   都需要 CEO 做出決定，並連同理由一起記錄。
9. **框架與 host、機器無關。** `framework/` 不寫任何 host 的工具名稱、也不寫任何機器的
   資訊。`tools/check_neutral.py` 在 CI 中檢查整個 repo。
10. **由機制決定誰負責，而不是靠規則。** 開了多個 session 時，由核心層級的鎖加上心跳租約
    選出 orchestrator，不需要人為每個 session 輸入任何東西。

## 授權

[MIT](LICENSE)
