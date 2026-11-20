# 当前自主研究开发

2026-11-20 **一轮两个增量：29 条阻塞的可复算判定，以及「修 B1 必然破坏 G5」这个前提被推翻（周期检查第 14 轮，零研究行动、零模型、零现金、零安装、零推送）**：用户指示「不需要等我确认，一直持续推进」，故不再逐项停下征询。**增量一**：`scripts/p2_blockers_check.py` 把 `blockers` 从自由文本变成可复算判定——**29 条里 7 条 `confirmed`（点名的模块本机确实不存在）、0 条 `stale`、22 条 `undecidable`（数据/许可/凭据/上游）、0 条 `unmapped`**。两条硬事实：① `stale=0` 说明第 10 轮转写没写进过时阻塞，Owner 照这份列表做决定不会被误导；② **「授权装依赖就能解锁 P2」是假的**——装齐 7 个包只把阻塞从 29 降到 22（−24%），卡 4 装了客户端仍没有 Elasticsearch 服务（实测 9200/9300 均 closed）。另纠一处措辞：第 10 卡写 `pandas versions` 读起来像「版本待核」，实测 **`pandas` 完全缺失**，而 numpy/scipy/pyyaml 都在——这解释了为什么 M 系列数值脚本能跑、表格/M4 路径不能。出口名从 `ALL_BLOCKERS_SETTLED` 改成 `MAPPING_COMPLETE` 并强制追加「22 条仍 undecidable，不是可跑」一行：**让绿只表示它真正表示的那件事**。**增量二**：`scripts/g5_pin_probe.py` 推翻第 11 轮「修 B1 必然让 G5 证据失配」——那句只对 LF 检出成立。本机 `core.autocrlf=true`、`.gitattributes` 只钉了 `fixture.py` 的 `eol=lf`，6 个被钉文件 **5 个 `eol_only`**：把盘上 CRLF 换回 LF 后哈希**等于** blob，且字节差与 CRLF 数逐个相等（685=685、56=56、117=117、761=761、866=866），记录里的 `1d39b54d…`/`3a335e10…` 正是 LF blob 的哈希。`scheduling_kernel.py` 的硬编码断言在本机读到 `493f0a4f…` → **这道门在任何人动手前就已经是红的**。于是本机修 B1 无额外代价，且多出选项 **C**：改 B1 + 让这 7 个文件按 LF 检出，不动校验器、不牺牲证据。**本轮自己踩的坑**：拿行前缀当 `Edit` 锚点，把注释行剩余部分留成语法错误，`Edit` 仍报成功——锚点要取整行，改完立刻 Read 或 `py_compile`。[阻塞报告](workbuddy/p2-blockers-20261120.md) · [B1×G5 报告](workbuddy/b1-g5-eol-20261120.md)

2026-11-20 **两个 `serve_*` 不是「挂住」而是「快速死掉」：一条错误记录的更正 + 分母身份（周期检查第 13 轮，零研究行动、零模型、零现金、零推送）**：本轮到得比第 12 轮晚，16:36:19 启动时另一会话正在写盘（16:38 改 `current.md`、16:39 提交 `2e3a665`）——按单 writer 纪律重叠期只读、不重复它的工作，改做它 §8 留的未做项。第 11 轮把两个 `serve_*` 记成「连 `--help` 都不返回（20 s 超时）→ 未测」，三处文档都建在这个未复现的观测上。**实测四配置**：无桩时两者 `RC=1`、2.4–3.9 s、死在同一行 `import fcntl`；桩上 `--help` `RC=0`（正常打 usage）、无参 `RC=2`（argparse 报缺 `--root`）——**没有一种会挂 20 秒**。唯一「不返回」的配置是「桩 + 合法 `--root`」，那时 `serve_forever()` 真的在服务，是服务器的正确行为。于是：**20 个判死入口不变**（静态扫描里两者本就 `unguarded_in_modules`），但验证覆盖从「18 已验证 + 2 未测」变成 **20/20 已测、29 个测量点 0 冲突**。**顺带修掉分母不稳定**：跑扫描得 145 个入口而非第 11 轮的 144，`git ls-tree` 逐提交核对确认增量恰好是第 12 轮新增的 `recipe_transcript_check.py`——**新写的校验器自己进了分母**，于是「20/144」与「20/145」看似可比实则不可比；给 `portability_scan.py` 加 `population_sha256`（只哈希入口名集合，当前 `e9fe6f05…`），自检 11/11 → **13/13**、退出码 0、两次扫描逐字节相同。**这是同族错误的第三次，也是「unknown 被误记成 fail」的第一次**：11 轮「`from . import a, b` 解析漏 → 判活」、12 轮「正则要求 `**` 紧跟冒号 → 判卡缺字段」、13 轮「20 s 超时 → 判挂起」，共同点是**观测是真的、解释是假的**。[报告](workbuddy/serve-hang-20261120.md)

2026-11-20 **配方清单的忠实性从「声明未核」变成「6 条规则重算」（周期检查第 12 轮，零研究行动、零模型、零现金）**：第 10 轮的 P2 门禁自己写着 `field_completeness_verified: false`——它核结构与证据，**不核清单是否忠实于卡片**。转写漂移是唯一能「让所有门禁都绿」的错误类型，因此单列一条。新增 `scripts/recipe_transcript_check.py`：R1 标题存在、R2 标题共享特征词、R3 **11 枚 commit/版本钉逐字命中卡面**、R4 草案状态**双向**一致、R5 标 `true` 的字段在卡上有标签、R6 编号一致；判定为 `match`/`mismatch`/`undecidable` 三态，**只有 mismatch 失败**（猜出来的失败同样有害）。**真实库 6/6 MATCH、`EXIT 0`**，自检 **10/10**、两次输出逐字节相同；**P2 判定一字未变**（仍 `EXIT 1`，同样三条）——只补了「清单没记错」，没碰「卡没跑过」。**真实运行先暴露的是校验器自己的假失败**：卡 9 写 `- **失败条件**（g0）：`，限定语在 `**` 之后、冒号之前，我的正则要求 `**` 紧跟冒号 → 整行未被抽到 → 报「卡 9 缺字段」。若只信校验器输出，就会去改**正确的数据**去迎合**错误的工具**；是打开卡片原文才拦住的。同时纠正清单说明里一句错话（称 `原产物` 只在 6 张 W04c 卡上，实测 10 张全有，6 张写 `原产物`、4 张写 `原产物（上游公布，非本项目）`）。`field_completeness_verified` **仍为 false**：6 条规则只证明「清单不与卡片矛盾」，不证明「字段抄全了」，`not_verified` 五项已写进清单。[报告](workbuddy/p2-transcript-20261120.md)

