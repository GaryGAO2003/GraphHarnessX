# M24/M25/M26 Runbook

> **08-24 晚 · 第三道探针收官(c8b7e059,单战役记忆版)= F30 + 错 15**:用户令"就用 M26 的"→档案砍到 10 次尝试,环照样 ship(processor 桶 steer,IV-4 咬一口后重试过关,污染 0)。**错 15(用户抓出)**:试药步帽 40 vs 战役 20——三次"对照臂暴热"(F26/F28/DOSSIER4-40cap)全是它,F28"手气"归因作废;鳄鱼题(答错型)不受影响反成对照。**战役同帽重跑(20 步、并发 15 错峰、20/20 真完成)**:父 2/10(=16% 底率,保真恢复)vs 修复 5/10;**按触发归因 +3 不算药的**——药触发的 3 rep 全挂(触发条件=死亡签名,选择效应),过题 5 rep 零触发。**步帽敏感性副产品:同日同配置 40 步 7/10 vs 20 步 2/10——此题一半失败是步数饥饿,最大杠杆在环作用域外**。SOP:试药必须逐项复刻战役任务参数(--max-steps!);对照臂异常热先查参数保真。

> **08-24 傍晚 · 低通过率题全流程重走(48eb8242,12% 底率)= F29(数字为串行补跑修正版)**:档案(58 attempts)→环净跑 ship 单件 `NASSpeciesQuery`(USGS NAS API v2 通用封装;**门全过**,0 污染)→试药首轮 10×10 被并发突刺污染:**8/20 rep 起飞 ≤1 秒即死被 `_run_task` 吞成 f,另有空 end_turn 幻影跑(2 秒 5 步 0 消息 exit=done)= 错 14**(用户一句"你确定不是设置有问题"抓出)。串行补跑(并发 1、间隔 2s,12/12 真完成)后按真完成计:**父 1/11(9.1%≈历史底率)vs 修复 0/12**。修复臂 11 个有答案 rep **全部答 7**(科级查全:niloticus 6+moreletii 1;NAS 全采用、WF 8→0);父臂散答 6/7/70/77/79(口径彩票),唯一过题 rep 原话 "the ONLY nonindigenous crocodile species…is the Nile Crocodile"——**=标注员同款漏点**。金标 6 已三层存档钉死为**标注执行错**(`nas_gold_archaeology.py` 一键重放):标注员自述流程(枚举每个叫 crocodile 的物种)忠实执行=7;2023-03 列表存档明列 Morelet's Crocodile;2022-08 其 CollectionInfo 存档已含 FL/2018 行(Specimen 1634169=今日 API 同条,无漂移)。⇒ **药治的病恰是过题的路:完备性把 ~9–12% 彩票通道关死成 0%,此题上过程质量与判分负相关**。与 851e570a(F27/F28,药对且门杀)对照:**这次门放行,墙=金标执行错**。SOP 新增:**N-rep 试验先数真完成数再报比分**(termination_reason 规则同族)。探针=runs/PROBE_DOSSIER3(PROBEV=首轮/PROBEV2=补跑),判据在 runs 外冻结。

> **08-24 下午 · 证据深度阶梯三连探针(A/B/档案)+ 试药收官**:A=裸孪生→格式药;B=孪生+化验单→病因感知行为药,被桶互斥杀;**档案净跑(判据泄漏事故=错13,隔离重跑后 0 污染)**=851e570a 全史 55 次→Planner 自推双峰律+跨战役持久性,Evolver **自发明 PythonRun 工具**(临时 .py+subprocess shell=False,结构性拆除 cmd 引号层)+steer 重定向,Critic 双接受判 ship→**IV-11/IV-9/IV-4 三门同轮杀双药**(全是战役旧账缺陷)。**替它上车试药 10×10**:分数 10/10 vs 9/10(+1 不显著,对照当日手气 9/10 vs 史上 ~4-5/10);**机制:Bash 中位 53→7、PythonRun 11 次/遍全采用,病灶通道被结构性替换**。台账 F26–F28;隔离区=recipe/gaia_evolver/quarantine_PROBE_*。**终定位:看见✅→记忆推理✅→开对药✅→治理杀药❌;瓶颈=治理形式主义,非感知/理解/处方。**


> **08-24 上午 · 孪生喂食探针(用户令:喂真实分歧轨迹给 AEGIS 环→环开处方→修复跑三遍)**:`runs/PROBE_TWIN7/`。设置=7 道 M26b 最终配置时代同配置摇摆题(3 升 3 降 + 851e570a),每题失败跑=r0/通过跑=r1、真实 flags [False,True] ⇒ **官方 Digester 的 PARTIAL_PASS 模板全项目首次点火**(四场战役全 k=1 从未触发)。纯 vendored 环(官方四角色+门),meta=v4-pro,预算帽 $40。
> **结果:上车 2 件**——C-R1-01(prompt:答案格式规则改为题目特定优先+交卷前格式/证据自检;预测写在 `tasks_will_stabilize` 而非 unlock,**语义正确**)、C-R1-02(config:加 Write/Edit 内置工具,原话"而不是 Windows-cmd python -c 引号地狱")。Planner 自查出 72e110e7/8b3379c0 的通过靠答案泄漏,Critic 核实候选未瞄它们。**诊断为"格式性失败"是孪生对比独有的产出**(纯失败病历从未给出)。
> 验证:`probe_twin_verify.py` 双臂 7×3 独立 session(绕开 pilot k>1 续跑陷阱;base_dir 重写进探针目录防污染归档;re.sub 模板串会吃 Windows 路径反斜杠 → lambda 替换)。在跑。


> **08-24 overnight(论文故事定稿夜)**:①用户令="总结→overnight 论文故事撰写,循环 review 至挑不出问题"。产出=`experiments/docs/thesis/STORY-V3-AUDITED.md`(主轴 V3,**此后各章唯一数字来源**,六轮 review 收敛)+ artifact 同 URL 更新。②**九个审计脚本固化**至 `experiments/analysis/audit_*.py`,全部数字可重算;候选定位 lift 独立复现与 08-23 子代理逐位一致(1.99/1.62/1.04/0.64)。③三个新定版事实:流向列**全臂** NO 75.0%/判用 8.1%(1442 轨迹 11,966 调用;150 条抽样的 68.1% 作废=错 12);**同配置重抽翻转率 20.5%**(824 对,pass@1;M22 八个无 ship 轮对);**重放门真相二次反转**——M26b 确有 7 次 REFUSED("edited but never ran",checked=True,整文件读取定案;我 08-23 深夜的"0 拒全弃权"是把每份文件尾部的图例当判词,此为十二错之 9)。④错误清单 10→12(新增:抽样漂移、k 混用);方向统计利己 7/自贬 3/中性 2。⑤τ² 对照臂 R0=90/114、R1(noop 同配置)=100/114——**τ² 同配置摆动 +10 题**,旁证可靠性主题(不入论文,按用户裁定)。


