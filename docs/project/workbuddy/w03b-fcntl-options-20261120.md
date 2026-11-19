# W03b · B1 三方案影响面、回归点与对照框架标注规则（2026-11-20）

- **成员**：产品接入 Agent `integration`，向主控 WorkBuddy 汇报。承接 W03 前半（B1 已由主控复核确认并登记为需 Owner 决定的阻塞）。
- **任务号**：W03b（派发：B1 三方案草案 / fcntl 回归点只读查询 / 对照框架断言层级标注规则）。
- **硬边界遵守**：零新增现金；未调用模型、未执行 `advance-recipe` 等推进状态/耗额度动作、未创建真实研究项目、未操作 AgentArts 中国站、未 git push、未外发、未安装依赖。**未修改任何源码或主控/他人文档**；补丁草案仅写在 `runs/continuous-20261120/integration/w03b/`。
- **推荐 ≠ 决定**：文末推荐为技术建议，B1 处置需 Owner 批准。

---

## 1. B1 根因复核（与主控 B1 一致）

- 根因：`src/autoresearch/bounded_study_ledger.py:9` 顶层无条件 `import fcntl`（POSIX 专属），Windows `.venv` 导入链 `run_research_project.py:15 → project_controller.py:8 → saved_study_reference.py:11 → bounded_study_ledger.py:9` 在 argparse 前即 `ModuleNotFoundError`，CLI 主入口 RC=1；只编译入口不触该链，RC=0。
- fcntl 引用实测（Grep）：**3 文件共 12 处**，主控所说「5 处」应指 `bounded_study_ledger.py` 单文件（9、139、143、234、245）。另 `c01_memory_loop.py`（65/78）、`research_project.py`（408/419）均为**函数内延迟导入且已有 `os.name=='nt' → msvcrt` 兜底**，Windows 不走 fcntl——唯独 `bounded_study_ledger.py` 顶层裸导入、无兜底，这是它能阻塞 CLI 启动的原因。

## 2. 三方案影响面与最小补丁草案（摘要）

完整 diff 草案文本见 `runs/continuous-20261120/integration/w03b/patch-drafts.md`。三方案均有具体行号与 diff 草案：

| 方案 | 改动文件/行号 | diff 草案 | 锁语义变化 | 影响其它模块 | 回退 | 触在途改动 |
|---|---|---|---|---|---|---|
| ① POSIX 环境（WSL/Linux）运行 | 无源码改动 | 仅调用命令从 `.venv/Scripts/python.exe` 换为该环境 `python` | 无（沿用 fcntl 原语义） | 无 | 弃用该环境即可 | 否 |
| ② 兼容 shim（msvcrt/条件导入） | 仅 `bounded_study_ledger.py:9/131/139/143/234/245` | 有（顶层条件导入 + `_lock_exclusive`/`_lock_release` 帮助函数 + `getattr(os,"O_NOFOLLOW",0)` + `os.O_BINARY` + 扩 `except`） | **有**：`flock`（建议锁/整文件/fd）↔ `msvcrt.locking`（字节范围/句柄）不等价；异常类型 `BlockingIOError`→`OSError`；`O_NOFOLLOW` 防护弱化 | 间接解除 `saved_study_reference.py:11`、`project_controller.py:8`、`run_research_project.py:15`、`export_project_report.py` 的导入阻塞 | `git checkout` 该文件（当前无在途改动，安全）；旧项目 `CODE_CHANGED` 需显式 upgrade | 否（但改全项目 code identity） |
| ③ 维持阻塞，挂到授权后 | 无 | 无 | 无 | 无 | 随时改选①/② | 否 |

方案②额外风险：`win-os-capability.txt` 实测 Windows `hasattr(os,'O_NOFOLLOW')=False`、`msvcrt.locking/LK_NBLCK=True`，故 shim 除 fcntl 外必须处理第131行 `os.O_NOFOLLOW`（不在 git 在途列表，但会影响 code identity 与并发行为，需专项回归）。

