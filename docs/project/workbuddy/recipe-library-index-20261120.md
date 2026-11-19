# Auto Research 配方库索引 · 2026-11-20

- 维护人：`upstream`（上游工作流 Agent）· 本文件 owner：upstream（只写本文件；共享状态/计划由主控集成）
- 依据：P2 验收（`continuous-plan.md` 第 36 行）——「十个或更多上游工作流的版本化配方，带原入口、数据与许可、典型输入、原产物、失败条件、反馈分支和 ICT 改造点；每条入库配方有可重跑的最小例和本项目调用记录；条件不足的候选标明阻塞及可替代来源；至少覆盖资料研究、数据评测和工程计算」
- **总体状态：配方卡数量达标（10 张），但 P2 未通过**——关键缺件「本项目调用记录」10/10 全为无。详见末尾差距说明。
- 口径：所有卡的数值均为上游公布/文档示例；**本项目复算实测值全部 unknown，未实跑**。

## 1. 配方卡总表（10 张）

| # | 配方 | 文档与锚点 | 固定版本/提交 | 覆盖类别 | 状态 | 本项目调用记录 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Matbench `matbench_steels` | `w04b-recipe-cards-20261120.md` 卡1 (L12) | automatminer `1.0.3.20200727` / matbench `0.1.0`；repo commit unknown | 数据评测 | 已固定·未实跑 | 无（待授权） |
| 2 | Fairlearn Credit Loan | `w04b-recipe-cards-20261120.md` 卡2 (L30) | Fairlearn `0.16.0.dev0`；依赖/commit unknown | 数据评测 | 已固定·未实跑 | 无（待授权） |
| 3 | NumPy ASV 版本对照 | `w04b-recipe-cards-20261120.md` 卡3 (L48) | NumPy `v2.6.dev0` 文档；asv 版本/对照 commit unknown | 工程计算 | 已固定·未实跑 | 无（待授权） |
| 4 | BEIR SciFact `evaluate_bm25.py` | `w04b-recipe-cards-20261120.md` 卡4 (L69) | beir commit `ef83d293…` / v2.2.0 | 数据评测 | 已固定·未实跑·阻塞(索引/ES) | 无（待授权） |
| 5 | OR-Tools Job Shop | `w04c-recipe-cards-20261120.md` 卡5 | or-tools commit `100f66e6…` / blob `a79406fe…` / Apache-2.0 | 工程计算 | 已固定(身份锚定)·未实跑 | 无（待授权） |
| 6 | OpenML-CC18 | `w04c-recipe-cards-20261120.md` 卡6 | study `study_99` / OpenML-CC18；openml 版本 unknown | 数据评测 | 已固定·未实跑·阻塞(API key/许可) | 无（待授权） |
| 7 | GPT Researcher Deep Agents | `w04c-recipe-cards-20261120.md` 卡7 | main 分支（release/commit unknown） | 资料研究 | 已固定·未实跑·阻塞(付费 API key) | 无（待授权） |
| 8 | data-to-paper `social_network` | `w04c-recipe-cards-20261120.md` 卡8 | PyPI（版本 unknown）；MIT | 资料研究 | 已固定·未实跑·阻塞(LLM token) | 无（待授权） |
| 9 | Agent Laboratory YAML 例 | `w04c-recipe-cards-20261120.md` 卡9 | commit `d9017d90…`（g0）；MIT；YAML 入口 unknown | 资料研究 | 复用 g0·未实跑·阻塞(runtime/模型) | 无（待授权） |
| 10 | M4 Hourly 官方评分（**仅 L0**） | `w04c-recipe-cards-20261120.md` 卡10 | datasetsforecast `1.1.0`（PyPI；官方页版本 unknown） | 数据评测 | L0 已固定·L1 未实跑·阻塞(依赖/数据/许可) | 无（待授权） |

文档路径均相对于 `docs/project/workbuddy/`。证据目录：`runs/continuous-20261120/upstream/w02/`、`w04/`、`w04b/`、`w04c/`。

## 2. 固定版本/提交一览

