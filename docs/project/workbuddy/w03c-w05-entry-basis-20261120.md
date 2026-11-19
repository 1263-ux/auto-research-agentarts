# W03c · W05 审批卡「可执行依据」只读核查（2026-11-20）

- **成员**：产品接入 Agent `integration`，向主控 WorkBuddy 汇报。W03c 为本启动日最后一轮零现金项。
- **性质**：本文是给主控写 W05 卡的**依据**，**不是卡本身**；不替主控起草审批卡，不替 Owner 做任何决定。所有结论只写查到的，查不到写 unknown + 缺口。
- **硬边界遵守**：零新增现金；未调用模型、未执行研究、未创建项目、未推进任何状态/额度、未操作 AgentArts 中国站、未改 `src/`/`scripts/`、未 git push、未外发、未安装依赖。保护 5 个他人在途改动文件与主控独占的 `continuous-status.md`、`integration-receipts.md`（均未触碰）。
- 工具说明：本轮 Bash stdout 显示层异常，故用「命令重定向到文件 + Read」与 Grep/Read 取回；回执在 `runs/continuous-20261120/integration/w03c/`。

## D 段门槛来源

独立评审 `docs/project/workbuddy/review-method-20261120.md:167-181` 列 W05 卡 9 项必备字段（独立数据 / 同预算强基线 / 评价口径 / 反馈分支 / 停止条件 / 原请求身份 / 功效现实性 / 键契约 / 判据冻结与复算路径），依据 `next-card-mdes-20261119.md` 与 `continuous-plan.md:65`。下文逐项回答「有没有现成实现可复用，还是缺口」，末尾给对照表。

---

## 1. 强固定流程 / 同预算对照 —— 有现成实现 + 历史证据（但本轮不可执行）

- **真实路径与入口**：`scripts/compare_project_policies.py`（文件头：`Run one frozen three-domain fixed/adaptive comparison; never retry failed runs`）；调用入口 `compare_project_policies.py --cases <JSON> --output <新目录>`（`docs/policy-comparison.md:33-35`）。
- **同预算/同输入/同工具的代码依据**（源码逐行核实）：
  - `compare_project_policies.py:25-27` 三域 `ORDER` 固定方法；`248-249` 两臂用同一 `frozen_source`、`budget_ref="A10:<id>:existing-history-not-reset"`、`max_tool_calls=1`。
  - `250-271` fixed 臂走 `project.step`/`project.read_evidence`，adaptive 臂走 `controller.advance`；两臂共用同一冻结来源包，`260-261` 校验除 task_ref 外 manifest 哈希一致。
  - `285-288` 统一预算门校验：行动总数 ≤2、`new_model_requests==new_fits==0`、`local_tool_call_limit==1`、`evidence_read_limit==8`；`303-308` 比较两臂 `normalized_outcome` 并算 counter delta。
  - `245/247` 冻结 `code_identities` 与 `source_sha256`，变更即 `CODE_CHANGED`/`EVIDENCE_CHANGED` 拒绝。
- **历史回执**：`docs/policy-comparison.md:12-31` 记录三域两臂实跑（每臂 1 主方法 + 1 来源读取，模型/拟合/联网为 0），原始证据 `runs/a10-policy-comparison-20261102/`、`runs/a10-policy-inputs-20261102/`（本机 ignored）。
- **可复用性判断**：**设计可直接复用**（同输入/同工具/同预算的强固定对照臂协议已实现且有历史结果）；但 `docs/policy-comparison.md:39` 明确「**这条命令会执行真实工具，并非只读 status**」，本轮 W05 只能引用其协议与历史，**不得执行**。
- **B1 可达性**：该文件第20行 `from autoresearch.project_controller import ProjectController`，B1 下 Windows 导入即失败 → **当前不可运行**（POSIX 环境可）。

## 2. 预算门 —— 部分有代码字段把关，部分是协调记录/历史事实（需区分）

- **代码内预算字段**：`src/autoresearch/research_project.py:508-512`，`ResearchProject.create` 固化项目 `budget`：
  - `historical_spend_cny: None`、`historical_request_counts: None`、`historical_unknowns_resolved: False`、`cash_settlement: "unknown"`、`existing_cash_cap_cny: 5`（对应 D 段「5 CNY 共享累计、unknown 不记 0」中的 5 元上限与 unknown 口径）；
  - `model_requests_allowed: 0`、`new_model_requests: 0`、`new_fits: 0`（模型调用数 0）；
  - `local_tool_call_limit: max_tool_calls`、`evidence_read_limit: 8`。
  - 这些是**新项目创建时的声明/归属字段**，不是跨项目累计现金的执法者：`budget_ref` 只保存历史预算归属引用，不导入旧请求计数（见 `docs/project-slice.md:167`，`historical_spend_cny`/`historical_request_counts` 保持 null、`cash_settlement=unknown`）。
