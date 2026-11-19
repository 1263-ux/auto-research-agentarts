# W04 · BEIR、OR-Tools 及其他上游候选核对报告

- 任务号：W04 · 执行人：`upstream`（上游工作流 Agent）· 日期：2026-11-20
- 报告 owner：upstream（只写本文件；共享状态/计划由主控集成）
- 一句话结论：**核对 9 个候选**（BEIR、OR-Tools、NumPy ASV、Fairlearn、Matbench、GPT Researcher、data-to-paper、OpenML-CC18、Agent Laboratory）。其中 8 项本轮新核官方来源（OR-Tools 官方页抓取失败改用镜像源码、GPT Researcher 换 main 分支命中），1 项（Agent Laboratory）复用 g0 已有调研。本机运行依赖全部缺失，9 项均**未实跑**；可重跑最小例与阻塞已逐项登记。

## 0. 通用边界与口径

- 零新增现金：未安装依赖、未下载数据集、未重建索引、未调用任何 LLM/API、未执行真实研究、未改平台状态、未发外发消息、未碰冻结包与在途文件。
- BEIR 索引红线：`evaluate_bm25.py` 默认 `initialize=True` 会**删除并重建索引**；本轮未运行、未重建。逐题结果需求已记录（见 BEIR 条）。
- 口径区分：下文所有「基线/公布值」均为**上游公布成绩**，非本项目复算；本项目复算一律「未执行」。
- 本机依赖探测（实际输出见证据 `preflight-and-sources.md`）：可用仅 scikit-learn 1.9.1 / numpy 2.5.4 / scipy 1.18.1；ortools、beir、datasets、elasticsearch、pytrec_eval、fairlearn、matbench、matminer、asv 全部 MISSING。→ 本轮无可实跑候选。

---

## 1. BEIR SciFact（本轮新核脚本 + 复用 g0 架构结论）

- **固定版本/提交**：`beir-cellar/beir` @ `ef83d29307061c65d04b035b4f4e7c18bd8374af`（g0 manifest 与官方固定链接一致）；BEIR v2.2.0（g0 architecture-notes）。
- **许可**：代码 Apache-2.0（g0 license-security-audit）；数据许可独立，README 明确警告代码许可≠数据许可，SciFact 数据许可 **unknown**，用前需确认。
- **原入口**：`examples/retrieval/evaluation/lexical/evaluate_bm25.py`；运行方式 `python evaluate_bm25.py`（dataset 在脚本内硬编码为 `scifact`）。
- **原基线**：官方公布 SciFact BM25 NDCG@10 数值——**unknown**（本脚本与 g0 文档均未逐字给出数值；勿猜）。可对照来源：BEIR README 结果与 `https://github.com/beir-cellar/beir` 结果表（待后续核）。
- **原始输入**：`https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip`（脚本内 `util.download_and_unzip`）；加载 `corpus.jsonl`/`queries.jsonl`/`qrels/test.tsv`；SciFact ~5K docs / 300 test queries（g0）。
- **产物**：`retriever.evaluate` 返回 `(ndcg, map, recall, precision)`；另有 `results`（qid→{docid:score}）即逐题结果，但**原脚本只在内存使用、未落盘**。
- **适配差异 / 风险**：
  - `initialize = True` → 删除旧索引并从零重建；`hostname="your-hostname"`、`index_name="your-index-name"` 为占位符，需替换为 localhost 与独立索引名。**本轮未运行、未重建索引**。
  - BM25 依赖本地 Elasticsearch（非纯内存），脚本顶部说明需本地安装 ES + `pip install beir`。
- **逐题结果需求（已记录，待办）**：为支持 Agent 诊断，需要在 `retriever.retrieve` 后把 `results` 序列化到文件（如 `results.json`），并把 `qrels`、query 文本一并冻结；原脚本不产出该件，属 ICT 改造点。
- **可重跑最小例（草案，未执行）**：
  ```bash
  # 前置：本地 Elasticsearch 运行 + pip install beir（需授权，本轮不做）
  # 在可写副本中把 hostname=localhost、index_name=<独立索引>、initialize=False（复用已建索引）
  python evaluate_bm25.py
  # ICT 改造：retrieve 后 json.dump(results) 落盘 + 冻结 qrels 哈希
  ```
