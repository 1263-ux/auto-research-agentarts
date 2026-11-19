# W02/W03 独立复核办法 · W01 现场独审 · W05 卡预审（2026-11-20）

- 评审角色：`review`（独立评审 Agent）· 向主控 WorkBuddy 汇报
- 独立性声明：本评审**未参与** W01/W02/W03 的实现；W02/W03 的复核办法在**不看上游 Agent 实现**的前提下写成。本轮**不预断 W02/W03 结果**（产物尚未产出），只准备办法、审现场。
- 硬边界遵守：零新增现金；未调用模型、未执行研究行动、未改冻结包、未 `git push`、未外发；未修改任何成员或主控的文件，未触碰 5 个他人在途改动文件与主控独占的 `continuous-status.md`。
- 本文件 owner：`review`。另写：`runs/continuous-20261120/review/m4_recompute.py`（复算草案）、`runs/continuous-20261120/review/w01-spotcheck.json`（独审实测证据）。两个 runs 文件均被 `.gitignore:33:runs/` 忽略。
- 依据：`continuous-plan.md`、`continuous-status.md`、`w01-facts.json`、`.agent/team-budget.json`、`.agent/CURRENT_STATE.md`、`AGENTS.md`、`docs/execution/g0/independent-review.md`、`docs/execution/g0/upstream/license-security-audit.md`、`docs/execution/g5-local/native-results-independent.json`、`docs/execution/pack-v2/00-charter/PRODUCT_CHARTER.md`、`docs/project/workbuddy/next-card-mdes-20261119.md`、`docs/recipe-research/integration.md`。
- 复核范式沿用项目既有独审范例：先固定字节与哈希、再独立算术复核、明确 `scope` 一字不扩写（`g5-local/native-results-independent.json` 的 `status: saved_artifacts_verified_no_reexecution` 与 `scope` 字段是可照抄的写法）。

---

## A. W02 的独立复核办法（Nixtla M4 Hourly 官方评分复算）

上游 Agent 的断言目标是：ESRNN 提交 118、`M4Evaluation.evaluate`、sMAPE 9.328 / MASE 0.893 / OWA 0.440、容差 `1e-3`。下面是在不看其实现的情况下，我判定「复算通过」所需的最小条件。

### A1. 固定输入怎么回源核（五项 identity，缺一不可）

| 编号 | 要固定的对象 | 必须记录的字段 | 通过标准 | 缺失时结论 |
| --- | --- | --- | --- | --- |
| I1 | 上游版本/提交 | 上游仓库 URL、`git` commit SHA（不是 tag/分支名）、克隆时间；评分模块文件路径 + 字节数 + SHA-256 | 提交可回链到官方仓库，模块哈希与所固定提交一致 | `needs_review`（口径不可核） |
| I2 | 预测文件（submission 118） | 文件路径、字节数、SHA-256、行数、列结构（id + H1..H48）、覆盖序列数 | 与官方示例所指提交文件字节级一致；行数 = 序列数 × 48；无缺行/重行 | `needs_review`；若非官方原件则不能算「上游公布成绩复算」 |
| I3 | 数据划分 | M4 组名 `Hourly`、数据源版本/下载方式、序列数（M4 Hourly 为 414）、预测步长 H=48、训练/测试切分口径、季节周期 m=24 | 切分与官方示例一致，训练段只用于 MASE 尺度 | `needs_review` |
| I4 | 运行环境 | Python 版本、`numpy` 版本、评分器依赖版本、命令全文、工作目录、随机种子（若评分路径无随机则记 `none`） | 与 I1 固定提交的要求相容；命令可原样重放 | `needs_review` |
| I5 | 产物原件 | 原评分器 stdout/stderr 全文（含三指标全精度）、退出码、任何临时文件 | 原件存在且未被事后编辑；编辑过需保留前后哈希 | `无法复算` |

注意：I1–I5 必须**由上游 Agent 交出**，我只能核其完整性、自洽性与字节哈希，不能替它固定。截至目前，仓库内**没有** datasetsforecast / M4Evaluation 源码，`.venv` 也**没有**安装 nixtla 系列依赖（实测，见 `w01-spotcheck.json`）；`upstream-manifest.json` 只固定了 8 个 G0 仓库，**不含** M4 上游。因此「上游公布成绩」目前只有计划 `continuous-plan.md:46` 的一行断言，不构成可复算输入。