**推荐（推荐 ≠ 决定，需 Owner 批准）**：近期 W03 复跑走**方案①**（回到模块引入前的原始可运行环境，零代码改动、无锁语义变化、不触发 `CODE_CHANGED`）；**方案②**作为待授权的修复候选单独排期；**方案③**为兜底登记状态。理由见补丁草案文件末节。任何实施均需 Owner 批准，本轮未实施。

## 3. fcntl 引入时点 / 回归点（只读 git 结论）

回执：`runs/continuous-20261120/integration/w03b/git-log-bounded.txt`、`git-blame-fcntl.txt`、`git-search-fcntl.txt`、`git-timeline.txt`、`git-a29-chain.txt`。

- **引入提交**：`bounded_study_ledger.py` 由 `62f09edbf15f90cdcd08450aab5d60199d44d63f`（`Add bounded three-arm scheduling policy study and resumable ledger`，**2026-11-14 07:36:46 +0000**）引入；`git blame -L 9,9` 确认第9行 `import fcntl` 正是该提交（作者 feng chen，同一时间）。`git log --follow` 只有这一个提交，无更早历史。
- **导入链配套提交**：`saved_study_reference.py` 由 `a1152b4`（2026-11-14 08:20:04 +0000）与 `79218f1`（09:42:19 +0000）引入，均 11-14。
- **A29/A30 当时基线**：`integration.md` 记录的 PR 合并提交 `13054f5`（2026-11-03 22:54 +0800）、`1a295132`（11-04 15:48 +0800）、`61a79ed2`（11-04 16:53 +0800）、`04c2cfee`（11-04 23:43 +0800）。`git-a29-chain.txt` 显示：基线 `61a79ed2` 时 `run_research_project.py` **已存在**，但 `project_controller.py` 第7行仅 `from . import method_registry as registry, project_knowledge, research_methods, project_selection`，**没有 `saved_study_reference` / `project_design` 导入**；当前文件第8行才有 `from . import project_design, saved_study_reference`。
- **结论（有 git 回执支撑）**：A29/A30（2026-11-04）实跑时，`bounded_study_ledger.py` 与 `saved_study_reference.py` **尚未引入**，CLI→控制器的 fcntl 导入链**尚不存在**。因此当时能跑是「模块后加之前的状态」，B1 是 **2026-11-14 后加模块造成的回归**，不是 A29/A30 当时就已存在的问题。
- **对方案①的判断**：结论支持方案①「回到模块引入前的原始可运行环境」在原理上可行。但必须诚实标注：git 只能证明「当时模块不存在」，**不能证明 A29/A30 当时跑在 POSIX 还是 Windows 环境**（该结论 git 查不到，记 **unknown**，不猜）。故方案①仍需先准备可用的 POSIX 环境并重新核对冻结输入 SHA/行尾，不是无条件保证。

## 4. W03 对照框架新增条款：仅到「上游断言层级」时的标注规则

> 背景：W02 已因依赖/数据缺失阻塞。官方断言已逐字固定（sMAPE 9.328 / MASE 0.893 / OWA 0.440，容差 1e-3），但**本项目复算实测值 unknown**。这是对 W03 前半框架第5节的补充，防止把「读到断言」误写成「已复算/已对照」。本节为规则条款，不含任何实测数值。

### 4.1 三层证据状态（必须区分，不得跳层）

| 层级 | 含义 | 可否填数值 | 标注 |
|---|---|---|---|
| L0 上游断言 | 官方/作者给出的公开数字，已逐字固定 | 仅可填「上游公布断言」并注明出处 | `upstream_assertion_literal` |
| L1 本项目复算 | 本项目用冻结输入 + 原评分器实际跑出的值 | 只有当次真实回执存在才可填 | `recompute_actual` 或 `unknown` |
| L2 ICT 入口对照 | 同一冻结输入经 ICT 正常入口的实测输出及 diff | 只有入口实测回执存在才可填 | `ict_entry_actual` 或 `unknown` |

当前状态：**L0 有（断言逐字固定）；L1 = unknown（W02 阻塞）；L2 = unknown（B1 + 无实测）**。禁止从 L0 推导 L1/L2。