- **失败条件**：ES 未运行/连接失败；索引名冲突或 `initialize=True` 误重建共享索引；数据 URL 不可达；pytrec_eval 依赖缺失；SciFact 许可未确认。
- **阻塞**：本机无 beir/elasticsearch/pytrec_eval；ES 服务缺失；数据许可 unknown；禁止重建索引；无授权安装。**状态：阻塞**。
- **下一验收**：获授权后，在明确允许的独立索引上以 `initialize=False` 跑，核对 NDCG@10 与官方表并落盘逐题结果；或走 g0 建议的确定性评分 fixture（纯本地 NDCG 计算）做 adapter 正确性验证，绕开 ES。

## 2. OR-Tools Job Shop（本轮新核；官方页失败，改用镜像源码）

- **固定版本/提交**：源码取 `google/or-tools` `stable` 分支 `ortools/sat/samples/minimal_jobshop_sat.py`（SDK v9.x+ 命名 `new_int_var`/`value`；Apache-2.0 头）。官方页面 `developers.google.com/optimization/scheduling/job_shop` 抓取失败（fetch failed，未反复重试）→ **官方页发布的具体排程数值 unknown**。
- **许可**：Apache-2.0（源码头明确）。
- **原入口**：`python ortools/sat/samples/minimal_jobshop_sat.py`（官方镜像源码；`from ortools.sat.python import cp_model`）。
- **原基线 / 原始输入**：数据固定为 3 job：`[(0,3),(1,2),(2,2)]`、`[(0,2),(2,1),(1,4)]`、`[(1,4),(2,3)]`（(machine, duration)）；机器按数据推导 3 台。官方 docstring 输出未出现在所取稳定版源码中 → 具体 makespan/排程 **unknown**（记为待核）。
- **产物**：`status`（`cp_model.OPTIMAL`/`FEASIBLE`，及 `No solution found.`）、`Optimal Schedule Length: <makespan>`、每机器排程行 `Machine k: job_i_task_j [start,end] ...`、统计（conflicts/branches/wall time）。
- **适配差异 / 固定约束与目标（源码逐字要点）**：
  - 约束：`model.add_no_overlap(machine_to_intervals[machine])`（每机器一次一任务）；job 内 `all_tasks[job_id,task_id+1].start >= all_tasks[job_id,task_id].end`（先后、不可重叠）。
  - 目标：`obj_var = model.new_int_var(0, horizon, "makespan")`；`model.add_max_equality(obj_var, [每个 job 最后 task 的 end])`；`model.minimize(obj_var)`。
  - 求解状态：`status = solver.solve(model)`，`if status == OPTIMAL or FEASIBLE` 打印排程，否则 `No solution found.`。
- **可重跑最小例（草案，未执行）**：`pip install ortools`（需授权）→ `python minimal_jobshop_sat.py` → 留存 status、makespan、排程逐字输出与源码哈希。
- **失败条件**：ortools 缺失/版本 API 差异（`new_int_var` vs `NewIntVar`）；官方页数值不可得导致无法对照；无 GPU 需求（纯 CPU）。
- **阻塞**：本机无 ortools；官方页数值 unknown；无授权安装。**状态：阻塞**。
- **下一验收**：获授权后装 ortools，在固定 3-job 数据上跑，记录 status/makespan/排程，并与官方页数值（另行取得）核对；作为「通用调用入口的最小验证」候选（P1 中 BEIR 阻塞时的替代）。

## 3. 其他候选（Matbench / OpenML-CC18 / GPT Researcher / data-to-paper / NumPy ASV / Fairlearn / Agent Laboratory）

