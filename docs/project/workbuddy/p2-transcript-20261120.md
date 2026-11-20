# 配方清单是否忠实转写：从「声明未核」到「6 条规则重算」

- 轮次：2026-11-20 第 12 轮（零研究行动、零模型、零现金、零安装）
- 起点：`5c406f6`（第 11 轮），工作树干净
- 交付：`scripts/recipe_transcript_check.py`（6 规则 + 10 条自检）、`runs/transcript-20261120/`
- 改动：`recipe-manifest-20261120.json` 的说明段与 `transcript_check` 证据块（**判定输入未动**，P2 结论未变）
- 结论层级：**冷上下文复核通过**，未经真人签字 → `needs_review`

## 1. 起因：门禁自己写下的盲区

第 10 轮把 P2 做成可复算门禁时，清单里留了一行：

```
"field_completeness_verified": false,
"field_completeness_note": "…scripts/p2_recipe_check.py verifies structure and evidence, not prose."
```

这句话是诚实的，但它同时说明：**清单是否忠实于卡片，没有任何机制在管**。如果清单与卡片漂移，下游 11 条规则全部照常通过，而它们描述的是一份卡片已经不再那么说的东西。转写错误是唯一能"让所有门禁都绿"的错误类型，所以它值得单独一条规则。

## 2. 先量字段写法，再写规则

第 10 轮踩过的坑是：拿一套想象的字段标签去匹配散文，结果四张卡被误报「缺原产物」。这次先统计再动手。两张卡文件里实际出现 **20 种** `- **标签**：` 写法：

| 归一名 | 卡上的实际写法 | 张数 |
|---|---|---|
| 原入口 | `原入口` | 10 |
| 数据与许可 | `数据与许可` | 10 |
| 典型输入 | `典型输入` | 10 |
| 反馈分支 | `反馈分支` | 10 |
| ICT 改造点 | `ICT 改造点` | 10 |
| 状态 | `状态` | 10 |
| 可重跑最小例 | `可重跑最小例（草案，未执行）` / `（草案，未执行且未完整定义）` | 9 + 1 |
| 固定版本/提交 | `固定版本/提交` / `固定版本/提交（g0 manifest）` | 8 + 1 |
| 失败条件 | `失败条件` / `失败条件（g0）` / `失败条件/阻塞` | 8 + 1 + 1 |
| 原产物 | `原产物` / `原产物（上游公布，非本项目）` | 6 + 4 |
| 原基线 | `原基线` / `原基线（上游公布，非本项目）` | 2 + 1 |
| L0 上游公布值 | `L0 上游公布值（非本项目）` | 1 |
| git blob SHA | `git blob SHA（内容哈希）` | 1 |
| 处理方式 | `处理方式` | 1 |

**顺手纠正清单里一句错话**：原说明写「`原产物` appears only on the six W04c cards」。实测 **10 张卡都有**（6 张写 `原产物`，4 张写 `原产物（上游公布，非本项目）`）。这句解释本身犯的正是它想解释的那个错误——按单一拼写去找。已在清单说明段改正，并说明错因。

## 3. 六条规则与三态

| 规则 | 判什么 |
|---|---|
| R1 heading | 每行都指向声明文件里真实存在的 `### 卡 N ·` 标题 |
| R2 title | 清单标题与卡标题至少共享一个 4 字符以上的特征词 |
| R3 anchors | `anchor_value` 里的 commit SHA / 版本号必须**逐字**出现在卡里 |
| R4 drafts | `min_example == draft_only` 与卡侧「草案」标注**双向**一致 |
| R5 field set | 每条标 `true` 的布尔字段，卡侧必须有对应标签（容忍 `（g0）` 这类限定语） |
| R6 numbering | 清单编号 1..10 与卡标题编号完全一致 |

三态是必须的：`match` / `mismatch` / `undecidable`，**只有 `mismatch` 失败**。做不出判断时说明做不出，而不是当作通过——第 10 轮的反面教训是「猜出来的失败同样有害」。

R4 写成了双向：清单说跑过而卡说草案要报错，清单说草案而卡标了已验证同样要报错。单向只能抓一半。

## 4. 真实结果：6/6 一致

