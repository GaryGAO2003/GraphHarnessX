# M24_103x3 — SOP 验收（三轮，08-21 01:15–04:23）

判定：**PASS（A–J 运维项全绿；K1–K10 机制项零 a 类 bug）** → 已按 runbook Phase 3a 于 05:36 续跑 R3–R15（`M24_103x3.r3plus.*.log`）。

## 1. 分数与成本

| 轮 | 过题 | 率 | evolve | 批成本 | 备注 |
|----|------|-----|--------|--------|------|
| R0 | 57/103 | 55.3% | baseline | $60.16 | =M22 种子重算值 57；种子池 59.6±3.58 内（−1.2σ） |
| R1 | 61/103 | 59.2% | ok（C-R1-01 上车） | $53.02 | +4 在 ±4-5 噪声内 |
| R2 | 59/103 | 57.3% | noop（IV-11 held） | $53.69 | −2 噪声 |

分层：L1 28→31→33（单调升）、L2 24→27→23、L3 5→3→3。
成本总账 ≈ **$358**（批 $166.87 + meta R1 $83.3 + meta R2 $108.0）。Stage P 稳定 $56±1/轮。
**16 轮外推 ≈ $2.2–2.4k 全程（剩余 ≈ $1.9k）** — 高于验收前口头报的 ~$1k，纪律=只记录不阻断。

## 2. 机制事件账（本轮的论文素材）

- **C-R1-01 = EmptyResultGuider（processor，图编辑 insert_node×1）**：manifest 引用 facts.md lift 表（`tool:WebSearch#empty` 0/57 恒败）、33/46 budget_no_commit、轨迹步级锚点；**刻意不动 Bash-empty，因 22 个通过任务的锥含它**（锥数据防误伤）。预测 1 题命中 1/1；scope 门判 additive/pop=0/predicted 1<6 → **sub_resolution 注记生效**（床级曲线主张出局，只按预测题记账）。
- **门重放首燃**：存在门无现成 U → 重放 task 7673d772 → U 产出（R0/sessions/gatereplay/R1-C-R1-01/），`proc:empty_result_guider` 64 次调用 ≥ floor 1 → direct。双形态别名（`proc:empty_result_guider` + `proc:py::_empty_result_guider`）工作。
- **归因判别护栏首燃**：ship 的 signature 在抽样非预测任务上也全燃（after_tool 全钩子处理器）→ vacuous presence → 账本评 **joint** 并写明理由。存在门的 direct（机制确实运行）与归因的 joint（在场≠判别）分层正确 = M5 层级落地。
- **三尺 triage 首个实战读数**：R1→R2 硬回归 7 个，统计尺 7 < 9.3±2.2 包络内；锥尺 in-cone **0**/7；streak 尺全部 streak=1 swinger。**Critic 的 decision.md 逐条引用三尺**得出"无回归义务阻断 shipping"——R16 式 governance-kills-medicine 在本轮结构上不可能发生。
- **R2 noop 的真相：IV-11 承诺门 held**。Evolver R2 弃攻 Planner 旗标的 tools/config（Bash-shell 失配）方向、另提 C-R2-01（StepCountdownProcessor，正是 M22 一次性 +7.4pp 的机制本体，瞄准 budget_no_commit×33）；Critic accept；但 vendored IV-11 要求"旗标方向不可行"必须附具体工具输出证据，宣言节太短 → **确定性门推翻 Critic，candidate held**（`applied/_C-R2-01_held/`）→ noop_streak=1。guidance 缝把拒绝文本路由进 `R2/graph_evidence/gate_refusals.md`（下轮 Evolver 头号读物）。**对症药死于证据纪律门 = 治理 vs 药的新形态**，R3+ 看环是否按 refusal 指引复活它。
- **population→Planner 接线实证**：R2 landscape.md 按名引用 population.md 并用 `budget_no_commit ×33`、`empty_consumed ×40`、20 个 M2-on-pass 泄漏旗做结构性论证。
- **103 床 motif 人口（论文级）**：empty_consumed 43→40（~40% 任务消费空结果）、budget_no_commit 33→33（32% 预算死亡无提交）、ungrounded_commit 5→2；M2-on-pass 泄漏旗 17→20（≈28-33% 的过题）。审计器独立重算与环内 population.md **逐数吻合**。
- **锚点引用率（IV-1 口径）**：R1 20/103、R2 19/103 ≈ **19%**（官方历史 7-8%，30×5 时 10-17%）。

## 3. 日志全扫账（E 项，零条未解释）