> **08-23 13:30 转向 τ²（用户令）**：①**GAIA 已停** —— M26b 于 R13 批中途人工停树（shim 35332/worker 11120 全树杀净，两监视器撤）。**有效数据 = R0–R12 共 13 个完整批**，R13 批作废。曲线 56,57ⁿ,61,62ⁿ,59ⁿ,64,62ⁿ,67,64ⁿ,71,67,65ⁿ,68ⁿ；账 $936（批$300+StageP$181+Evolver$329+Critic$72+Planner$53）。②**成本归因终裁**（对照 M22-L0 官方基线 $131/轮 vs M26b $73/轮）：省的 −$58/轮 = 消化器换单发 −$35（**可移植到 HX**）+ noop 轮只跑翻转族 −$21（**纯台账，可移植**）+ 步数下降 −$3（两环都会）；**图那层 +$1.4/轮 = 净贵**。⇒ **成本轴不能作为 GHX 证据**，论文里单列为 harness 工程贡献。③**上限分析**（子代理，13 轮从未过的 14 题逐题判读）：**harness 可修只有 3 题（3pp 上限）**；B 推理 4 / C 编造 6 / D 床坏 1。RARE 队列（≤2 次过）8 题里 5 题是机械故障（Windows 引号 2、缺 OCR 2、WebFetch 403 1）。**Windows cmd 引号环是全数据集第一大机械故障**。④**τ² 环境已修好并 smoke 通过**（见下节）。

## τ² 基线与选床（08-23 晚）

**三域 L0 基线（官方底盘原封不动、`--num-rounds 1` 走 is_last ⇒ 零 meta 成本、k=1）**

| 域 | 基线 | 失败 | 判断 |
|---|---|---|---|
| airline | **44/50 = 88.0%** | 6 | 太简单，出局 |
| retail | **92/114 = 80.7%** | 22 | 可用，空间偏窄 |
| ~~telecom（60 步）~~ | ~~86/114 = 75.4%~~ | ~~28~~ | **作废**，见下 |
| **telecom（200 步）** | **111/114 = 97.4%** | 3 | 放开步数后几乎饱和 |

> 🔴 **选床结论翻转（19:35）**：**retail 才是最难的域（22 题失败），telecom 最简单（3 题）。** 我此前"telecom 公认最难"的说法依据是官方 commit 留言"telecom v3 R2 hit 100% (vs v1/v2 never recovered from R1's 55% crash)"——**那句说的是某个变体演化中途崩了，不是域基线**；我把它读成了域难度，随后自己的 60 步天花板又"印证"了这个结论，**两个错误互相背书**。已验证 retail 22 题与 airline 6 题**全部 `user_stop` 且评分器跑完**，不含步数砍断，两组数干净。
> ⇒ **主床 = retail**。telecom 分支的身份层不作废：它对任何非纯数字 id 的床都必需，对 retail/airline 是无操作（安全 id 原样返回）。

**对照臂在飞**：`C0_retail_L0_5r`（retail 114 题 × 5 轮 × `--ghx-level 0` × 200 步，19:37 起飞，监视器 `bd3vt49h5`）。这一跑同时给：①官方底盘在 τ² 上能否自我改进（官方跑过但从未公开）②每轮 meta 真实成本（双臂预算依据）③GHX 臂将与之做**配对**比较的对照曲线。

> 🔴 **`B3_telecom_L0` 作废（归档为 `B3_telecom_L0_capped60`）**：28 题失败**全部**是 `max_steps` 终止、`reward_breakdown` 为 null——**评分器根本没跑**。原因是仿真步数上限沿用了 retail smoke 的 60，而 telecom 是工作流域（消息数中位 49、最长 66），四分之一的题被拦腰砍断记零分。**那个数不是基线，是我设的天花板。** 已参数化（默认 200 = 官方脚本值），超时同步提到 600 秒（`2b87c26`）。
> **SOP 新增一条**：**任何基线跑，先读 `termination_reason` 分布，再读分数。** 一个全是 `max_steps` 的失败集，测的是操作者，不是 agent。这是 τ² 上抓到的第七个问题，与前六个同族——**我方设置正确、与另一侧的实际形状不符**；前六个是数据形状，这个是参数形状。

**retail 22 题失败的程序化归因**（τ² 的对错由 DB 状态 + 动作检查 + NL 断言判定，不用模型判读）：DB+动作 15 / 只有 NL 3 / DB+动作+NL 2 / 只有动作 1 / 只有 DB 1 ⇒ **19/22 是"该调的写工具没调对"，3/22 是"该说的话没说全"，零题属于"模型不会推理"或"数据源没了"**。对照 GAIA 的 14 题从未过里只有 3 题 harness 可修 ⇒ **可修空间从 3pp 变成 19pp，且性质全部对路**。
**失败高度集中在少数节点**：`cancel_pending_order` 7 题、`exchange_delivered_order_items` 6 题、两个 address 类各 3 题 —— 两个工具占了 13/22。**这正是锥定位需要的地形**（GAIA 上每题坏法都不同，facts.md 自己写"This map carries no information"）。

**噪声与读法（必须写进实验设计）**：n=114、p=0.807 ⇒ 二项 sd=4.2 题，单抽 95% 带 **±8.3 题（±7.2pp）**。按 GAIA 实测 25% 兑换率，22 题 headroom 只买到 **+5.5 题——淹在噪声里**；50% 兑换才 +11 题勉强露头。⇒ **不许比总分，必须配对读（McNemar）**：GHX 修 8 题、打坏 1 题，配对下 p≈0.04 显著，而同一组数据比总分是"分不开"。第二杠杆 k=2（官方 τ² 自己就是 2 trials），臂均值 sd 4.2→3.0 题。**这是 M22–M26 读数纪律缺的一环：换床同时换读法。**