- **5 CNY / confirmed_cash_spent=null→unknown 的真实关卡**：`.agent/team-budget.json`（`cumulative_additional_cash_limit: 5`、`confirmed_cash_spent: null`、`status: reconcile_before_next_paid_call`）——但该文件自述 `purpose: "Team coordination record; not an automatic spending guard or provider bill"`，是**协调记录，不是代码自动门**；`confirmed_cash_spent=null→unknown` 是团队口径（见 `continuous-status.md:27`），由人工对账执行。
- **M1/M1b 各 2/2 用尽**：这是**历史研究事实**（`continuous-status.md:28`、`m1-primary-20261119.md`、`m1b-primary-20261119.md`），**代码里没有「M1/M1b 2/2」字段或自动锁**；保护靠「不重开」的团队纪律与旧请求/账本本身。属于**缺口/人工约束**，不能说成代码门。
- **执行期工具额度门**：`ProjectController._selection_context` 用 `local_tool_calls_used+reserved >= limit` 过滤候选（`project_controller.py:82,209-218`），`_advance` 有 `STALE_STATE` 版本门（`1261-1262`）与 `BUDGET_EXHAUSTED` blocker；这是**工具行动额度门**，与现金门分开。
- **可复用性判断**：新课题的 `budget` 字段结构可直接复用（`ResearchProject.create` 自动写入）；但「M1/M1b 2/2、5 CNY 共享、confirmed=null→unknown」的**跨卡累计约束无代码自动执法**，卡上须人工写死并交主控/独审核。

## 3. 原请求身份与恢复 —— 有现成实现（源码依据充分），B1 下 CLI 不可达

- **实现模块/函数**（W03 前半已定位，本轮复核）：
  - `src/autoresearch/project_controller.py`：`_parent`（:323-325）、`_response`（:328-333）、`_advance`（:1214-1294）、`advance_recipe`（:1202-1212）——同 request ID 命中旧父记录、比对 `request_sha256`/配方指纹、冻结 `selection_context`、`replayed=true` 返回原结果。
  - `src/autoresearch/research_project.py:1298 def resume(self, *, request_id)`——项目级重放；`status`（:529）只读回读。
  - `scripts/run_research_project.py:142-143 status / :181-192 selection-context/advance-recipe`——CLI 分发。
  - 四文件报告包 `src/autoresearch/project_report.py:1580-1594`（report.json/md/pdf/input.json + manifest），`recipe_selections` 在 `:410,458`。
- **B1 下可达性**：CLI 主入口 `run_research_project.py` 经 `project_controller→saved_study_reference→bounded_study_ledger:9` 导入即失败（`cli-help.txt`/`status-a14.txt`，W03 回执）→ **当前 Windows 不可达**；`export_project_report.py` 同 Fail（`export-help.txt`）。恢复机制在源码层存在，但**本轮无法实测重放**。POSIX 环境下可达。
- **可复用性判断**：恢复协议（同 ID + 原 state_version + 原输入哈希）可直接写进卡字段；但「恢复后状态与用量不变」的**实测回执**需 B1 解除或 POSIX 环境才能取得，当前为 unknown。

## 4. 评价口径 —— 脚本齐全 + 双指标预注册有实现，可复用（需按 D 段陷阱约束）

- **可复用脚本（均实测存在，`eval-basis.txt`）**：
  - `scripts/plan_mdes.py`（`--json`）——MDES/题量复算；产物 `runs/mdes-20261119/plan.json` 存在（3755 bytes）。本轮实测 `.venv/Scripts/python.exe -B scripts/plan_mdes.py --help` **RC=0**（`plan-mdes-help.txt`），**B1 下可达**。
  - `scripts/crosscheck_m0_packet.py`、`scripts/m1_preflight.py`、`scripts/m1b_preflight.py`、`scripts/audit_packet_keys.py`——M0 原件交叉核对（历史 23/23）、M1/M1b 预检、键契约审计（历史 7 项）。
