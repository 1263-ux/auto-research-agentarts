# W04c · 配方库补卡（6 张，与 W04b 4 张合计 10 张）

- 任务号：W04c · 执行人：`upstream`（上游工作流 Agent）· 日期：2026-11-20
- 报告 owner：upstream（只写本文件；共享状态/计划由主控集成）
- 边界：零新增现金；**不安装、不下载数据集、不实跑评分/重建索引、不调用模型、不执行新真实研究行动、不改源码/冻结包、不外发、不 push**。
- 全局声明：**本文件全部 6 张卡均为只读固定；每张「本卡未实跑，实测值 unknown」「本项目调用记录：无（待授权）」。所有数值仅为上游公布/文档示例，不是本项目复算。不得为凑「调用记录」编造或实跑。**
- 字段沿用 W04b：原入口 / 固定版本或提交 / 数据与许可 / 典型输入 / 原产物 / 失败条件 / 反馈分支 / ICT 改造点 / 可重跑最小例（命令/输入/预期产物形状）。

---

### 卡 5 · OR-Tools Job Shop（`minimal_jobshop_sat.py`）

- **原入口**：官方源码 `google/or-tools` `ortools/sat/samples/minimal_jobshop_sat.py`（官方开发者页 `developers.google.com/optimization/scheduling/job_shop` 本轮抓取失败）；运行 `python ...minimal_jobshop_sat.py`
- **固定版本/提交**（已锚定，可回溯）：commit `100f66e6242ab8bf8d32feb8f3bf086db66ae2b5`（`stable` 分支 HEAD，date `2026-09-17T13:02:24Z`）；文件 git blob SHA（内容哈希）`a79406febd49176474364c5697f41eee1d91e849`；size `5483`
  - 可回溯 URL：`https://github.com/google/or-tools/blob/100f66e6242ab8bf8d32feb8f3bf086db66ae2b5/ortools/sat/samples/minimal_jobshop_sat.py`
  - 证据：`runs/continuous-20261120/upstream/w04b/ortools-identity.md`
- **数据与许可**：许可 Apache-2.0（源码 header 逐字）；无外部数据集（数据内嵌于源码 `jobs_data`）
- **典型输入**：3 job `[(0,3),(1,2),(2,2)] / [(0,2),(2,1),(1,4)] / [(1,4),(2,3)]`（task=(machine,duration)）；horizon 为时长总和
- **原产物**：`status`（OPTIMAL/FEASIBLE 或 `No solution found.`）；每机器排程行 `Machine k: job_i_task_j [start,end]`；`Optimal Schedule Length: <makespan>`；Statistics（conflicts/branches/wall time）
- **失败条件**：`ortools` 缺失/版本 API 差异（`new_int_var` vs `NewIntVar`）；官方页具体排程数值 unknown（源码 docstring 无输出样例），无法逐字对照；纯 CPU
- **反馈分支**：获授权装 ortools 后固定 3-job 数据跑 → 记录 status/makespan/排程 → 与官方页数值（另行取得）核对；可作为「通用调用入口最小验证」（P1 中 BEIR 阻塞时的替代）
- **ICT 改造点**：把 CP-SAT 求解封装为确定性工程计算原语（固定数据+固定约束+固定目标+固定求解参数）；status 与 makespan 作为反馈信号；排程作为原产物留存
- **可重跑最小例（草案，未执行）**：
  ```bash
  # 前置（需授权）：pip install ortools
  python ortools/sat/samples/minimal_jobshop_sat.py
  # 输入：源码内嵌 jobs_data；预期产物形状：status + 每机器排程行 + Optimal Schedule Length + Statistics
  ```
- **状态**：**本卡未实跑，实测值 unknown**。**本项目调用记录：无（待授权）**。

### 卡 6 · OpenML-CC18 基准套件