### 3.1 Matbench（matbench_steels，本轮新核）
- **版本**：`automatminer==1.0.3.20200727`、`matbench==0.1.0`（`python: [...]` 逐字）；AMMExpress v2020。
- **许可**：unknown（本轮未读仓库 LICENSE）。**入口**：`matbench` 仓库 benchmark notebook；页面未给逐字 CLI 命令（unknown）。**基线（上游公布，非本项目）**：matbench_steels 五折 MAE mean `97.4929`（fold 80.4188–115.4851）、RMSE mean `154.0161`、mape* mean `0.0696`、max_error mean `708.0205`（逐 fold 值见证据/原文）。**输入**：matbench_steels 数据集，五折 `fold_0..fold_4`；样本数与固定折规则页面未给（unknown）。**产物**：五折 score stats。**适配差异**：旧版环境（`express, default`，TPOTAdaptor，population 200，max_time 1440 min）极重，旧依赖可行性存疑。**失败条件**：旧版依赖不可装/不兼容；折与样本定义不在该页。**阻塞**：本机无 matbench/matminer；旧环境重；无授权。**下一验收**：先固定折数据哈希与样本数（matbench 主仓），再评估旧 venv 可行性；可先用发布分数做「只读基线卡」入库。

### 3.2 OpenML-CC18（本轮新核）
- **版本/标识**：suite `OpenML-CC18` / study `study_99` / `https://www.openml.org/s/99`；任务数页面未声明（列表参数 `size=73` 不等于任务数，记 unknown）。**许可**：页面未声明（unknown）。**入口**：`openml.study.get_suite('OpenML-CC18')` + `openml.runs.run_model_on_task(clf, task)`（Python 示例逐字）；R `getOMLStudy`/`runTaskMlr`。**基线**：独立 baseline 页无；结果 API `api/v1/xml/run/list/study/OpenML-CC18` + `openml/benchmark-suites` notebook。**输入**：task 集合封装数据集+预置 train-test splits+target；10-fold/stratified CV 口径由 task 固定。**产物**：run 对象（预测+分数，如 `accuracy_score`）。**适配差异**：全量 72/73 任务需联网下载数据与 API；`run.publish()` 需 API key（外发/平台变更，本轮禁）。**失败条件**：无 API key 不能发布；数据许可 unknown；`sklearn.preprocessing.Imputer` 为旧 API。**阻塞**：本机无 openml 包；发布需 key 且禁平台变更。**下一验收**：固定 task id 列表与 split 哈希后，本地（不 publish）跑单任务对照；API key 与外发单独授权。

### 3.3 GPT Researcher（deep_agents 示例，本轮新核）
- **版本**：仓库 main 分支 README（未给 release 号，unknown）；要求 Python 3.12+。**许可**：README 未声明（unknown）。**入口**：`pip install -r requirements.txt -r deep_agents/requirements.txt` → `export OPENAI_API_KEY=...; export TAVILY_API_KEY=...` → `python deep_agents/main.py`（逐字）。**基线（上游公布）**：DeepResearch Bench 10 任务，RACE overall raw-search `0.503` vs GPTR `0.512`；verified citations/report `18.6` vs `35.2 (+89%)`（逐字）。**输入**：`task.json`（query/model/max_sections/source/follow_guidelines/guidelines/verbose）；`source` 支持 `web|local|hybrid`，本地文档经 `DOC_PATH`。**产物**：`deep_agents/outputs/run_/report.md` + `sections/*.md`（含内联引用与去重参考文献）。**适配差异**：与「引用/未解问题回写下一工作流」目标契合（本地/混合资料、报告带来源）；但**强依赖 OPENAI_API_KEY + TAVILY_API_KEY + 联网**，触发零新增现金/API 红线。**失败条件**：无 API key/额度；联网；成本不可控。**阻塞**：需付费 API key（硬边界禁止调用）。**下一验收**：仅做只读配方卡；若未来获授权，用本地 `source=local` + 已批预算跑最小例，核 report.md 引用可追溯性。