**telecom 身份层（分支 `ghx/tau2-telecom`）**：telecom 114 个 id 全带 Windows 非法字符、最长 215 字符（`[mobile_data_issue]airplane_mode_on|user_abroad_roaming_enabled_off[PERSONA:None]`），而 id 同时是 session 目录名/轨迹名/Stage P 的 raw 文件名/digest 键/账本键 ⇒ 一起飞就 WinError 123。修法：pilot 在记录构建处**一次性规范化**为 slug（清洗+截断 48+全 id 哈希 10），保留 `task_id_full`；τ² 侧的 sim↔task join 用真 id、不受影响（`737baa0`）。
**两个必须成立的性质**：① **slug 幂等**——适配器用真 id 命名 session、解析器用记录里的 slug 推导，两边必须同一目录；原实现不幂等（产出 59 字符 > 截断阈 48 会二次哈希），已修 `af2db86`。② **方括号必须清洗**——Windows 允许，但它是 glob 元字符，`find_task_u` 的模式匹配会把 `[...]` 当字符类而匹配不到任何东西（测试先于跑抓到）。

## τ² 工程（08-23 起，用户令"开始tau2的工程"）

**为什么换床**：官方 AEGIS 唯一成套实验就是 τ²（3 域 × ≤4 模型 × 10 轮 × 2 trials，11 个 `run_aegis_*.sh` —— 我们 `recipe/tau2_evolver/` 里正好 11 个，是 vendored 的官方实验层）；**GAIA 官方零数字**（runner 默认 MAX_TASKS=1 smoke、无 .sh、论文 GAIA 头条靠的变体池机制在发布代码里不存在）。vendored Evolver 模板有硬编码 `benchmark_context == "tau2"` 分支 ⇒ **底盘是照 τ² 长的**。τ² 对错由程序判定（DB 状态 + 动作检查）⇒ 验证墙消失；失败是流程性的 ⇒ harness 有空间。

**环境（已验证可用）**
- 独立 venv `.venv-tau2`（Python 3.12.10，repo `.gitignore` 已含 `.venv*/`）；**`.venv312` 未动**
- `tau2` 1.0.1 从 `C:\Users\Admin\tau2-bench`（`git clone --depth 1 sierra-research/tau2-bench`）editable 安装；data 750M 在 `C:\Users\Admin\tau2-bench\data`
- 补装的 harnessx 依赖：omegaconf hydra-core structlog prompt_toolkit aiofiles html2text anthropic websockets
- **必需环境变量**：`PYTHONUTF8=1`（不设则 runner import 就 GBK 解码崩）、`PYTHONPATH=<repo>`、`TAU2_DATA_DIR=C:\Users\Admin\tau2-bench\data`
- 任务数：airline 50 / retail 114 / telecom 114（`from tau2.runner.helpers import get_tasks` 与 vendored runner 调用签名完全一致）
- 网关合规：全部走 `https://litellm.yangtzeailab.com/v1`。agent=`openai/deepseek-v4-flash`、user-sim=`openai/Qwen3-235B-A22B-Instruct-2507-FP8`、meta=`openai/deepseek-v4-pro`。网关 28 个模型
- **T0 smoke PASS**（`recipe/tau2_evolver/run_t0_smoke.sh`，retail 2 题 1 trial `--num-rounds 1` ⇒ `is_last` 跳过 evolve ⇒ 零 meta 成本）：2/2 过、reward 1.0、DB+5/5 动作检查全绿、27s/题
- **落盘格式天然兼容**：τ² runner 写的 `data/task_history.jsonl` 字段与 GAIA pilot 完全同构（round/task_id/passed/passed_flags/k/exit/steps/cost_usd/tools_used）⇒ flip ledger 与 noop-audit 的翻转族选择可直接读

**已知缺口（待修）**：① `cost_usd` 落 0（LiteLLMProvider 路径不带成本，GAIA 走的是 OpenAIProvider）② `level` 为 null（τ² 无难度分层，按 level 分组的 GHX 代码要容 None）

**GHX 接线（08-23 下午完成，分支 `ghx/tau2-port`，6 commits，2673+ 测试绿）**

接线过程中实测出**两个此前不知道的结构缺口**，都已修好并活体验证：

| 缺口 | 症状（实测） | 修法 | 验证 |
|---|---|---|---|
| ① U 只覆盖**最后一轮**，不是整题 | τ² 一道题多次 `Harness.run()`（每对话轮一次），run_id 由 resume_state 跨轮复用，但 recorder 每次新建 + `write_unfolded` 覆盖写 ⇒ 9 轮的题只剩 13 节点/1 次模型调用 | `recorder_for_run` 按 (session, run) 复用 recorder，旗 `HARNESSX_GHX_UNFOLD_ACCUMULATE`；线程安全 + LRU 封顶。默认关，GAIA 行为不变 | 同一题 **13 节点 → 107 节点 / 9 次模型调用**（`87d31c9`） |
| ② U 里**零工具节点** | τ² 的工具由域执行（`interrupt_on` 拦截），runloop 的工具位从不点火 ⇒ 所有锥签名全同、`consecutive_empty` 谓词永不可能触发 | `harnessx/ghx/external_tools.py::ExternalToolBridge`——读回灌的 `role=tool` 消息，按同一套 `tool:<name>` 节点 id 和同一套 outcome 词汇（`payload_is_empty`）记进 U；**不造控制边**（桥接的工具跑在别的进程，没有 before_tool 可连，造边等于伪造因果） | 单题 **6 个工具节点**、名字+outcome 正确、与账本 5 种工具吻合（`b930e27`） |

**另外三件**：③ session 命名——τ² 无 rollout 调用点可捕获 run_id，改由适配器把 session 命名为 `{轮}-{task_id}`（GAIA 同形），`harnessx/ghx/tau2_layout.py` 按目录解析；缺失一律返回 None（unavailable，绝不当空图）（`d9cc144`）。④ **共用化重构**：overlay 路由器 + 两个组合代理 → `harnessx/ghx/round_router.py`；阶梯表 → `harnessx/ghx/ladder.py`；`ever_passed` 彩票过滤器同迁。**两张床跑同一个路由器、同一张阶梯表**——这句话本身就是泛化证据（`e5dc910`/`0fd05a6`）。⑤ 启动器 `recipe/tau2_evolver/run_meta_aegis_ghx.py`（GAIA 版的 1/10 大小，只剩床相关的一半；`--ghx-level 0` = 对照臂，与处理臂同一个二进制）+ 6 个测试（`c028d2a`）。