| 类 | 次数 | 定性 |
|----|------|------|
| 网关 API 重试（504 等） | 29 | 瞬态，自愈 |
| Bing scrape failed | 23 | 既知床噪声 |
| Wikipedia 403 | ~15 | 既知 UA 摩擦，任务自动退避 serper |
| digest 断锚（IV-1 抓获） | 9+1 | **digester 写字面 `...` 省略路径 / 行号越界 / 零锚**，校验器按设计打旗；b 类 |
| Critic verdict IV-4 失败 | 3（R1×2, R2×1） | Critic 引用 repo 源码路径当锚；advisory 计数，adoption 走独立 decision.md；b 类 |
| `Event loop is closed` ×4 + unclosed session ×3 | 7 | 门重放 fresh loop 收尾的 httpx aclose 孤儿；重放结果无损；**修复排队** |
| ResourceWarning unclosed file | 大量 | vendored trace_facts.py:292 + ghx projection.py:183 迭代习惯；**修复排队**（projection 侧） |
| 退出挂起（新发现） | 1 | 某 rollout 的 shell 子进程（pid 33068）未退出 → 阻塞 executor 线程 → atexit join 卡死解释器；数据无损，人工杀树收场；**修复排队**（launcher 收尾杀子进程树） |
| WKD v5.3 兼容 note（resume 时） | 1 | 快照层既知良性提示 |

## 4. 已知缺口与修复队列（下个改码窗口，均非阻断）

1. launcher 收尾杀存活子进程树（修退出挂起）。
2. gate-replay runner 返回前显式 aclose provider httpx 客户端（修 teardown 噪声）。
3. projection.py `with path.open()`（修 ResourceWarning 刷屏）。
4. shadow_projection_audit 的 sequence/payload 腿适配 Layer A′ 表（现 digest 行=0，两腿失效；motif 腿正常）。
5. **resume 跳过首轮 meta**（vendored）：R3 直接开批，batch 2 永不被 digest/evolve，且 curves 把 R3 标 `evolve_status=ok`（实为 R1 配置的直跑）。分析时 R3 按"noop 批"读；如再有 resume，同款折扣。
6. K9 已闭合（08-21 下午）：M22 audit.jsonl 实测 Stage P $34–59/轮（中位 ~43）vs M24 $41–77（中位 ~53）≈ **+25%**，且 M24 侧震荡非单调涨。

## 4b. 已批改进队列（用户 08-21 下午批，跑完后与修复一起做）

- **[已落地 33d79b0] tools 桶编辑面**（用户 08-21 晚批）：insert_tool/remove_tool 图操作（作用 tool_registry.custom，genotype 不动，file-URI 手写工具带 import 预检）；core 加载器同名 custom **覆盖**内建（POSIX Bash 顶 cmd.exe Bash 的形态）；surface 以 `tool:<name>` 节点进 nodes_added/removed（scope 门/锥检直接生效）。6 新测试，全套 2551 过。**IV-11 死锁的结构性解**：环从此能顺着 tools 旗直接开药。
- **[复现已证] 单发 digester**：S1/S2/S3 三独立轮 ×0.114/×0.112/×0.112，单任务带宽中位 9%；fm 标签自一致 14-15/40 与 agentic 天花板同值=标签不稳是模型属性非循环形态属性。**余下工作=活体缝**（`HARNESSX_GHX_SINGLESHOT_DIGESTER` patch `preprocess._run_digester`，按 k/轨迹长度自动分流回退 agentic——agentic 的设计动机=k>1 跨 rollout grep（digester.py 注释原文），我们 k=1 全程闲置）。
- **[论文侧核实，2606.14249 v1-v3 逐字检索]**：论文**从未说明 digester 的内部机制**（agentic 还是单发——两种措辞全文零出现），只说其职能是"compresses traces"（§4.3：~10M 原始轨迹 token → ~10K 结构化摘要，理由=上下文限制+朴素截断丢信号）；**全文无逐角色成本分账**；唯一相关消融（§6.4）把 AEGIS 相对单会话进化器省的 ~12-14% token **归功于 digester 的压缩**，却从未计入压缩自身的开销。**定位修正（用户 08-21 深夜点破）：论文的 10M/轮是 pass@2 制（§4.3 原文），折 ~97K token/题；我们 pass@1 床实测 ~16K/题——压缩压力差 6 倍。** 故主张不是"改进官方效率论证"，而是 **Stage P 的 pass@1 adaption**：官方 agentic 形态为 pass@2 跨 rollout 分析设计（该场景下单发一次 ~100K 逼近失中率，agentic 有实辩护）；pass@1 制下该能力结构性闲置，单发特化五重验证无损、×0.11；活体缝按 k/轨迹长度自动分流，k≥2 或超窗回退官方形态。符合 F2 搬运句式。agentic 的成文理由只在 vendored 代码注释（论文未说明机制，"Stage P" 亦是本仓局部命名）；引用纪律：不得把 "agentic digester" 归为论文主张。我方内部对比全程 pass@1（种子 57 重算同口径），不受影响。
- **[质量五重验证毕，08-21 深夜]** ①代理指标持平 ②三轮复现 ③**vendored IV-1 校验器：S 38-39/40 > A 35/40** ④**乱序双盲评审（pro 判官、facts 为基准、40 对，$1.9）：S 胜 25 / A 胜 15 / 平 0**（p≈0.08 方向利 S）⑤**vendored aggregate 下游腿：两臂产出逐字一致**（actionability 1.0 同 reason、pattern 计数同）。结论从"不劣"升格为"**不劣且方向占优**"；仅剩环内影子轮（Planner/Evolver 消费面）未测。

