# WorkBuddy 持续推进 · 接续状态

- **启动**：2026-11-20 00:05 +08（北京时间）· 主控 WorkBuddy · Owner feng
- **集成轮次**：00:28（第一轮）→ 00:41（第二轮）→ 00:50（第三轮）→ 02:24–03:05（第 7 轮，三小时对齐）→ 13:28–14:05（第 8 轮，三小时对齐）→ 15:07–15:40（第 9、10 轮）→ **16:09–（第 11 轮，三小时对齐点 16:28）**
- **下次三小时对齐**：2026-11-20 19:28 +08（第 11 轮已覆盖 16:28 对齐点；对齐只是检查点，手上任务照常推进）
- **依据**：[持续推进计划](continuous-plan.md) · [启动指令](continuous-handoff.md) · [当前事实](../current.md)
- **本文件 owner**：主控（单一写者）。成员不得改本文件；各自交付写入自己的文件，由主控集成。

## W01 · 现场检查（完成，00:05；00:28 按独审修订）

| 项 | 实测 |
| --- | --- |
| 仓库根 / HEAD | `D:/XiangMuLuoDi/Development/ICT/track2/auto-research` · `3049e74946e9993dbd4eb31d186eeab010ade27b`（main，ahead origin/main 2，origin `1b0f065`） |
| 在途改动 | 5 个用户文件（`M current.md`、`M workbuddy/README.md`、`M workbuddy/execution-plan.md`、`?? continuous-handoff.md`、`?? continuous-plan.md`，23:47–23:49 写入）→ **保护不动**；主控独占新文件另列于 `w01-facts.json` |
| 活跃写者 / lease | 未见活跃 lease 或 `.git/*.lock`；**写者纪律是约定，不是机制**，故每次集成做 SHA-256 比对留未覆盖回执 |
| 运行时 | `.venv/Scripts/python.exe` = 3.12.14 + numpy 2.5.4；官方 `freeze.py --check` 须用它 |
| 版本口径 | 托管目录名 `3.13.12` / 二进制自报 `3.13.14` / 无 numpy（两者都留，不判谁错）；`Python314` = 3.14.0 + numpy 2.3.5；PATH `python` = 3.13.14；node v22.22.2 |
| 旧证据可见 | `runs/` 下 M0 / M1 / M1b / mdes 各冻结目录均在（gitignored） |
| 本机状态滞后 | `.agent/CURRENT_STATE.md:3` 仍写「基线 `1b0f065`，工作树干净」，落后一轮 → **只在此标注，未改该文件** |

**首个可运行任务**：W02 —— 固定 Nixtla M4 Hourly 示例的**版本、输入与评价口径并列出缺项**；本机无 `datasetsforecast` / M4 数据 / 评分器，**当前不是「已可实跑」**（独审修订措辞）。

## 第 7 轮 · 三小时对齐（02:24–03:05 +08，零研究行动）

| 项 | 实测 |
| --- | --- |
| 起点 | `3049e74`（main，ahead origin/main 2）；`git status -- src/ scripts/` = **0 项**（本轮新增的 `scripts/w05_card_check.py` 是本轮自有） |
| 保护文件 | 5 个在途/共享文件 SHA-256 **与 00:27:58 基线逐字相同（5/5 未覆盖）**；判定本轮无并发写者（最近写入 00:51，之后 90 分钟无人动盘） |
| 上一会话遗留 | 16 个未提交交付物（`w02`/`w03`/`w03b`/`w03c`/`w04`/`w04b`/`w04c`、`review-*`、`recipe-library-index`、`continuous-*`）**已随本轮入库**，内容未改一字 |
| 交付 | `docs/project/workbuddy/w05-card-draft-20261120.md`（卡草案 v0.1）+ `scripts/w05_card_check.py`（12 规则，退出码 0/2/1） |
| 判定 | 卡 **7 frozen / 1 open / 1 blocked** → **未达 9/9，不得执行**；校验器对本卡 `EXIT 2 DRAFT_OK_NEEDS_OWNER`；自检 **20/20** |
| 复算 | 卡内 7 个数字与 `runs/mdes-20261119/plan.json` 逐个相等（426 / 107 / 48 / 336 / 84 / 0.210508 / 23·1） |
| 用量 | 现金 0 / 模型 0 / 研究行动 0 / 推送 0 / 外发 0 / 平台未知 |