- **原入口**：`https://docs.openml.org/benchmark/`；Python `openml.study.get_suite('OpenML-CC18')` + `openml.runs.run_model_on_task(clf, task)`；REST `https://www.openml.org/api/v1/xml/study/OpenML-CC18`
- **固定版本/提交**：suite alias `OpenML-CC18` / study `study_99` / `https://www.openml.org/s/99`（已核，页面原文）；openml 包版本与仓库 commit **unknown**（本轮未固定）；任务数页面未声明（`size=73` 是列表参数，非任务数）→ **unknown**
- **数据与许可**：数据集经 task 封装；数据许可页面未声明 → **unknown**；发布/上传结果需 OpenML API key（外发/平台变更）
- **典型输入**：task 集合（封装数据集 + 预置 train-test splits + target feature）；评价 `sklearn.metrics.accuracy_score`；10-fold / stratified CV 口径由 task 固定；示例分类器 `DecisionTreeClassifier`（注：示例用旧 `sklearn.preprocessing.Imputer`）
- **原产物**：run 对象（predictions + scores）；结果 API `api/v1/xml/run/list/study/OpenML-CC18`；`openml/benchmark-suites` notebook 做结果分析；独立 baseline 页无 → 具体基线数值 **unknown**
- **失败条件**：无 API key 不能 `run.publish()`；数据许可 unknown；全量任务需联网下载；`Imputer` 旧 API 与 sklearn 1.9.1 不兼容
- **反馈分支**：固定 task id 列表与 split 哈希 → 本地（不 publish）单任务对照 → 如需发布单独授权；以失败的数据条件做对照
- **ICT 改造点**：把「task 固定 split + 本地评测」封装为数据评测原语；与 W03 正常入口等价性对照；`run.publish()` 外发动作单列授权
- **可重跑最小例（草案，未执行）**：
  ```bash
  # 前置（需授权）：pip install openml；本地不设 apikey、不 publish
  python - <<'PY'
  import openml, sklearn
  suite = openml.study.get_suite('OpenML-CC18')
  task = openml.tasks.get_task(suite.tasks[0])
  # run_model_on_task(clf, task) -> score（预期产物形状：accuracy 标量 + run 对象）
  PY
  ```
- **状态**：**本卡未实跑，实测值 unknown**。**本项目调用记录：无（待授权）**。

### 卡 7 · GPT Researcher Deep Agents（本地资料示例）

- **原入口**：`https://github.com/assafelovic/gpt-researcher` `main` 分支 `deep_agents/README.md`；`pip install -r requirements.txt -r deep_agents/requirements.txt` → `python deep_agents/main.py`
- **固定版本/提交**：仓库 main 分支（本轮命中；master 分支 README 404）；要求 Python 3.12+；**release 号与 commit 未固定 → unknown**
- **数据与许可**：许可页面未声明 → **unknown**；`task.json` 配置；`source` 支持 `web|local|hybrid`，本地资料经 `DOC_PATH`；强依赖 `OPENAI_API_KEY` + `TAVILY_API_KEY` + 联网
- **典型输入**：`task.json`（query/model=`provider:model`/max_sections/source/follow_guidelines/guidelines/verbose）；示例 `model="openai:gpt-5.4"`
- **原产物**：`deep_agents/outputs/run_/report.md` + `sections/*.md`（内联引用 + 去重参考文献）
- **原基线（上游公布，非本项目）**：DeepResearch Bench 10 任务 RACE overall `0.503`(raw)→`0.512`(GPTR)；verified citations/report `18.6`→`35.2(+89%)`；零可验证引用 `2/10`→`0/10`
- **失败条件**：无付费 API key/额度（硬边界禁止调用）；联网；成本不可控；LLM 输出需人工核查
- **反馈分支**：与「引用/未解问题回写下一工作流」契合；若获授权用 `source=local` + 已批预算跑最小例，核 report.md 引用可追溯性；未授权则仅保留只读卡
- **ICT 改造点**：把「报告主张→来源引用→未解问题」结构化回写为下一工作流输入；`source=local` 便于零外发资料研究
- **可重跑最小例（草案，未执行）**：
  ```bash
  # 前置（需授权，本轮不做）：OPENAI_API_KEY/TAVILY_API_KEY + pip install（付费 API + 联网）
  python deep_agents/main.py
  # 输入：task.json；预期产物形状：outputs/run_/report.md + sections/*.md（带引用）
  ```