### A2. 原评分器的实现口径要核什么（不看实现也要列出的核对清单）

- **sMAPE**：核分子/分母是否为 `|y-ŷ|` / `(|y|+|ŷ|)`、是否乘 200 并以百分数表示；`y=ŷ=0` 与 `y=0,ŷ≠0`（及反向）的零分母处理；聚合是**所有序列×步长 pooled** 还是逐序列先算再宏平均；是否丢弃缺失点。M4 官方口径是整组所有预测点 pooled。
- **MASE**：核季节周期 **m=24（Hourly）**；尺度分母是否为训练段 `mean(|y_t − y_{t−m}|)`（只用 in-sample，不得用测试段）；逐序列分子 `mean(|y−ŷ|)/尺度` 后再对序列取均值，还是 pooled；零/近零尺度序列如何处理；是否有 clip。m 或分母区间取错会系统性改变 MASE。
- **OWA**：核是否为 `0.5 × (sMAPE/sMAPE_naive2 + MASE/MASE_naive2)`；**两个 naive2 分母的来源**（是 M4Evaluation 内固定常数，还是示例内现算 naive2 预测）——这是最容易被含糊过去的一项，必须给出常数值及其所在文件/行的哈希证据；OWA 用未舍入还是已舍入的三指标计算。
- **rounding 与聚合**：核舍入发生的位置（仅最终展示 3 位，还是中间步骤也舍入）、舍入位数、是否先按序列聚合再舍入；核对 414 条序列是否全部纳入、有无按长度加权。
- **口径变更禁令**：若复算不通过，禁止改评分器/冻结输入去迁就数字（`AGENTS.md:5`、`AGENTS.md:14`、`CURRENT_STATE.md:18`）。只可判差异并保留双方原件。

### A3. 容差 `1e-3` 怎么用

- 判为**绝对差**：`|复算值 − 断言值| ≤ 1e-3`，逐指标独立判定，三项**同时**成立才算复算通过。
- **不是相对差**：`rtol=1e-3` 在 9.328 上约等于 ±0.0093，比 3 位小数的发布值宽一个量级，会把版本漂移误判为通过。若原示例确用 `np.isclose`，必须记录其 `rtol`/`atol` 实参；默认应按 `rtol=0, atol=1e-3` 解释。
- **不是整体判**：不得用「三指标差值的均值/最大值 ≤ 1e-3」或任一项通过即宣告通过；也不得用「复算值四舍五入到 3 位等于 9.328」替代绝对差判定（可作辅助证据）。
- 边界：由于断言值本身只给 3 位小数，`1e-3` 已覆盖其舍入误差（±5e-4）；若全精度差落在 `(1e-3, 1e-2]`，判 `needs_review`（疑似版本/口径差异，不判通过也不判失败）；`> 1e-2` 判差异。

### A4. 「复算通过」的最低原始证据与判定矩阵

**最少证据（同时具备才成立）**：I1–I5 全套 identity；原评分器三指标全精度输出；独立复算脚本（我写的草案或其等价实现）+ 其 SHA-256；输入文件哈希；逐指标 absolute diff 与三项 verdict；一段明确写的 `scope`（复算的是「在冻结提交 118 预测文件上的公开评分算术」，不含模型训练、不含数据集许可认证、不含平台调用）。

| 情形 | 结论 |
| --- | --- |
| I1–I5 齐全，独立算术复核三项绝对差 ≤ 1e-3 | **复算通过**（仅限公开预测评分复算这一 scope） |
| 只有截图/Markdown 表格里的三个数字，无预测原件 | **无法复算** |
| 有预测文件但哈希/字节数与官方不一致，或版本未固定 | `needs_review`（输入未钉死） |
| 评分器未固定提交、naive2 分母未披露 | `needs_review`（口径不可核） |
| 全精度差落在 `(1e-3, 1e-2]` | `needs_review`，保留双方原件，不改冻结包 |
| 全精度差 `> 1e-2`，或序列数/H/m 与官方不符 | **差异**（不通过） |
| 预测文件为本地重新生成而非官方提交 118 原件 | 不能算「上游公布成绩复算」；至多是「原版复现」尝试，另记 |

### A5. 三层（实为四层）证据门槛，防止混淆