2026-11-20 **B1 的可达面算清了：20 个入口在 Windows 上死于同一行 import（周期检查第 11 轮，零研究行动、零模型、零现金、零修改源码）**：此前 10 轮都把 B1 写成「三处现象 + 等 Owner」，但没回答两个更基本的问题——到底多少入口是死的、修掉 import 之后是不是就能跑。新增 `scripts/portability_scan.py`（纯标准库、静态 AST、不导入 `src.autoresearch`，因此在已坏的平台上也能跑）区分**模块体导入**（模块根本无法导入）与**函数内导入**（导入正常、执行才失败），两者修法完全不同，混为一谈就会补出一个仍在调用时崩掉的补丁。**实测判定**：144 个入口里 **20 个在 Windows 上判死、16 个 lazy-only**，根因单一 —— `src/autoresearch/bounded_study_ledger.py:9` 的 `import fcntl`，经 `saved_study_reference` → `project_controller` 拖进几乎所有研究入口。**判定经测量裁决**：18 个判死入口全部 `RC≠0` 且含 `No module named 'fcntl'`、9 个 lazy 抽样全部 `RC=0`，合计 **27 个测量点 0 冲突**；两个 `serve_*` 连 `--help` 都挂住（20 秒超时）故记为**未测**、不计入已验证。**探针（非修复）**：桩入 `PYTHONPATH` 后 `run_research_project.py status` 立刻输出 `PROJECT_NOT_FOUND` 结构化 JSON → **fcntl 是这条链上唯一的导入期阻塞**。**决定性冲突**：`run_scheduling_policy_transfer.py` 用 `SOURCE_ROOT = parents[1]`（活工作树）把该文件哈希算进 `source_fingerprints` 并与固定协议比对，**修 B1 必然破坏 G5 存档证据**，故 B1 是取舍而非工程量；另查明 `saved_study_reference.py:30` 那枚同名钉解析在 `/workspace/...` 快照上（本机不存在），**不拦活文件**，但说明 L2 原版复现仍结构性不可达。自检 **11/11**、退出码 0。**自查错三处**（全部保留）：重复计数、`from . import a, b` 解析漏导致 `run_research_project.py` 被判活（假阴性）、闭包把惰性边当导入期边导致两个脚本被判死（假阳性）。[报告](workbuddy/portability-b1-20261120.md)

2026-11-20 **P2「配方库未通过」做成可复算判定（周期检查第 10 轮，零研究行动、零模型、零现金、零安装）**：W05 线全卡在 Owner，本轮转做工台本阶段重点的另一半。索引里「P2 未通过」原是人工结论，下一轮只能选择相信或重读 239 行散文；现在由 `docs/project/workbuddy/recipe-manifest-20261120.json`（10 张卡的机器可读转写）+ `scripts/p2_recipe_check.py`（11 条规则）重算。**先试过往散文上套标签规则，失败了**：四张 W04b 卡被误报「缺原产物」，`可重跑最小例` 因带后缀被正则漏掉 → 改为「数据 + 只核结构与证据」的分层，清单里显式写 `field_completeness_verified: false`，不把转写声明冒充成验证过的事实。**实测**：`EXIT 1 (R5_anchor, R6_call_record, R7_min_example)`——R6/R7 是 **10/10 全缺**（不是「大概缺」），R5 精确到 GPT Researcher（`main` 分支）与 data-to-paper（只有 PyPI 名）两张没版本化；R1/R2/R3/R4（资料 3 / 评测 5 / 工程 2）/R8/R9/R10/R11 全 PASS。抗伪造：声明 `present` 但证据文件不存在 → 直接 FAIL。自检 **15/15**（含「合成的全满足清单 → EXIT 0」，证明 11 条规则可以同时满足，不是死门）。**解锁方式很具体**：任何一张卡真跑通一次最小例，改两个字段 + 给日志路径，门禁就少一条失败项。[报告](workbuddy/p2-gate-20261120.md)

2026-11-20 **F2 的缺口做成机械门禁（周期检查第 9 轮，零研究行动、零模型、零现金、零推送）**：上一轮查出 F2 冻结了 `fb_terms=10` 却没定「扩展词表怎么选」，当时只写进报告——那就是还没修。本轮给 `scripts/w05_card_check.py` 加 **R13**（F2 必须编码 `original_term_policy`，闭集 `{combined_top_k, always_retain}`；缺失=FAIL、`null`=PENDING、出闭集=FAIL、**与 `w05a_rm3.PROTOCOL` 不一致=FAIL**）与 **R14**（F2 的 7 个数字必须与模块 `PROTOCOL` 逐项相等）。为此把判定从 pass/fail 改成 **pass/pending/fail 三态**：`pending` 表示「结构正确、等 Owner 决定」，仍走 `EXIT 2`，不让未签草案看起来像坏文件。卡上只补编码不动数值：F2 增 `arm`（把已冻结的 7 个数字原样转写）与 `original_term_policy: null`（已登记未定），正文加「F2 修订提案（pending，未生效）」。**实测**：故障注入自检 **27/27**（原 20 + 7 条新变异），本卡 `EXIT 2`、`R13 PENDING` / `R14 PASS`、其余 12 条 PASS，连跑两次输出逐字节相同（`28b34cac…`）。最有用的是那条「决定必须落到代码里才算数」：只看卡上写了 `always_retain`、代码仍跑默认值，两边都不报错而数对不上卡。**未替 Owner 选策略**——补个值就能让卡变绿，但这正是不能做的事。[报告](workbuddy/w05-gate-r13-r14-20261120.md)

2026-11-20 **W05a RM3 模块做成可运行、可证伪的工程件（周期检查第 8 轮 / 三小时对齐 13:28 起，零研究行动、零模型、零现金、零推送）**：`scripts/w05a_rm3.py`（284 行，纯函数，只 import `math`/`re`）+ `scripts/w05a_selftest.py`（267 行），自检 **49/49**、退出码 0、输出连跑两次逐字节相同（`runs/w05a-20261120/selftest.txt`，`ef5f654f…`）。**没写第三份 BM25 常量**——`k1/b/top_k/...` 全作数据放 `PROTOCOL`，自检逐项断言它等于 `relevance_retrieval_adapter.COMPARISON`，并在合成语料上比对 `adapter.retrieve(bm25)` 排序（4 条查询 + 1 条排除例）完全相等，任一侧改常量都会红。唯一真正强的退化断言是 `orig_weight=1.0`：反馈系数为 0，浮点上精确成立，两阶段排序必须**与单路 top-k 完全相等**（已过）。**新发现一个会改数的卡缺口**：F2 冻结了 `fb_terms=10` 却没说扩展词表怎么选；`combined_top_k`（Indri 读法）与 `always_retain`（补回原始查询词）在 `fb_terms=1` 时给出不同结果（一个 3 篇、一个 4 篇），且 `always_retain` 会让 `fb_terms` 退化成空参数（本例 1 与 10 同结果）。**W05 执行前 F2 必须补 `original_term_policy` 并由 Owner 冻结**，否则两套数都算合规。模块**未接线**（全仓仅自检引用它）、**未碰冻结语料**、`src/` 一行未改、`git diff` 为空；W05 卡仍 `not_authorized`，M1b 代理签名仍 `needs_review` 未代签。[报告](workbuddy/w05a-rm3-20261120.md)

