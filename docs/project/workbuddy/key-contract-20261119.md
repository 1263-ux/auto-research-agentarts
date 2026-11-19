# 冻结包的键契约：把「id 不是键」变成构建期断言

2026-11-19 23:14–23:4x（北京时间），周期对齐检查第 6 轮。**零研究行动、零模型、零付费。** 冻结包一字未动（`freeze.py --check` → `FROZEN PACKET INTACT`，snapshot `f8f35400…`）。

## 一、阶段判定（先看，不靠记忆）

| 依据 | 读到的内容 |
| --- | --- |
| `docs/project/current.md` | M0/M1/M1b 全部完成；M1 与 M1b **各 2/2 行动已用尽**，无新卡 |
| 工作台 `30-当前迭代.md`（23:12 重写） | 「当前进入方案讨论，排期与分工在讨论后确定」；待讨论项是**十个以上初始配方**及外部已发表基线 |
| 工作台 `历史/2026-11-19/README.md`（23:12 新建） | 11-19 阶段已归档，产品记录**固定在提交 `1b0f065`** |
| `docs/plan.md`（11-12 未改） | 「开发推进已按用户要求停止。新的实现任务和排期尚未确定」 |
| `runs/` | 只有 M0/M1/M1b 相关目录，**没有 M1 之后的 M2/M3 报告**（不存在可推断的 M2 阶段） |

结论：**当前阶段不是 M2，而是 M1 线收尾后的新计划期**。M1b 那张卡仍是代理签名 `needs_review`，没有真人签字；没有新卡就没有新的真实研究额度。按硬边界，本轮只能做零模型、本地可复算的工程增量——不跑排名、不重开 M1/M1b 额度。

一个时间上的事实值得记：工作台在 **23:11:09–23:12:14** 被另一个写者归档并重写（`30-当前迭代.md` → 800 字节指针 + `30-当前迭代.history-20261119.md` + `历史/2026-11-19/`）。这是本轮开始前 2 分钟的事，属并发写者刚完成。按「单 writer、一文件一 owner」纪律，本轮**不重写该文件主段**，只在末尾追加一行指针。

## 二、对齐核对

- `git status` 干净，HEAD `1b0f065`；`origin/main..HEAD` = 0、`HEAD..origin/main` = 0。**本轮未推送 GitHub**（用户未在该轮授权）。
- `.agent/team-budget.json`：`confirmed_cash_spent=null`、`status=reconcile_before_next_paid_call`，本轮无新增支出条目，5 CNY 共享上限未动用。
- `docs/project/latest-report.md` 属前几轮 WorkBuddy 记录，本轮在其顶部追加一节，不改旧节。
- 未伪造 lease。`scripts/project_autonomy_guard.py` 在 Windows 因 `fcntl` 缺失不可用，这一事实沿用，不用替代物假装有锁。

## 三、本轮增量：`scripts/packet_key_contract.py`

上一轮留下的工程候选中，最具体的一条是「新包构建期立键契约（禁 `(id, kept_as)`）」。本轮把它做成可执行断言，而不是再写一段说明。

**契约 v1**（`schema = packet-key-contract-v1`）：

1. 两张表的每一行都带非空 `partition`，取值闭集 `{kept, excluded}`；
2. `(id, partition)` 在表内、跨表均唯一；
3. `id` 单用、`(id, kept_as)` 复合均**不得**当键。

检查项：`C1_MISSING_FIELD` / `C2_DUPLICATE_WITHIN_TABLE` / `C3_DUPLICATE_ACROSS_TABLES` 为阻塞项；`C4_ID_ALONE_COLLIDES` / `C5_ID_KEPT_AS_COLLIDES` 只作证据输出，永不阻塞——因为一个干净的新包完全可能在不同分区里复用同一个 id。

脚本只用标准库，不导入 `src.autoresearch`：包构建器的错误不能在这里自我掩盖。对外入口是 `assert_contract(documents, exclusions)`，新构建器在冻结前调用一次即可，失败抛 `KeyContractError`。

### 自检（故障注入，9/9）

| 用例 | 期望 | 实测 |
| --- | --- | --- |
| 干净包 | PASS | PASS |
| 同一 id 分处两分区 | PASS | PASS |
| 单表内重复 | FAIL / C2 | FAIL / C2 |
| 跨表同分区重复 | FAIL / C3 | FAIL / C3 |
| 缺 `partition` | FAIL / C1 | FAIL / C1 |
| `partition` 为空白 | FAIL / C1 | FAIL / C1 |
| `partition` 越出闭集 | FAIL / C1 | FAIL / C1 |
| 遗留 `(id, kept_as)` 同值 | FAIL 且 C5 计数 1 | FAIL 且 C5 计数 1 |
| `assert_contract` 对不合格包抛错 | 抛错 | 抛错 |

