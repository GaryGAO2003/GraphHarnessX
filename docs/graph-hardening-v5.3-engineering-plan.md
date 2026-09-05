# HarnessX Core ↔ Graph v5.3 工程实施计划

> 状态：待实施；本文件是执行计划，不是 v5.2 规格替代品。
>
> 依据：`docs/graph-hardening-v5.md`、`experiments/docs/TODO/GRAPH-MECHANISM-ASSESSMENT.md`、
> `experiments/docs/TODO/GS-D-diagnostic-chain-graphification.md`。

## 1. 目标与非目标

### 目标

建立一条可验证、可回滚、无 graph/runtime 分叉的配置演化链：

```text
HarnessConfig
  → canonical processor registrations
  → GraphSnapshot (genotype)
  → typed GraphEdit transaction
  → fail-closed validation
  → graph → config materialization
  → HarnessBuilder.build()
  → re-graph + hash/roundtrip verification
  → selective retest
  → VariantPool / SuccessLedger
```

必须保证：

- `_processor_regs` 是唯一可写注册真相；
- graph 是派生表示，runtime overlay 不污染 genotype；
- persistent、deployment、observed 三层 hash 语义互不重叠；
- 所有接受的候选都能 build、roundtrip，并留下 lineage/provenance；
- 调用方取消、构造失败、插件冲突和非法图编辑都 fail-closed。

### 非目标

- 不把 Mermaid 作为 canonical IR；
- 不用 LLM 生成 Python 作为可信编译器；
- 不在本计划中实现完整任意多智能体 DAG；
- 不提前实现 GS-A/B/C、valid-time、SCC/def-use、archive/Pareto/island 等未证明有消费者的机制；
- 不在 v5.3 期间改变 runloop 的固定生命周期语义。

## 2. 关键不变量（编码前冻结）

这些决定必须在 Phase 0 通过评审后冻结，后续阶段不得自行改名或改变含义。

| ID | 不变量 | 验证位置 |
|---|---|---|
| I1 | `PROCESSOR_HOOK_NAMES` 是 core 中唯一的 canonical 8-hook tuple | processor/declaration/snapshot 单元测试 |
| I2 | `_processor_regs` 是唯一可写注册序列；`processors` 与 `_rt_procs` 只是视图 | HarnessConfig 测试 |
| I3 | `SerializedReg` 的 presence/value 是 `dict_ref` 动态读取 | VM20b |
| I4 | RuntimeReg 不修改共享 processor 实例 | builder/runtime 测试 |
| I5 | runloop 只执行裸 processor，不执行 RuntimeReg/RoutingEnvelope | routing 集成测试 |
| I6 | `nodes/edges` 只表示 genotype；`runtime_nodes/runtime_edges` 不进入 genotype hash | VM10/VM19 |
| I7 | `EXECUTES_BEFORE` 必须与实际 routing 排序同源 | builder/runtime/graph 对照测试 |
| I8 | `apply_edits()` 失败时原 snapshot 完整不变 | 事务回滚测试 |
| I9 | rejected candidate 不得进入 executor、ledger 或 active config | candidate gate 集成测试 |
| I10 | observed trace 只能提供证据，不能静默改写声明式 graph | reconciliation/journal 测试 |

### Hash 命名决策

实施前必须选定并记录最终名称。推荐：

- `genotype_hash`：持久 graph nodes/edges；
- `deployment_hash`：genotype + runtime overlay + deployment edges；
- `phenotype_hash`：deployment + observed edges；
- 若需要“仅 observed IR”的哈希，新增 `ir_observed_hash`，不要复用 `phenotype_hash`。

禁止在同一版本中让 `phenotype_hash` 同时表示两个不同对象。

## 3. 阶段总览与依赖

```text
P0 语义冻结与测试骨架
 ↓
P1 Core runtime canonicalization
 ↓
P2 Graph snapshot / overlay / hash
 ↓
P3 GraphEdit transactional validator
 ↓
P4 全库消费者迁移与兼容清理
 ↓
P5 Shadow-mode typed evolution
 ↓
P6 History / crossover
 └──────────────→ P7 optional GS-D / WorkflowPlanGraph
```

P0–P4 是生产安全前置；P5 才是 MermaidFlow-inspired 机制的首次接入；P6/P7 不得阻塞前五阶段。

## 4. P0 — 语义冻结与测试骨架

### 工作项

