# W04b · 只读配方卡、W02 补依赖决策清单、OR-Tools 源码身份固定

- 任务号：W04b · 执行人：`upstream`（上游工作流 Agent）· 日期：2026-11-20
- 报告 owner：upstream（只写本文件；共享状态/计划由主控集成）
- 边界：零新增现金；**只写卡，不安装、不下载、不实跑、不重建索引、不调用模型、不改源码/冻结包、不外发、不 push**。
- 重要声明：**以下所有配方卡均为「上游公布成绩/入口」的只读固定，本卡未实跑，实测值 unknown。任何数值都是上游公布基线，不是本项目复算。**

---

## 第一部分：只读可重跑配方卡（4 张）

### 卡 1 · Matbench `matbench_steels`（AMMExpress v2020）

- **原入口**：`https://github.com/materialsproject/matbench` 的 `benchmarks/matbench_v0.1_automatminer_expressv2020/`（原始 notebook + 数据下载）；结果页 `https://github.com/materialsproject/matbench/blob/main/docs_src/Full%20Benchmark%20Data/matbench_v0.1_automatminer_expressv2020.md`
- **固定版本/提交**：`automatminer==1.0.3.20200727`、`matbench==0.1.0`（页面逐字 `{'python': ['automatminer==1.0.3.20200727','matbench==0.1.0']}`）；仓库具体 commit/tag **unknown**（本轮未固定）
- **数据与许可**：`matbench_steels` 回归数据集（组件钢材屈服强度）；样本数与五折划分规则在该结果页未给 → **unknown**；许可 **unknown**（未读仓库 LICENSE，不猜）
- **典型输入**：`group='matbench_steels'`，五折 `fold_0..fold_4`；配置 `express/default`，`learner_name=TPOTAdaptor,population_size=200,max_time_mins=1440`（逐字）
- **原产物（上游公布，非本项目）**：五折 MAE mean `97.4929`（fold 80.4188–115.4851）、RMSE mean `154.0161`、mape* mean `0.0696`、max_error mean `708.0205`；逐 fold 值见 W04 报告
- **失败条件**：旧版依赖不可装/与 Python 3.12.14 不兼容；五折数据哈希无法固定；配置 `max_time_mins=1440` 极重
- **反馈分支**：先固定折数据哈希与样本数 → 评估旧 venv 可行性；可先以「只读基线卡」入库，不实跑
- **ICT 改造点**：把固定折 + 固定配置封装为可重算评测原语；`max_time_mins` 作为 ICT 预算旋钮，比较「同折同输入、改预算」的反馈
- **可重跑最小例（草案，未执行）**：
  ```
  # 前置（需授权）：按 v0.1 约束建旧 venv 装 automatminer/matbench
  # 入口：matbench 仓库 benchmarks/matbench_v0.1_automatminer_expressv2020 notebook
  # 预期产物形状：fold_0..fold_4 各一组 {mae, rmse, mape*, max_error} + 五折 mean/std
  ```
- **状态**：**本卡未实跑，实测值 unknown**。

### 卡 2 · Fairlearn `plot_credit_loan_decisions`（Credit Loan Decisions）