**首次真跑（T5_ghx2，retail 15×2×L2）**：**两轮全完成**，R0 13/15、R1 14/15。AEGIS 四角色在 τ² 上全套跑通（digests/Planner/Evolver/Critic/门）。Critic 判决书质量高：点名任务 5"编造每单一次操作规则"、任务 8"未确认就触发一次性破坏工具"，并**读锥后自己判定"无区分性节点(overlap 1.0)，故提示词才是正确杠杆"**。

**由此抓到第三个缺口（真跑才暴露）**：桥接的工具节点**无边 ⇒ 每张锥都看不见它**（锥是从终点反向可达）。我原先坚持"不造控制边"是对的，但代价是节点隐形。正解在 U 自带的 M12 消息面：**工具是结果消息的作者，下一次模型调用读它**——记一条 `log_message_access(write)`，"工具→模型"数据边由到达定义分析自动生成（runloop 自己的工具位就是这么做的）。不是造边，是记录一条本来就被观测到、只是从没声明过的关系。修复 `740a34c`。**活体验证（T6_edges）**：失败题的锥现在带 5 个工具节点，且与通过题差一个 `tool:get_user_details`；对照 T5 的 facts.md 原话是"**This map carries no information**"。

**τ² vs GAIA 的轮目录语义不同（重要，未修）**：GAIA 是 `R{n}/trajectories` 装 batch n−1（有偏移）；**τ² 没有偏移**，`R{n}/trajectories` 就是第 n 轮自己的 rollout（实测 T5：R0/trajectories=15 题）。启动器算的 `rollout_round = round_n − 1` 是对的（pilot 用 `R{round_idx}/raw` 去 evolve `round_n=round_idx+1`，活体锥落在正确的失败题上）；但**任何自己从轨迹路径推轮号的缝**（Layer A 的 `R{n}→R{n-1}`、attribution 回填的账本 join）在 τ² 上会连错轮。⇒ **τ² 暂只跑到 L2**，L6 那组缝需要按床区分布局后才可信。

**第四、五、六个缺口（T6/T7 digest 一眼看出，单元测试永远抓不到——单元是对的，契约是跟一份 byte-frozen 的读者签的）**

| # | 症状 | 根因 | 修复 |
|---|---|---|---|
| ④ | 轨迹里**用户回话 8 缺 6、工具结果 0 条** | journal 只记 `run()` 内部；环境的半边发生在两次 run 之间，journal 从没见过 | `harnessx/ghx/tau2_trace.py` 与 τ² 自己的完整记录合并（两边对 agent 轮次的顺序一致 ⇒ 那就是缝）。**保留 journal 独有事件**（步界、注入的 steer）——直接换成 τ² 视图会抹掉 GHX 最在乎的记录。活体：用户 2→8、工具 0→6、记录 22→34（`e1d80e9`） |
| ⑤ | Layer A 表里每条工具都是 `return_type=missing / len=0` | vendored `trace_facts.py` 按 **`raw_tool`** 建工具结果索引，我发的是 `tool` | 改发 `raw_tool`（`3b48d56`） |
| ⑥ | 每份 τ² 轨迹都报 **`interrupted / 0 steps`** | 抽取器取**第一条** `episode_end`；适配器每轮调一次 `run()` ⇒ 九条，第一条正是 interrupted | 把每轮的 end 收敛成真正结束的那一条，`total_steps` 按轮求和（对观测值做算术，不是新主张），并钉在文件末尾（`3b48d56`） |

**方法论教训（值得写进论文的工程章）**：τ² 港口的六个缺口**没有一个是单元测试能抓的**——每一个都是"我方代码正确、但与另一侧的形状契约不符"，而另一侧要么是 byte-frozen 的 vendored 读者，要么是基准自己的运行时。抓到它们的全是**真跑产物的肉眼审查**（U 的节点数、facts.md 的自述、digest 表里的 missing、Critic 的否决理由）。⇒ 新床接入的 SOP 必须包含"读第一批产物"，不能只看绿灯。

**τ² 特有的候选陷阱（IV-9）**：τ² 注入自己的 23K 域策略且配置用 `NullSystemPromptBuilder`（vendored 模板硬禁替换），所以**改提示词只能靠一个 .py 处理器**——但 prompt 桶只允许 .md/.yaml ⇒ T5、T6 的 `C-R1-01` 都是 prompt 桶带 .py，两次都死在 IV-9 桶文件不匹配。正解是环该报 processor 桶；`gate_refusals.md` 会把死因回灌（P-19），后续轮应自行纠正——**这条正好可以当"门的反馈是否有效"的观察项**。

**已知缺口（未修）**：① `cost_usd` 落 0（LiteLLMProvider 路径不带成本核算，GAIA 走 OpenAIProvider）② `level` 为 null（τ² 无难度分层）③ noop-audit / flip ledger 未移植（都读 `data/task_history.jsonl`，字段已同构，移植成本低）④ 一次 rollout 在网关卡死 10 分钟无上限 ⇒ smoke/正式跑都已加 `--sim-timeout`。