- **[批] Evolver 图面 cheatsheet + 验证模板库**：一页 GraphProposal op schema + insert_node/mutate_params 成例 + `_verify.py` 模板 + 上轮成功 manifest 证据节样例（guidance 缝路由）。目标：杀掉每轮重付的 `_gp_inspect×10` 学习成本，减少 400 步撞顶。
- **[批] result_readers 列压缩**：`t102,t177,…` 全列 → `readers=N(first→last) final=yes/no`。
- **[已测·否决] digester 输入截断**（08-21 傍晚，n=8 对照 + 8 试点 + 40 主样本，~$81）：v2 规则（system 头 8KB、schema 折叠、结果 2KB 帽）砍掉 31.5% 字符，但 **token 中位数仅 −8.8%、均值 +14.6%、符号检验不显著（B<A 23/40）**——收益被 digester 智能体循环的自身方差淹没（对照组：同输入两跑 token 差 2×、failure_mode 自一致 6/8、strategy 标签自一致 0/6）。质量面根因叙述保住但 B 臂省略号锚 15 vs A 3。**结论：截断不是有效杠杆；真杠杆是循环形态（单发 digester，文件内容只付一次，估 3-5×）**，列新候选、需动 vendored `_run_digester`、复用本实验的 48 对数据与 `digester_truncation_ab.py` 指标做质量验证。附带产出：digester 自复现噪声地板（±25%/2×、标签不稳定）= 论文可用校准值。
- **[已测·通过] 单发 digester**（08-21 晚，40 对全量 vs agentic A 臂，$7.5）：**token ×0.11、成本 ×0.18、40/40 同向**（符号检验 p≈2e-12），比值带宽 0.08–0.21（agentic 自方差 0.58–1.97 消失）；质量与 agentic 不可区分——failure_mode 一致 14/40 恰等于 agentic 自一致 13/39 天花板、锚点 462 vs 443、根因关键词 832 vs 857、零错误。**Stage P $55/轮 → ~$11/轮，16 轮省 ~$550**。落地形态：GHX 缝 patch `preprocess._run_digester`（单发版，flag 门控 `HARNESSX_GHX_SINGLESHOT_DIGESTER`），vendored 零改动；脚本=`experiments/analysis/digester_singleshot_ab.py`。待令实施。
- **[候选] 锚点自动修复**：IV-1 遇 digester 写的 `..._r0.jsonl` 缩写路径时按 digest 文件名还原全路径（修复而非打旗），零 LLM。
- **[候选] IV-1b 语义抽核**：锚点 snippet 与被锚行做字符串比对（"指针有效"→"内容有据"，回应 Onweller 2026）。
- **[候选] strategy 人口表（pass 侧对偶）**：vendored `digester_all_pass` 逐题萃取 `strategy:` 标签但**零消费**（aggregate/planner 均不读，又一"只写不读"）；建确定性 strategy→任务数→跨轮存活表喂 Planner/Evolver，成功路径固化 + 为日后瘦身 pass 侧重复 digest 铺路。分层 digest 提案（原省钱方案 1）改为在此库建成后再做，避免砍掉成功路径萃取。

## 5. 续跑参数（在飞）

R3–R15，同目录同 13 flags，`--start-round 3 --num-rounds 16 --no-early-stop`；日志 `M24_103x3.r3plus.{out,err}.log`；shim 4660 / worker 9604；监视器 b6d7316fd（事件流）+ b52cbntnb（退出/卡死哨兵，75min 阈）。预计 ~9-10h（≈15:00-16:00 收官），观察项：环对 gate_refusals.md 的响应（StepCountdown 复活 or 攻 shell 失配方向）、R8 前是否 ship 出 M2/M3a 对症药（只记录）。