**本轮新增的两条硬事实**：

1. **仓库无任何 RM3 / 伪相关反馈实现**（`rm3`、`pseudo.relevance`、`robertson` 在 `src/`、`scripts/` 三词 0 命中）→ W05 的 B 臂必须先做 W05a 模块 + 退化夹具单测，且**不改** `COMPARISON` 既有常量。
2. **336 与 426 之差是两个常数不是四舍五入**：检测用双侧 `7.848879`，TOST（±.05，mrr@10）用单侧 `6.182558`。合并即算错题量。已写进卡与复算表。

## 第 8 轮 · 三小时对齐（13:28–14:05 +08，零研究行动）

| 项 | 实测 |
| --- | --- |
| 起点 | `ec6d7af`（main，ahead origin/main 4，**未推**）；`git status` = **0 项**；`git diff --stat` 全程为空（本轮只新增文件） |
| 写者 | 最近写盘 02:27:55（第 7 轮 `current.md`/`latest-report.md`），之后约 11 小时无人动盘 → 无并发写者；未伪造 lease |
| 预算 | `.agent/team-budget.json` 未改；`confirmed_cash_spent=null` → unknown；平台用量 unknown |
| 判定 | 阶段仍是**配方库/计划期**（W05 卡 7 frozen / 1 open / 1 blocked），不是 M2/M3 |
| 交付 | `scripts/w05a_rm3.py`（284 行）+ `scripts/w05a_selftest.py`（267 行）+ `runs/w05a-20261120/selftest.txt` + 报告 `w05a-rm3-20261120.md` |
| 结果 | 自检 **49/49**、退出码 0、输出连跑两次逐字节相同（`ef5f654f…`）；包内 `freeze.py --check` = `FROZEN PACKET INTACT` / `f8f35400…`；`w05_card_check.py` 对卡仍 `EXIT 2` |
| 用量 | 现金 0 / 模型 0 / 研究行动 0 / 推送 0 / 外发 0 / 平台未知 |

**本轮新增的三条硬事实**：

1. **F2 漏字段**：卡冻结了 `fb_terms=10` 却没说明扩展词表怎么选。`combined_top_k`（Indri 读法）与 `always_retain`（补回原始词）在 `fb_terms=1` 时给出不同结果（一个返回 3 篇、一个 4 篇）。**W05 执行前 F2 必须补 `original_term_policy` 并由 Owner 冻结**，否则两套数都算合规。
2. **`always_retain` 会让 `fb_terms` 退化**：补回原始词后扩展预算不再约束结果，本例 `fb_terms=1` 与 `10` 完全同结果。选这条策略等于把卡里一个参数变成空参数。
3. **W05a 不写第二份 BM25 常量**：`PROTOCOL` 全部作数据，自检逐项断言与 `relevance_retrieval_adapter.COMPARISON` 相等，并在合成语料上比对 `adapter.retrieve(bm25)` 排序（4 查询 + 1 排除例）全等。第三份实现 = 已知隐患的来源，这次从结构上避开。



## 第 9 轮 · F2 缺口转为机械门禁（15:07 +08，零研究行动）