> **在飞（08-23 02:30 起，b 航）**：`M26_100x16b` 全程 16 轮，无像素 100 题床。HEAD=7af672c。shim 35332/worker 11120，日志 `runs/M26_100x16b.{out,err}.log`。
> **b 航中程（08-23 10:50 记，R11 meta 在飞）**：曲线 R0–R10 = 56, 57ⁿ, 61, 62ⁿ, 59ⁿ, 64, 62ⁿ, 67, 64ⁿ, 71, **67**（ⁿ=noop-scoped）。ship 六件：R2×3（prompt/processor/tools）、R5 processor、R9 tools、R10 config=**C-R10-01 consecutive-empty-steer（环史首条在跑策略规则）**。账：批$280+meta$463=$743。R1 首 noop carried 账当场审过（75 carried、分数==R0、steps=0）。R6 批中一次 `Invalid \uXXXX` 崩（344 盘上工件全扫干净=瞬态模型响应），tripwire=第二次即停修。**R10 首读（规则条件面，离线）**：live 19 fire/10 题（7 题打满 max_fires=2）；4 慢性过题被擦到全过=零误伤；4 慢性挂题零转化（fired 队列 6/10 vs 同队列 R9 7/10、R7 6/10）；71→67 的 −4 分解=fired −1 / 非 fired −3，即回落主体与规则无关（R11 三尺若回滚此规则，此账为对照）。样本 a7feb290：steer 后模型**立即换命令类**（服从）但新类引号仍炸，countdown 压顶后原样编造"My check found 0 papers"（未跑过的检查）——**anti-guess 句输给 step-countdown 的 MUST**，= 验证墙+countdown 冲突的单轨全证。851e570a（1/10 慢挂）R10 过但 R9 已先过（credit 归 C-R9-01 为主）。剩 R11–R15，ETA ~17:00–19:00；收官走 M26 终局验收（P1 负/P2 达成于 R10、fired-cohort 账、countdown-截断伤害检查、IV-11 鞭打账、成本书）。
> **a 航事故（02:16 R1 meta 崩，已修复弃航）**：scope 门首次活体拒绝触发双 bug——①拒绝路径写 dict 进 gate_results，vendored audit（orchestrator.py:699）对每值做 `.ok` → AttributeError 崩掉 evolve；②拒的对象恰是环第一条 runtime-policy 规则填充（C-R1-02，empty3+search5 双规则、离线重放 fired-set 已算），拒因"目标节点 0 败锥"= 0332fd9"按改了什么记账"的必然副作用：**空表引擎不改事件→不进 U→永远 0 锥→armed 候选被判结构性无能**（死锁）。修复 `7af672c`：拒绝条目改对象；population=0 降级为 additive 等价（强制 sub_resolution），population>0 但预测锥全缺的原保护不变。2657 全绿。a 航沉没成本 ≈$170，数据留档不 resume（resume 会跳 R1 meta，得不偿失）。**b 航从零起飞，P2 的复现观察重新开始。**
> ~~在飞（08-23 00:55 起）：`M26_100x16` 全程 16 轮~~ HEAD=f65a5ea（a 航，已弃）。旗=--ghx-level 6 + FLIP_LEDGER env + --runtime-policy（空表）+ --noop-audit 25。日志 `runs/M26_100x16.{out,err}.log`，shim 8720/worker 22364。监视=事件流（已知 asyncio 噪声族滤除）+ 75min 停滞/退出哨兵。**绿灯门全过后起飞**：特例测试五项（12 新测试，2654 全绿），途中抓获并修复 carried 落盘丢标（`f65a5ea`——vendored append 白名单丢 carried:true，pilot 侧落盘重挂+steps 清零）。首个 noop-scoped 轮当场审 carried 账（对不上=停跑 → --start-round k --noop-audit 0 重启）。注册预测 P1–P5 = M25 验收 §6，已冻结。基线（/100 重算）：HX 台地 67.00±2.77、M25 带 65–73。跑动中禁改被 import 的码。
>
> **状态 08-23（M25 收官）**：`M25_103x16` 已定稿收官——14 完整批（R0–R13），第 14 轮飞行中外部停树（非崩溃，E 项日志全扫裁定）。**终局验收 = `experiments/docs/M25-103x16-FINAL-ACCEPTANCE.md`**（四注册预测裁决 / $1,375 全账 / 机制终账 / M26 注册预测底稿）。不再 resume。
> **M26 起飞前置**：① outcome-fidelity 投影修复（loop_health 实测 ×20，policy `consecutive_empty` 谓词依赖，必修）→ ② 6×2 smoke（新缝首燃三查：map.md 含 flip_ledger 节 / runtime policy 空表加载 / L6 生效）→ ③ nopixel-100 床起飞。决议：主臂不开 `--extra-tools`；`--runtime-policy-seed` 仅诊断臂。
> **M26 过夜作战令（用户 08-23 凌晨，原文要旨）**：特例测试全绿后即起飞 `M26_100x16`，规则按既有夜间规约（小问题=当场修好继续+commit-per-fix+测试；大问题=不擅断、收数据+research 早上给结论；跑动中禁改被 import 的码）。
> **绿灯门**：①noop-audit 落账管线 ②policy 规则全链 ③rollback×新缝 三个集成测试（coder 在飞）审毕+全绿+提交。④resume（已过，重确认 vendored 首轮跳 meta 老账）⑤台账消费探针（已过，v4-pro 引锚点/聚病族/全 id 预测）。
> **起飞命令**（绿灯后执行）：env `PYTHONUTF8=1 HARNESSX_GHX_FLIP_LEDGER=1`，`run_meta_aegis_ghx.py --tasks data/webthinker_gaia_dev_nopixel.json --max-tasks 0 --num-rounds 16 --k-all 1 --search-backend serper --no-early-stop --evolve-max-steps 400 --ghx-level 6 --runtime-policy --noop-audit 25 --run-tag M26_100x16`，detached+新日志名，monitor 盯 err.log（ROUND/StageP/Evolver/Critic/ROLLBACK/shipped/noop/Traceback/flip 降级），另布 75min 停滞哨兵。
> **过夜剧本**：首个 noop-scoped 轮 → 当场审 carried 账（对不上=停跑 → `--start-round k --noop-audit 0` 重启，新日志名）；卡死>75min → §2 杀树恢复；ROLLBACK → 只记录+读三尺，不干预；P1/P2 观察项只记录。注册预测 P1–P5 = M25 验收文档 §6，起飞即冻结。早晨交付：跑况+SOP+P1/P2 观察+账。
> **08-23 00:05 前置①②完成**：fidelity 修复 `a041a7d`（共享 `payload_is_empty`，857 测试绿）；smoke `M26_6x2_smoke` **PASS**（23:28–00:02，~$23）——三查全过（flip_ledger 两轮落盘+缝进 map.md / policy `rules: []` 进 R1 基因型 / L6 十六旗 set+effective），**fidelity 活体读数 3=3**（M25 ×20 → 闭合），门重放出 U、双 ship 带预测题集、无退出挂起、错误全为已知 asyncio 收尾族（23 行/6 Traceback）。loop_health 唯一 warn=attribution 无 backfill——2 轮 smoke 结构性缺 R2 回填，非 bug。**待用户拍板 ③ 正式起飞**（nopixel-100×16，~$1.2–1.4k）。