2026-11-20 **W05 审批卡草案 v0.1 已起草并机械校验（周期检查第 7 轮 / 三小时对齐点 03:05，零研究行动、零模型、零现金）**：`docs/project/workbuddy/w05-card-draft-20261120.md` 按独审门槛 9 字段全部落位，其中 **7 项 frozen / 1 项 open / 1 项 blocked**，因此**未达 9/9、不得执行**。open 的是 F1 独立数据（三候选 O1 同卷换题 / O2 另一 CFR title 固定卷 / O3 其他公有领域源，推荐 O2 但推荐≠决定，属 Owner 级）；blocked 的是 F4 反馈分支（真实回执来源 `ProjectController.advance` 在 Windows 因 B1 不可达，分支条件可写、回执驱动无法实测）。课题从「BM25 vs TF-IDF」换成**结构**比较：A=单路 BM25，B=BM25 粗排 100 → RM3 伪相关反馈（fb_docs=20、fb_terms=10、orig_weight=0.5）重排取 20；主终点 mrr@10 单侧 α=.05，次终点 ndcg@10，**明确不主张等价**（等价需 TOST）。已查明本仓库**无任何 RM3/伪相关反馈实现**（`rm3`/`pseudo.relevance`/`robertson` 三词在 `src/`、`scripts/` 均 0 命中），故卡批准后先做 W05a（新模块 + 退化夹具单测），且不改既有 `COMPARISON` 常量。校验器 `scripts/w05_card_check.py` 12 条规则、退出码 0/2/1，对本卡判 `EXIT 2 DRAFT_OK_NEEDS_OWNER`，故障注入自检 **20/20**；独立复算卡内 7 个数字与 `runs/mdes-20261119/plan.json` 逐个相等（426/107/48/336/84/0.210508/23·1）。顺带查清 336 与 426 之差是**两个常数**（TOST 用单侧 6.182558，检测用双侧 7.848879），不是四舍五入，日后不得合并。[卡片](workbuddy/w05-card-draft-20261120.md)

2026-11-19 后续安排见 [WorkBuddy 持续推进计划](workbuddy/continuous-plan.md)。上游工作流接入、十个以上配方、自主推进和交付按阶段验收。实际执行结果继续在本页登记。

**WorkBuddy 手动交接（2026-11-18）**。入口包含首轮任务、团队分工、阶段验收、外部调研和首个真实检索课题草案。先交可评审的输入与预注册证据，研究执行按批准范围开始。[WorkBuddy 交接](workbuddy/README.md)

2026-11-19 **键契约做成构建期断言（周期检查第 6 轮，零研究行动）**：`scripts/packet_key_contract.py` 把「`id` 不是键」变成可执行契约（`(id, partition)` 唯一、`partition` 必填且闭集 `{kept, excluded}`），新包构建器调 `assert_contract()` 即卡住重复键；自检故障注入 9/9，输出连跑两次逐字节相同（`7eed1336…`）。**在 M1b 真实行上的实测修正了上一轮的一句话**：只重打 id 只能把碰撞降到 0（`route_a` 0 处）却过不了 C1（缺 `partition`），**只加分区字段就已足够**（`route_b` 是唯一单步 PASS），两者组合也可行但重打 id 不再必要。原样包报 `LEGACY_VIOLATION_EXPECTED`：裸 `id` 碰撞 10、`(id, kept_as)` 碰撞 10（独立实现的第二次确认）。冻结包一字未动（`INTACT` / `f8f35400…`）。阶段判定：M1 线收尾后的**新计划期**，不是 M2；工作台已于 23:12 归档并固定在提交 `1b0f065`。[报告](workbuddy/key-contract-20261119.md)

2026-11-19 **下一张卡的题量算出来了（零研究行动）**：`scripts/plan_mdes.py` 从 M1b 逐题指标只读复算，本包能看见的最小效应是 **|Δmrr@10| ≥ .2105**（α=.05 双侧、power=.80、n=24），而观测值 +.0232 只有它的 **1/9**——不是没有效应，是尺子的刻度比要量的东西大一个量级。`recall@20` 的 24 题里 **23 题两臂完全相同**，有效样本量其实是 1。要量 0.10 的差：mrr@10 需 **107** 题、ndcg@10 80、recall@20 33；二元符号检验需 **60 / 150 / 196** 题（分别对应翻转题全同向 / 4 中 3 / 10 中 7）。等价性另算：mrr@10 上「检测 .05 的差」要 426 题、「证明等价于 ±.05」只要 **336** 题（TOST，单侧 α=.05）——**p>0.05 不是等价证据**。含义：同一语料单纯加题量只是把「近似零」测得更精确，要看到有量级的差应换范式（词法 vs 稠密/重排），而不是继续 BM25 vs TF-IDF。[报告](workbuddy/next-card-mdes-20261119.md)

2026-11-19 **文档键审计（周期检查第 5 轮，零研究行动）**：M1b 勘误 E1 建议的复合键 `(id, kept_as)` **被证否**——10 个共享 id 上，被保留的文档与被丢弃的副本 `kept_as` 都是 `distractor`，实测仍是 10 处碰撞；能用的只有「给被弃副本重打 id」或「加 `partition` 字段」，两者都要重建 manifest/ledger，属新包。同时校正计数口径：源 XML（`fbaf04e9…`，992 个 `SECTION`）里编号字符串**完全重复 10 个**、编号干冲突 15 个，多出的 5 个是 `3.31/3.31A`、`300.20/300.20a` 这类字母后缀变体，字符串不同故不参与 id 碰撞；根因是 `id == "d-16-" + sectno` 丢了副本序号（940+52 行 0 例外）。门禁补 **G10**「排除清单不得覆盖所需文档」（qrels ⊆ 语料、正例池 ⊆ 语料、正例池 ∩ 排除 = ∅、跨清单共享 id ⊆ 已登记集合），故障注入自检 10/10，完整门禁在包副本上重跑 `GO (10/10)`——不追溯推翻已发布包；**G10 的 PASS 只表示共享集合与已登记的一致，不表示键没问题**。冻结资产一字未动。[报告](workbuddy/m1b-key-audit-20261119.md) · [勘误 E6](workbuddy/m1b-errata-20261119.md)

2026-11-19 **M1b 开放语料复核已执行（2/2 行动用尽，唯一一次）**：操作者 16:49「同意，你可以都试试」口头授权，第 4 项推送仍未授权。干扰池从 85 篇扩到 940 篇（同一冻结卷全部条款，正例 85 篇正文与 M0 逐字节相同，题目/qrels 逐字节相同），`top_k=20` 覆盖率 23.5% → 2.1%。预注册判据见 [协议](workbuddy/m1b-protocol-20261119.md)，命中 **D4**：validation Δrecall@20 **−0.041667（0/23/1）**、Δmrr@10 **+0.023214（4/15/5）**——M1 的召回优势未复现且反向，MRR 优势腰斩，`recall@5` 两臂完全相同。dev（8 题）仍显示候选领先（Δmrr +0.1875），dev/validation 分歧本身是结论：8 题不足以给两个词法排序器排名。**量级提醒**：`q-val-11`/`q-val-23` 两臂各项全 0，故本包 `recall@20` 可达上限 22/24 = .916667，BM25 正好触顶——「谁更好」只剩一题空间，而那题（`q-val-13`）tf-idf 输了。→ **A 路线（改主终点为 recall@5）被本轮数据否掉**，C 路线暂不成立（五个指标全在噪声带内）。[结果](workbuddy/m1b-primary-20261119.md) · [M1 截断事后分析](workbuddy/m1-cutoff-reanalysis-20261119.md) · [勘误](workbuddy/m1b-errata-20261119.md) · [独立核对](workbuddy/m1b-verification-20261119.md)（结构 27 项 + 结果复算 14 项，320 次指标比较 0 不一致；本轮新增两条：recall@20 的差值只有一题、两题两臂都够不到故上限 22/24 且 BM25 已触顶；卡上签名是代理记录，该项 needs_review）

