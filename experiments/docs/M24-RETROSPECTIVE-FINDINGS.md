# M24 回溯研究 — 四个开放问题的答案（08-21/22 夜）

> 数据源：M22_L0_ghx0（官方 17 轮）与 M24_103x3（GHX 13 批）全量磁盘取证；
> 两个专项 agent 扫描（R7 复发取证 28 次读取；empty_consumed 逐题分类 36 次读取），
> 结论均带 file:line 证据索引（见各 agent 报告原文，本文只收判决与论文级叙述）。

## Q9 · 官方 R7 复发机理 — 判决：环自己换掉了自己的药，且永远没弄明白

机制链（全部有 config/源码 diff 佐证）：

1. R2/R3 的药 = 内建 `StepCountdownProcessor`，其升级文案是无条件强制令
   （"STOP researching NOW: output your FINAL ANSWER…"）——按它自己的 docstring，
   职能就是把濒死任务转成交卷。R3–R6 期间该处理器与 prompt **逐字节未动**（R3↔R6
   config 零功能 diff），budget 败 37→1–5。
2. **R7 的 C-R7-01 在同 hook/同 order(40)/同 singleton_group 把它换成了自制
   `SafeCountdownProcessor`**——为治一个真实的、有 digest 证据的副作用（强制交卷催生
   自信的错答案），把升级文案改成"没证据就再试一次检索，或答 could-not-verify"。
   **管道层完美平替，语义层恰好拆掉了强制函数。**
3. 后果 100% 精准命中预测人群：R7 的 14 个 budget 败**全部**是 R0-R2 的原病灶队列
   （10 个 R3-R6 全绿的当场冷复发），零新增。
4. **环注意到了回归、但归因止步于桶级**：R8 的机械 diff 把 C-R7-01 列为
   joint-suspect 并逼出一个 no_op；但 landscape 把病因写成泛泛的"组合边界"，
   **此后 R9-R16 的九份 decision 再也没提过 StepCountdown 一个字**，换掉的药
   在 config 里原样躺到 R15，budget 败率终生回不到地板。

**论文意义（CH5/CH6 的正反面钉子）**：这正是 GHX 三尺 triage 与 mutation surface
为之而生的场景，在对照臂里自然发生——官方的归因天花板是"哪个 ship 可疑"（桶级），
而定位真凶需要 **节点级 mutation surface（`step_countdown` 节点被 mutated）+
锥归属（14 个回归全在该节点的锥内）+ 包络判决（14 >> 9.3±2.2 = EXCESS）**——
GHX 的机器会给出 kill/rollback 判决；官方给出的是一个方向错误的 config-knob 建议。
另一层对称性：官方的强制交卷药有幻觉副作用（他们为此换药致复发）；GHX 的同族药
CommitBand 有同样的副作用（24 题 cohort 里 17 题变成"按时交卷但答错"）——差别是
**GHX 的 M2-on-pass 泄漏旗逐轮计量这个副作用**（17→21），换药与否可以带着数据决策。

## Q10 · GHX 零的持久性 — 修正后的诚实结论

R7 取证抬高了持久性的证明门槛：官方的药也曾干净整整 4 轮，然后**被环自己的下一次
编辑**打破。GHX 现有 3 批零（R10-12），数量上还不如官方的蜜月期长。但两个结构性
差异改变了风险构成：

- 官方复发的机制（后续 ship 静默换掉药节点）在 GHX 域内**被两道机器拦截**：
  mutation surface 会把 same-slot 替换报为 `nodes_mutated`（scope 门 modify 路径 +
  锥可达检查），复发发生时三尺 triage 会给出 in-cone EXCESS 判决——这是"防同型复发
  机制在位"的主张，可以写，且有对照臂的反例佐证其必要性。
- 但"药自身衰减/漂移"型复发（非编辑致）仍只有 3 批证据挡着。
- **措辞纪律**：论文只能写"三批保持 + 同型复发的结构性防护在位（对照臂展示了
  无防护的后果）"；"根治"需要 ≥5-7 批延长观测（M25 或 resume 可补）。

## Q11 · IV-11 净值 — 双侧都有数了，判决延后到下一跑

- **成本侧（已量化）**：杀 4 个 Critic-accepted 候选（R2/R11/R12×2 同款死因），
  budget 药迟到 8 轮，期间每轮多扛 24-35 个 budget 败。
- **收益侧（本轮新证据）**：R7 取证展示了**无证据纪律的进化**会发生什么——C-R7-01
  的安全论证（"hard stop 保留了"）真实但不相关，一段错误的等价性主张畅通上车。
  证据门的价值主张（逼真实验证）由此获得对照臂级别的反面教材；但要诚实：拦下
  C-R7-01 那类换药的是 GHX 的 surface/锥机器，不是 IV-11 本身。
- **死锁已拆**：IV-11 之税的结构性根源（旗指向不可表达的 tools 桶）已被 insert_tool
  (33d79b0) 消解。下一跑里若 Evolver 顺旗直接开 tools 药，税自然消失，剩下的
  就是纯收益——**净值问题转为下一跑的实证观察项**。

## Q12 · empty_consumed 残余层 — 逐题分类完毕，药效期望首次有数

R11 队列 24 题全分类（主因）：

| 根因 | 题数 | tools 药可达性 |
|---|---|---|
| (a) Bash/cmd.exe 失配 | **10**（另 5 题作次因，链条在场 ~15/24） | POSIX bash = 单点最高杠杆 |
| (b) 反爬墙/CAPTCHA/403 | 4 | 部分（硬墙 1 题不可达） |
| (c) WebFetch 空返回（无墙） | 4 | 硬化 fetch 可达（含 1 题纯"取到没交给模型"的 surfacing bug：8b3379c0，服务端已拿到 29KB） |
| (d) 视觉/PDF 模态缺失 | 3 | 2 题结构不可达（无视觉通道） |
| (e) 搜索质量 | 2 | 基本不可达（行为面） |
| (f) 其他（格式规则冲突） | 1 | 不可达且属 motif 过度归因 |

**三档判决：洁净可达 10 / 部分可达 9 / 结构不可达 5。** 三轮稳定核 16/24（余下有
进出 churn，R11→R12 队列 +8 超出既测噪声带）。药效期望：POSIX bash（insert_tool
一发）+ 硬化 fetch 若都落地，本层可攻下 10±5 题——**这就是 M25 的主注册预测**。

附带两个方法学发现：① motif 检测器对 2 题过度归因（真死因是格式规则/推理缺陷，
不在检索层）——CH7 的检测器局限一句话；② `dc22a632` 同时携带两个 motif——
motif 非互斥，人口表口径要写明。

## 工程批注（同夜落地，供交叉引用）

批改 #1-#6 全部提交：readers 压缩 c1cc003、单发 digester 缝 4014fdb、cheatsheet
b7b3daa、strategy 人口表 fc8d10c、锚点修复+IV-1b 23185ac、tools 桶 e2e 强制链
（与 insert_tool 33d79b0 同链）。新 flag 四枚：SINGLESHOT_DIGESTER / CHEATSHEET /
STRATEGY_POP / ANCHOR_REPAIR（合计 17 枚）。GHX 套件 225 过。