| 项 | 实测 |
| --- | --- |
| 起点 | `f98965e`（main，ahead origin/main 6，未推）；`git status` 干净 |
| 交付 | `scripts/w05_card_check.py` 加 R13/R14 + 三态判定；卡 F2 补 `arm` 与 `original_term_policy: null`（不改冻结数值）+ 「F2 修订提案（pending）」；报告 `w05-gate-r13-r14-20261120.md` |
| 结果 | 自检 **27/27**（原 20 + 7 新变异）；本卡 `EXIT 2`、`R13 PENDING` / `R14 PASS`；两次输出逐字节相同（`28b34cac…`）；脚本 SHA `81bdf2dc…` |
| 用量 | 现金 0 / 模型 0 / 研究行动 0 / 推送 0 / 外发 0 / 平台未知 |

**本轮最关键的一条**：R13 不只看「卡上写了什么」，还比「模块默认是什么」。否则 Owner 在纸上选 `always_retain`、代码跑 `combined_top_k`，两边都不报错——**决定没落到代码里就不算数**。

**未验项（登记）**：「`w05a_rm3` 加载失败 → R14 FAIL」这条路径没有独立注入测试（要临时移走文件）；`PROTOCOL` 的 `original_term_policy` 默认值是我的选择不是 Owner 的，R13 只保证「卡与默认一致」，不保证「默认正确」。

## 第 10 轮 · P2 配方库门禁（15:10 +08，零研究行动）

| 项 | 实测 |
| --- | --- |
| 起点 | `d1c88cc`（main，ahead origin/main 7，未推）；工作树干净 |
| 交付 | `docs/project/workbuddy/recipe-manifest-20261120.json` + `scripts/p2_recipe_check.py`（11 规则）+ 报告 `p2-gate-20261120.md` |
| 结果 | 真实库 `EXIT 1 (R5_anchor, R6_call_record, R7_min_example)`；R6/R7 均 **10/10 全缺**；自检 **15/15**（含「合成全满足 → EXIT 0」）；两次输出逐字节相同 |
| 用量 | 现金 0 / 模型 0 / 研究行动 0 / 安装 0 / 推送 0 / 平台未知 |

**方法上的一条修正**：直接给卡片散文套字段标签规则会假失败（四张 W04b 卡被误报「缺原产物」）。改为「机器可读清单 + 只核结构与证据存在」，清单显式声明 `field_completeness_verified: false`，不让转写冒充验证。

**解锁路径**：任一张卡跑通最小例 → 改 `min_example`/`call_record` 两个字段 + 给日志路径 → 门禁自动少一条失败项。P2 的进度因此可量化，不必再讨论「是否通过」。



## 第 11 轮 · B1 可达面（2026-11-20 16:09– +08，零研究行动）

| 项 | 实测 |
| --- | --- |
| 起点 | `097f888`（main，ahead origin/main 8，未推）；工作树干净 |
| 交付 | `scripts/portability_scan.py`（静态 AST 可达性）+ 报告 `portability-b1-20261120.md` + `runs/portability-20261120/`（gitignored） |
| 判定 | 144 个入口 → **20 个在 Windows 上判死、16 个 lazy-only**；offending module 只有 1 个：`bounded_study_ledger.py:9` |
| 测量校验 | 18 个判死逐个 `--help` → 全部 `RC≠0` 且含 `No module named 'fcntl'`；9 个 lazy 抽样 → 全部 `RC=0`；**27 个测量点 0 冲突**；2 个 `serve_*` 连 `--help` 都挂（20s 超时）→ **记为未测** |
| 探针（非修复） | 空 `fcntl` 桩入 `PYTHONPATH` → `status` 输出 `PROJECT_NOT_FOUND` 结构化 JSON → **fcntl 是唯一导入期阻塞** |
| 自检 | `--selftest` **11/11**、退出码 0 |
| 用量 | 现金 0 / 模型 0 / 研究行动 0 / 安装 0 / 推送 0 / 平台未知；`src/` 一行未改 |

**决定性冲突（B1 从「等决定」变成「一个二选一」）**：`run_scheduling_policy_transfer.py` 用 `SOURCE_ROOT = Path(__file__).resolve().parents[1]`（**活工作树**）把 `bounded_study_ledger.py` 的哈希算进 `source_fingerprints` 并与固定协议比对。因此「修好 20 个入口」与「保住 G5 存档证据可验证」**互斥**——任何字节改动都会让指纹失配。