2026-11-19 **M1 primary 已执行（唯一一次）**：审批卡第 1–3 项获操作者口头授权（16:40，代理代记，第 4 项推送未授权）；预检 GO；`capture_source` + `execute` 恰好用尽 2/2 行动，`model_calls=0`、`native_fits=0`、现金 0。validation 24 题：bm25 r@5 .7917/r@10 .9583/mrr .670007；tfidf r@5 .9167/r@10 1.0/mrr .722569，配对均值 Δr@5 +.125（3/21/0）、Δmrr +.052563（6/15/3）。**但 `recall@20` 两臂 32 题全为 1.0（天花板，无方差）**，故「Recall@20 提升是否伴随 MRR@10 下降」在本包上无法回答；3 题 MRR/nDCG 退化已逐题列出，其中 `q-val-22` 召回不变而 MRR 1.0→1/3。[结果](workbuddy/m1-primary-20261119.md)

2026-11-19 预检门禁：M1 开跑判定做成可重复执行的 `scripts/m1_preflight.py`（九项，退出码 0 GO / 2 仅因未签字 / 1 真失败），本轮判定 **NO_GO_UNSIGNED**——签字是唯一剩下的事。除签字外全绿，含指标合同对 7 个手算夹具（正例第 14 位、12 正例、第 21 位）、排序合同（tie-break/截断/排除序/两处实现一致）、`staged_adapter_identity` 从字节独立重算 == `0d659650…`。门禁自身故障注入 11/11。新查三件事：① `staged_adapter_identity` 折进 `sys.version` 与 pypdf 版本，换解释器会在字节全同的情况下让 `--check` 报变化；② `ignore_identical_ids` 在本包内交集为 0、从未行使；③ 排序逻辑有字面量与 `COMPARISON` 两份实现。研究工具行动仍 0。[报告](workbuddy/m1-preflight-20261119.md)

2026-11-19 复核：M0 冻结包独立交叉核对 23/23（`scripts/crosscheck_m0_packet.py`，纯标准库、不导入作者代码），snapshot 用另一套实现重算与发布值逐字符相同，85 篇正文逐篇命中源 SECTION，补上「适配器不校验内容字节」的空白。新增两条执行前提：冻结绑定本机行尾（语料/许可 LF，题目/qrels/spec CRLF）；官方 `freeze.py --check` 须用 `.venv`（托管 3.13.12 缺 numpy）。审批卡仍待签字，M1 仍未执行，研究工具行动 0。[报告](workbuddy/m0-crosscheck-20261119.md)

S139 独立审查及一次隔离合成测试确认入口未接、claim和时间复核不全；测试按缺失方法失败，WIP/原快照保留，不可用于研究。[审查](../execution/SPRINT-139-review.md)。

S139 修复S138第二关联漂移缺口尚未完成/测试；实现成员被平台风险筛查中断，完整未提交WIP保存在 runs/s139-checkpoint-002/manifest.json，保留工作树、不覆盖。详见 latest-report。

S138 真实合成负例确认：质量v2关联parent后报告或child后source漂移仍会执行，实际payload为原缓存；每案2/2工具。第二行动时间门缺口待修，不能外推S136首行动保护。[记录](../execution/SPRINT-138.md)。

S137 固定人工时间门6次真实SIGKILL、2次旧入口抢先、3次source/report漂移；副本核验11案，原工具耗用/预留如实记录。无真实UCI/断电证明。[记录](../execution/SPRINT-137.md)。

S136 新独立strict入口将S134合成时间登记绑定质量首行动及原ID恢复，独审17/17、旧合同3/3和marker负例通过；非全局门/真实UCI，竞争为注入。[记录](../execution/SPRINT-136.md)。

S135 新增人工时间报告在原S084登记后、行动前的独立预登记；事务claim与原ID恢复独审53/53。尚未接派发门，非真实UCI或全局时间保证。[记录](../execution/SPRINT-135.md)。

S134 新建仅内建人工时间源与机械报告，独审11/11及独立重算28小时/26完整对；不认证真实UCI/时区，也不是派发门。[记录](../execution/SPRINT-134.md)。

S133 固定合成包9次真实SIGKILL及2次旧入口竞争已留证；原verifier因3个journal停查，独立副本改写核验11案通过，原库恢复状态unknown。[记录](../execution/SPRINT-133.md)。

S132 合成固定包的严格质量首行动与原ID恢复已独审72/72；非终态停查，合法质量unknown可回读但后继停查。非真实UCI、非真实竞争/断电验证。[记录](../execution/SPRINT-132.md)。

UCI 501 [单站描述性条件协议](uci-501-single-station-descriptive-proposal-20261115.md)已独审；站点/时区/权利、时间绑定及安全恢复仍阻断执行。两次未授权 Firecrawl 各显示1 credit，已停止、实际结算unknown。

S131 续用两原合成项目保存人工plan2，浏览器丢回执同body/ID恢复；独审核前后备份、claims及预算不变，预览不派发。仅合成。[记录](../execution/SPRINT-131.md)。

S130 同pin两全新合成项目先登记同规则再行动：S127 [0,0]→wait 1/2；S129白盒 [0,-0.5]→audit 2/2。独审复算排名/claims；非真实科研或未见评估。[记录](../execution/SPRINT-130.md)。

S129 固定第二白盒合成输入，按已知查询构造干扰；独立格式21/21，预测 MRR 差−0.5尚未实测。它不是盲测或真实科研。[记录](../execution/SPRINT-129.md)。

S128 用 S127 单一人工包完成事前登记→primary [0,0]→wait→人工计划v2→浏览器丢回执原ID恢复与预览；独立只读复算300指标，原rank观测器挂错保留失败。仅合成单分支。[记录](../execution/SPRINT-128.md)。

S127 内建纯合成准备器固定去重与1000/50/100映射，独立复算和15/15通过；仅简化人工XML，不解析真实dump、不证明许可或研究收益。[记录](../execution/SPRINT-127.md)。

S126 为 staged 检索增加操作者显式用途声明，独立合成14/14及旧pin保护通过；声明不授权研究，状态只核形状且双字段非防伪。[记录](../execution/SPRINT-126.md)。

Wikinews [条件性研究草案](wikinews-retrieval-study-proposal-20261115.md)已独审，许可、超限源、解析、用途声明与合成预演未决，不是研究授权或已执行；[候选记录](retrieval-candidate-audit-20261115.md)包括UCI元数据冲突及NFCorpus一次意外样本曝光。