- **状态**：**本卡未实跑，实测值 unknown**。**本项目调用记录：无（待授权；需付费 API key）**。

### 卡 8 · data-to-paper `social_network`

- **原入口**：`https://github.com/Technion-Kishony-lab/data-to-paper`；`pip install data-to-paper` → `data-to-paper social_network`
- **固定版本/提交**：PyPI `data-to-paper`（本轮未固定版本号 → **unknown**）；关联论文 arXiv:2404.17605 / NEJM AI DOI `10.1056/AIoa2400555`（逐字）
- **数据与许可**：许可 MIT（README badge）；输入为 Twitter 117th Congress 成员交互有向图（Fink et al.，PMC10493874）；示例手稿在 `rkishony/data-to-paper-supplementary`（受控补充仓）；数据许可 **unknown**
- **典型输入**：`data-to-paper social_network`（open goal）；无额外参数（页面逐字）
- **原产物**：data-chained 手稿（数值可点击回溯到生成代码行）；data-to-paper 会加 AI 创建 watermark（不得移除）
- **原基线**：无数值基线；示例产物为 Supplementary Data-chained Manuscript B
- **失败条件**：需外部 LLM API（README 明确 token 成本警示，硬边界禁止调用）；LLM 生成代码本地执行风险（免责声明）；需 human-in-the-loop；数据半合成/补充仓可用性
- **反馈分支**：若获授权，最小跑 social_network 并验证「主张→代码行」回溯链与 watermark 保留；否则仅只读卡
- **ICT 改造点**：与「报告主张关联回计算和原数据」高度契合；把 data-chaining 机制作为本项目「主张→原产物」可追溯性的候选底座
- **可重跑最小例（草案，未执行）**：
  ```bash
  # 前置（需授权，本轮不做）：pip install data-to-paper + LLM API key（付费）
  data-to-paper social_network
  # 输入：内置 social_network 数据；预期产物形状：data-chained 手稿（主张→代码行）+ watermark
  ```
- **状态**：**本卡未实跑，实测值 unknown**。**本项目调用记录：无（待授权；需 LLM API token）**。

### 卡 9 · Agent Laboratory（YAML 研究例）

- **原入口**：`https://github.com/SamuelSchmidgall/AgentLaboratory`（g0 已固定源码）；关联论文 `https://aclanthology.org/2025.findings-emnlp.320/`（本轮未抓取）；YAML 研究例的逐字入口本轮未核 → **unknown**
- **固定版本/提交**（g0 manifest）：commit `d9017d90e329112d2a80b7712f37ee9094d2cd27`；许可 MIT；g0 已读源码、AST 解析通过，runtime `not_installed_not_executed`
- **数据与许可**：数据/模型依赖模型 API（凭证）；具体数据许可 **unknown**
- **典型输入**：YAML 研究例配置（阶段：文献→实验→报告）；具体字段本轮未核 → **unknown**
- **原产物**：阶段产物（文献/实验/报告）与 native ledger；g0 未逐字核具体产物形态 → **unknown**
- **原基线**：无（g0 `inspiration_only`，未复现）
- **失败条件**（g0）：`tools.py:298` subprocess exec、`tools.py:123` 数据集远程代码、`ai_lab_repo.py:113` pickle 状态无可靠恢复、启动删除旧研究目录；需模型凭证
- **反馈分支**：若启用，先核 YAML 例的输入/阶段产物与恢复机制；禁止对共享资产运行或加载不可信 pickle；runtime smoke 仍是 deferred/blocked
- **ICT 改造点**：阶段上下文与 copilot 复核思路可借鉴；但需以 JSON resume 替代 pickle、保留失败产物；不得直接吸收 exec/远程代码行为
- **可重跑最小例（草案，未执行且未完整定义）**：
  ```bash
  # 前置（需授权，本轮不做）：模型 API 凭证 + pip install；先核 YAML 例入口（当前 unknown）
  # 预期产物形状：文献/实验/报告阶段产物 + ledger（具体形态待核）
  ```