| 主张 | 证据门槛 | 本轮能否成立 |
| --- | --- | --- |
| **上游公布成绩** | 官方 Nixtla 页面/示例的出处链接 + 断言三指标 + 其所指 submission 118 原件可回源；不需要本地执行 | 目前只有 `continuous-plan.md:46` 的一行转述，**出处链接与原件都未落盘**，只能记为「待核的上游断言」 |
| **本项目复算** | A4 最少证据全套；对同一冻结预测文件、同一评分口径独立算出三指标且 ≤ 1e-3 | 产物未出，本轮不预判 |
| **原版复现** | 从原始数据与固定 seed 重新训练 ESRNN（或运行上游入口）生成提交 118 文件，文件哈希/指标与官方一致；需要额外算力与时间，与本轮零现金、零研究行动边界冲突 | **未授权，不得声称** |
| **真实自主运行（P3）** | AgentArts 原项目/运行/请求 ID、两轮闭环证据、触发下一轮的观察、预算原账 | D1 未解除（`CURRENT_STATE.md:31`），**无法启动** |

报告里四者必须分别命名，禁止用「已验证/已复现」统称。

### A6. 不依赖作者实现的可执行复核算式与脚本草案

草案：`runs/continuous-20261120/review/m4_recompute.py`（纯标准库 + numpy，已落盘但**未对任何真实数据运行**——输入尚未产出）。

算式（与作者实现无关的定义）：

```
sMAPE = 200 * mean_over_all_points( |y - ŷ| / (|y| + |ŷ|) )        # pooled；零分母按 A2 规则处理并计数
MASE_s = ( (1/H) * Σ_h |y_{s,h} - ŷ_{s,h}| ) / ( (1/(T_s-m)) * Σ_{t=m+1..T_s} |y_{s,t} - y_{s,t-m}| )
MASE  = mean_over_series(MASE_s)                                   # m=24, H=48
OWA   = 0.5 * ( sMAPE / SMAPE_NAIVE2 + MASE / MASE_NAIVE2 )        # 分母必须来自已固定评分器源码
verdict_i = |computed_i - asserted_i| <= 1e-3   (i ∈ {smape, mase, owa})
```

脚本要点：
- `--owa-smape-naive2` 与 `--owa-mase-naive2` 为**必填**参数，迫使评审从已固定评分器源码抄入分母并记录来源哈希；脚本内**不内置**任何未经固定的常数值，避免把记忆当证据。
- 对预测/实际文件计算 SHA-256，检查 `(序列数 × H)` 覆盖、无重行缺行；输出全精度指标、逐指标绝对差、三项 verdict、零分母计数。
- `--self-test` 用合成数据（naive2 分母取 1）只验证算术实现，不冒充任何上游结果。

**适用边界**：只验证「给定预测文件上的评分算术 + 输入 identity」，不验证预测来自 ESRNN、不重训模型、不验证 naive2 常数本身的正确性（只验证它被固定且被正确使用）、不验证数据许可/来源声明、不证明平台接入。它依赖 `numpy` 浮点；若与原评分器全精度差 > 1e-9，须先排查公式变体（聚合顺序、零分母处理），不得直接判通过。

---

## B. W03 的独立复核办法（同输入等价性、原请求恢复、预算、入口证据分界）

### B1. 同输入等价性怎么判

- **同输入**不是「看起来同一份数据」，而是字节级 identity 相同：A1 的 I2/I3/I5 在 W02 基线与 W03 ICT 调用两侧**同一文件哈希、同一切分、同一评分器版本**，且传入ICT入口的参数逐字段相同。
- **等价性判据（两层，都要）**：
  1. 产物层：两次调用产出的四文件包（`input.json`/`report.json`/`report.md`/`report.pdf`，见 `integration.md:52`）逐文件 SHA-256 + 字节数一致（或至少 `input.json`/`report.json` 的机器可读部分逐字段一致；PDF 若因时间戳不同，须显式说明并只比较机器字段）；
  2. 指标层：三指标**全精度**一致（确定性算术应绝对相等；若不等，`needs_review`，不得用「都四舍五入成 9.328」判等价）。
- 不等价时先定位差异源：入口参数、版本值、context 封印、评分器版本、聚合顺序。禁止通过重建项目/换版本值消除差异（`integration.md:44`）。

### B2. 原请求恢复核什么字段

按 `integration.md:30-35, 70` 的固定恢复机制，逐字段核：