- **原入口**：`https://fairlearn.org/main/auto_examples/plot_credit_loan_decisions.html`；下载件 `plot_credit_loan_decisions.py` / `.ipynb` / `.zip`
- **固定版本/提交**：文档 `Fairlearn 0.16.0.dev0`（页面标题）；页面无安装命令、无依赖固定版本、无仓库 commit → 依赖版本/commit **unknown**；`rand_seed=1234`（逐字）
- **数据与许可**：UCI `default of credit card clients`（2005 台湾，30000×24），URL `http://archive.ics.uci.edu/ml/machine-learning-databases/00350/default%20of%20credit%20card%20clients.xls`；数据许可 **unknown**；原始白皮书数据不可得，示例注入半合成 `Interest = N(2*Y, scale=A)`（逐字）
- **典型输入**：`Y=default`、`A=SEX`、`X`=去敏感列 one-hot；`train_test_split(test_size=0.35, stratify=Y)`；`Y/A/X` 定义逐字见 W04 报告
- **原产物（上游公布，非本项目）**：未缓解 overall `balanced_accuracy 0.801682 / FPR 0.207656 / FNR 0.188980`；ThresholdOptimizer difference `0.019392/0.002971/0.035814`、overall `0.761550/0.270270/0.206629`；ExponentiatedGradient 分组 female `0.763±0.013/0.227±0.012/0.248±0.023`、male `0.847±0.013/0.145±0.012/0.161±0.023`；ROC AUC `0.8782`
- **失败条件**：缺 lightgbm/pandas/fairlearn（本机全无）；UCI xls URL 不可达；半合成特征依赖未固定随机状态 → 不可复现
- **反馈分支**：冻结数据哈希与 `rand_seed` → 本地单跑复核 overall 三指标；再比较两种缓解算法干预前后差异
- **ICT 改造点**：把 `MetricFrame` 分组指标封装为确定性评测原语；保留「干预前后对照」作为反馈分支证据
- **可重跑最小例（草案，未执行）**：
  ```
  # 前置（需授权）：pip install fairlearn lightgbm pandas；下载 UCI xls
  python plot_credit_loan_decisions.py
  # 预期产物形状：MetricFrame overall/by_group/difference 指标表 + 权衡图；运行时约 52s、181MB（页面元数据）
  ```
- **状态**：**本卡未实跑，实测值 unknown**。

### 卡 3 · NumPy ASV 版本对照（Airspeed Velocity）

- **原入口**：`https://numpy.org/devdocs/benchmarking.html`；仓库根 `spin bench`，`cd benchmarks && asv ...`
- **固定版本/提交**：文档 `NumPy v2.6.dev0`；`pip install asv`、`pip install virtualenv`（逐字）；具体 asv 版本与对照 commit/tag 由使用者固定 → **unknown**（页面示例 `v1.6.2`、`20d03bcfd`、`main`）
- **数据与许可**：无外部数据集，基准在 `benchmarks/`；环境由 asv 自建 virtualenv；许可 **unknown**（页面未声明）
- **典型输入**：正则 `$REGEXP="bench.*Ufunc"`；对照目标 `--compare v1.6.2` 或 commit/`main`；`--python=same` 用当前解释器
- **原产物（上游公布，非本项目）**：`spin bench` 控制台逐次计时分布；`asv run -n -e --python=same` → `asv publish` → `asv preview` 生成可跨版本比较的 HTML；页面**未给具体退化数值** → **unknown**
- **失败条件**：需 numpy 源码树与 benchmark 目录；构建耗时；无 asv；重复计时分布需多跑
- **反馈分支**：固定基准与 commit → 单基准 `--python=same --quick` 冒烟 → 全量 `--compare` 得退化项 → 回写下一轮
- **ICT 改造点**：把「固定基准 + 固定 commit + 固定环境」封装为可复算计时卡；`--compare` 的退化项作为反馈信号
- **可重跑最小例（草案，未执行）**：
  ```bash
  pip install asv virtualenv
  cd benchmarks/
  export REGEXP="bench.*Ufunc"
  asv run --dry-run --show-stderr --python=same --quick -b $REGEXP
  spin bench --compare v1.6.2 -t bench_core
  # 预期产物形状：控制台计时分布 + (asv publish 后) HTML 结果页
  ```
- **状态**：**本卡未实跑，实测值 unknown**。

### 卡 4 · BEIR SciFact `evaluate_bm25.py`（固定提交 ef83d293…）

