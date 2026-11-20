# 退出码不是判定：给对齐工具加一列语义（周期检查第 15 轮）

2026-11-20 · 零研究行动 / 零模型 / 零现金 / 零安装 / 零推送 / 平台用量 unknown

## 问题

`scripts/round_align.py` 是此后每轮开头的唯一入口，第 14 轮的设计原则写得很清楚：**「只出报告不做裁决，把退出码折叠成『全绿』正是反复记录的失败模式」**。这一原则对了一半。

它打印 `rc` 原样值，但 **`rc` 本身仍然有歧义**：

| rc | 可能是 | 可能是 |
| --- | --- | --- |
| 1 | 门禁判定「对象不合格」 | 门禁在判定之前就抛异常了 |
| 2 | 设计上的 `pending`（W05 卡就是这么用的） | argparse 拒绝了调用参数 |
| 0 | 门禁判定通过 | 自检跑完打印 `13/13` 但根本没碰对象 |

第 13 轮把「unknown 被误记成 fail」记为同族错误的第三次。**只印 rc 就是留了第四次的口子**：下一轮读到 `rc=1` 时，无法判断该写「P2 仍未通过」还是「P2 门禁坏了」。

## 实测

### 当前 8 个门禁：全部是真判定，没有故障行

| 门禁 | rc | `how` | 判定内容 |
| --- | --- | --- | --- |
| P2 recipe gate | 1 | `verdict` | `FAIL: R5_anchor, R6_call_record, R7_min_example` |
| recipe transcript | 0 | `verdict` | `TRANSCRIPT_CONSISTENT` |
| blocker probe | 0 | `verdict` | `MAPPING_COMPLETE` |
| W05 card | 2 | `verdict` | `DRAFT_OK_NEEDS_OWNER` |
| G5 pin probe | 2 | `verdict` | `EOL_ONLY_GATE_ALREADY_RED` |
| portability selftest | 0 | `selftest` | `13/13 checks passed` |
| blocker selftest | 0 | `selftest` | `10/10 checks passed` |
| pin probe selftest | 0 | `selftest` | `8/8 checks passed` |

**所以这一轮是预防性的，不是修 bug。**必须这么写：本轮没有发现任何门禁在崩，把预防性改动说成「修好了某问题」是同一类夸大。

### 但这个混淆是可达的，而且本轮我自己就踩了两次

**第一次**：为核验各门禁打印的判定与进程码是否一致，我写了一个探测脚本，把 `w05_card_check.py` 的自检参数写成 `--selftest`（真名是 `--self-test`）。结果是 **`rc=2`、stdout 无任何 `EXIT` 行、stderr 只有 argparse 的 usage 文本**。在旧表里，这一行与 W05 卡门禁「设计上的 pending」在 `rc=` 列**完全相同**，都是 `rc=2`；差别只在被截断到 92 字符的 `last_line` 里。若不是我正好认得那句 usage，这一行就会被记成「W05 卡门禁仍是 pending」——而它其实**根本没跑**。

**第二次**：`scripts/p2_unlock_probe.py` 首跑崩在 `Path.relative_to()`（相对证据目录 vs 绝对仓库根），`rc=1`。而该脚本的「场景与期望不符」也是 `rc=1`。**崩了和判失败，退出码一模一样**，只有 stderr 里有没有 traceback 能分开。

两次都不是门禁的问题，但两次都证明：**只看 rc 会把「没跑」读成「跑了并给了结论」**。

## 改动

`scripts/round_align.py` 每行新增 `how` 与两个结构化字段（`stated_exit` / `verdict_token` / `checks`），7 类取值：

| `how` | 含义 | 判据 |
| --- | --- | --- |
| `verdict` | 门禁自报了退出码，且与进程码一致 | 有 `EXIT n (TOKEN)` 行且 `n == rc` |
| `VERDICT-MISMATCH` | 自报码与进程码不一致 | 两者不等 → 必有一方在说谎 |
| `selftest` | 自检跑完，保留分子与分母 | 有 `n/m checks passed` |
| `crashed` | 抛异常，`rc` 不是判定 | stderr 含 `Traceback (most recent call last)` |
| `usage` | argparse 拒绝调用 | stderr 含 `unrecognized arguments` / `the following arguments are required` / `invalid choice` 等 |
| `silent` | `rc=0` 但什么都没说 | 上述皆无 |
| `died` | `rc≠0` 但什么都没说 | 上述皆无 |

两条顺序规则是有意的：

1. **traceback 压过一切**。门禁可能在前一阶段打印过 `EXIT` 行再崩，那行不是对被测对象的陈述。
2. **usage 压过 `EXIT` 解析**。argparse 用 2，而门禁也用 2 表示 `pending`；不先判 usage，「参数打错」就会被读成一个 `pending` 判定。

渲染时若存在非判定行，表尾强制追加：

```
NOTE 1 row(s) whose rc is not a verdict: ...
     a non-verdict rc must not be quoted as 'the gate still says X'
```

## 验证

- 自检 **9/9 → 24/24**（新增 S6–S12：一致判定、双向 mismatch、traceback 压过判定、usage 与 pending 的 `rc=2` 同值不同义、selftest 分子分母、`silent` vs `died`、NOTE 只在非判定行触发）
- 真实跑两次，**除「最近写入分钟数」外逐字节相同**
- `--json` 同步带上 `how` 字段
- 未改任何门禁脚本；`src/` 一行未动
- 冻结包 `f8f35400…` 未复跑（本轮不碰它），门禁自身 `EXIT 2` 未变

## 未验项（明确登记）

1. **usage 标记词跨版本会变**。`USAGE_MARKERS` 是 5 条字面量，只在本机 Python 3.12.14 上核对过。换解释器若措辞变了，`usage` 会静默退化成 `died`——**这是本次改动新引入的单点，须在下次换环境时重跑 `--selftest`**。
2. **`silent` 与「真的没话说」不可区分**。一个设计上只靠退出码表达结果的门禁会被归到 `silent`。当前 8 个门禁都有话可说，所以未发生。
3. 本轮没有把 `how` 回填进历史报告。第 1–14 轮的报告里「rc=X」的表述仍按当时的工具解释，不回改。

## 一句话

**让红也只表示它真正表示的那件事**——第 14 轮把这话用在「绿」上（`MAPPING_COMPLETE` 后面强制跟一句「22 条仍 undecidable」），这轮把它用在「红」上。