S125 工作台支持人工后继计划保存及原body/ID恢复；同源tab锁、未决扫描和存储异常停查，独立合成浏览器/HTTP通过；5秒测试曾超时，旧pin不迁移。[记录](../execution/SPRINT-125.md)。

S124 新管理器 pin 的 Python resume-only 在同锁内核原 body/ID及计划claim，缺失停查、完整时仅补原回执；独立合成10/10及旧pin保护通过。未接HTTP/UI，不迁移旧项目。[记录](../execution/SPRINT-124.md)。

S123 工作台页面可显式预览后继计划的等待或需另授权的事后审计建议；独立浏览器/HTTP合成与旧pin兼容通过，不派发或写账本，锁可能写。S121保存仍为Python，无真实科研收益。[记录](../execution/SPRINT-123.md)。

S122 Python 管理器可认证后继计划并预览默认等待或需另行授权的事后审计建议，不写研究账本、不派发；独立合成验收通过，协作锁有文件副作用。无网页或真实科研收益。[记录](../execution/SPRINT-122.md)。

S121 工作台 Python 管理器支持将认证的已知 staged 反馈绑定到人工填写的直接后继计划；禁止已有保留评估项目，独立合成审查通过。无 HTTP/UI 或自动策略，非真实科研收益。[记录](../execution/SPRINT-121.md)。

S120 修复严格反馈策略冻结同 ID 重放误判，独立合成两臂、原ID和负例通过；TFIDF臂 final MRR 差 -0.75，非真实科研或模型自主。[记录](../execution/SPRINT-120.md)。

S119：工作台对显式选中的已发布后验经验提供可编辑、仅填空的计划提示；不自动设阈值、引用、登记或执行。独立合成浏览器验收通过，不证明模型自主或科研收益。[记录](../execution/SPRINT-119.md)。
Status: resumable

S118 同一新合成Project真实页面从公开后验经验导入→人工计划引用→事前登记→原ID primary→已知反馈→报告/原ID恢复，独立wait 1/2、audit 2/2；人工合成非模型自主或真实科研收益，后端无独立网络/fit/rank哨兵。[SPRINT-118](../execution/SPRINT-118.md)。

S117 工作台可显式按原登记处理已认证known staged反馈，显示总体条件/原分支/实际wait或audit；unknown与阻塞停查、audit可能额外1工具。独立合成浏览器和后端通过，真实研究未新增。[SPRINT-117](../execution/SPRINT-117.md)。

S116 对严格staged反馈在新合成项目完成十个真实SIGKILL窗口、两个真实旧入口竞争和四种不同分支，独审逐项复算；非断电/任意并发证明。反馈页面仍未接。[SPRINT-116](../execution/SPRINT-116.md)。

S115 已认证completed primary的已知双指标反馈可走严格后端wait或原登记audit，unknown/缺凭据停查；独审52+51合成及3项事务负例通过，S115多进程竞争/UI尚未验证或接入。[SPRINT-115](../execution/SPRINT-115.md)。

S114 页面可显式按事前登记的原future ID执行staged primary，明确最多1工具和dev/validation排名评分；原body保留、resume-only核claim，独立浏览器/回归通过。反馈分支UI仍未接，旧pin不迁移。[SPRINT-114](../execution/SPRINT-114.md)。

S113 独立真实多进程验证staged primary七个SIGKILL窗口及旧Controller抢先，八场与claim独审通过；仅合成/选定切点，未证断电或恶意隔离，UI仍未接。[SPRINT-113](../execution/SPRINT-113.md)。

S112 后端新增以原登记future ID显式staged primary与只核终态恢复，parent/child各自事务claim；独审43+42合成通过，direct抢占仅函数注入、尚无UI。旧pin登记不可自动升级。[SPRINT-112](../execution/SPRINT-112.md)。

S111 工作台可安全显式登记staged验证集双指标及只读反馈；Project登记/claim同事务、原ID缺失停查，独立50项+浏览器/两进程故障通过。新入口需 `-B` 和新空PYTHONPYCACHEPREFIX；未来ID执行和反馈推进UI尚未接。[SPRINT-111](../execution/SPRINT-111.md)。

S110 工作台页面可显式选择并导入S109后验经验包，独立合成Chromium/HTTP验收坏包、跨项目、文件乱序和原ID HTTP重放；未测浏览器失联后恢复按钮，不自动写计划或调用研究。[SPRINT-110](../execution/SPRINT-110.md)。

S109 已将S108两条已发布聚合实际导入独立持久Memory并各自导出；独审核记录隔离/哈希，重入各0。未创建真实目标Project或声明模型采纳；本轮未打开旧Project核预算。[SPRINT-109](../execution/SPRINT-109.md)。

S109 新增S108两条已发布后验结果的独立Memory类型，支持Project显式导入、上下文/计划引用和报告；原行动只作来源、字节绑定不等于重算，独立合成及浏览器验证。页面只能展示，文件选择器尚不支持新类型。[SPRINT-109](../execution/SPRINT-109.md)。

S108 对已曝光S065/S067 validation只读事后计算：召回不变且MRR下降子集分别16题/平均下降0.4026、24题/0.3724；独立Decimal复算，原各3/3预算不变。不是全体平均、盲测或因果收益。[SPRINT-108](../execution/SPRINT-108.md)。

S107 已在独立合成项目真实浏览器贯通质量材料预览→准备→人工回复原文件导入→选句核对→严格采纳→报告与原ID回放；四个同会话异常窗口和44项独审通过。人工回复模型身份/次数/费用unknown，非真实模型或科研收益。[SPRINT-107](../execution/SPRINT-107.md)。

S106 页面可显式严格采纳已供应质量材料；独立resume-only在锁内拒绝无原意图的首次接受，回执不符保留原body。双路径/异常经独立合成Chromium/HTTP验证，详见[SPRINT-106](../execution/SPRINT-106.md)；无真实模型/研究新增。

S105 工作台计划页可显式选择原质量登记并只读预览，旧wire/预算保持；独立双合成项目真实Chromium/HTTP、跨项目与重复预览竞态修复验收，混合/四项上限为模拟。页面严格采纳按钮仍未接。[SPRINT-105](../execution/SPRINT-105.md)。

S104 工作台页面可对已封存质量材料的Host计划选句核对，独立真实Chromium/本地HTTP和23项合成回归通过；跨项目切换仅静态核查，页面尚不能新建质量材料请求或严格采纳。[SPRINT-104](../execution/SPRINT-104.md)。

S103 原有事实核对可显式比较用户选定的原回答片段与冻结质量登记/结果，区分0与unknown；修后作者50、独审50及另一独审20项合成通过。仅人工映射与所选片段，不认证当前source或模型理解。[SPRINT-103](../execution/SPRINT-103.md)。

S102 对严格三层采纳4个固定窗口实际 SIGKILL 并由不同PID原ID恢复，作者与独审各4/4；前三停查，末点核凭据仅补管理回执。仅合成，非断电/全时序或模型理解证明。[SPRINT-102](../execution/SPRINT-102.md)。