### 4.2 ICT 列怎么标

- 对照表「ICT 正常入口（待实测）」列：一律填 **`unknown`**，并附原因标记 `W02_BLOCKED` 与 `B1_FCNTL`。
- 不得填入 9.328/0.893/0.440 或任何由断言推算、四舍五入、按容差反推的数值；这些数字只能出现在「上游断言（L0）」列，且必须带「公开断言，非本项目复算」字样。
- 「是否一致」列填 **`unknown（无法判定）`**，不得填「一致 / 通过 / PASS」。

### 4.3 等价性结论怎么标

- 「输出口径一致」判定：记 **`unknown - 未进行对照`**，不记「一致」也不记「不一致」。
- 「原请求恢复」「预算不重开」两节的「待实测」项：在无真实回执时保持 `unknown`，不因「源码已接线」而改为「已核」。
- 独审结论：当前标 `not_started`（无 L1/L2 实测可供复算或抽查）。
- 任何「源码已接线」的事实只能写在接线/代码依据栏，**不得**据此把等价性、复算、实测栏从 unknown 改为已确认。

### 4.4 最终判定怎么标

W03 最终状态字段：`blocked`，`blockers = [W02_DEPENDENCY_DATA_MISSING, B1_FCNTL]`；`scientific_validation = false`；`assertion_layer_only = true`。即「仅到上游断言层级」是一个被明确记录的状态，不是待补全的占位。

### 4.5 绝对不能写的话（防冒充清单）

以下表述在 L1/L2 为 unknown 时**一律禁止**，出现即为违规，须改为 unknown 标注：

- ❌「输出口径一致」「口径一致」「与上游一致」（无实测不得判一致）
- ❌「已复现」「已复算」「已完成 M4 评分复算」（L1 unknown）
- ❌「已对照」「等价」「与 ICT 入口等价」「通过等价性验证」（L2 unknown）
- ❌「已接入平台」「智能体已接入平台」（D1 暂缓，平台接入继续暂停；与 B1 无关也禁止）
- ❌ 把 9.328/0.893/0.440 写成「本项目结果 / ICT 结果 / 复算结果」（只能是上游断言）
- ❌「容差 1e-3 已通过 / 已核」（没有两次实测值就无法计算差值，容差规则存在≠已通过）
- ❌ 用「源码已接线 / 编译入口 RC=0 / 文档声明」代替「实测通过」的任何措辞

允许且推荐写：「上游公布断言 sMAPE 9.328 / MASE 0.893 / OWA 0.440（逐字固定，L0）；本项目复算实测 unknown（W02 依赖/数据缺失）；ICT 入口对照 unknown（W02_BLOCKED + B1_FCNTL）；输出口径一致判定 unknown，未进行对照；状态 blocked，待 W02 原输出与 B1 处置后复测。」

## 5. 证据路径

- 主文档：`docs/project/workbuddy/w03b-fcntl-options-20261120.md`（本文件）。
- 补丁草案：`runs/continuous-20261120/integration/w03b/patch-drafts.md`。
- git 回归点回执：`runs/continuous-20261120/integration/w03b/` 下 `git-log-bounded.txt`、`git-blame-fcntl.txt`、`git-search-fcntl.txt`、`git-timeline.txt`、`git-a29-chain.txt`。
- 能力探测回执：`win-os-capability.txt`；探测用 `probe2.txt`（HEAD 确认 `3049e749…`）。

## 6. 下一项可做任务（我判断）

1. 等 Owner 对 B1 方案①/②/③作决定；若选①，主控指定 POSIX 环境后我按第4节规则补 L1/L2 实测并交独审。
2. 若选②，需先授权源码改动与 bounded study 专项回归资源，再单独排期（不塞入 W03 临界路径）。
3. 可并行的零成本项：继续只读核 `advance_recipe` 之外原请求恢复路径的代码依据，为 W03b 恢复核验补强（仍受 B1 限制，仅源码定位）。

（未知项一律写 unknown；本轮未获取任何 M4 复算实测值，全部留空标注。）