- **状态**：**本卡未实跑，实测值 unknown**。**本项目调用记录：无（待授权；runtime smoke 未做）。** 本卡为 g0 已有调研复用，非本轮新核。

### 卡 10 · M4 Hourly 官方评分示例（**严格 L0 层**）

> **层级声明**：本卡只包含 **L0 官方断言层**（上游公布值）。**L1 本项目复算层 = unknown（未实跑）**。禁止把 L0 数值写成 L1 结果。

- **原入口**：`https://nixtlaverse.nixtla.io/datasetsforecast/m4.html`；评分器 `datasetsforecast.m4.M4Evaluation.evaluate(directory, group, y_hat)`
- **固定版本/提交**：包 `datasetsforecast`（PyPI 最新 `1.1.0`，只读查询；**官方示例页未标注版本 → unknown**）；Python 3.12.14（本机）
- **数据与许可**：M4 Hourly 数据 `source_url='https://raw.githubusercontent.com/Mcompetitions/M4-methods/master/Dataset/'`（`M4.load` 缓存 `data/.cache/*.parquet`）；ESRNN 118 提交 `https://github.com/Nixtla/m4-forecasts/raw/master/forecasts/submission-118.zip`；数据许可 **unknown**（代码许可≠数据许可）
- **典型输入**：`group='Hourly'`（n_ts=414, horizon=48, seasonality=24）；`y_hat` 为提交 zip URL 或 `(n_series, horizon)` ndarray
- **原产物**：`pd.DataFrame`（列 OWA/SMAPE/MASE，group 索引）+ 三个 `np.isclose` 断言
- **L0 上游公布值（非本项目）**：**sMAPE 9.328 / MASE 0.893 / OWA 0.440**，`atol=1e-3`（numpy 默认另含 `rtol=1e-5`，判据组合只记录、不自行定，见 W04b 容差口径）
- **L1 本项目复算**：**unknown（未实跑）**；缺项与补依赖见指针
- **失败条件/阻塞**：本机 datasetsforecast/pandas 缺失、M4 数据与提交 zip 无副本、无离线 wheel；补齐需安装+下载+许可，超只读边界 → 阻塞
- **反馈分支**：获 Owner 一次性授权后按补依赖清单执行复算 → 通过转 W03 ICT 入口等价性；断言不符先排查版本/API/数据再判负
- **ICT 改造点**：把固定评分器封装为确定性评测原语（冻结 y_hat + 冻结输入哈希，避免每次联网），供 W03 做同输入两口径一致性对照
- **可重跑最小例（草案，未执行）**：
  ```python
  # 前置（需授权）：见下方指针；本轮未安装/未下载/未执行
  from datasetsforecast.m4 import M4Evaluation
  esrnn_evaluation = M4Evaluation.evaluate('data', 'Hourly',
      'https://github.com/Nixtla/m4-forecasts/raw/master/forecasts/submission-118.zip')
  # 预期产物形状：DataFrame[OWA, SMAPE, MASE]；L1 实测值当前 unknown
  ```
- **补依赖清单指针**：`docs/project/workbuddy/w02-m4-upstream-20261120.md`（§3–4 缺项/判定、§6 配方卡）、`runs/continuous-20261120/upstream/w02/rerun-plan.md`（命令草案）、`runs/continuous-20261120/upstream/w04b/w02-dependency-decision.json`（结构化补依赖决策）
- **状态**：**本卡未实跑，L1 实测值 unknown（L0 为上游公布值）**。**本项目调用记录：无（待授权）**。

---

## 本轮自检

- 补卡 6 张（卡 5–10），与 W04b 卡 1–4 合计 **10 张**。
- 每张均带可重跑最小例（卡 9 因 YAML 入口未核，草案注明「未完整定义」）、显式「本卡未实跑，实测值 unknown」「本项目调用记录：无（待授权）」。
- M4 卡严格停在 L0；L1 unknown；未把任何上游基线写成项目复算。
- 全程未安装/下载/实跑/调模型/改源码/碰禁止文件。