```
R1_heading       MATCH        10 rows map to 10 headings in 2 files
R2_title         MATCH        all 10 titles share a distinctive token
R3_anchors       MATCH        11 pins from anchor_value found verbatim in the cards
R4_drafts        MATCH        every draft_only row has a card-side draft label
R5_field_set     MATCH        all flagged fields have a card-side label
R6_numbering     MATCH        numbers 1..10 present in both

6 rules, 6 matched, 0 mismatched, 0 undecidable, 10 cards parsed
EXIT 0 (TRANSCRIPT_CONSISTENT)
```

**11 枚钉逐一在卡上命中**，其中包括 OR-Tools 的 `100f66e6…`、BEIR 的 `ef83d293…`、Agent Laboratory 的 `d9017d90…`。自检 **10/10**、退出码 0、两次输出逐字节相同。

**P2 判定没有因此变绿**：`p2_recipe_check.py` 仍 `EXIT 1 (R5_anchor, R6_call_record, R7_min_example)`——本轮只补了"清单没记错"这一条，没碰"卡没跑过"这一条。这两件事不能混。

## 5. 两个校验器缺陷（都由真实运行暴露）

**缺陷一（假失败，最重要）**：第一次跑真实库报 `card 9: no label for failure_conditions`。看着像卡片漏字段，实际卡 9 明明白白写着：

```
- **失败条件**（g0）：`tools.py:298` subprocess exec、…
```

限定语 `（g0）` 在 `**` **之后**、冒号之前，而我的正则要求 `**` 紧跟 `：`，于是**整行都没被抽出来**。这不是归一化问题（我一开始误判成这个方向，先改了一版归一化，无效），而是标签抽取问题。正解是把 `**` 与冒号之间留给任意非冒号字符：

```
^- \*\*(.+?)\*\*[^：:\n]{0,24}[：:]
```

**这件事本身值得记**：如果只看校验器输出，会得出「卡 9 缺字段、清单过度声明」的错误结论，并去改清单——那就等于**用错误的工具结论去篡改正确的数据**。是打开卡片原文才拦住的。

**缺陷二（测试自身）**：S5 单向判断（只查「清单说草案而卡说已验证」的一半），S9 里 `code`/`rules` 被前面的 `mutate()` 重绑，导致「两次运行一致」比的是最后一次变异结果。两处都在测试里，不在被测代码里。

## 6. 这个通过意味着什么，不意味着什么

已核（`verified_scope`）：标题与编号、11 枚钉逐字命中、草案状态双向一致、标 `true` 的布尔字段在卡上有标签。

**未核（`not_verified`，已写进清单）**：blockers 列表内容、category 与 anchor_strength 的归类、substitute 措辞、ict_change 文意、依赖在当前环境是否存在。

因此 `field_completeness_verified` **仍为 false**。6 条规则全绿只说明「清单不与卡片矛盾」，不说明「清单把每个字段都抄全了」。把 false 翻成 true 会让一个部分验证看起来像全面验证——这正是这个项目反复要防的那类夸大。

## 7. 边界与预算

- 研究行动 0 / 模型 0 / fit 0 / 现金 0 / 安装 0 / 推送 0 / 外发 0；平台用量 **unknown**
- 只读卡片与清单；未改任何卡片内容；`src/` 未改；冻结包未动
- P2 门禁结论未变（`EXIT 1`，同样三条）；W05 卡仍 `not_authorized` + `R13 PENDING`；M1b 代理签字仍 `needs_review`
- 本报告与校验器未经真人签字 → `needs_review`

## 8. 下一任务

1. **仍挂起、需 Owner**：B1×G5 取舍（第 11 轮的二选一）、W05 F1 语料、W05 F2 `original_term_policy`、M1b 签字、报名状态（截止 2026-11-30）。
2. 零成本可续：把 `not_verified` 里最容易做的一项做成规则——**blockers 与卡片「失败条件」条目的对应**（目前清单的 `blockers` 是自由文本，没有反向校验）。这是 P2 里唯一还没有机械判定的字段族。
3. 仍可查：两个 `serve_*` 入口在 `--help` 下挂起（第 11 轮记为未测）。