> **夜间自治规约（用户 08-22 01:55 令，睡前）**：稳步执行既定计划；**小问题=当场修好继续**（我方缝的边角 bug、日志噪声、卡死/退出挂起按 §2 恢复，修复配测试+commit-per-fix，跑动中禁改被 import 的码——修复放在轮间或用 resume）；**大问题=不擅自决断，收集数据+做 research，早上给结论**（大=需要杀跑/改设计/动 vendored/花大钱/改变论文主张的事）。早上交付：一份跑况+SOP+发现的简报。
>
> **在飞（08-22 01:02 起）**：`M25_103x16` 全程 16 轮，17 flag，HEAD=d85f438。日志 `runs/M25_103x16.{out,err}.log`，shim 26316/worker 31496，监视器 b4oflarrq（事件）+ bglvaf3ox（哨兵 75min）。
> 前两段已 PASS：6×2（5/6→6/6，四新缝首燃）、30×3（22→26→24，四桶四 ship，**tools 桶首 ship=WebFetch 覆盖药**，修复正则边角 d85f438）。
> 预计 ~13-16h 收官（明日午后），成本 ~$1.5k（单发 digester 已把 Stage P 压到 ~$11/轮）。收官走 §6 终局验收 + 对账主注册预测（empty_consumed 10±5 / budget 维持 0 / IV-11 税消失 / Stage P 成本）。退出挂起属预期（杀树即可）。已知账新增：outcome-fidelity 漂移在自定义工具 payload 下加宽（×3.7，修复队列）；loop_health 归因通道看不见护栏 joint（修饰性）；OVERRIDES 警告每任务一条（刷屏预期）。

> **M25 三段点火（用户 08-22 令）**：`6×2 测联通 → smoke-SOP → 30×3 测可用 → SOP → 103×16 全程`。
> 全 17 flag（旧 13 + SINGLESHOT_DIGESTER/CHEATSHEET/STRATEGY_POP/ANCHOR_REPAIR），HEAD=24c3dfd，2571 测试绿。
> 每段 SOP：verify_m24_seams + 日志全扫 + **四个新缝首燃**（单发 digester=看 Stage P 成本骤降至 ~$0.1-0.2/题 + 无 fallback 警告；cheatsheet="cheatsheet: wrote" 行 + R{n}/graph_evidence/evolver_cheatsheet.md；strategy 表=strategy_population.md + summary 尾节；锚修复="anchor repair:" 行/IV-1b 建议旗）+ insert_tool 若 Evolver 用了则查 tools 桶全链。**小床分数一律不判**。
> 主注册预测（103×16 终局验收时对账）：①POSIX bash+硬化 fetch 类药攻下 empty_consumed 10±5 题 ②budget_no_commit 维持 0 ③Stage P ~$11/轮 ④IV-11 税消失（旗可顺打）。
> 失败处置：任一段 SOP 发现 a 类 bug → 修复 → 重跑该段；vendored 行为异常先查我方缝再怀疑床。
> 旧 M24 内容如下（历史参考）。

# M24 Overnight Runbook — 103×3 → SOP → 16 轮

> 用户指令（2026-08-21 凌晨，原文）：跑完三轮后，进行详细的检查 SOP（所有产出、in/output、logs、warnings、errors）。
> 如一切正常 → 继续跑到 R16。如有问题 → 修复 → 6×3 测联通 + SOP → ok 则跑 103×16，不 ok 则重复。
> 本文件是跨 context 的记忆锚：**每次 compaction 后先读这份文件再行动。**

---

> **状态更新 08-21 19:05 — 用户令停跑**：M24_103x3 于 R13 批中途人工停止（分数面 GHX vs HX 未决定性分离，用户改令：停跑→改单发 digester 本地测试→全面研究已跑 GHX 轨迹）。**有效数据 = R0–R12 共 13 个完整批 + R1–R13 的 meta 全套**；R13 批不完整作废（C-R13-01 已上车但无批分）。监视器已全撤。核心已知：CommitBand 使 budget_no_commit 33→0 且三批保持；同配置组均 71.0 vs M22 台地 67.3（1.2σ）；IV-11 杀 4 候选成系统病；已花 ≈$1.95k。**不再 resume 本 run**，后续= digester 单发实验（`_digester_ab_R11/` 48 对数据）+ 13 批回溯分析。

> ~~状态更新 08-21 05:45~~：三轮已收官（57/61/59），SOP 全检 **PASS**（验收=`experiments/docs/M24-103x3-SOP-ACCEPTANCE.md`），已进入 Phase 3a：**R3–R15 在飞**，日志 `M24_103x3.r3plus.{out,err}.log`，shim 4660 / worker 9604，监视器 b6d7316fd（事件）+ b52cbntnb（哨兵）。注意：resume 跳过 R3 meta（batch 2 不被 evolve，R3 的 evolve_status=ok 是假标签）；跑完走 §6 终局验收。已知退出挂起模式：curves 齐了但进程不退 → 杀树即可。

## 0. 现状快照（写于 08-21 02:05）

- **在飞**：`M24_103x3`（103 题 × 3 轮，R0..R2），01:15 起飞。
  - R0 批 01:38 完成（23 min）；R1 Stage P 01:59 完成（digesters 103/103，**$57.107 / 16.5M tokens**）。
  - 进程：shim PID 32000 + worker PID 33564（双 python = 垫片 + worker，正常）。
  - 日志:`recipe/gaia_evolver/runs/M24_103x3.err.log`（logging 全在 stderr）、`.out.log`（print）。
  - Monitor 任务 `bzrlmk7kv` 盯 err.log（活着，01:59 刚报过事件），模式含 ROUND/Stage P/Evolver/Critic/ROLLBACK/gate replay/attribution backfill/evolver fallback/Traceback。
- **代码**：分支 `ghx/m24-p0-projection`，HEAD=243641c，243 测试全绿。**跑动期间禁止改动任何被 import 的代码。**
- **Flags（13 个已设，RUNTIME 故意不开）**：L5 六旗 `HARNESSX_GHX_{UNFOLD,IDENTITY,AEGIS_EVIDENCE,GUIDANCE,GRAPH_GATE,GRAPH_PROPOSALS}` + M24 七旗 `HARNESSX_GHX_{LAYER_A,REGRESSION_TRIAGE,POPULATION,GATE_SCOPE,GATE_REPLAY,EVOLVER_FALLBACK,ATTRIBUTION}`，外加 `PYTHONUTF8=1`。模型/网关 key 由 pilot import 自动读 `.env`（litellm 网关 only，禁直连）。
- **原始命令**（resume/复跑的基准）：
  `run_meta_aegis_ghx.py --tasks recipe/gaia_evolver/data/webthinker_gaia_dev.json --max-tasks 0 --num-rounds 3 --k-all 1 --search-backend serper --no-early-stop --evolve-max-steps 400 --ghx-level 5 --run-tag M24_103x3`

---

## 1. 总流程（决策树）

```
M24_103x3 (R0..R2) 跑完
   │
   ▼
Phase 2: SOP 全检（§3）
   │
   ├─ 全绿 ──► Phase 3a: 同目录 resume 到 16 轮（R3..R15），§4
   │              └─ 跑完 → Phase 4: 终局验收（§6）
   │
   └─ 有问题 ─► Phase 3b: 修复(commit-per-fix) → 6×3 smoke → smoke-SOP
                  ├─ ok ──► 新目录跑 103×16（R0..R15），§5 → Phase 4
                  └─ 不 ok → 回到修复，循环
```