- **双指标预注册 / 冻结判据实现**：`src/autoresearch/hypothesis_feedback.py`：`:53` 要求 `exactly two preregistered metric conditions`；`:299-335` joint=`all` 配对差判据；`:455-496` 双指标联合条件校验；`:418` 容差注释（仅核对独立四舍五入后的聚合一致性）。这是 staged 事前联合条件（S059）的现成实现。
- **D 段口径陷阱的文档依据**（`next-card-mdes-20261119.md`）：`:28` MDES 公式 `2.8016·SD/√24`（α=.05 双侧、power=.80）；`:40` mrr@10 Δ=0.10 需 107 题；`:50` 等价界 ±.05 需 336 题（TOST）；`:55` `p>0.05 不是等价证据`；`:82-84` 停止条件写死（等价界/无差界/中间判不确定不加题）；`:104-105` 键契约禁 `(id,kept_as)`、G10 四条构建期断言。
- **可复用性判断**：**可直接复用**——评价脚本与双指标预注册代码存在且 B1 下（`plan_mdes.py` 等纯标准库脚本）可跑；容差沿用 1e-3 是 M4 的口径（本卡是多指标检索终点，须按 D 段写死各自量纲/方向/显著水平，**不能把 M4 的 1e-3 直接套到 MRR/recall**）。注意 `hypothesis_feedback.py` 不触 fcntl（其自述为 staged 事前判据），但 W05 若走完整流程仍受 B1。

## 5. B1 对 W05 的实际影响（落到具体卡字段）

- **若 Owner 选「维持阻塞」（③）**：W05 卡中依赖 CLI/控制器/报告导出的字段只能写 **`待环境恢复（B1_FCNTL）`**：
  - D2「同预算强基线」的**执行**（`compare_project_policies.py` 需 ProjectController）→ 待环境恢复；协议设计可先写。
  - D6「原请求身份」的**恢复实测回执**（`resume`/advance 重放）→ 待环境恢复；ID 与 state_version 协议可先写。
  - D4「反馈分支」的**真实回执来源**（来自 advance/advance_recipe 的实际 outcome）→ 待环境恢复。
  - D5「停止条件」的**复算验证**（若需跑控制器链）→ 待环境恢复；规则文本可先写。
  - D1/D3/D7/D8/D9 中**纯文档或纯标准库脚本部分**（数据身份声明、评价口径定义、MDES 数字、键契约、plan_mdes 复算命令）不依赖 B1，可正常写/跑。
  - 卡状态应标 `needs_review` 或 `blocked`（缺实测回执），不得因「源码已接线」判通过。
- **若 Owner 选「POSIX 环境」（①）**：以下入口**可立即用于 W05 只读预演**（仍零现金、不执行研究）：
  - `run_research_project.py status/selection-context`（读现有项目状态/候选，不写）；
  - `compile_research_recipe.py --recipe ... --context ... --output <新目录>`（只读编译预览，已实测 RC=0）；
  - `plan_mdes.py --json`、`crosscheck_m0_packet.py`、`m1_preflight.py`、`m1b_preflight.py`、`audit_packet_keys.py`（评价/键契约复算，纯标准库，Windows 本就可跑，POSIX 同样可跑）。
  - **不能**用 POSIX 环境直接执行 `compare_project_policies.py` 或 `advance-recipe` 来「预演」——它们会执行真实工具/推进状态/耗额度，超出 W05 准备阶段边界；仅可作卡内「执行路径」的引用，需另授权。

---

## W05 卡字段 → 现有实现 / 缺口 / 需授权（对照表，供主控写卡用；非卡本身）