| 配方 | 锚定强度 | 值 |
| --- | --- | --- |
| OR-Tools Job Shop | 强（commit+blob+size+URL） | `100f66e6242ab8bf8d32feb8f3bf086db66ae2b5` / `a79406febd49176474364c5697f41eee1d91e849` |
| BEIR SciFact | 强（commit+脚本 SHA） | `ef83d29307061c65d04b035b4f4e7c18bd8374af` |
| Agent Laboratory | 强（commit，g0） | `d9017d90e329112d2a80b7712f37ee9094d2cd27` |
| Matbench | 中（包版本精确，repo commit 缺） | `automatminer==1.0.3.20200727` / `matbench==0.1.0` |
| Fairlearn | 中（文档版本，依赖/commit 缺） | `0.16.0.dev0` |
| NumPy ASV | 中（文档版本，对照 commit 缺） | `v2.6.dev0` |
| OpenML-CC18 | 中（study 标识，包版本缺） | `study_99` |
| M4 Hourly | 中（PyPI 最新，官方页版本缺） | `datasetsforecast 1.1.0` |
| GPT Researcher | 弱（分支名，release/commit 缺） | `main` |
| data-to-paper | 弱（PyPI 名，版本缺） | `data-to-paper`（版本 unknown） |

## 3. 三类覆盖自检（如实，不平均凑数）

- **资料研究（3 张：GPT Researcher、data-to-paper、Agent Laboratory）**：数量够，但**覆盖质量薄弱**——三者全部因付费 API/模型凭证或 runtime 未做而阻塞，无一张在本机实跑或可零成本实跑；能直接零现金工作的只有「引用/未解问题回写」「主张→代码行回溯」等**设计借鉴**，不是可调用配方。GPT Researcher/data-to-paper 的 release/commit 也最弱（unknown）。
- **数据评测（5 张：Matbench、Fairlearn、BEIR、OpenML-CC18、M4）**：数量最多、覆盖最实，含检索/公平性/材料回归/分类基准/预测评分多种口径；但同样全部未实跑。M4 严格停在 L0，L1 复算未做——这是 P1 的核心缺口。BEIR 卡受「ES + 禁止重建索引」约束，OpenML-CC18 受 API key 与许可约束。
- **工程计算（2 张：NumPy ASV、OR-Tools）**：**覆盖薄弱**——仅两张。OR-Tools 身份锚定最强（已固定 commit+blob），是与 W03 通用调用入口最匹配的候选；NumPy ASV 只有命令固定、无对照数值。两者均未实跑；工程计算类明显少于数据评测类，未做平均覆盖。

结论：三类**形式上都有覆盖**，但资料研究类全部阻塞、工程计算类仅 2 张且未实跑，覆盖不均衡；这是如实记录，不通过平均分配掩盖。

## 4. 缺件与下一验收（逐类汇总）

| 配方 | 主要缺件 | 下一验收方式 |
| --- | --- | --- |
| Matbench | 折数据哈希/样本数、旧 venv 可行性、repo commit | 固定折数据后评估旧环境，先入只读基线卡 |
| Fairlearn | fairlearn/lightgbm 依赖、UCI 数据哈希、rand_seed 固定 | 授权后单跑复核 overall 三指标与分组差异 |
| NumPy ASV | asv 安装、numpy benchmark 树、对照 commit | 授权后单基准 `--python=same` 记录计时分布 |
| BEIR | ES 服务、独立索引、pytrec_eval、SciFact 许可、NDCG@10 数值 | 授权后独立索引 `initialize=False` 跑并落盘逐题结果；或本地评分 fixture |
| OR-Tools | ortools 安装、官方页排程数值 | 授权后固定 3-job 跑，记 status/makespan/排程 |
| OpenML-CC18 | openml 包、task 列表/split 哈希、API key、数据许可 | 授权后本地单任务（不 publish）对照 |
| GPT Researcher | 付费 OPENAI/TAVILY key、联网、release 固定 | 授权后用 `source=local` + 预算跑最小例，核引用可追溯 |
| data-to-paper | LLM token、示例手稿可得性 | 授权后最小跑 social_network，核主张→代码行回溯与 watermark |
| Agent Laboratory | YAML 入口/阶段产物（unknown）、runtime smoke、模型凭证 | 先核 YAML 例输入与恢复机制；禁不可信 pickle |
| M4 Hourly | datasetsforecast/pandas、M4 数据、submission-118.zip、数据许可；L1 复算 | 一次性授权后按 W02 补依赖清单复算，通过转 W03 |