轮数语义：`--num-rounds 16` = R0..R15 共 16 轮（banner 是 0-index：`ROUND 0/15`）。与 M22-L0 十六轮踏车同长度，头对头可比。

---

## 2. Phase 1 — 监控到 3 轮跑完

**完成判据**（全部满足）：out.log 出现终局 banner / curves 覆盖 R0..R2；两个 python 进程退出；err.log 不再增长。

**卡死判据**：err.log **mtime 停滞 > 60 min**（批阶段正常 ~23 min；meta 阶段 Stage P ~21 min + Evolver ≤400 步 + Critic + gate replay 有 600s 上限，正常总时 < 60 min）。

**卡死恢复**（既定程序）：
1. `Get-Process python` 确认 PID → **shim 和 worker 一起杀**（只杀其一无意义；误杀垫片=杀 run，所以要杀就全杀）。
2. 半截轮目录归档：`R{k}` → `archive/R{k}.partial-<时间戳>/`。
3. 原命令 + `--start-round {k}` 重启（launcher pre-flight `_fix_merged_after_rollback` 自动处理 rollback 后的 merged.yaml）。**注意换新日志文件名**（Start-Process 的 Redirect 是覆盖不是追加）。
4. 重新 arm monitor 盯新 err.log。

---

## 3. Phase 2 — SOP 全检清单

> 上一轮 30×5 建立的纪律：**检查全部 logs / warnings / inputs / outputs**，逐条归类，零条未解释。

| # | 项 | 命令 / 位置 | 通过判据 |
|---|----|------------|---------|
| A | 进程与完成 | out.log 终局 banner；curves.json | 3 轮全在，退出码正常 |
| B | 运动学读数 | `.venv312/Scripts/python.exe experiments/analysis/analyze_m24_run.py recipe/gaia_evolver/runs/M24_103x3` | 8 节全出，无异常 |
| C | 缝验证 | `experiments/analysis/verify_m24_seams.py <run>` | exit 0，逐轮 PASS |
| D | loop_health | `python -m harnessx.ghx.loop_health <run>`（含五条 GHX 通道） | 全 OK；u_coverage ≈103/轮 |
| E | 日志全扫 | err+out 两个 log 全量 `Select-String -CaseSensitive 'WARNING|ERROR|Traceback \(most'`（**必须 -CaseSensitive**，否则 ResourceWarning 里的 "traceback" 全命中） | 每条 distinct 警告都有归类；零 Traceback；零未解释 ERROR |
| F | 产出抽查（逐轮） | R{n}/digests：Layer A′ 8 列表 + motif 节 + 反引号锚点；aggregate 里 population 表；regressions.md 里 triage 块；gates.md 六门全答（含图门）；machine_manifest predicted 键；scope gate 注记 | 结构齐全，无空段 |
| G | 新缝首燃 | err.log 里 `attribution backfill: graph answered k/n`（R2 Stage P 给 R1 ship 评级）或 vacuous-presence 行；`gate replay` 行（图门缺 U 时）；`evolver fallback`（只在烧穿时应出现） | 语义正确；fallback 无烧穿则应缺席 |
| H | U 覆盖 | `R{n}/sessions/aegis/*/graph/*_unfolded.jsonl` 计数 | ≈103/轮，无系统性缺失 |
| I | 分数（只记录，不做门槛） | R0 vs 种子池 **59.6±3.58**（8 obs）；R1/R2 delta vs 103 床噪声包络（总分极差 ~4-5 题）；adoption/ROLLBACK 事件 | 记录进报告 |
| J | 成本（只记录） | Stage P cost 行合计 + curves/usage；线性外推 16 轮 | 记录进报告（R1 Stage P 实测 $57/轮 → 16 轮 meta 约 $850+批约百余刀，写明） |

**PASS = A–H 全绿 且 K1–K10 无 a 类机制 bug**（I/J 仅记录；K 的 b 类环行为发现只进报告）。任何 Traceback、未解释 ERROR、缝失火、结构性缺产出、机制 bug → FAIL → Phase 3b。

### 3b. 机制检查（K1–K10，用户 08-21 追加：跑完三轮不止查运维，还要查机制）

> 判定分流：**(a) 机制 bug**（缝/门/投影的行为与设计不符）→ 计 FAIL → Phase 3b 修复；
> **(b) 环行为发现**（我们的机器忠实，是 loop 自己决策差）→ 记进报告作论文素材，**不阻断续跑**。

| # | 机制 | 怎么查 | bug 判据（a 类） |
|---|------|--------|-----------------|
| K1 | Layer A′ 被消费 | 逐轮统计 digest 引用锚点率（IV-1 口径；30×5 参考 10-17% vs 官方 7-8%） | 引用率≈0 = 锚点格式又断了 |
| K2 | population→Planner | aggregate 里 population 表存在；Planner 产出的 focus 与 top motif 对齐度 | 表在但 Planner prompt 里没带上 = 接线断 |
| K3 | Evolver 靶向性 | R1/R2 candidate manifest 是否引用 motif/图证据，还是泛泛 prompt 重写 | manifest 引用了不存在的 motif 键 = 接口漂移 |
| K4 | 六门答案质量 | gates.md 逐门非模板化；图门 in-cone 判断抽 1-2 个人工复核（cone 节点确实是 candidate 触碰的） | in-cone 判断与 U 不符 |
| K5 | scope gate 数字 | 注记 predicted_with_cones / sub_resolution 与 manifest 对照；refusal 理由核实 | 误杀（refusal 的 modify 判断错） |
| K6 | gate replay | 若燃：replay U 真生成且被门消费；耗时/超时账 | 燃了但门仍按无 U 走 |
| K7 | attribution backfill | R2 对 R1 ship 的评级：direct 抽查 signature 在 U 里 fired+discriminative 属实；vacuous→joint 行为核实 | direct 评给了从未 fired 的 signature |
| K8 | triage 三尺 | statistical/cone/streak 读数 vs regression 名单；mandate 文本按 triage 措辞（无 R16 式全杀令） | mandate 又出现越权 kill 措辞 |
| K9 | 成本机制 | Stage P $57/16.5M tokens vs M22-L0 同轮 Stage P（图化是否显著加大 digester 输入） | 无 bug 判据；**+>30% 记机制代价并出瘦身提案**，默认不阻断 |
| K10 | U 保真 | 复用 `experiments/analysis/shadow_projection_audit.py` 抽 2-3 题对 U 序列 vs trajectory | 序列错位/丢调用 |

