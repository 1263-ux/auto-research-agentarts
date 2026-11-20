# B1 的可达面：20 个入口在 Windows 上死于同一行 import

- 轮次：2026-11-20 第 11 轮（三小时对齐窗口内，零研究行动）
- 起点：`097f888`（第 10 轮 P2 门禁），工作树干净
- 涉及文件：新增 `scripts/portability_scan.py`、`runs/portability-20261120/{selftest,scan}.{txt,json}`
- 未改动：`src/` 一行未改（`git diff --stat` 为空）；未执行任何排名、未调用模型、未推送
- 结论层级：**冷上下文复核通过**，未经真人签字 → `needs_review`

## 1. 为什么这轮做这件事

前 10 轮反复出现同一句判断：「B1 阻塞，处置需 Owner 决定」。但此前只记录了三处现象（`run_research_project.py` 的 status / selection-context / advance-recipe 报 `No module named 'fcntl'`），没有回答两个更基本的问题：

1. 到底**多少**入口在 Windows 上是死的？只报三个可能严重低估。
2. 修掉 `import fcntl` 之后，这条链**是不是就能跑**？如果还有第二层阻塞，那么「修 import」就是一个假修复。

这两个问题都能用零成本方式回答，于是本轮只做测量，不改代码。

## 2. 实测：真实退出码与真实下一个阻塞

先纠正第 8 轮的一处记录缺陷。当时用 `python ... | tail -4; echo "RC=$?"` 取退出码，拿到的是 **`tail` 的退出码 0**，而不是 Python 的。重取：

```
status            RC=1
selection-context RC=1
advance-recipe    RC=1
ModuleNotFoundError: No module named 'fcntl'
```

三个子命令都是 `RC=1`。这条修正只影响记录准确性，不改变「B1 阻塞」的判断。

接着做一次**探针**（不是修复）：把只有一个 `flock`/`LOCK_*` 空实现的 `fcntl.py` 放到 `PYTHONPATH` 上，观察导入链能否走通：

```
PYTHONPATH=runs/_probe/fcntl_stub  python scripts/run_research_project.py status --workspace .
→ RC=2  {"ok": false, "code": "PROJECT_NOT_FOUND", "message": "Create the project first."}
```

结论：**`fcntl` 是这条链上唯一的导入期阻塞**。桩一旦就位，入口立刻输出结构化 JSON 错误，说明参数解析、控制器装配、错误码路径全都活着。这个探针本身**不是修复**——空实现等于关掉文件锁，在 POSIX 上会破坏互斥语义，所以桩只放在 `runs/_probe/`（已 gitignore），不进仓库、不被任何脚本引用。

## 3. 把「三个现象」变成「全量判定」

新增 `scripts/portability_scan.py`，纯标准库、静态 AST，不导入 `src.autoresearch`（因此不会触发锁、写盘或网络），在已经坏掉的平台上也能跑。

它区分两类，因为两者的修法完全不同：

| 形态 | 含义 | 修法 |
|---|---|---|
| **unguarded**：`import fcntl` 在模块体（列 0） | 模块根本无法被导入 | 守卫式导入 / 平台分支 |
| **lazy**：`import fcntl` 在函数体内 | 导入正常，执行到该函数才失败 | 需要真正的跨平台锁实现 |

把两者混为一谈，就会写出「补一个 try/except」却仍在调用时崩掉的补丁。

**真实仓库判定**（144 个入口脚本）：

```
unguarded (module cannot import): 1  fcntl
lazy (imports, fails on call)   : 1  fcntl
offending modules: 1  autoresearch.bounded_study_ledger

Entrypoints: 144 total, 20 dead on Windows, 16 lazy-only
EXIT 1 (DEAD ENTRYPOINTS PRESENT)
```