## 5. P2 差距说明（必须如实，索引不代表 P2 已通过）

**当前 P2 未通过。** 逐条对照验收条件：

1. **「十个或更多版本化配方」——数量达标但不完整**：卡数 10，满足数量；但其中 4 张（GPT Researcher、data-to-paper、Agent Laboratory、data-to-paper 类）的 release/commit、数据许可或入口为 unknown，版本化固定不完整；M4 卡只有 L0。
2. **「每条入库配方有可重跑的最小例」——形式达标**：10 张均写了可重跑最小例草案（卡 9 因 YAML 入口未核而标注「未完整定义」）。但**最小例全部未执行验证**，其可执行性未经本项目确认。
3. **「每条入库配方有本项目调用记录」——完全缺失（关键阻断项）**：**10/10 张卡的「本项目调用记录」均为「无（待授权）」**。没有任何一条配方在本项目里被真实调用过，没有任何调用回执。这是 P2 最核心的未达项，不能因卡数达标而视为通过。
4. **「至少覆盖资料研究、数据评测、工程计算」——形式覆盖但不均衡**：见第 3 节；资料研究类全部阻塞，工程计算类仅 2 张。
5. **「条件不足的候选标明阻塞及可替代来源」——已做**：阻塞与可替代来源（如 BEIR 本地评分 fixture、OR-Tools 作通用入口验证）已逐卡登记。
6. **上游成绩/本项目复算/原版复现/真实自主运行的区分——已做**：全部卡均标上游公布值与 L1 unknown，未见冒充。

**结论**：本索引证明的是「**配方卡骨架齐备（10 张）**」，不是「P2 已验收」。P2 的真实通过取决于后续**获得 Owner 授权**后至少一批配方的**真实调用回执**——在此之前 P2 保持未通过/待授权。

## 6. 需要 Owner 授权才能做的事项（本轮不自行执行）

1. W02 M4 L1 复算：装 `datasetsforecast==1.1.0` + 依赖、下载 M4 Hourly 数据与 `submission-118.zip`、确认数据许可；按 `w02-dependency-decision.json` 一次性决策。
2. 任一配方产生「本项目调用记录」：所有 10 张卡的最小例实跑均需授权，且不得改变冻结包与在途文件。
3. BEIR：独立索引上跑（需明确允许）并确认不重建共享索引；SciFact 数据许可确认。
4. GPT Researcher / data-to-paper / Agent Laboratory：付费 API key / LLM token / 模型凭证与联网，零新增现金边界下禁止，需单独预算授权。
5. OpenML-CC18：API key 与外发（`run.publish()`）需平台变更授权。
6. OR-Tools、NumPy ASV、Matbench、Fairlearn：依赖安装与外部数据下载需授权。

## 7. 证据路径

- 补卡：`docs/project/workbuddy/w04c-recipe-cards-20261120.md`
- 原 4 卡：`docs/project/workbuddy/w04b-recipe-cards-20261120.md`
- 候选骨架与来源：`docs/project/workbuddy/w04-upstream-candidates-20261120.md`、`runs/continuous-20261120/upstream/w04/preflight-and-sources.md`
- W02 决策与复算草案：`docs/project/workbuddy/w02-m4-upstream-20261120.md`、`runs/continuous-20261120/upstream/w02/`、`runs/continuous-20261120/upstream/w04b/w02-dependency-decision.json`
- OR-Tools 身份：`runs/continuous-20261120/upstream/w04b/ortools-identity.md`
- 本轮证据：`runs/continuous-20261120/upstream/w04c/`

## 8. 失败与未解记录

- 全程零现金只读：未安装、未下载数据集、未实跑、未重建索引、未调用模型、未改源码/冻结包、未 push、未外发；未碰 5 个在途文件、`continuous-status.md`、`integration-receipts.md`。
- 未验证量（各 release/commit、许可、样本数、SciFact NDCG@10、OR-Tools 排程数值、下载体量、YAML 入口等）写 unknown，无猜测。
- OR-Tools 官方页抓取失败、curl schannel TLS 失败已如实登记；未反复重试。