**已知非致命警告账**（预归类，不算 FAIL）：
- `ResourceWarning: unclosed file` — vendored `trace_facts.py:292` 与 `ghx/projection.py:183` 的逐行迭代习惯 + `_ProactorSocketTransport`。纯 GC 噪声，量大（刷屏）。**修复窗口=下次改码批**：projection.py 改成 `with path.open()`（vendored 不动）。
- `RuntimeError: Event loop is closed` ×3（02:20:05，已定性）— 门重放收尾噪声：`run_coro_bounded` 的 fresh loop 关闭后，重放 harness 的 httpx `AsyncClient.aclose()` 孤儿任务往死循环 `call_soon`，asyncio "Task exception was never retrieved" 打日志。**重放 U 正常产出（C-R1-01 → R0/sessions/gatereplay/R1-C-R1-01/graph/…），门正常消费，主循环无影响**。每次门重放后料再现 ×N。修复（下个改码窗口）：gate-replay runner 返回前在 replay 循环内显式 aclose provider 的 httpx 客户端。
- litellm/httpx 的连接池嘟囔（若有）——历史已归类为噪声。

---

## 4. Phase 3a — 全绿：同目录续跑到 16 轮

```powershell
# 在 D:\PycharmProj\HarnessX，先确认旧进程已退出
$env:PYTHONUTF8="1"
$env:HARNESSX_GHX_UNFOLD="1"; $env:HARNESSX_GHX_IDENTITY="1"; $env:HARNESSX_GHX_AEGIS_EVIDENCE="1"
$env:HARNESSX_GHX_GUIDANCE="1"; $env:HARNESSX_GHX_GRAPH_GATE="1"; $env:HARNESSX_GHX_GRAPH_PROPOSALS="1"
$env:HARNESSX_GHX_LAYER_A="1"; $env:HARNESSX_GHX_REGRESSION_TRIAGE="1"; $env:HARNESSX_GHX_POPULATION="1"
$env:HARNESSX_GHX_GATE_SCOPE="1"; $env:HARNESSX_GHX_GATE_REPLAY="1"; $env:HARNESSX_GHX_EVOLVER_FALLBACK="1"
$env:HARNESSX_GHX_ATTRIBUTION="1"
Start-Process -FilePath "D:\PycharmProj\HarnessX\.venv312\Scripts\python.exe" `
  -ArgumentList "recipe/gaia_evolver/run_meta_aegis_ghx.py","--tasks","recipe/gaia_evolver/data/webthinker_gaia_dev.json","--max-tasks","0","--num-rounds","16","--start-round","3","--k-all","1","--search-backend","serper","--no-early-stop","--evolve-max-steps","400","--ghx-level","5","--run-tag","M24_103x3" `
  -WorkingDirectory "D:\PycharmProj\HarnessX" -WindowStyle Hidden `
  -RedirectStandardOutput "recipe/gaia_evolver/runs/M24_103x3.r3plus.out.log" `
  -RedirectStandardError  "recipe/gaia_evolver/runs/M24_103x3.r3plus.err.log"
```

- 同 `--run-tag M24_103x3` + `--start-round 3` = 复用同目录，R0..R2 数据保留。
- **日志必须换名**（`.r3plus.*`）——Redirect 会覆盖原文件。
- 起飞后：确认双 python；arm monitor 盯 `.r3plus.err.log`（同模式 + `ROUND \d+/15`）；每 2-3 轮抽查一次 E/G 两项（轻量），不必每轮全检。
- 观察项（只记录，不动作）：若到 R8 环仍未 ship 出 M2/M3a 对症药，写进报告作为 capability-arm 讨论素材，**不擅自开叉**。

## 5. Phase 3b — 有问题：修复循环

1. **修复**：逐病修，commit-per-fix（带测试；vendored 只准 monkeypatch）。跑前全测试套过绿。
2. **6×3 联通 smoke**：原命令改 `--max-tasks 6 --num-rounds 3 --run-tag M24_6x3_fix<N>`（新日志名，detached，monitor）。
3. **smoke-SOP**（§3 的 C/D/E/F/G/H 项照做；**分数不看**——6 床 ±33pp 是既定噪声，任何按分数的判断都无效）。
4. ok → **新目录跑 103×16**：`--max-tasks 0 --num-rounds 16 --run-tag M24_103x16`（从 R0 全新；不 resume 带病数据）。不 ok → 回到 1。

## 6. Phase 4 — 16 轮跑完的终局验收

1. §3 全套 SOP 应用到 16 轮全量。
2. 头对头：vs M22-L0 十六轮基线 —— 种子 59.6±3.58、台地 **67.29±2.84**、一次性 +7.4pp（StepCountdown+prompt 归因）、fix-one-break-one 编辑面、churn z=+0.21。M24 的问题是：台地更高吗？增益是否不止一次性？triage 是否防住了 governance-kills-medicine？直接/孤儿归因分布 vs M23 全 joint？
3. 写 `experiments/docs/M24-103x16-ACCEPTANCE.md` + 更新 memory（m24 条）+ 报告。
4. 顺手账（跑完后代码批一起）：projection.py 文件句柄修复；`M22-L0-BASELINE-FINAL-ANALYSIS.md` 与 baseline artifact 的 +10.0pp→+7.4pp、bash-guard→StepCountdown 改数（早已认领未做）。

---

## 7. 操作纪律（血泪帐，违者重蹈）

- **后台跑必须 detached**（PowerShell `Start-Process -WindowStyle Hidden`，env 先在 session 设好）。session 绑定的后台 Bash 已死过两次。
- **monitor 必须盯 err.log**（logging→stderr；Start-Process 分流，盯 out.log = 零事件）。
- **杀进程先看 ParentProcessId**：双 python = 垫片+worker；要杀就整树杀。
- **Select-String 默认大小写不敏感**：抓 Traceback 必须 `-CaseSensitive`。
- **禁直连厂商端点**：一切走 litellm 网关（合规只看 base_url）。
- **Redirect 日志是覆盖**：每次重启换新日志文件名。
- **跑动中禁改码**；修复只在两跑之间，配测试，commit-per-fix。
- 带反引号的文本禁止走 bash 双引号 python -c（会被替换）——用 Write/heredoc。