1. 将 `replace_runtime_regs` 统一命名为 `replace_processor_regs`，旧名只保留短期兼容 wrapper（如确有调用者）。
2. 冻结 canonical 8 hooks 与旧 10-hook 快照迁移策略。
3. 冻结四类注册项的状态转换：

   ```text
   dict → SerializedReg
   processor → RuntimeReg
   SerializedReg(instantiated) → RuntimeReg
   RuntimeReg → RoutingEnvelope → routed processor
   ```

4. 冻结 dropped serialized entry、dict plugin、空 hook、显式 falsey 元数据的政策：
   - 可恢复的缺失字段：natural fallback；
   - 显式空值：保留并停止执行；
   - 无法实例化：记录原因并从本轮路由剔除；
   - 冲突/非法结构：抛异常，不进入评测。
5. 创建测试目录和 fixture，不实现功能代码。

### 产物

- `docs/graph-hardening-v5.3-engineering-plan.md`（本文件）；
- `tests/graph/fixtures/`：serialized/runtime/plugin 混合配置；
- `tests/graph/test_contract_matrix.py`：I1–I10 的空壳测试；
- 一份旧 v5.2 配置迁移说明。

### 退出条件

- 所有命名冲突已解决；
- 8-hook 与旧快照迁移策略有测试样例；
- `pytest` 可发现新测试但不改变现有行为。

## 5. P1 — Core runtime canonicalization

### 文件归属

- 新增/维护：`harnessx/core/runtime.py`；
- 修改：`harnessx/core/processor.py`、`harnessx/core/builder.py`、`harnessx/core/harness.py`；
- 测试：`tests/core/test_runtime.py`、`tests/core/test_builder_runtime.py`、`tests/core/test_cleanup.py`。

### 实施内容

1. 在 `processor.py` 中实现 `_EVENT_TO_HOOK_NAME`、`PROCESSOR_HOOK_NAMES`、`_find_class_hook`、`compute_effective_hooks`、`get_graph_metadata`。
2. 在 `runtime.py` 中实现：
   - `RuntimeReg`；
   - `SerializedReg` 动态 presence properties；
   - `RoutingEnvelope`；
   - `normalize_processor_reg`；
   - `coerce_runtime_reg` / `unwrap_runtime_proc`；
   - `stable_topological_sort`；
   - `HarnessConflictError`；
   - owner identity registry。
3. `HarnessConfig.__post_init__` 只构造 `_processor_regs`，并从 canonical 重建两个只读视图。
4. `_instantiate_runtime` 只消费 `_processor_regs` 一次，插件使用 `max(seq)+1` 尾部 envelope。
5. `_route_processors` 按 registration bucket 分桶，再按 `order → after → seq` 排序，输出裸实例。
6. 构造异常回滚当前 owner token；cleanup 使用 shielded task，所有 await 完成后才释放资源和 owner。

### 必测分支

- MRO hook 继承、显式 `_hook=None/""`、`@on` 继承；
- dict/runtime/dict/runtime 混合顺序；
- explicit falsey 与 missing 四字段；
- after 跨 order、同 order cycle、soft dependency；
- dropped serialized seq 空洞；
- plugin 同实例去重；
- 不可哈希 processor 的 owner claim；
- cleanup 在 sub/plugin/sandbox 三个 await 点被取消后的重试。

### 退出条件

- VM1、VM5、VM6、VM15–VM18 通过；
- 核心测试不依赖 graph 模块，避免反向 import；
- 任一非法注册不会产生部分路由或部分 owner claim。

## 6. P2 — Graph snapshot、runtime overlay 与 hash

### 文件归属

- 修改：`harnessx/graph/types.py`、`harnessx/graph/declaration.py`、`harnessx/graph/snapshot.py`、`harnessx/graph/identity.py`、`harnessx/graph/transform.py`；
- 兼容迁移：`harnessx/graph/edit.py`；
- 测试：`tests/graph/test_snapshot.py`、`test_identity.py`、`test_transform.py`、`test_runtime_overlay.py`。

### 实施内容