### 3.4 data-to-paper（social_network，本轮新核）
- **版本**：PyPI `data-to-paper`（未给固定号，unknown）；关联论文 arXiv:2404.17605 / NEJM AI DOI。**许可**：MIT（README badge）。**入口**：`pip install data-to-paper` → `data-to-paper social_network`（逐字）。**基线**：无数值基线；示例产物为 data-chained manuscript（Supplementary Manuscript B）。**输入**：Twitter 117th Congress 交互有向图（Fink et al.），来自 supplementary 仓库。**产物**：可点击回溯到生成代码行的「data-chained」论文手稿（主张→数值→代码行）。**适配差异**：与「报告主张关联回计算和原数据」高度契合（backward-traceable/data-chaining）；但由 LLM agents 驱动，**需外部模型 API，token 成本明确警示**。**失败条件**：LLM API 成本/不可用；LLM 生成代码在本地执行的风险（README 免责声明）；需 human-in-the-loop。**阻塞**：需付费 LLM API（硬边界禁止调用）。**下一验收**：只读配方卡；若获授权，最小跑 social_network 并验证「主张→代码行」回溯链与 watermark 保留。

### 3.5 NumPy ASV（本轮新核）
- **版本**：NumPy v2.6.dev0 文档；`pip install asv`、`pip install virtualenv`（逐字）。**许可**：unknown（页面未声明）。**入口**：仓库根 `spin bench`；`cd benchmarks && asv run --dry-run --show-stderr --python=same --quick -b $REGEXP`；`spin bench --compare v1.6.2 -t bench_core`；`asv run -n -e --python=same` + `asv publish` + `asv preview`（均逐字）。**基线**：版本对照 `spin bench --compare <commit|tag|branch>`；退化项由对照结果判定（页面未给具体数值）。**输入**：`benchmarks/` 下的 ASV 基准，固定环境由 asv 管理 virtualenv。**产物**：ASV 结果（可保存并生成 HTML，用于跨版本比较）。**适配差异**：重复计时通过多跑测分布、`--quick` 跳过重复；构建 NumPy 耗时。**失败条件**：构建慢；需 numpy 源码树与 asv。**阻塞**：本机无 asv、无 numpy 源码 benchmark 树；无授权安装/构建。**下一验收**：获授权后在固定 commit 跑 `--python=same` 单基准，记录重复计时分布与 `--compare` 退化项。

### 3.6 Fairlearn（credit loan decisions，本轮新核）
- **版本**：文档 Fairlearn `0.16.0.dev0`（页面标题）；页面无安装命令、无依赖固定版本。**许可**：unknown（本页未声明）。**入口**：Sphinx-Gallery 下载件 `plot_credit_loan_decisions.py`/`.ipynb`；运行元数据 `Total running time 0min52s`、`Estimated memory 181MB`（逐字）。**基线（上游公布，非本项目）**：未缓解 overall balanced_accuracy `0.801682` / FPR `0.207656` / FNR `0.188980`；ThresholdOptimizer difference `0.019392/0.002971/0.035814`、overall `0.761550/0.270270/0.206629`；ExponentiatedGradient 分组 female `0.763±0.013/0.227±0.012/0.248±0.023`、male `0.847±0.013/0.145±0.012/0.161±0.023`；ROC AUC `0.8782`（逐字）。**输入**：UCI `default of credit card clients`（2005 台湾，30000 行）× 半合成 `Interest`；`Y=default`、`A=SEX`、`X`=去敏感列后 one-hot；`test_size=0.35, stratify=Y`，seed 1234。**产物**：`MetricFrame` 分组/整体指标、权衡图、缓解前后对照。**适配差异**：需 lightgbm/pandas/matplotlib（本机无）；UCI xls URL 需联网；原白皮书数据不可得（用半合成替代）。**失败条件**：缺 lightgbm/pandas；UCI URL 不可达；数据半合成需注意可复现性。**阻塞**：本机无 fairlearn/lightgbm/pandas；无授权安装/下载。**下一验收**：获授权后冻结数据哈希与 seed，跑最小例复核 overall 三指标与分组差异（容差自定并登记）。

### 3.7 Agent Laboratory（YAML 研究例，复用 g0 调研，本轮未新核）