- **原入口**：`https://github.com/beir-cellar/beir/blob/ef83d29307061c65d04b035b4f4e7c18bd8374af/examples/retrieval/evaluation/lexical/evaluate_bm25.py`；运行 `python evaluate_bm25.py`
- **固定版本/提交**：commit `ef83d29307061c65d04b035b4f4e7c18bd8374af`（已核，g0/官方一致）；BEIR v2.2.0（g0）；脚本 SHA 见 g0 manifest `303165f...`（evaluate_bm25.py）
- **数据与许可**：SciFact zip `https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip`（~5K docs / 300 test queries，g0）；代码 Apache-2.0（g0），数据许可独立且 **unknown**（g0 README 警告代码许可≠数据许可）
- **典型输入**：`GenericDataLoader(data_path).load(split="test")`；BM25 参数 `hostname/index_name` 占位符需替换、`number_of_shards=1`、`initialize=True/False`
- **原产物（上游公布，非本项目）**：`retriever.evaluate` 返回 `(ndcg, map, recall, precision)`；具体 SciFact NDCG@10 数值 **unknown**（本脚本与 g0 均未逐字给出，不猜）
- **失败条件**：Elasticsearch 未运行/连接失败；`initialize=True` 会删旧索引并重建（**不得对共享/生产索引运行**）；pytrec_eval 依赖缺失；数据 URL 不可达
- **反馈分支**：获授权后在独立索引用 `initialize=False` 跑 → 核 NDCG@10 并落盘逐题 `results`；或走 g0 建议的本地确定性评分 fixture 绕开 ES
- **ICT 改造点**：`retrieve` 后把 `results` 序列化落盘（原脚本只在内存用），冻结 qrels/query 哈希；BM25 索引作为可复用外部状态，避免每次重建
- **可重跑最小例（草案，未执行）**：
  ```bash
  # 前置（需授权）：本地 ES 运行 + pip install beir；在可写副本改 hostname=localhost、index_name=<独立索引>、initialize=False
  python evaluate_bm25.py
  # 预期产物形状：(ndcg, map, recall, precision) 四组指标 + results{qid:{docid:score}}（需 ICT 改造落盘）
  ```
- **状态**：**本卡未实跑，实测值 unknown**。本轮未重建索引、未运行。

---

## 第二部分：W02 最小补依赖决策清单（供 Owner 一次决策）

完整结构化版见 `runs/continuous-20261120/upstream/w04b/w02-dependency-decision.json`。要点如下，逐项标状态。

### 要安装的包

| 包 | 精确版本 | 状态 | 说明 |
| --- | --- | --- | --- |
| `datasetsforecast` | **1.1.0** | **已核**（PyPI 只读查询） | 官方示例页未标注版本；与示例 API 兼容性**待核** |
| `pandas` | unknown | **待核** | datasetsforecast 依赖；本机 MISSING；精确版本需读 1.1.0 元数据 |
| `numpy` | 2.5.4 | **已核**（本机） | 本机已装；与 1.1.0 兼容性待核 |
| `scipy` | 1.18.1 | **已核**（本机） | 本机已装 |
| 传递依赖（utilsforecast/mlforecast 等） | unknown | **unknown** | 由 pip 解析决定，未装未读，不猜 |

### 要下载的数据

| 项 | 来源 URL | 体量 | 许可 | 状态 |
| --- | --- | --- | --- | --- |
| M4 Hourly 原始数据 | `https://raw.githubusercontent.com/Mcompetitions/M4-methods/master/Dataset/`（`M4.load` 缓存 `data/.cache/*.parquet`） | unknown（Hourly n_ts=414/horizon=48 已核，字节数未下载） | unknown | URL **已核**；体量/许可 **unknown** |
| ESRNN 118 提交 `submission-118.zip` | `https://github.com/Nixtla/m4-forecasts/raw/master/forecasts/submission-118.zip` | unknown | unknown | URL **已核**；体量/许可 **unknown** |

### 评分器与本机改动

- 评分器模块：`datasetsforecast.m4.M4Evaluation.evaluate(directory, group, y_hat)` → `pd.DataFrame[OWA, SMAPE, MASE]`（**已核**，官方页）。
- 会改动本机路径：`.venv/Lib/site-packages/`（安装包）；`data/.cache/*.parquet`（数据缓存，directory 可配置）。不碰 `src/`、`scripts/`、冻结包、全局环境。

### 为何零现金仍需单独授权