1. `request_id`：**复用原 ID**，不得新建绕过；
2. 原配方/原命令全文（字节一致，含 `--recipe`、`--need`）；
3. 原 `need`（如 `next_check`）；
4. 原版本值 `state_version` / `--expected-state-version`（**关键是执行前的值，不是执行后的 v7/v11**）；
5. 命令身份 `controller.advance_recipe` 与上下文身份 `selection_context`、父/子请求关系；
6. 快照 `snapshot_ref`、`code_identity`、原 action IDs、结果哈希（范式见 `g5-local/native-results-independent.json:30-43, 70`）；
7. 恢复后的行为：状态/用量/快照**无新增**（`integration.md:70` 的三条 ID 重放先例）；
8. 未知执行状态只沿原恢复路径核对，不用新 ID（`integration.md:35`）。
缺任一字段判 `needs_review`；ID 被替换或版本值被换成执行后的值判**差异**。

### B3. 预算不重开怎么核

- 前后各取一次 `.agent/team-budget.json` 的 SHA-256 + 全文字节：`cumulative_additional_cash_limit` 仍为 5、`confirmed_cash_spent` 仍为 `null`（记 unknown，**不得写 0**）、`status`/`known_activity` 未变、`maintainer`/rules 未变。
- 对照 `w01-facts.json:45-53`：M1/M1b 各 2/2 不变；体验额度 `2026-11-20 23:59:59 +08` 未被续期或改写；平台用量仍 unknown；本轮新增现金 0。
- 重放/对照的回执中 `model_requests=0`、`new_fits=0`、本地工具调用与证据读取计数为 0 或与原回执一致（`integration.md:70-72`、`g5-local/native-results-independent.json:44-69`）；出现任何新付费、新购买、新持久化运行时、新额度消耗即判**阻塞**。
- 报告必须保留「历史现金 unknown」字样，禁止因重放成功把 unknown 改写成 0。

### B4. 什么证据证明「本地入口调用」，而**不能**证明「已接入 AgentArts 平台」

**能证明本地入口调用**（W03 应交付的上限）：CLI 回执（`scripts/run_research_project.py` 的 `status`/`selection-context`/`advance-recipe` 退出码与输出）；`research-recipe-decision-v1` 的 `decision.json` 与六字段 `proposal.json`；`controller_requests[].request` 中命令身份 `controller.advance_recipe`；四文件报告包及清单哈希；`state_version` 迁移链（如 v3→v7→v11→v12）；同 ID 重放无用量为证（`integration.md:24-44, 68-82`）。

**不能推出平台接入**：上述全部证据都发生在本地工作区/本地控制器。缺少下列任意一项即**不得**写成「已接入 AgentArts 平台」：
- AgentArts 原生 `project_id` / `run_id` / 平台侧 `request_id` 与工作台/画布可点回的原产物（`g5-local/native-results-independent.json:30-35` 是原生证据的样子）；
- 平台侧 action/result 哈希、平台用量回执、平台快照 ref；
- D1 解除的 Owner 决定（`CURRENT_STATE.md:31`、`continuous-status.md:35` 明确仍暂缓）。

规则依据：`AGENTS.md:13`（local runner 不是 AgentArts 集成）、`AGENTS.md:20`、`CURRENT_STATE.md:20`、`PRODUCT_CHARTER.md §3C`、`continuous-plan.md:35`（同一冻结输入单独运行与经 ICT 调用口径一致 ≠ 平台闭环）。W03 的正确措辞是「本地正常入口调用回执 + 同输入对照框架」，**平台接入保持 unknown/暂缓**。

---

## C. W01 现场与预算逐项独审结论

结论级别：`通过` / `差异` / `阻塞` / `needs_review`。「差异」= 与实测不符或字段范围误导；「阻塞」= 计划中已登记、本轮不得自行解除；「needs_review」= 事实方向正确但证据或措辞不足，需主控澄清。所有引用均为 `continuous-status.md`（下称 S）与 `w01-facts.json`（下称 F）的行/字段。

