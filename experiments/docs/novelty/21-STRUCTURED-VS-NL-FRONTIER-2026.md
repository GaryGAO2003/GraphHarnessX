# 21 · 结构化 vs 自然语言 — 前沿模型世代文献卡（2026-08-21 双轮扫描）

> 过滤门槛（用户定）：实验必须含 Opus 4.5+/GPT-5.x/Gemini 3/DeepSeek V4/Kimi K2 世代模型。
> 两轮 researcher 扫描，全部条目经 arXiv 原页核对（标题/作者/日期/模型名单）。
> 背景动机："75 vs 90" 的记忆出处不存在逐字对应表——最近源头是 Tam 等 "Let Me Speak Freely?"
> (EMNLP-Ind 2024, 2408.02442)：GPT-3.5 文本 76.0 vs JSON+schema 49.3；Claude-3-Haiku 86.5→23.4；
> GPT-4o-mini 94.6 vs 87.0。dottxt 复现反驳（"Say What You Mean"，仅博客）得 77 vs 78 持平。

## A. 输出约束 vs 自由推理（旗舰级证据仍稀缺——诚实缺口）

| 论文 | arXiv | 达标模型 | 关键数 | 一句话 |
|---|---|---|---|---|
| The Format Tax (2026) | 2604.03616 | claude-haiku-4.5, grok-4.1-fast | qwen3-32b −6.8pp、3B −11.9pp；haiku-4.5 **+1.2pp**、grok-4.1 **+2.5pp** | 税来自"要求格式"的指令；前沿闭源基本逃税 |
| Capacity, Not Format (2026) | 2606.09410 | 新 Opus/Sonnet/Haiku | Sonnet JSON/CoT 88.7/89.3 无差；Haiku −36.2pp；Opus AIME 96.2→91.0 | 是容量/token 预算效应，非结构本身 |
| 因果分析 (EACL26-F) | 2509.21791 | GPT-4o（未达标但方法关键） | 48 场景 43 无因果效应 | Tam 式前后对比混淆指令变化 |
| TOON vs JSON (2026) | 2603.03306 | Kimi-K2 | 约束 vs 裸 JSON **完全同分** | 旗舰级零差（但任务是产结构记录非推理） |
| Thinking Before Constraining (EMNLP26) | 2601.07525 | Qwen3.5 2/4/9B（小尺寸） | 9B −4.2pp、4B 持平、2B **+22.6pp** | 约束效应随容量翻号 |
| Calibration Floor (2026) | 2608.04355 | Qwen3.5 系（小尺寸） | "自纠"收益 ~95% 是格式修复非推理 | 自纠增益多为可解析性伪象 |

**缺口**：无任何 GPT-5.x/Gemini-3/DeepSeek-V4/Grok-4 旗舰上的经典推理基准结构化对比；Grok 4+ 全线无人测。

## B. 输入序列化（最强线）

| 论文 | arXiv | 达标模型 | 关键数 | 一句话 |
|---|---|---|---|---|
| Structured Context Engineering (2026, 独著预印本) | 2602.05447 | opus-4.5, haiku-4.5, gpt-5.2, gemini-2.5-pro, deepseek-v3.2, kimi-k2 | 顶级层格式差 1.6–5.4pp（聚合 p=0.484 不显著）；**haiku-4.5 12.2pp、kimi-k2 11.1pp**；层级差(86.0 vs 64.6)碾压格式差 | **格式敏感度是层级现象**：最强旗舰无所谓，次级(=我们 deepseek 档)仍敏感 |
| JTON (2026, 独著+自家格式利益) | 2604.05865 | GPT-5.1(-codex), GPT-5-mini, Gemini 3 Pro, Kimi K2 | 10 模型净 +0.3pp；GPT-5.1 单独 −8.6pp | 平均格式中性，个别模型例外 |
| TABVERSE (2026, ARR) | 2606.09578 | GPT-5.2, Gemini-3-Flash | markdown 一致小胜 HTML/LaTeX 0.4–2.9pp | markdown 是表格的安全默认 |

## C. 结构化引用可靠性（对我们锚点体系最直接）

| 论文 | arXiv | 达标模型 | 关键数 | 一句话 |
|---|---|---|---|---|
| Cited but Not Verified (2026) | 2605.06635 | Opus 4.5/4.6, Sonnet 4.5/4.6, Haiku 4.5, GPT-5.2/5.4, Gemini 3.1 | 链接有效 ~99–100%；**内容支持仅 48–77%**（GPT-5.4：链接 100%/事实核查 47.7%）；随工具调用 2→150 再降 ~42% | **指针有效已解决，内容有据没解决**——IV-1b 的文献根据 |
| SWE-Explore (2026) | 2606.07297 | GPT-5.4, Kimi-K2.6, Sonnet-4.5, Gemini-3-Pro | 行级定位召回仅 5–19% | 旗舰的结构化定位（行级）精度仍很低 |
| AgentHallu (2026) | 2601.06818 | GPT-5, Gemini-2.5-Pro, Sonnet-4.5 | 最佳判官对工具幻觉的步定位仅 19.4%（注意：测的是判官归因力） | 幻觉步归因是最未解子问题 |

## D. 结构化 vs 叙述式记忆（仅一篇干净匹配）

| 论文 | arXiv | 达标模型 | 关键数 | 一句话 |
|---|---|---|---|---|
| Retrieval vs Utilization Bottlenecks (2026) | 2603.02473 | GPT-5-mini（执行）/GPT-5.2（判官） | 结构化抽取在 cosine/hybrid 下 +2.1/+4.0pp 胜叙述、BM25 下 **−13.3pp** 负于叙述；检索方式差(20pp)碾压格式差(3–8pp)；裸 RAG 双双打平或胜 | 检索方式 > 记忆格式；结构化不是免费胜 |

（StructMemEval 2602.11243 模型阵容达标但测的是记忆*组织*非格式；上一轮的 0.06 vs 0.66 属组织差异，引用时注意口径。）

## 对 GHX 论文的定位含义

1. **我们的模型档（deepseek flash/pro ≈ haiku-4.5/kimi-k2 层）恰在格式敏感层**（B#1 的 11–12pp 层），markdown+锚点是文献支持的安全选择；meta 角色不上 JSON 强制 schema 同样有据（A 线小模型税）。
2. **前沿的剩余失效在"内容有据"不在"指针有效"**（C#1 的 99% vs 48–77% 解耦）——结构的价值必须落在机器可判定验证（我们的门/锥/尺），这正是 GHX 分工；IV-1b 语义抽核的直接文献根据。
3. **跨线总结论**：格式敏感 = 容量/层级现象而非"前沿 vs 非前沿"；本仓的三处 LLM 产结构失误（digester 缩写路径、Critic 锚违规、manifest 自造键）是该层级的预期行为，确定性校验器是正解。
4. **CH2 要诚实写的缺口**：旗舰推理基准上的结构化输出对比只有两篇 anchor；Grok 4+ 零覆盖；B#1/B#2 是独著未评审预印本（其一有自家格式利益），引用降权。