1. 环境变更：pip install 写入 `.venv`，改变依赖树，可能影响共享/冻结环境兼容性；
2. 新增外部数据：下载数据集与提交 zip，引入外部内容，需确认来源与固定哈希；
3. 许可待核：M4 数据条款未在官方页声明，代码许可≠数据许可；
4. 超出本轮「只读核验」边界：安装+下载+执行属真实环境操作。

### 授权后第一条可跑命令

```bash
cd "D:/XiangMuLuoDi/Development/ICT/track2/auto-research" && .venv/Scripts/python.exe -m pip install "datasetsforecast==1.1.0"
```

### 容差口径（只记录，不自行定判据）

- 官方断言 `np.isclose(metric, ref, atol=1e-3)`；numpy 默认 `rtol=1e-5`（官方未显式写）。
- 有效判据 `|a-b| <= atol + rtol*|b|`（绝对 1e-3 + 相对 1e-5×参考值）；对 9.328/0.893/0.440 阈值约 `0.001093 / 0.001009 / 0.001004`。
- **处理方式**：只记录口径；由主控/独审决定「按 `np.isclose` 原样」还是「收紧为纯 atol」。本 Agent 不自行定判据。

---

## 第三部分：OR-Tools 官方源码身份固定

上一轮官方页抓取失败、两个 raw 路径 404；本轮通过 GitHub REST API 固定到确定 commit + blob（**固定成功**）：

- 仓库/分支：`google/or-tools` @ `stable`，HEAD commit `100f66e6242ab8bf8d32feb8f3bf086db66ae2b5`（date `2026-09-17T13:02:24Z`）
- 文件：`ortools/sat/samples/minimal_jobshop_sat.py`
- **git blob SHA（内容哈希）**：`a79406febd49176474364c5697f41eee1d91e849`；字节数 `5483`；许可 Apache-2.0
- 可回溯 URL：`https://github.com/google/or-tools/blob/100f66e6242ab8bf8d32feb8f3bf086db66ae2b5/ortools/sat/samples/minimal_jobshop_sat.py`；raw 与 API 地址见证据文件
- 关键约束/目标片段已核对（每机器 NoOverlap、job 内先后、makespan `add_max_equality`+`minimize`、status 判定），见证据文件
- 官方发布的具体排程/makespan 数值：**unknown**（官方页失败且稳定版源码 docstring 无输出样例，不猜）
- 可重跑最小例草案（未实跑）：`pip install ortools`（需授权）→ `python ortools/sat/samples/minimal_jobshop_sat.py` → 预期 `status` / 每机器排程行 / `Optimal Schedule Length` / Statistics
- 失败记录：本轮 `curl` 直下 raw 遇 `schannel` TLS 握手失败（exit 35，仅 1 次，未重试）→ 本地 SHA256 **unknown**；blob SHA 已由 API 权威取得，身份可回溯不受影响

---

## 4. 证据路径

- `runs/continuous-20261120/upstream/w04b/ortools-identity.md`、`curl.log`
- `runs/continuous-20261120/upstream/w04b/w02-dependency-decision.json`
- 数值来源沿用 `docs/project/workbuddy/w04-upstream-candidates-20261120.md` 与各 WebFetch 原文（来源/次数登记在 `runs/continuous-20261120/upstream/w04/preflight-and-sources.md`）

## 5. 失败与未解记录

- 4 张卡均未实跑、实测值 unknown；上游数值仅作基线，未冒充本项目复算。
- curl raw 下载失败（schannel TLS，exit 35），未反复重试；本地 SHA256 unknown，但 OR-Tools 身份已用 blob SHA 固定。
- 各许可、commit/tag（除 OR-Tools）、样本数、SciFact NDCG@10、下载体量等未验证量写 unknown，无猜测。
- 未安装依赖、未下载数据集、未实跑、未重建索引、未调用模型、未改源码/冻结包、未碰在途文件与 continuous-status.md。
- 下一可做项：配方卡已具备「可重跑最小例 + 未实跑标记」，可入 P2 配方库；任一卡的实跑均需 Owner 单独授权（依赖/数据/许可）；W02 待一次性授权后按补依赖清单执行。