1. `GraphSnapshot` 增加 `runtime_nodes`、`runtime_edges`、`deployment_hash`，并冻结默认值。
2. `_extract_declaration` 先累积字段，再一次构造 `ComponentDecl`；使用键存在性而非 truthiness。
3. 所有 hook、wildcard 和生命周期排序只引用 core canonical tuple。
4. persistent processor、runtime-only processor、plugin processor 分别进入正确层；runtime slot 不污染 `snapshot.nodes`。
5. 增加 dynamic slot/event-field edges，并限制跨层 edge endpoint。
6. 实现 persistent-relative 与 mixed `EXECUTES_BEFORE` 链；统一调用 P1 sorter。
7. `_sort_dict(at_root=...)` 在顶层白名单键排序，嵌套结构绝对保序。
8. `genotype_hash`、`deployment_hash`、`phenotype_hash` 使用共享 `_hash_nodes_edges` 并写回缓存。
9. `graph_to_config_dict` 保留 falsey metadata、`_ctor_kwargs_` 和 `_after_` 优先级；runtime-only 节点不写回 persistent processors。

### 退出条件

- VM2–VM4、VM7–VM14、VM19–VM20 通过；
- 不导入 `_target_` 指向的类也能完成纯 serialized graph 导出；
- graph→config→build→graph 的 hash/registration 顺序满足 roundtrip；
- runtime overlay 改变不会改变 genotype hash。

## 7. P3 — GraphEdit transactional validator

### 文件归属

- 新增：`harnessx/graph/validate.py`、`harnessx/graph/operators.py`；
- 修改：`harnessx/graph/edit.py`、`harnessx/graph/types.py`；
- 接入：`experiments/variant_pool/graph_gate.py`；
- 测试：`tests/graph/test_validate.py`、`test_edit_transaction.py`、`test_operators.py`。

### Validator 分层

| 层 | 检查内容 | 失败策略 |
|---|---|---|
| S0 | schema、类型、字段、ID 格式 | reject |
| S1 | endpoint 存在、edge-kind/node-kind 合法 | reject |
| S2 | hook coverage、singleton、order、after、owner | reject |
| S3 | slot/event/bundle interface signature | reject |
| S4 | apply 后 roundtrip、build、hash 稳定 | reject |
| S5 | smoke/held-out runtime evaluation | candidate score only |

### 事务协议

```text
deepcopy(parent)
  → validate edit preconditions
  → apply all edits
  → validate full snapshot
  → clear derived hashes
  → materialize config
  → build
  → re-graph
  → compare invariants
  → commit candidate or discard copy
```

原 snapshot 不得被中间失败污染。`EXECUTES_BEFORE` 等派生边在重新 `to_graph()` 前视为 stale，不得用于评分。

### 第一批确定性 operators

- `MutateProcessorParams`；
- `InsertProcessor`；
- `RemoveProcessor`；
- `ReplaceSameSingletonGroup`；
- `RewireOrdering`；
- `SwapBundle`（只接受相同 boundary signature）。

暂不实现 crossover；先以单父代 shadow mode 验证 operator kernel。

### 退出条件

- 所有非法 edit 都 fail-closed；
- 所有合法 edit 都能 materialize 或明确返回不可 materialize 原因；
- `graph_gate` 不再把 build 异常降级成 warning 后继续通过；
- 事务 rollback、边类型、cycle、roundtrip 均有回归测试。

## 8. P4 — 全库消费者迁移

### 必迁移调用点

- `trajectory_digester.py`：使用 `dataclasses.replace(reg, proc=new)`；
- `benchmarks/tau2/agent.py`：使用 `add_runtime_reg`；
- `spawn_subagent.py`：直接变换 `_processor_regs`；
- `cli.py`、`api/routes/run.py`、`gateway/main.py`：copy 时保留混合 canonical；
- `meta_harness/agent.py`、`validate_workflow.py`、recipe 渲染器、trajectory reader：使用 `unwrap_runtime_proc`；
- `graph/edit.py`：迁移到 `_compute_slug`。

### 迁移规则

- 禁止任何新代码写 `_rt_procs`；
- 禁止以 `list(config.processors) + list(config._rt_procs)` 重组顺序；
- 禁止把 RuntimeReg 当 processor 直接读取属性；
- 每个迁移点必须增加一条混合顺序回归测试。

### 退出条件

- `rg "_rt_procs\s*=|_rt_procs\.append|list\(.*processors.*\).*_rt_procs"` 只剩测试或兼容诊断；
- CLI/API/gateway/spawn/digester 的 S-R-S-R 序列保持不变；
- 全量 unit/integration test 通过。

## 9. P5 — MermaidFlow-inspired shadow evolution

### 数据流

```text
Evolver/LLM
  → structured GraphEdit[] only
  → candidate normalization
  → GraphValidator S0–S4
  → build + re-graph
  → Critic (advisory)
  → selective retest
  → VariantPool / SuccessLedger
```