| # | 审核项 | 结论 | 具体字段与实测 |
| --- | --- | --- | --- |
| C1 | HEAD / 分支 / ahead / 远端基线 | **通过** | S:12-14、F:`head`/`branch`/`ahead_of_origin_main`/`origin_main`。实测 `git rev-parse HEAD` = `3049e74946e9993dbd4eb31d186eeab010ade27b`（一致）；`origin/main` = `1b0f065b76944f998e56a12bec466e1f75c8adcc`（F 记 `1b0f065` 为缩写，一致）；`git rev-list --left-right --count origin/main...HEAD` = `0 2`，即 ahead 2（一致）；分支 `main`（一致）。 |
| C2 | 5 个未提交改动的归属与保护 | **通过（归属/保护）；needs_review（字段范围）** | S:15、F:`uncommitted[10-16]`。5 个文件与实测完全对应：`M current.md`、`M workbuddy/README.md`、`M workbuddy/execution-plan.md`、`?? continuous-handoff.md`、`?? continuous-plan.md`；归属 `user (23:47-23:49)` / `protect` 与 S:15「他人在途改动，保护不动、不 reset/clean/覆盖」一致。但字段名为 `uncommitted`，语义像「全部未提交改动」；实测共有 **6** 个（上述 5 个 + 主控独占的 `?? continuous-status.md`，S:6 自称 owner）。**建议**改名 `protected_user_in_flight` 并另列 `lead_owned_new_files`，否则后续读者会把 status.md 误判为无主外来改动。 |
| C3 | 活跃写者 / lease / 锁 | **通过** | S:16、F:`active_lease:null`、`git_lock_files:[]`。实测无 `.git/*.lock`；`runs/a7-project-software-20261102/writer.lock` 与 `runs/a7-project-steel-20261102/writer.lock` 确为 11-02 历史产物，未被当成本轮 lease。 |
| C4 | 运行时版本 | **差异（needs_review）** | S:17 写「官方 `freeze.py --check` 须用 `.venv`，**托管 3.13.12 缺 numpy**」。实测 `.venv/Scripts/python.exe` = **3.12.14**（与 S:17、F:`runtimes.venv_python` 一致），node v22.22.2（一致）；但系统 `python --version` = **3.13.14**，import numpy 失败。「缺 numpy」的结论成立，**版本号 3.13.12 写错**；且 F:`runtimes` 根本没记录托管 Python 字段，该断言无原始证据字段支撑。建议改成「托管 Python 3.13.14（实测），缺 numpy」或补 F 字段。 |
| C5 | 旧运行可见性 | **通过（文字层面）** | S:18 列 8 个目录、F:`frozen_evidence_dirs_visible` 列 12 个（多出 `m0-crosscheck-20261119`、`m1-preflight-20261119`、`m1-reanalysis-20261119`、`m1b-preflight-check-20261119`）。实测 12 个目录全部存在，S 的 8 个是其子集，「均在」成立。仅粒度不同，不算错误。 |
| C6 | 上游资料可见性 | **通过** | S:19、F:`upstream_material_visible`。实测 `docs/execution/g0/upstream/` 下 6 个文件（architecture-notes.md、reuse-matrix.md、license-security-audit.md、upstream-manifest.json、smoke-test-results.md、static-checks.json）全部存在。注意：该目录**不含 M4/Nixtla 上游**，与 A1 的缺口一致。 |
| C7 | 正常调用入口线索 | **通过（线索级）** | S:20、F:`normal_entry_candidates`。与 `integration.md:20-44` 一致（CLI 三子命令、只编译入口、`ProjectController.advance_recipe`、四文件包 + 同 request ID 恢复）。S:20 明写「W03 待实查『已接线』还是『文档声明』」，没有把文档当回执，措辞正确。 |
| C8 | worktree | **通过** | S:21 `.agent/worktrees/research-evidence/`（10-30 历史）；本轮不切换。未发现本轮切换证据。 |
| C9 | 共享 5 CNY 上限 | **通过** | S:27、F:`budget.cumulative_additional_cash_limit_cny:5`、`.agent/team-budget.json:5`。一致；`continuous-plan.md:75` 亦为 5，且明确「共享、累计、不因换目录/对齐/换执行者重开」。 |
| C10 | `confirmed_cash_spent` 记 unknown | **通过** | S:27、F:`budget.confirmed_cash_spent:null` + `interpretation:"unknown, not zero"`、`.agent/team-budget.json:6-8`（`null`/`remaining:null`/`reconcile_before_next_paid_call`）、`CURRENT_STATE.md:62`。**没有**被写成 0，符合要求。 |
| C11 | M1/M1b 各 2/2 已用尽 | **通过** | S:28、F:`budget.m1_actions`/`m1b_actions` = `2/2 exhausted`、`CURRENT_STATE.md:17,36-37`。一致；未出现重置或重开措辞。 |
| C12 | 体验额度到期时间 | **通过** | S:29 `2026-11-20 23:59:59 +08`、`.agent/team-budget.json:79,106` 同值。一致（A100/A107 两条记录）。 |
| C13 | 平台用量 unknown / 本轮新增现金 0 | **通过** | S:29-30、F:`budget.platform_usage:"unknown"`、`new_cash_this_round:0`。一致。 |
| C14 | D1 平台接入暂缓、未由 Owner 决定 | **通过（阻塞，登记无误）** | S:35、F:`blockers[0]`、`CURRENT_STATE.md:31` D1 待 Owner、`AGENTS.md:20` integration remains deferred。措辞「未由 Owner 决定」「W03 只做入口核查，不做平台操作」正确。本评审不解除。 |
| C15 | M1b 签名 `needs_review` | **通过（阻塞，登记无误）** | S:36、F:`blockers[1]`、`CURRENT_STATE.md:50`（「feng（口头授权，代理记录），仅本人可清」）。一致；S 没有越权清理。 |
| C16 | 报名状态 unknown | **通过（阻塞，登记无误）** | S:37、F:`blockers[2]`、`CURRENT_STATE.md:52`。一致（截止 2026-11-30）。 |
| C17 | W05 需新授权 | **通过（阻塞，登记无误）** | S:38、F:`blockers[3]`、`CURRENT_STATE.md:51`（无 M2 预注册卡，必须新卡）。一致。 |
| C18 | 「首个可运行任务 W02」 | **通过（队列顺序）；needs_review（「可运行」措辞）** | S:23 与 `continuous-plan.md:61-62` 一致（W01 完成即 W02）。但「可运行」若被理解为「可立即跑出评分」则过强：实测仓库无 M4Evaluation 源码、`.venv` 无 nixtla/datasetsforecast 依赖（见 `w01-spotcheck.json`）。按 `continuous-plan.md:62`，W02 本轮的可运行部分应是「固定版本/输入/口径 + 列缺项」，若依赖未齐转 W04 登记阻塞。建议在 S:23 补这句限定。 |
| C19 | 队列与角色分工对齐计划 | **通过** | S:40-50 对照 `continuous-plan.md:59-66`：W01→W05/W06 七项、承担者与交付物一致；S:54-61 对照 `continuous-plan.md:17-22`：主控 + upstream/integration/review 三角色一致；独审角色明确标注「未参与实现」（S:61），与计划第 22 行要求一致。 |
| C20 | 写者纪律足以防并发覆盖 | **通过（设计层）；needs_review（执行保障层）** | S:6、S:63-65 与 `continuous-plan.md:26,28,72` 一致：一文件一 owner、成员不写共享状态主段、后到者不写、无 lease 时保持单写者。但本轮 `active_lease:null`、无锁，纪律是**约定而非机制**。建议主控在每次集成前对 5 个保护文件 + `continuous-status.md` 做一次哈希比对，留下「未覆盖」回执；否则「足以防止」只能算设计意图，未获执行证明。 |
| C21 | `CURRENT_STATE.md` 与 W01 现场的时效 | **needs_review（未标记的状态陈旧）** | `CURRENT_STATE.md:3` 仍写「基线 `1b0f065`，工作树干净」，实测 HEAD 已到 `3049e74`、有 6 个未提交改动。该文件本轮受保护不改，但 S 未提示「CURRENT_STATE 落后一轮」。建议主控在下一次对齐摘要里标注它仅作 D1/边界口径依据，不作当前 HEAD/工作树事实。 |