20 个判死的入口：`check_plan_fact`、`compare_project_policies`、`export_project_report`、`import_local_project`、`prepare_experience_pair`、`probe_codex_selection`、`read_saved_study_reference`、`run_bike_2011_study`、`run_boolq_case_comparison_study`、`run_concrete_reproduction`、`run_host_selection`、`run_hotpot_support_study`、`run_recipe_improvement`、`run_research_project`、`run_scheduling_policy_transfer`、`run_squad_paragraph_study`、`run_squad_train_conditional_study`、`serve_local_workbench`、`serve_project_workbench`、`verify_research_recipe`。

单点根因只有一个：`src/autoresearch/bounded_study_ledger.py:9` 的 `import fcntl`。它被 `saved_study_reference.py` → `project_controller.py` 这条链拖进几乎所有研究入口。

### 判定的实测校验

静态判定只有在被测量裁决后才有价值。逐项跑（`--help`，只测导入，不进入业务）：

| 类别 | 实测 | 结果 |
|---|---|---|
| 判死的 18 个（排除两个 `serve_*`） | 全部 `RC≠0` 且含 `No module named 'fcntl'` | **18/18 一致** |
| 判为 lazy-only 的 9 个抽样 | 全部 `RC=0`（导入正常） | **9/9 一致** |
| 第 2 节的前置探针 | 3 个子命令 | 一致 |

合计 **27 个测量点，0 冲突**。两个 `serve_*` 脚本**未测**：它们连 `--help` 都不返回（20 秒超时，进程被 SIGTERM），因此只保留静态判定，不计入「已验证」。

## 4. 决定性的冲突：修 B1 会破坏 G5 的证据

这是本轮最重要的发现，也是「B1 为什么不能随手改」的真正理由。

`scripts/run_scheduling_policy_transfer.py` 里：

```
SOURCE_ROOT = Path(__file__).resolve().parents[1]        # 活的工作树，不是快照
SOURCE_FILES = (..., 'src/autoresearch/bounded_study_ledger.py', ...)
_fingerprints() = {relative: _sha(_read(SOURCE_ROOT/relative)) for relative in SOURCE_FILES}
```

它把**活工作树**里 `bounded_study_ledger.py` 的哈希算进 `source_fingerprints`，并与固定协议（`protocol['source_files'] == list(SOURCE_FILES)`）和存档证据比对。于是：

- 要让 20 个入口在 Windows 上活 → 必须改 `bounded_study_ledger.py`
- 要让 G5 transfer 证据保持可验证 → 该文件必须逐字节不变

**两者互斥。** 任何字节改动（哪怕只加一个 `try/except`）都会让 `source_fingerprints` 变化，G5 存档证据立即与代码不一致。所以 B1 不是「改一行 import」的工程量问题，而是一个取舍：

1. 承认 G5 证据为**历史证据**（绑定 `62f09ed`），再打补丁；
2. 或保留文件不变，用仓库外的平台层解决锁（但这只能绕过，不能修好 `run_*` 系列）；
3. 或把锁抽成独立模块并重跑 G5（需 Linux 环境与 fcntl，本轮不具备）。

### 附带查清的一件事：这一枚钉不拦编辑

`saved_study_reference.py:30` 也钉了同名文件，值为 `1d39b54d…`，而盘上实际是 `32758129…`。初看像是「已被改动过」，但第 55 行显示它解析在 `_SOURCE` 上：

```
'**{'source:' + key: _SOURCE / key for key in _SOURCE_SHAS}
_SOURCE = Path('/workspace/work/scheduling-threshold-source-62f09ed')
```

即这枚钉绑的是**原始 Linux 快照**，不是活工作树；快照不在本机（`/workspace` 不存在，`runs/g5-scheduling-threshold-transfer-20261114-01` 也不存在）。所以：

- 它**不会**因为编辑活文件而报错（这点与直觉相反，值得记下）；
- 但它也说明 G5 的「原版复现」（L2）在本机**结构性不可达**——证据描述的是本仓库里没有的一份源码快照。这不是新阻塞，而是把 L2 仍记为 unknown 的又一条依据。

## 5. 我自己写错的三个地方（保留）