S101 将严格质量材料采纳显式接入 Workbench/HTTP，manager、Host v4和Project事务claim三层绑定；作者52、独审36、相关65项合成检查通过。四窗口为故障注入而非本版本真实SIGKILL，未证明模型理解/科研收益。[SPRINT-101](../execution/SPRINT-101.md)。

S100 新增 Python 显式严格采纳：将封存的质量登记材料与原回复引用、原计划及事务归属绑定；作者12项/旧42项和独审54项隔离合成通过，仅证明封存/引用，尚未接Workbench或证明模型理解。[SPRINT-100](../execution/SPRINT-100.md)。

S099 显式把事前登记质量条件和三态反馈供给 Host 计划上下文，保留原身份、未知与预算边界；最终隔离合成14项、旧合同58项、独审38项通过。原计划漂移拒绝供应，材料固定不证明送达模型或科研收益。[验证与负例](../execution/SPRINT-099.md)。

S080 已完成获批的 Bike 2011 真实研究并独立复算：总体/编码0/编码1 Pearson r 为 0.771214/0.762433/0.779847，n 为 365/115/250，预先固定方向条件满足；两项工具 2/2、0 model/fit/native evidence，原计划等待。[结果和限制](../execution/g1-local/bike-2011-results.md)。这是操作者根据质量反馈修订计划的描述性链，不是模型自主或因果/跨年收益。唯一 claim、原 Project 与源码 pin `7926608e981eaf1fdfc94c0d125ae04b7f4423da` 必须保留，不重开额度。

通用表格质量反馈按[设计](tabular-quality-feedback-design.md)继续推进：S081 有界条件、S082 事前登记和原行动认证、S083 显式 Controller 策略之后，S084 已将登记、读取和推进接入 LocalWorkbench/Python/HTTP，并以同事务归属凭据保护两层原ID恢复。隔离合成 HTTP 和故障注入已独审；没有新真实研究、模型自主或科研收益声明。旧项目沿原 pin、原预算保持。[S083](../execution/SPRINT-083.md) · [S084](../execution/SPRINT-084.md)。

S085 Project Python 能保存引用原质量行动的直接后续 plan v2；S086 显式 Controller v2 策略可重新认证原行动与真实最新计划；S087 已通过独立 Workbench/Python/HTTP 入口连接质量引用读取、计划保存和v2推进，原 manager/core 归属同事务绑定。隔离合成和独审通过；旧普通计划入口仍拒新字段，只读宿主新 GET 未开放，context仅校引用形状。[S085](../execution/SPRINT-085.md) · [S086](../execution/SPRINT-086.md) · [S087](../execution/SPRINT-087.md)。

S088 在五个固定 manager/core 节点以独立合成Project真实 SIGKILL 子进程，再由不同进程用原ID/body验证停查或终态回执收敛；作者、主代理和独审各5/5，原Project DB/工件/预算不变。只覆盖选定进程切点，不证明断电或所有恢复时序。[S088](../execution/SPRINT-088.md)。

S089 修复旧 Controller 对原 parent `unknown` 漏阻断：合成真实恢复链曾出现 child 已完成但 parent 仍未知时新候选被展示且新 parent 被接受，测试哨兵阻断第二次工具；修复后预览阻断、新ID锁内拒绝、原ID仍可收敛。75项相关回归与独审通过，按新安全合同更新三处旧测试断言，保留原失败。[S089](../execution/SPRINT-089.md)。

S090 将相同未知父请求保护延伸到 Project 的新预算、来源、工具与升级请求；旧子行动原ID恢复及prepared parent首次child保持。只读selection/report可查看合法 parent unknown→原 child后续completed 的未收敛状态，仍保留parent/原child快照unknown；纯view不核磁盘，report另核工件。隔离合成、模拟网络及独审通过；不代表真实断电或科学收益。[S090](../execution/SPRINT-090.md)。

S091 为普通活动 Workbench 增加按 Project/snapshot 查询 unknown Controller parent 的只读端点，返回有界原ID、身份差异与 partial/截断状态，不输出 body 或自动恢复；S092 已将该 GET 安全开放到受限只读宿主，在此查询中用 immutable SQLite、sidecar/文件身份核查；POST仍禁用。隔离合成和独审通过。[S091](../execution/SPRINT-091.md) · [S092](../execution/SPRINT-092.md)。

S093 修正合法 manager `advance_feedback` 对应 core `controller.advance_selection` 在保存历史中被误报完整性错误：有限原登记候选与manager双摘要和原封存context/提案匹配时只标 partial/current-reader语义匹配、producer未验证，不披露body或授权恢复；明确冲突仍报完整性错误。合成及独审通过。[S093](../execution/SPRINT-093.md)。

S094 新增显式 Host Python 质量计划采用入口：保留原已保存proposal四文本/理由，宿主附加经认证原质量行动引用，以原Host意图及Project同事务claim绑定；S097 已接显式 Workbench/Python/HTTP，三层原意图身份可核并受中断停查。隔离合成无真实模型调用，不能宣称模型实际看到/理解或科研收益。S095单独修复既存工作台错误优先级失败并保留原日志。[S094](../execution/SPRINT-094.md) · [S097](../execution/SPRINT-097.md)。

S096 用隔离合成Host回复在意图已存/core前与core计划+claim已提交/Host回执前两个栅栏实际SIGKILL，并以不同进程原ID恢复；作者和独审各2/2通过。前者停查，后者核原claim只读收敛；不证明断电/所有中断或真实模型采纳。[S096](../execution/SPRINT-096.md)。

S098 对 S097 的 manager→Host→Project 四个固定提交切点用隔离合成实际 SIGKILL 子进程、不同进程原ID恢复；作者和独审各4/4。前三停查，仅Host已applied且原链匹配时补manager回执；不证明断电/全部时序/真实模型。[S098](../execution/SPRINT-098.md)。

参考调研：本轮固定并只读审查 MIT 的 Meta Ax `fd8a67a524b063b2615815c638af2c94b034f476`；它允许行动完成但指标缺失，印证本项目应区分完成状态与反馈 unknown。转移/暂停顺序与本项目规则不同，不直接合入或覆盖原预算门；未运行 Ax。[源码对照](ax-transition-review-20261115.md)。

2026-11-15 用户已对 Bike 2011 方案回复“同意”，批准一次独立真实项目，最多 2 次本地工具、0 模型、0 拟合、0 新增原生 evidence-read；不改变其他预算。原云盘和原全局执行者状态仍未知。

S079检索候选元数据筛选未找到可直接准入项；PubMedQA许可未核且搜索返回公开示例，QASPER许可检索亦意外返回公开test示例，现已停止查看样本，不可称完全未曝/盲测；bioCADDIE规模和qrels权利未核。无新数据下载/项目/排序/模型。[审计](retrieval-candidate-audit-20261115.md)。

S078当时完成并独审Bike方案的隔离合成预演：两个合成Project各2/2工具、0 model/fit/evidence，可计算与constant_predictor/unknown、原观察→人工plan v2→关联、作者原ID新进程重放，独审复算并核回执但未自行重放；该轮未下载真实Bike或创建真实项目。之后用户批准且 S080 已完成真实研究，见文首。[SPRINT-078](../execution/SPRINT-078.md)。