- **来源**：g0 `upstream-manifest.json`（commit `d9017d90e329112d2a80b7712f37ee9094d2cd27`）、`reuse-matrix.md`、`license-security-audit.md`、`smoke-test-results.md`；派发链接 `https://aclanthology.org/2025.findings-emnlp.320/`（本轮未抓取，记未新核）。
- **许可**：MIT（g0）。**入口/原基线/原始输入/产物**：YAML 研究例的逐字入口与阶段产物本轮**未核**（unknown）；g0 仅确认源码已读、AST 解析通过、runtime `not_installed_not_executed`。**适配差异/风险（g0）**：`tools.py:298` subprocess exec、`tools.py:123` 数据集远程代码、`ai_lab_repo.py:113` pickle 状态无可靠恢复、启动删除旧研究目录。**失败条件**：exec/pickle 风险；需模型凭证。**阻塞**：runtime smoke 未做且 deferred/blocked；需模型 API。**下一验收**：若启用，先核 YAML 例的输入/阶段产物与恢复机制，禁止对共享资产运行或加载不可信 pickle。

## 4. 候选汇总表（9 项）

| 候选 | 归属 | 版本/提交固定 | 许可 | 入口固定 | 上游基线 | 可重跑最小例 | 本机可跑 | 阻塞要点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BEIR SciFact | 新核+g0 | ef83d293 / v2.2.0 | Apache-2.0(数据unknown) | evaluate_bm25.py | NDCG@10 unknown | 有(需ES+独立索引) | 否 | 依赖/ES/索引红线/许可 |
| OR-Tools Job Shop | 新核 | stable 镜像源码 | Apache-2.0 | minimal_jobshop_sat.py | 排程数值 unknown | 有 | 否 | 官方页失败/无 ortools |
| NumPy ASV | 新核 | v2.6.dev0 文档 | unknown | spin bench/asv run | 对照退化(无数值) | 有 | 否 | 无 asv/源码树 |
| Fairlearn | 新核 | 0.16.0.dev0 | unknown | plot_credit_loan_decisions.py | 多组数值已录 | 有 | 否 | 无 fairlearn/lightgbm/pandas |
| Matbench | 新核 | automatminer 1.0.3.20200727 | unknown | notebook(命令unknown) | 五折 MAE 等已录 | 部分 | 否 | 旧环境重/无包 |
| OpenML-CC18 | 新核 | study_99 | unknown | openml study/run API | 结果API | 有 | 否 | 无 openml/发布需key |
| GPT Researcher | 新核 | main(号unknown) | unknown | python deep_agents/main.py | RACE 0.503→0.512 | 有 | 否 | 需 OPENAI/TAVILY key(红线) |
| data-to-paper | 新核 | PyPI(号unknown) | MIT | data-to-paper social_network | 无数值 | 有 | 否 | 需 LLM API(红线) |
| Agent Laboratory | g0已有 | d9017d90 | MIT | YAML例未核 | 未核 | 未核 | 否 | runtime 未做/需模型API |

## 5. 证据路径

- `runs/continuous-20261120/upstream/w04/preflight-and-sources.md`（本机依赖探测输出 + 来源抓取清单 + g0 复用说明）
- 各候选逐字数值与命令摘录见本报告对应条目（来源 URL 与次数在 preflight-and-sources.md 登记）

## 6. 失败与未解记录

- OR-Tools 官方开发者页首次抓取失败，未反复重试；两个猜测 raw 路径 404；经一次域内搜索定位官方镜像源码，具体排程数值仍 unknown。
- GPT Researcher master 分支 README 404，改 main 命中；未固定 release 号（unknown）。
- 所有未验证量（NDCG@10 具体值、OR-Tools makespan、各许可、任务数、CLI 命令等）写 unknown，未猜测。
- 未安装依赖、未下载数据、未重建索引、未调用 API、未改平台状态。
- 下一可做项：按 P1/P2 目标，优先把「已有可固定输入+数值」的配方先入库为只读配方卡（Matbench 五折、Fairlearn 指标、NumPy ASV 命令、BEIR 脚本入口），OR-Tools/BEIR 待授权后做本地最小实跑；W02 亦待安装+下载+许可授权后恢复。
