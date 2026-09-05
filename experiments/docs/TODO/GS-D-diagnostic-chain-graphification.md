# GS-D · 诊断链图化（Digester / Planner）

> 待办。2026-08-08 提出，未实施、未登记进 `novelty/00-NUMBERING.md`。
> 不属于 GS-A/B/C（run 内三位），也不在 16 号已封批的 Δ1–Δ17 内。

## 1. 原来的问题

AEGIS 环的前半段是纯文本管道，图一点没进去。
代码坐实（2026-08-08 全仓 grep）：`harnessx/meta_harness/` **零 import `harnessx.graph`**；
图模块的消费方只有 `experiments/analysis/` 与 `experiments/variant_pool/`。

| 号 | 缺陷 |
|---|---|
| HX-5 | 每个 Digester 只见本任务，跨任务聚合 = 对 digest 头部做正则。「六任务同根因」没有组件有视野看见 |
| HX-6 | Evolver 唯一战略输入是 landscape.md，从不接触原始证据；候选质量天花板 = 转述质量 |
| HX-7 | actionability 四档硬楼梯 1.0/0.8/0.3/0.0，最贵的开关只有两比特分辨率 |

（HX-4 病理词表冻结**不在本条射程内**，别硬套。）

## 2. graph 的优势

失败轨迹已有 `CoverageFootprint`（`graph/footprint.py`），成功与失败足迹都在存
（`FootprintStore.get_all`）⇒ Tarantula 式可疑度的两列现成，**无需切片、无需 GS-C**。

```
Digester 输入   trajectory 文本  +  CoverageFootprint
Planner  聚合   正则解析          →  足迹集合运算（失败集 ∩ / 对成功集取差）
Planner  输出   landscape.md      +  可疑节点/边有序表
Evolver  输入   自由文本          +  target_node_id = GraphEdit 的合法作用域
```

- HX-5 → 共同根因变成**集合运算**，机器可判，不需要 LLM 拿全局视野
- HX-6 → 结构指针**不经过转述**，绕开转述质量天花板
- HX-7 → a_t 由交集锐度**连续**算出，两比特 → 连续量
- `GraphEdit.target_node_id` 本来就需要靶点，现在由 Evolver 自己从文本里猜；Planner 侧递过去，链才闭合

**与 16 号 Δ2 的关系**：Δ2 是切片版、落点 S4、依赖 GS-C（零实现）。
本条是**足迹版降级实现**——精度低一档（足迹比切片粗，含偶发探索），但立即可做。

## 3. 期望结果

**先决（零 API，加进 T0 作第八量）**：失败足迹交集的锐度分布。
足迹密度 ≈ 1 ⇒ 交集 = 全集 ⇒ 可疑度恒等 ⇒ **整条死**。与 S2 的 ⑦ 同源，不能先斩后奏。

| 读数 | 期望方向 |
|---|---|
| 同根因失败任务的足迹交集大小 | 稀疏且跨轮稳定 |
| Planner 靶区命中率（靶区 ∩ 实际 ship 的编辑作用域） | > 文本臂 Evolver 自选靶点 |
| 提案有效率 | ↑（靶点合法性前置） |
| actionability 分辨率 | 四档 → 连续；旱灾轮误判率 ↓ |
| final pass@k | **仅守非劣**，不作主张 |

**盲区（须明记，不默认收敛）**：观测层三缺口之一——拦截型干预在早返回前不发射
⇒ **控制边不可观测** ⇒ 「某 processor 闸掉了流」这类根因图看不见。靶区目前只能建在数据边上。

**对 S7 的影响**：对照轴从「Evolver 提交面」扩成「整条 AEGIS 链」。
T3 消融须加两格：`G−digester-footprint`、`G−planner-target`，否则说不清增益是
图编辑挣的还是靶区挣的。Digester/Planner prompt 变化 ⇒ 元 agent token 单独记账。