**一枚不拦编辑的钉（反直觉，需记住）**：`saved_study_reference.py:30` 也钉同名文件（`1d39b54d…` vs 盘上 `32758129…`），但它解析在 `_SOURCE = /workspace/work/scheduling-threshold-source-62f09ed` 上（第 55 行），绑的是**原始 Linux 快照**，本机不存在 → **不拦活文件**，同时说明 G5 的 L2 原版复现结构性不可达（L2 继续 unknown）。

**自己写错的三处（保留，已固化为夹具）**：① 模块级 import 被 `ast.walk` 与 `tree.body` 各算一次，同时进 `top`/`lazy`；② `from . import a, b` 的名字在 `node.names` 而非 `node.module` → 把 `run_research_project.py` 判成健康（**假阴性，最危险**）；③ 闭包把惰性边当导入期边 → `compile_research_recipe.py`、`fetch_project_source.py` 被判死而实测 `RC=0`（假阳性）。修法：每模块保留 `edges` 与 `eager` 两套边，导入期可达性只用 `eager`。

**计数陷阱（新形态）**：修完再数 `fcntl` 出现次数，24 → 35，多出的 11 次全来自新写的扫描器自己。**新增一个「提到某词的文件」会改变这个词的计数**，与「`grep | head` 截断少计」是同一类错误的另一面；报告中的计数一律注明范围。

## 预算与授权边界（沿用，不重开）

- 共享累计现金上限 **5 CNY**；`confirmed_cash_spent = null` → **unknown**，不记 0。
- M1、M1b 各 2/2 研究行动**已用尽**；旧请求、pin、失败记录不重开、不重置。
- AgentArts 中国站限量体验额度 `2026-11-20 23:59:59 +08` 到期；平台用量 unknown。
- 本启动日：**新增现金 0、模型调用 0、研究行动 0、推送 0、外发 0**；只做零现金的上游核对、只读核验与文档工作。
- 报告严格区分：上游公布成绩 / 本项目复算 / 原版复现 / 真实自主运行。L0/L1/L2 分层见 W03b，当前 L0 已固定、**L1/L2 = unknown，不得跳层推导**。

## 三轮验收总表（主控集成）

| 轮次 | 任务 | 交付 | 判定 |
| --- | --- | --- | --- |
| 1 | W02 M4 复算 | `w02-m4-upstream-20261120.md` | **阻塞但处置正确**：四项前置全缺，官方断言逐字固定（SMAPE 9.328 / MASE 0.893 / OWA 0.440，`atol=1e-3`、另有 `rtol=1e-5`），本项目复算实测值 unknown；按启动指令转 W04 |
| 1 | W03 入口定位 | `w03-entry-map-20261120.md` | 7 类入口有源码依据；**发现新阻塞 B1**；只编译入口 RC=0 并有真实回执 |
| 1 | W04 候选核对 | `w04-upstream-candidates-20261120.md` | 9 候选（8 新核 + 1 复用 g0），均未实跑，逐项登记；OR-Tools 官方页抓取失败如实记录 |
| 1 | 独立评审 | `review-method-20261120.md` + `m4_recompute.py` | 3 处差异 + 2 处措辞限定，主控全部采纳修订 |
| 2 | W04b 配方卡 / 补依赖清单 | `w04b-recipe-cards-20261120.md` | 4 张只读卡；OR-Tools 身份锚定成功（commit `100f66e6…` / blob SHA `a79406fe…` / Apache-2.0）；W02 补依赖清单可供 Owner 一次决策 |
| 2 | W03b B1 处置 | `w03b-fcntl-options-20261120.md` | 三方案 diff 草案（推荐① POSIX 环境，**推荐≠决定**）；**B1 回归点查明**；L0/L1/L2 标注规则与禁写清单 |
| 2 | R1 修订复核 | `review-r1-20261120.md` | 5 处修订 4 已落地、1 部分落地；抓到主控 `grep | head -5` 截断成 5 处（实为 8 处） |
| 3 | W04c 配方库 | `w04c-recipe-cards-20261120.md` + `recipe-library-index-20261120.md` | **10 张卡**；三类覆盖如实（资料 3 / 评测 5 / 工程 2，工程薄弱）；**P2 明确未通过** |
| 3 | W03c W05 依据 | `w03c-w05-entry-basis-20261120.md` | 9 项中 6 项有现成实现、1 项部分、2 项实质缺口；B1 对 W05 卡字段的影响已落到具体项 |
| 3 | R2 独审 | `review-r2-20261120.md` | 两项 needs_review 闭环；W04b/W03b 主体属实、整体口径无夸大；新增 3 项 needs_review（本版已处理） |