S077新表格Project可显式保存操作者描述性研究用途，已独审推送 `3ba33b62a0d8456fb0d04765285e11d0b7e1195c`；默认旧wire/旧pin不变，仅Python创建支持，非授权/领域验证/新研究。原S065只读status字节同与3/3预算保持，pin193项匹配。[SPRINT-077](../execution/SPRINT-077.md)。

S076真实表格候选[Bike 2011预案](bike-sharing-2011-study-proposal.md)当时仅元数据/接口独审；S077补Python创建的显式用途声明，Workbench直接创建不支持该选项。随后用户单独批准，S080 已按独立范围实际执行；勿将 S076 时未取得原件、未授权等历史状态误认为当前事实。

S075已发布后只读S065/S067原保存validation联合分析并独立复算，结果 [S075](../execution/SPRINT-075.md)：S065召回提高3题其中2题MRR下降；S067召回不变198题中24题MRR下降/12上升。已曝数据事后描述、非盲测/总体收益/迁移；无新模型/fit/排名/行动，原3/3预算保持。reader commit `a8207f63c3201eb2e601dc81642d15342943813b`、pin195项匹配，公开结果SHA c0adf1d0edda145af95da1dfdf94f19a85ceb71decb0e290a90fbdd3734e31cb。

**当前执行基线：** [自主研究任务基线（2026-11-15）](research-baseline-20261115.md)，外部证据与适配见[方法调研](baseline-research-20261115.md)。以可复核真实问题、反馈改变下一决定及原身份接续为首要验收；工程测试不替代科研收益。S074已完成限定范围验收，按基线登记并验证下一研究切片；不改旧盘、预算或授权。

S074计划引用UI与原请求恢复已独审推送 `ea8152e595abca322870a9eb6c7fbc0b9e1eebbf`：两真实进程中断窗口同ID恢复、原来源漂移拒绝、脱敏和跨项目pending已验；UI未保存草稿跨项目返回的完整往返独审未完成，旧无body为unknown。原正文仅本地manager，禁止假称零写入/OS隔离；pin195项匹配。[SPRINT-074](../execution/SPRINT-074.md)。

S073可选计划结构化case引用已独审推送 `340e198ec5bc5a45585e4ddd2360d31d6f0741c3`，锁内核active原bytes、历史按接受版本、撤回后原ID可重放，登记后的计划改变不放松原假设绑定；四条长声明逐条完整出现在Markdown/PDF。固定相关33/前版71，独审5+2及旧wire通过，仍无Workbench引用编辑控件；pin193项匹配/1本地probe。[SPRINT-073](../execution/SPRINT-073.md)。

S072原项目wait→经验引用→原登记primary→新conditional闭环已做合成工程验证并推送 `9df7f3ad6743763a2471ac45d9ae6d0982da1b32`；原wait/primary/conditional跨进程原ID重放，3/3正向、额度用尽等待、unknown null及漂移拒绝均核实，作者/独审各3/3。无产品源码/真实科研/模型新增；pin 193项相同，3本机probe不在Git pin。[SPRINT-072](../execution/SPRINT-072.md)。

S071等待经验已独审推送 `49a9274dc243eb311e18eb00615ba873917a11f0`：known反馈绑定原primary，controller_not_started的action/value保持null，final仅当时未测、后续可继续；Memory/目标计划/报告/Workbench接入，项目漂移拒绝。旧工程原件只读；固定版23相关/独审4及真实浏览器两种导入+同ID恢复通过，旧版相关59；真实研究/模型未新增。源码pin 49a9274 196项匹配。[SPRINT-071](../execution/SPRINT-071.md)。

S070修复Workbench拒绝staged v1/v2/v3和错误Ridge卡片，代码推送 `dd7cf66cefe1940d96c08e5e7e7a7388a9439301`；真实Chromium+原后端独立目标导入三版本、原字节与同ID重启恢复通过，加载期间禁用、unknown/单臂与安全文本正确。旧Ridge/CPU独审仅预览；原研究48文件/claim不变，工程目标工具0。隔离构建四产物字节同，pin dd7cf66 238项匹配。[SPRINT-070](../execution/SPRINT-070.md)。

S069可选v3外层比较经验已独审并推送 `5d091b16e45b5b172bf8bee1dc8cbd05c78eccc9`：只对固定S067回源核验后进入Memory/计划/报告，BM25/BM25保留unknown；外层规则是操作者规则，离线不能证明原始绑定和锚前快照。40相关/独审7、旧v1/v2摘要与报告逐字节一致；目标工具used0，原48文件/claim和3/3预算不变。源码pin 5d091b1 的192文件匹配冻结；[SPRINT-069](../execution/SPRINT-069.md)。S068 v2接入见[SPRINT-068](../execution/SPRINT-068.md)。

S067已完成一次真实BoolQ对照并独审：源码pin `5bd9883dd435a1d39b857a51bb6f4d20a53f156b`，project `project-dc1b1b59889f49c0b744254b1a1afd68` / run `run-276475c33d7542509c840bc575005271`；验证集R20差0、MRR差−.023367，A/B均选BM25，final 200题BM25 R20 .97/MRR .858728，双规则比较unknown、TFIDF反事实未测。3/3工具、0model/fit，原ID恢复与48文件相同；公开源/标签曾读取，不盲测、不宣称迁移收益。[SPRINT-067](../execution/SPRINT-067.md)。

S066已完成独审，本提交保存结果：真实S065的事前条件、validation正面和final MRR/nDCG下降已捕获为独立v2 Memory case `s065-hotpot-support-history`，导入工程目标Project并供原计划context；target工具limit1/used0、model/fit/evidence 0，原S065 42文件/claim和3/3预算不变。离线需回源核audit/final，完整bundle/plan留本地；非模型采纳或迁移收益。[SPRINT-066](../execution/SPRINT-066.md)。

S065已按已发布 `5d431097f3b4846ac240745121e56070edd78e86` 和原claim真实完成一次Hotpot支持文档检索：validation R20 +.01/MRR +.0085595/留一最小 +.0050505，事前条件met→原audit→TFIDF；final支持文档R20 .91→.92，但MRR .865984→.830095、nDCG下降。3/3原工具、0model/fit，原ID新进程resume响应及42文件字节相同；费用/token unknown。原project `project-2376ca4a6db64027a1099bd737ca9640` / run `run-a1a631efa41541e2800b43ae047c4c66`，唯一workspace `/workspace/development-continuation-20261114/source-pins/5d43109/runs/s065-hotpot-support-v1`，summary SHA a0eff1bf71981b4a41774e70fcf2fa5aedd0f4c9e421ff250c2bfa52048edcb3。真实实验独立验收已完成；最终是覆盖提升/排名下降的取舍，不宣称整体科研收益或盲测，原语料/报告只留本地。[输入](../execution/g5-local/hotpot-prepared-input.json)。S066已只读捕获这次真实负结果至原生Memory，未重开3/3。

