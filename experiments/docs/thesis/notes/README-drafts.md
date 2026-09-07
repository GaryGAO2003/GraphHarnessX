> **入口(08-24 起)**:章节写作的唯一数字来源与主轴 = [STORY-V3-AUDITED.md](STORY-V3-AUDITED.md)(审计定稿,F1–F21 台账,§10 撤回登记不得回引)。旧主轴 THESIS-RESTRUCTURE-GHX-V2.md 仅作结构参考。

# 论文草稿（纳入版本控制）

> **Aug-12 重排 v2**：主轴 = GHX 图运行时 + 官方 AEGIS 底盘 + 阶梯实验
> （L0/L1/L2/L4）。总纲 = `../THESIS-RESTRUCTURE-GHX-V2.md`（取代 Aug-08 版）。
> 工程事实以 `docs/ghx-v6-build-log.md` 为准；阶梯 as-built 定义以
> `../BASELINE-L0-STATUS.md` §6 为准。

**本目录是草稿的权威副本，今后请改这里的文件。**

## 现行章（GHX 轴，Aug-12 新写）

| 文件 | 状态 |
|---|---|
| `CH1-INTRO-DRAFT.md` | ✅ 重写完（新三 RQ：诊断/机制/干预；四层贡献；claim 纪律） |
| `CH3-DIAGNOSIS-DRAFT.md` | ✅ 二稿（按用户裁定重写：**立在官方源码上**——自账簿之坏 off-by-one/IV-4/rollback、提案通道之脆 YAML/烧穿、噪声成"进步"三标本、仪器；e2_A 降为 §3.6 非承重佐证；池/K=8 材料删除）——数据全在手 |
| `CH4-METHOD-GHX-DRAFT.md` | ✅ 新写（G/U/三哈希/归因/因果锥；诊断桌 L2；审批桌 L4；**§4.9 候选面 L5=主系统**；完整性；范围诚实）——数据无关 |
| `CH5-EXPERIMENT-DESIGN-DRAFT.md` | ✅ 新写（阶梯=系统+消融：**headline = L5 vs L0，L2/L4=消融**；判分三层加固、去污 census、预注册 endpoint 与分支、L5 赶不上窗口的预声明 fallback、对称纪律）。**轮数参数化 `R`** |
| `CH6-RESULTS-DRAFT.md` | 🟡 §6.1 commissioning 已填（v1/v2/v3 名义 vs 审计表、L1 零干预、L2/L4 smoke）；§6.2 正式战役留槽 `[PENDING]` |
| `CH7-DISCUSSION-THREATS-GHX-DRAFT.md` | ✅ 新写（10 条威胁 + 两类增益边界 + 递延项） |
| `CH2-BACKGROUND-DRAFT.md` | ✅ 重写完（§2.2.6 双实现现状；新增 §2.3 架构即图（AgentFlow/MermaidFlow/SIGIL/Agentproof/HarnessForge/NLAH + DSPy/TextGrad 分界）、§2.4 门-噪声+judge 可靠性、§2.5 SE 根基、§2.8 三位定位）。**注意：DSPy/TextGrad 两条 identifier 是记忆级，交稿前须一手核验** |
| `APPENDIX-A-DEVIATIONS-TABLE.md` | ⚠️ 过期（止于 M-26）；定稿由 `../PAPER-METHODOLOGY-DEVIATIONS.md`（现至 M-42）直转 |

## 已退役（superseded 横幅在文件顶部，勿再编辑）

`CH3-REPRODUCTION-DRAFT.md`（纪律节被新 CH3/附录 A 继承）·
`CH4-METHOD-DRAFT.md`（分工方法，两条纪律移 CH5，余作附录 C 候选）·
`CH7-DISCUSSION-THREATS-DRAFT.md`（7.4.1/7.4.6/7.4.7 已迁入新 CH7）

## UCL 合规（源 = `ucl paper/` Barber 指导页 + project_report 模板，2026-08-12 对照）

- [ ] **LaTeX 化**：全部章节灌入 `project_report - pg.tex` 模板（report 类、UCL logo、
      disclaimer 脚注选一种分发条款、abstract、TOC、alpha 式 bibliography）
- [ ] **~50 页预算**（Barber 口径，单倍行距双面；模板给的是 1.5 倍——排版时定一个）：
      现七章折算约在预算附近，转 LaTeX 后跑一次页数审计，超了先砍 CH5（并入 CH6）
- [ ] **~50 篇引用**：Barber 预期量级；现稿 ~35（含 SE 经典）。补源：registry 21 篇、
      退役轴旧 CH2 的可迁移条目、judge/污染各 2-3 篇——**不发明，只从已核语料扩**
- [ ] **第二读者 = 不熟本方向的 CS 老师**：CH1 前几页降密度（读不懂前几页=没高分）；
      术语表/notation 页；"linear story" 通读校对（每段承接上段）
- [ ] Abstract + CH8 Conclusion（Barber：诚实评估成败）未写
- [ ] 非 ML 工程劳动必须入账并被承认（Barber 明文）——我们的仪器加固/运维叙事
      已按"结果"写（CH3 §3.5、CH5 §5.3、附录 B），转写时保持可见
- [ ] 封面字段：学位名、导师名、提交日期
- Barber 铁律两条已天然满足：8 月初开写引言章 ✓；"多一个魔法实验 < 把论文写好看"
      ——降档决策时引用这条

## 待办

- CH2 按上表改写；附录 A 直转（M-01..M-42+）；附录 B 运维叙事
  （504 风暴 / Windows Update 双杀 / venv 垫片 / serper 事故 → 四条 SOP）
- 103 床正式数据落地后：CH6 §6.2 填数 → CH1/CH5 数字校核 → endpoint 分支判定
- 轮数口径冻结后：全局替换 `R rounds` 占位（现约定：正文不写死轮数）