## 关键结论（不夸大）

1. **W02 未复算**。`datasetsforecast==1.1.0`、pandas 版本、M4 Hourly 数据与 `submission-118.zip`、数据体量与许可均待核；官方断言只是 L0。W03 的 M4 对照框架已备，**ICT 列与等价性结论保持 unknown**。
2. **P2 未通过**。10 张配方卡数达标，但 **10/10 的「本项目调用记录」全为无（待授权）**、最小例均未执行验证、4 张版本/提交/许可仍 unknown、三类覆盖不均衡。索引已单列差距说明。
3. **B1 是回归，不是历史行为**：`src/autoresearch/bounded_study_ledger.py` 由 `62f09ed`（2026-11-14 07:36 UTC）引入，第 9 行顶层 `import fcntl`；A29/A30（11-03~04）时该导入链不存在。git 只能证明「模块当时不存在」，**当时是 POSIX 还是 Windows = unknown**。
4. **B1 数字口径统一**（R2 指出 W03b 与主控自述冲突，实测三口径）：`import fcntl` 语句 **8 处**（其中顶层无条件 1 处 = B1 直接原因）；若按 `fcntl` token 含 `flock` 计，src 三文件 **12 处**；全仓含 `.pyc` **26 处**。对外统一用「import 语句 8 处」，其余口径须注明范围。核心结论不受影响。**第 11 轮补充一条计数陷阱**：新增 `scripts/portability_scan.py` 后，`src`+`scripts` 内含 `fcntl` 的行数由 24 变 35（多出的 11 行全来自扫描器自身）。**任何计数都必须连同「当时的文件集合」一起报**，否则同一个词会因新增文件而变数。
5. **W05 前置依据已备**：`scripts/compare_project_policies.py` 有同预算两臂设计但 B1 下 Windows 不可运行且会执行真实工具；`plan_mdes.py --help` 在 B1 下可达；预算门部分是代码、部分是协调记录，跨卡累计需人工写死。**W05 卡草案仍待主控起草**，执行需新授权。
6. **口径防线**：禁写「输出口径一致 / 已复现 / 已复算 / 已对照 / 等价 / 已接入平台」「容差已通过」等，直到有真实回执。`p>0.05 ≠ 等价证据`（需 TOST）；MDES \|Δmrr@10\| ≥ .2105、recall@20 有效样本量为 1。

## 阻塞与待 Owner 决定事项（全部挂起，不自行解除）