S064经验v2已完成独立验证并推送5e397b2693f2385f26e203af12e7f3f02c6d2507：原事前登记/反馈/audit/freeze/final聚合沿现有Memory绑定目标Project/计划，保留负结果；55相关/独审3+两个目标子例通过，合成原件源状态预算保持，原100文件保持，offline必须回源核原策略及最终聚合。未调用模型/新科研，见[SPRINT-064](../execution/SPRINT-064.md)。

S063已完成固定验证并推送a7f6284cd648e875f2fa309219cfd29e5242706e：新holdout显式事前feedback映射实际控制原freeze选臂，unknown/wait与错误audit不得绕过；专项11/相关92及独审通过，两个合成case正确TFIDF/BM25并原ID新进程恢复，原100文件与v1反馈字节保持。v2经验捕获明确拒绝；无新模型/真实研究收益。[S063](../execution/SPRINT-063.md)。

S062已完成固定验证并推送8090aa7191b3cff8132edd6dcff7e9309ba90e62：staged事前双指标可选单题留一条件，未知整体等待，旧v1/v2及原freeze不变；47相关、5独审，两组实际合成HTTP及异PID原body重放通过，隔离对照中两mean通过但LOO失败正确wait；100原文件未改。见[SPRINT-062](../execution/SPRINT-062.md)。

本轮S061已完成独立验证并推送777f92acaf08ee0c695d94cfd97d70706b308d71：显式plan材料staged_validation_stability供原validation双指标胜负平与单题留一聚合；42相关/5独审、两原案只读对照S060一致，旧freeze/预算和CODE_CHANGED保持。无新模型或科研行动；精确scope见[SPRINT-061](../execution/SPRINT-061.md)。

目标是事前问题/假设→真实实验→反馈→下一决定→原ID恢复。三小时只对齐与汇报，不假称轮间常驻模型。本轮北京时间2026-11-15 07:44:27开始，连续完成S059/S060，精确起止/失败/范围见[最新报告](latest-report.json)。

## 本轮已完成

S059产品/合同 **030af51c4ff06813d08a5f75610dea9f6573ad26** 已推main并回读。新staged-only事前conditions恰2不同validation paired指标，合成AND，单一原primary校验summary供两值，任一未知则整体unknown等待；旧scalar v1不变，新registration/context-v2及混合staged记录明确。原Source/SQL/父子/ID/预算门不放松，S052 freeze仍原Recall20，非全局多目标优化。49相关/6独审纯机制、3真实工程HTTP及新进程原body响应/状态/预算/公开文件精确重放通过，原S054 v1反馈/notice/state/budget旧新进程字节相同。fixed191源SHA4903d279ad6a31045de7b1ec4090cdd29cc67dbfa73c501e050d075d853c98dd/corea05f668cb8de230b134ab4e0394c17297b7aa5cd026c378172bce2001325b4b5；初源兼容微差和HTTP夹具拒绝原件保留。[合同](../hypothesis-feedback.md#显式双指标联合条件s059)。

S060脚本/固定事后方案 **4e17a63af164cd8d0cb49a1e5a3feae458df459d** 在实际计算前推送。原S046/S054各100validation题、R20/MRR两项共400对+400留一均值全量独算通过，3算术边界通过。S054 R20+.01是1胜/0负/99平，移除一题归零；MRR−.00690476为7胜/10负/83平，一题移除可反号。S046 R20−.01是0/1/99，移除一题归零；MRR−.0355556为1/12/87，所有单题移除后仍负。不是新实验/盲确认/总体显著或跨cohort因果收益；没有p/CI，原研究strict freeze未改。[精确输入/分析](../execution/g5-local/saved-validation-stability-results.json)。原输出SHA9c4d2d8bc1297856b89317e4f279cca030f756e3e5e1635ab3d98bece06e7d38留ignored runs/s060-verification。分析reader核public dev+validation、只输出validation，private/final/非primary/Host/执行/写入哨兵；全case完整性hash在guard外读private字节，范围不混。

0新科研project/action/model/fit/rank/score，S059合成HTTP3/1/0工具另计，开发token/费用unknown，工程全dispatch未独立计。原S04636/S05017/S05447共100文件全同，科研预算/永久claim不改。

## 恢复与边界

源码repo /workspace/development-continuation-20261114/auto-research-agentarts，origin open-agent-power/auto-research-agentarts；旧/workspace/auto-research-agentarts、原云盘/参考8库不可见，原全局executorunknown，不重建历史。S054实际研究producer/sourcepin f23de20fb2cfe0cb3ff04117cefc8a8f394186f4，workspace /workspace/development-continuation-20261114/source-pins/f23de20/runs/s054-squad-train-conditional-v1，project-e5200655762d4ae6abca80cfddcf1e3d/run-7f74b125d1ad443e96bbf0f81f0165d9；原core300421…保持，3/3预算满，只原pin --resume已完成只读，无deadline重置，旧CODE_CHANGED执行门保持。S046原pin4a159a9e5a0142c3a69a091aaf1e9a9c110b7be0/3工具/negative保留。旧原50fit及S0353逻辑委派/2工具不重开。

S050仍pin29564822df9705021753a2ad79c156b96fd0d8b1/17文件、prepare b2a2d3fe880e8dffdeb142bdc4a5495e862994b445eb59d1c13301070b7b9e2f。新增一次模型请求仍pending，无approval/launch/Hostgrant，禁止execute，不套S035旧批准。S058前轮本地27816933B/123成员ZIP SHA1c1df555a0a6e3f96b0a73a9d2f8bd22efffe83b0b81b83479bea84412cfedd6已核；GitHub附件07:11上传401/同draft445432218/assets0，远端未交付，本轮无新证据未重试。普通Git/API可用不等于uploads权限。

AAW02e72e3e411bec53db2288651df01afb27d8904d/v0.3.1远端仍同、7安装文件再次同hash，dev-system归档。本轮复用root/engineering/capability_review三人，后两均已交回，无活跃分派，无新增成员/livehook/原生挂载或工具隔离声明。owner root-g5-continuation-20261115T0744提交推送后release，实际receipt runs/s060-closing/lease-release.json；下轮实查guard，永久study claim保留。

下一优先真实模型反馈选择/计划修订，须S050已有申请明确批准；继续独立零模型工作不改旧fullbudget、协议或最终集。附件需新凭据证据后官方上传+下载核SHA。下次计划2026-11-15 10:47:27+08，平台完成/投递unknown。受信local，不声称OS/sealed/RSI完整Gates。

本轮源码pin `/workspace/development-continuation-20261114/source-pins/4e17a63` 为clean detached 4e17a63af164cd8d0cb49a1e5a3feae458df459d，191源与原reader freeze相同；数据仍在原case路径，源pin不等于整套环境已可移植恢复。

本轮S063源码pin `/workspace/development-continuation-20261114/source-pins/a7f6284` 含191源码+1专项，与fixed freeze逐项同；继续S064评估v2结果能否版本化保存在原Memory并绑定下个计划，当前尚未通过。

S064源码pin `/workspace/development-continuation-20261114/source-pins/5e397b2` 与191源码+2test固定清单同，旧研究未迁移。此后S065真实CPU研究和S066经验导入已完成，见文首及对应Sprint。