| D段# | W05 卡字段 | 现有实现（文件/函数/脚本） | 状态 | 需 Owner 授权 / 缺口 |
|---|---|---|---|---|
| 1 | 独立数据 | 数据身份/哈希/清单可用 `audit_packet_keys.py`、`crosscheck_m0_packet.py`（纯标准库，B1 下可达）；MDES 题量表 `next-card-mdes-20261119.md` | 部分有实现 | 新语料来源/许可/题目数为**缺口**，须主控与 Owner 确定；不得与 M1/M1b 24 题 validation 混用 |
| 2 | 同预算强基线 | `scripts/compare_project_policies.py:25-27,248-249,285-288`（同输入/同预算 fixed/adaptive）；`docs/policy-comparison.md:12-31` + `runs/a10-policy-comparison-20261102/` 历史 | 有实现+历史，B1 下不可运行 | 执行需 POSIX 环境（方案①）或 B1 修复（方案②）；两臂定义/常量冻结需主控写；执行需新授权 |
| 3 | 评价口径 | `scripts/plan_mdes.py --json`（实测 RC=0）；`hypothesis_feedback.py:53,299-335,455-496` 双指标预注册；`next-card-mdes-20261119.md:28,55,82-84` 公式/陷阱 | 有实现，可复用 | 新卡须写死量纲/方向/显著水平；`p>0.05≠等价`、等价需 TOST；主终点题量按表取；不得套用 M4 的 1e-3 |
| 4 | 反馈分支 | `ProjectController.advance/advance_recipe` 的 outcome/blockers 是真实回执来源（源码存在，B1 下 CLI 不可达）；`PRODUCT_CHARTER.md §2,§3B` 触发条件 | 部分有实现 | 真实回执获取需 B1 解除 + 新授权；分支触发条件文本可由主控写 |
| 5 | 停止条件 | `next-card-mdes-20261119.md:82-84,102` 等价界/无差界/不确定不加题规则；`plan_mdes.py` 可复算 | 规则有依据，复算脚本可达 | 规则须排序前写死并冻结；不得事后挑终点；等价需 TOST 非 p 值 |
| 6 | 原请求身份 | `project_controller.py:323-333,1202-1294`、`research_project.py:1298 resume`、四文件包 `project_report.py:1580-1594`；同 ID+原 state_version+原输入哈希恢复 | 有实现（源码），B1 下不可实测 | 新卡需独立 id/版本/资金来源；旧 M1/M1b ID/pin/失败不重开；恢复实测回执需 B1 解除或 POSIX + 新授权 |
| 7 | 功效现实性（必附数字） | `runs/mdes-20261119/plan.json`（存在）；`next-card-mdes-20261119.md:11,24,30-31,40,50` MDES@24≥0.2105、+0.0232 仅 1/9、有效 n=1、107/336 题 | 有数字依据 | 沿用 24 题须显式承认尺子不够；换语料需重估 SD；正态近似偏乐观，真实题量更大 |
| 8 | 键契约 | `scripts/audit_packet_keys.py`（存在，B1 下可达）；G10 四条约束构建期断言（`next-card-mdes-20261119.md:104-105`） | 有实现脚本 | 新卡须写 `id` 唯一到副本或带 `partition`；禁 `(id,kept_as)`；断言须构建期执行 |
| 9 | 判据冻结与复算路径 | `scripts/plan_mdes.py --json` + `runs/mdes-20261119/plan.json`（实测可达）；`hypothesis_feedback.py` 冻结判据 | 有实现，可复用 | 复算命令与产物路径写进卡；判据写于任何排名之前；SD 随语料重估 |

**汇总**：9 项中 **6 项有现成实现/数字依据可直接复用**（#2 设计、#3、#5 规则、#7、#8、#9；其中 #2 执行受 B1 限），**1 项部分有实现**（#6 恢复源码存在但实测不可达），**2 项含实质缺口需主控/Owner 决定**（#1 新语料数据、#4 反馈真实回执来源；#4 也受 B1）。跨卡的「M1/M1b 2/2、5 CNY 共享、confirmed=null→unknown」**无代码自动门**，属人工约束（见 §2）。

**需 Owner 授权事项（仅列出，不决定）**：① B1 处置方案（①/②/③，W03b 已呈）；② W05 新真实课题执行授权（D 段 #6、`continuous-status.md:38`、`CURRENT_STATE.md:51`）；③ 若选方案②，源码改动与 bounded study 专项回归资源；④ 新语料来源/许可/题量（#1）。本轮均未执行、未决定。

## 证据路径

- 本文：`docs/project/workbuddy/w03c-w05-entry-basis-20261120.md`。
- 只读回执：`runs/continuous-20261120/integration/w03c/` 下 `dir-scan.txt`、`policy-evidence.txt`、`eval-basis.txt`、`b1-reachability.txt`、`plan-mdes-help.txt`。
- 引用（只读）：`review-method-20261120.md:167-181`、`next-card-mdes-20261119.md`、`policy-comparison.md`、`continuous-status.md`、`CURRENT_STATE.md`、`docs/project-slice.md:167`。

（未知项写 unknown；本轮未获取任何新课题实测数据，未替主控写卡，未替 Owner 决定。）