| 编号 | 事项 | 需要什么 |
| --- | --- | --- |
| D1 | 平台接入继续暂缓 | Owner 决定是否解除；P3 的 AgentArts 两轮闭环无法启动 |
| **B1** | CLI 主入口在 Windows 因 `fcntl` 不可用 | 第 11 轮已量化：**144 个入口中 20 个判死、16 个 lazy-only**，根因单一（`bounded_study_ledger.py:9`）；27 个测量点 0 冲突。选项收敛为「见 B1×G5 取舍」一行 |
| **W02 补依赖** | 官方评分复算 | 一次性授权：装 `datasetsforecast==1.1.0` + 依赖、下载 M4 数据与 `submission-118.zip`、确认数据许可。零现金但改本机环境并新增外部数据 |
| 配方实跑 | P2 的「本项目调用记录」 | 各配方的依赖安装、数据下载、索引/API 授权（BEIR 独立索引、OpenML API key、GPT Researcher 等模型凭证） |
| M1b 签字 | 审批卡 `needs_review` | 仅本人可清 |
| 报名状态 | unknown | 核实是否已报名（截止 2026-11-30） |
| **B1×G5 取舍** | 第 11 轮新发现：修 B1 **必然**让 G5 transfer 证据的 `source_fingerprints` 失配 | 一个二选一：是否同意把 G5 scheduling-threshold-transfer 证据标记为**历史证据（绑定 `62f09ed`）**，从而允许修改 `bounded_study_ledger.py`？同意→下一轮做守卫式导入 + Windows 锁抽象并显式更新期望指纹；不同意→20 个入口保持不可用，P2 调用记录只走不依赖该链的独立模块路径 |
| `serve_*` 挂起 | 第 11 轮副作用发现：`serve_local_workbench.py` / `serve_project_workbench.py` 连 `--help` 都不返回（20s 超时被 SIGTERM） | 零成本可查（不属研究行动）：是否忽略参数直接起服务；查清前这两个入口的可用性记 **unknown**，不写「已通过」 |
| **W05 F1 独立数据** | 卡草案的 open 项 | Owner 在 O1 同卷换题 / O2 另一 CFR title 固定卷（推荐）/ O3 其他公有领域源 中选一；选后定题量 |
| **W05 F2 扩展词策略** | 卡草案的**新缺口**（第 8 轮发现） | F2 只冻结了 `fb_terms=10`，未定「扩展词表怎么选」。实测 `combined_top_k` 与 `always_retain` 在 `fb_terms=1` 时结果不同（3 篇 vs 4 篇）→ Owner 需在 F2 补 `original_term_policy` 并冻结；**不改视为未达 9/9** |
| **W05 F4 反馈分支** | 卡草案的 blocked 项 | 依赖 B1 处置（同上）；分支条件已冻结、真实回执无法取得 |
| W05 执行 | 新真实研究 | 卡 9/9 冻结 + 本人签字 + 行动额度（建议 2 次）；批准后先做 W05a |
| W05a RM3 模块 | **完成（第 8 轮）**：`scripts/w05a_rm3.py` + `scripts/w05a_selftest.py` 49/49、退出码 0；未接线、未碰冻结语料、未改 `COMPARISON`。**新缺口**：F2 需补 `original_term_policy`（Owner 冻结） |
| W06 汇集证据 | 交付证据 | 依赖 P3/P4 真实产物；当前无可汇集的平台回执 |

## 队列状态

| 任务 | 状态 |
| --- | --- |
| W01 现场与接续记录 | **完成**（含 5 处独审修订） |
| W02 M4 复算 | **阻塞**：断言与缺项已固定，转 W04；需授权 |
| W03 入口定位 / 对照框架 | 入口定位**完成**（含 B1）；对照框架已备，ICT 列待 W02 原输出；**第 11 轮把 B1 量化**：144 入口 / 20 判死 / 16 lazy-only，`scripts/portability_scan.py` 自检 11/11 |
| W04 / W04b / W04c 候选与配方库 | **完成**：9 候选登记 + 10 张只读卡 + 索引；**第 10 轮把 P2 判定做成可复算门禁**（`recipe-manifest` + `p2_recipe_check.py`，11 规则，自检 15/15）→ 当前 `EXIT 1`：R5 两张未版本化、R6/R7 **10/10 全缺** |
| 独立评审（办法 / R1 / R2） | **完成**：两项 needs_review 已闭环，3 项新增已在本版处理 |
| W05 新课题卡 | **草案 v0.1 已起草**（第 7 轮）：7 frozen / 1 open / 1 blocked，机械校验 `EXIT 2`；**执行仍需授权**；批准后先做 W05a（RM3 模块 + 单测） |
| W06 汇集证据 | 待 P3/P4 真实产物 |