### 规则

- 每轮最多 4 个候选；候选全部先过硬 gate，再允许 critic 排序；
- LLM 不输出 Python、canonical YAML 或 canonical Mermaid；
- runtime overlay 不作为 genotype mutation 输入；
- 所有候选保存 parent id、operator、boundary signature、validation report、hash、evaluation scope；
- 只在 shadow mode 运行，不自动修改生产配置。

### 对照实验

- A：现有 text/YAML pipeline；
- B：相同 proposer budget + deterministic typed edits；
- C：B + history sampling；
- D：C + matched-boundary crossover（后续阶段）。

### 评价指标

- proposal parse rate；
- S0–S4 pass rate；
- graph→config roundtrip rate；
- build/smoke success rate；
- unique genotype diversity；
- reward per evaluation/token；
- 首个可接受改进的时间；
- held-out regression rate；
- selective-retest savings。

### 上线门禁

- 不接受任何 invariant/roundtrip violation；
- shadow mode 与现有 pipeline 的 regression 不得增加；
- 只有 deterministic gate 和 measured evaluation 可以写入 APPLY/FORK/REJECT 决策；
- LLM judge 不得单独提升候选为可部署配置。

## 10. P6 — History、sampling 与 crossover（可选）

只有 P5 连续运行稳定后才执行。

1. `VariantPool` 保存 genotype/deployment hash、lineage、operator、父代、验证报告和评测成本。
2. parent sampler 使用 uniform exploration + score-weighted exploitation，但按 task/domain cluster 分池。
3. crossover 只允许 persistent genotype，且两侧 boundary signature、hook、slot/event、singleton/order 约束完全兼容。
4. crossover 结果必须经过完整 P3 事务验证，不允许使用“算子定义上保证闭包”替代实际验证。

## 11. P7 — 后续独立项目

### GS-D diagnostic chain

独立于 Core↔Graph 主线，使用：

```text
trajectory + CoverageFootprint
  → cross-task root-cause intersection
  → ordered suspicious node/edge table
  → Evolver target_node_id
```

必须先验证其确实改变 `GraphEdit.target_node_id` 的命中率，再实现更重的 slice/SCC/valid-time 系统。

### WorkflowPlanGraph

如果确实需要 MermaidFlow 那种任务级 agent/ensemble/test DAG，新增独立 IR 和 executor；不扩张当前 `GraphSnapshot`。它与 HarnessGraph 的关系应是：

```text
WorkflowPlanGraph → workflow plugin / sub-harness executor
Harness GraphSnapshot → processor/hook/slot/runtime configuration
```

## 12. 测试与发布策略

### 测试层级

1. Unit：纯函数、presence、排序、hash、slug、声明合并。
2. Property-based：合法 edit 闭包、随机混合 registration、roundtrip。
3. Integration：Builder → HarnessConfig → routing → to_graph。
4. Failure injection：owner conflict、constructor failure、plugin stop failure、取消 cleanup。
5. Shadow evaluation：A/B/C/D pipeline 对照，不改变生产配置。

### 每阶段必跑

```text
pytest tests/core tests/graph
pytest tests/graph -q
python smoke_test_graph.py
```

进入 P5 前必须通过全量测试，并保存 baseline hashes、候选通过率和评测成本。

### 回滚

- P1–P4 通过 feature flag 或兼容 wrapper 保留旧读取路径，但禁止新增旧写入路径；
- P5 只写 shadow ledger，不写 active config；
- 任意 hash/schema 迁移失败时，恢复旧命名 alias，不删除旧数据；
- 不使用 destructive git reset/checkout 清理工作区。

## 13. 交付清单

- [ ] P0 语义冻结、fixture 和测试骨架
- [ ] P1 Core runtime + VM1/5/6/15–18
- [ ] P2 snapshot/overlay/hash + VM2–4/7–14/19–20
- [ ] P3 transactional GraphEdit + S0–S4 validator
- [ ] P4 全库消费者迁移与 grep 审计
- [ ] P5 shadow-mode typed evolution 与对照实验
- [ ] P6 history/crossover（可选）
- [ ] P7 GS-D / WorkflowPlanGraph（独立立项）

## 14. 明确的实施起点

下一步只做 P0：冻结 hash/API/hook 语义并建立测试骨架。P0 未通过前，不实现 runtime.py、GraphEdit、MermaidFlow operator 或任何新演化入口。