### 真实包实测（M1b 冻结包原样只读，940 + 52 行）

| 视图 | 判定 | 阻塞项 | 跨表键碰撞 |
| --- | --- | --- | --- |
| `as_frozen`（原样） | `LEGACY_VIOLATION_EXPECTED` | C1、C3 | **10** |
| `route_a_restamp_ids`（只给重复 id 加后缀） | **FAIL** | **C1** | 0 |
| `route_b_partition_field`（只加 `partition`） | **PASS** | 无 | 0 |
| `route_a_plus_b`（重打 id + 声明分区） | **PASS** | 无 | 0 |

另有两条证据项在原样包上被复现：`C4` 裸 `id` 碰撞 **10**（与上一轮独立审计同值），`C5` `(id, kept_as)` 碰撞 **10**——第二次以独立实现确认「勘误建议的复合键不成立」。

## 四、负结果：上一轮那句话需要修正

上一轮报告写「能用的修法只有『给被弃副本重打 id』或『加 `partition` 字段』，两者都要重建 manifest/ledger」。**本轮实测前半句不完全成立**：

- **只重打 id 不足以满足契约**。它确实把跨表键碰撞降到 0（`route_a_collisions = 0`），但整包仍因缺 `partition` 字段在 C1 上失败。也就是说，重打 id 修的是「唯一性」，修不了「消费者无法分辨一行属于哪一侧」。
- **只加分区字段就已经足够**（`route_b` 唯一一个单步 PASS）。因为它同时解决了唯一性（`(id, partition)` 唯一）和可分辨性。
- 两者组合也可行（`route_a_plus_b` PASS），但重打 id 在此不再必要。

所以对下一张卡的构建契约，最小可写的建议是**一条**：`partition` 必填且进键；重打 id 是可选的加固，不是必需项。这与上一轮的表述有实质差别，记在此处以免沿错误结论开新包。

这条负结果也说明一件事：**在真实行上跑一遍「修复方案」，比在报告里推理「两个方案都可以」更有价值**——差别只有一行输出，但会直接影响下一个包要不要写重打逻辑。

## 五、复算与可重复性

- 自检 9/9；输出 JSON 连跑两次逐字节相同（SHA-256 `7eed1336…8c26`）。
- 脚本 SHA-256 `4152210a…d88be`；报告工具链只用 `.venv/Scripts/python.exe`（3.12.14，托管 3.13.12 缺 numpy 的老问题不涉及本脚本，但仍按既有约定统一）。
- 冻结包未改：`freeze.py --check` → `FROZEN PACKET INTACT`，`snapshot_sha256 f8f35400efbdc9ac6bd96eade20200b11d1f1717084e3a87e39f041109b005ac`。
- 产物：`runs/key-contract-20261119/contract.json`（gitignored）。

## 六、预算

| 项 | 已用 | 预留 |
| --- | --- | --- |
| 研究工具行动 | 0（M1 2/2、M1b 2/2 各自已满，未重开） | 0 |
| 模型请求 | 0 | 0 |
| 原生 fit / evidence | 0 / 0 | 0 |
| 现金 | 0（账本 `confirmed_cash_spent=null`） | 0 |
| 平台自身用量 | unknown（不可见） | — |

## 七、下一任务

1. **仍是 `needs_review`**：M1b 审批卡上是「feng（口头授权，代理记录）」，需本人签字才能把该轮从 needs_review 清掉。本轮未代为清除。
2. 工作台已转向「十个以上初始配方 + 外部已发表基线」的方案讨论。这属**计划期**，不是已批准的研究动作；任何配方复跑都需先有预注册卡（范围/终点/停止条件/预算/键契约）。
3. 若开新包：`partition` 必填并进键，构建器调一次 `assert_contract` 即卡住重复键；不必再写 `(id, kept_as)` 那套。
4. 未做但可继续零模型推进的候选：把契约接进新卡的 preflight 模板（当前 `m1b_preflight.py` 的 G10 是只读核查，不是构建期断言），或为工作台的配方清单做只读资料索引。

**对外结论口径**：本轮的通过项均为「冷上下文复核通过」；M1b 卡的授权仍标 `needs_review`；无真人签字，不宣称任何研究收益或等价性。