**C 汇总**：新增差异/需澄清 **3** 处（C4 托管 Python 版本号、C2 `uncommitted` 字段范围、C21 CURRENT_STATE 陈旧未标注），全部为 `needs_review`/措辞级，**没有**发现 HEAD、ahead、5 文件归属与保护、预算四项口径（5 CNY/null unknown/2-2 用尽/到期时间/平台用量/新增现金 0）的实质性写错。另有 2 处措辞限定需要补（C18「可运行」、C20 执行保障）。4 项既有阻塞（C14–C17）经核登记无误，本评审不解除。

---

## D. W05 新课题卡的预审口径要求（产物未出，先固定门槛）

依据 `next-card-mdes-20261119.md` 与 `continuous-plan.md:65`。一张合格审批卡必须在**任何排名/结果产生之前**冻结下列字段；缺任一项判 `needs_review`，不得进入执行：

1. **独立数据**：语料来源与版本、是否沿用 CFR 固定卷、题目来源与数量（按 MDES 表 2/表 3 取数并写明依据）、数据身份/哈希、许可与归属；不得与 M1/M1b 的 24 题 validation 混用为「新证据」。
2. **同预算强基线**：两臂定义（建议换范式：词法 vs 稠密，或单路 vs 两阶段重排，而非 BM25 vs TF-IDF 同族微调，`next-card-mdes-20261119.md:79-81`）；强固定流程对照臂必须保留，不得为制造收益删掉（`integration.md:88`）；tokenizer/top_k/tie-break 常量冻结。
3. **评价口径**：单一主终点 + 至多两个次要终点；主终点必须预先声明单侧方向或写明双侧；量纲、计算式、聚合方式、显著水平写死。**已知陷阱**：现有五指标全部 `p>0.05`，但 **`p>0.05` 不是等价证据**（`next-card-mdes-20261119.md:53-56`）；要断言等价必须走 TOST（等价界 ±0.05 时 mrr@10 需 336 题，见同文件表），不能拿「不显著」当「等价」。
4. **反馈分支**：继续 / 改道 / 补证据 / 等待 / 停止各自的触发条件（`PRODUCT_CHARTER.md §2,§3B`）；反馈必须来自真实回执，不得由配置选中或来源抽取成功充当科学批准（`integration.md:52,86`）。
5. **停止条件**：预先写明等价界、无差界与「介于两者之间判不确定且不再加题」（`next-card-mdes-20261119.md:82-84`）；停止规则写在排序之前并冻结在包内。**不得事后挑终点**（同文件 `:92-93`）。
6. **原请求身份**：新卡必须有独立 `id`/版本与资金来源；原 M1/M1b 的 request ID、pin、失败记录不重开、不重置；执行需新授权（`continuous-status.md:38`、`CURRENT_STATE.md:51`）。卡内声明预算：行动数、**模型调用数 0**、fit 数、现金 0（本轮边界）。
7. **功效现实性（必附数字）**：`|Δmrr@10|` 的 MDES@24 ≥ **0.2105**，实测 +0.0232 只是门槛的 1/9；`recall@20` 的 24 题里 23 题两臂完全相同，**有效样本量只有 1**（`next-card-mdes-20261119.md:11,24,30-31`）。卡里若沿用 24 题设计，必须显式承认尺子不够细；主终点改 mrr@10 时要按表 2 取数（Δ=0.10 需 107 题）。正态近似对有界粗颗粒指标偏乐观，真实题量应更大（`:89-90`）。
8. **键契约**：`id` 唯一到副本或显式带 `partition`；G10 四条约束做成**构建期断言**；禁止再用 `(id, kept_as)`（`next-card-mdes-20261119.md:104-105`）。
9. **判据冻结与复算路径**：所有判据写于任何排名之前；附 `scripts/plan_mdes.py --json` 的复算命令与产物路径；SD 来自同一批题目的 pilot planning，换语料需重估（`:88`）。

预审结论：当前**尚无** W05 卡产物（S:49 标「待主控准备」），以上为门槛清单而非对某张卡的通过判定。卡到位后我按 1–9 逐项核，未产出内容不预判为通过。

---

## E. 本轮边界与下一项可做的独审任务

- 本轮已写：A/B 办法、C 逐项结论、D 门槛清单；产物：本报告 + 复算草案 + W01 实测证据。未调用模型、未执行研究行动、未改冻结包、未外发、未 push。
- 下一项可做的独审（不需等新授权、零现金）：**待主控把上游 Agent 的 W02 产物（I1–I5 原件、三指标全精度输出）转来后，按 A1–A4 做实质性独立复算**，用 `m4_recompute.py --self-test` 先确认算术实现，再对固定输入算出三项绝对差并给 `通过 / needs_review / 无法复算` 判定；若产物只到「公开断言」层级，则按 A5 判为「待核的上游断言」，不预断通过。其次可做 W03 回执的 B1–B4 核对（同输入哈希、原请求字段、预算前后哈希、本地≠平台措辞）。