扫描器第一版给出的数是错的，三个缺陷都属于同一类：**把「可达」当成了「导入期可达」**。

1. **重复计数**：先 `ast.walk` 全树（把模块级 import 标成非顶层），再走 `tree.body`，于是同一个 import 同时进 `top` 和 `lazy`。表现是「lazy: 1 fcntl」来自一个其实属于 unguarded 的模块。
2. **假阴性（最严重）**：`from . import project_design, saved_study_reference` 这种形式中 `node.module` 为空、名字在 `node.names` 里；解析器只返回包本身，于是**漏掉了 `run_research_project.py` 这条已知必死的路径**——扫描器报告它健康，而实测 RC=1。若没做实测校验，这份报告会把一个最容易复现的阻塞判成不存在。
3. **假阳性**：闭包把惰性边也当成导入期边，于是 `compile_research_recipe.py`、`fetch_project_source.py` 被判死，而实测 `--help` 都是 `RC=0`。

修法：为每个模块同时保留 `edges`（全部）与 `eager`（仅模块体），导入期可达性只用 `eager`；`from . import a, b` 展开为同级模块。三条都有夹具断言（T5/T6/T7/T8）。

另有一处**计数陷阱**：修完后再数 `fcntl` 出现次数，从 24 变成 35。多出的 11 次全部来自新写的扫描器自己（`POSIX_ONLY` 列表、夹具、说明文字）。**新增一个「提到某词的文件」会改变这个词的计数**——旧记忆里「`grep | head` 截断会把 8 处写成 5 处」是同一类错误的另一面。报告中的计数一律注明范围。

## 6. 自检与可复现

`scripts/portability_scan.py --selftest` → **11/11 通过、退出码 0**。

夹具覆盖：模块体 POSIX 导入 → 判死（T1）；函数内导入 → 只算 lazy（T2）；顶层导入死模块 → 判死（T3）；惰性导入死模块 → 判活但报 lazy（T4/T4b）；`from . import sibling` 展开（T5/T9）；同一 import 不得既算顶层又算惰性（T6）；相对导入展开到两个同级模块、不存在的同级不得凭空生成（T7/T8）；两次扫描结果一致（T10）。

产物：`runs/portability-20261120/selftest.txt`、`scan.txt`、`scan.json`。`runs/` 被 gitignore，这些只在盘上。

## 7. 边界与预算

- 研究行动 0 / 模型调用 0 / fit 0 / 现金 0 / 推送 0 / 外发 0；平台用量 **unknown**
- `src/` 未改、冻结输入未动、`COMPARISON` 未动；探针桩隔离在 `runs/_probe/`
- W05 卡仍 `execution=not_authorized`、`R13 PENDING`；M1b 代理签字仍 `needs_review`；均未动
- 本报告与扫描器未经真人签字 → `needs_review`，只可写「冷上下文复核通过」

## 8. 下一任务

B1 已经不能再用「等 Owner 决定」糊过去，现在有一个**具体的、二选一的问题**可以问：

> 是否同意把 G5 scheduling-threshold-transfer 证据标记为「历史证据（绑定 `62f09ed`）」，从而允许修改 `src/autoresearch/bounded_study_ledger.py` 以解除 20 个入口在 Windows 上的死锁？

- 同意 → 下一轮做「守卫式导入 + Windows 锁抽象」，并显式更新 `run_scheduling_policy_transfer.py` 的期望指纹，同时把 G5 证据降级为历史；
- 不同意 → 20 个入口保持不可用，`run_research_project.py` 全线不可用，P2 所需的「本项目调用记录」只能走不依赖该链的路径（例如 `scripts/w05a_selftest.py` 这种独立模块级证据）。

另外两件零成本、无争议的事可以并行做：两个 `serve_*` 入口在 `--help` 下挂起（疑似忽略参数直接起服务）值得单独查一次；配方库 P2 的 R5（两张卡缺版本化）也仍是待办。