## 独审 needs_review 台账

- R1 提出 2 项 → **均闭环**：哈希回执集成后比对已回填（00:41:10，5/5 一致）；fcntl 清单补全为 8 处并记教训「写计数前不要用带 `head` 的截断输出」。
- R2 提出 3 项 → **均处理**：B1 三口径已在上文统一；对齐记录/派发表已更新到 00:50；L0/L1/L2 当前 `not_started`，拿到实测时不得跳层。
- **第 7 轮新增 2 项**：① `w05-card-draft-20261120.md` 由主控起草、**未经独立评审**（起草人不能自审自己的卡），按门槛清单原样交独审；② 校验器首版 R8 假失败（在散文里搜机器字段）已修，保留为「先跑真实对象再看自检」的教训。
- 保留：M1b 审批卡签名 `needs_review`（仅本人可清）；W02/W03/P3 实质结果、平台用量、历史现金结算 = unknown。

## 团队与写者纪律

本会话**无在途成员可复用**（新会话，无活跃 lease 或成员回执），按计划角色新建三名成员；复用项目已有角色口径、开发导航索引与 g0 上游资料。后续同类任务**全部交回原成员**（保留上下文），共三轮。

| 角色 | 成员名 | 任务链 |
| --- | --- | --- |
| 主控 | WorkBuddy | W01、派活、验收、集成、队列、对齐摘要 |
| 上游工作流 Agent | `upstream` | W02 → W04 → W04b → W04c |
| 产品接入 Agent | `integration` | W03 → W03b → W03c |
| 独立评审 Agent | `review` | 复核办法 → R1 → R2（未参与任何实现） |

每个文件同一时间只有一名 owner；成员只写自己名下交付与 `runs/continuous-20261120/<角色>/`。**最终哈希回执（00:50:23 +08）：5 个保护文件 SHA-256 与基线逐字一致（5/5，未覆盖）；`git status -- src/ scripts/` = clean，全程未改源码**；独审 R1/R2 各自独立实测一致。

## 对齐记录

| 时间（+08） | 完成项 | 用量 | 待决事项 | 下一项 |
| --- | --- | --- | --- | --- |
| 00:28 | W01、组队、第一轮 W02/W03/W04/独审、5 处修订 | 现金 0 / 模型 0 / 研究行动 0 / 平台 unknown | D1、B1、W02 补依赖、M1b 签字、报名、W05 | 第二轮 W04b/W03b/R1 |
| 00:41 | 4 张卡、OR-Tools 身份、B1 三方案与回归点、R1 | 同上 | 同上 | 第三轮 W04c/W03c/R2 |
| **00:50** | 10 张卡 + 索引（P2 未通过）、W05 依据、R2、needs_review 闭环、三口径统一 | **现金 0 / 模型 0 / 研究行动 0 / 推送 0 / 外发 0 / 平台用量 unknown** | 见「阻塞与待 Owner 决定事项」 | 起草 W05 卡草案（零成本）；其余均需授权 |

## 会话边界与恢复

- **本启动日零现金可做项已用尽**（三名成员与主控均已确认），剩余全部需 Owner 授权，故按计划「所有可执行工作同时受阻」结束当前推进并交接。
- 三小时对齐点是 **06:05 +08**；本次会话结束后**不常驻、不假称轮间常驻模型**。接续点已完整保存：本文件、`w01-facts.json`、`integration-receipts.md`、W05 卡草案与各成员交付。下次说「继续」即从「阻塞表 → W05 卡草案待 Owner 审 / W05a」接上，用原任务号与原请求身份，不重复启动已完成工作。
- 恢复时先核：保护文件哈希、在途状态、`src/`/`scripts/` 是否 clean、以及 Owner 是否已对 D1/B1/W02 作出决定。
