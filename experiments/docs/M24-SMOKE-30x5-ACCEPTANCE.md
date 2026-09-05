# M24 · 30×5 smoke 验收与分析

> 跑：`recipe/gaia_evolver/runs/M24_smoke_30x5`，30 题 × 5 轮，`--ghx-level 5` + M24 五旗
> （LAYER_A / REGRESSION_TRIAGE / POPULATION / GATE_SCOPE / GATE_REPLAY）
> 时：08-20 16:54 → 22:33（含一次卡死中断与续飞）
> 验收器：`experiments/analysis/analyze_m24_run.py`（8 节全量读数）
> 结论：**全部 M24 seam 在 30 题规模活体点火，0 个 seam 失败；第六道闸门 4/4 答题（M23 全程 0/6）。**

---

## 1 · 验收总表（逐 evolve 轮）

| seam | R1 | R3 | R4 |
|---|---|---|---|
| Layer A′ 接管 | 29/29 图投影、0 假信号残留 | 30/30 | 30/30 |
| population 表 + summary 段 | ✓ | ✓ | ✓ |
| 回归分诊三把尺 | ✓ | ✓ | ✓（锥尺 in=4/out=0 ×2；反事实正确拒绝全摇摆集） |
| 锥/cone_sigs | ✓ | ✓ | ✓ |
| scope 闸门 + resolution.json | 2 verdict | 2 verdict | SKIP（本轮无船） |
| **Gate B replay** | **2/2 checked=True, direct** | **2/2 checked=True, direct** | SKIP |
| loop_health | 0 BROKEN | 0 BROKEN | 0 BROKEN |

（R2 无 evolve 产物：见 §4 事件账——中断轮作废，批 2 跑 R1 配置，等效 noop。）

## 2 · 曲线与成本

```
R0=24/30 (80.0%)  baseline   $7.42
R1=21/30 (70.0%)  ship ×2    $4.13
R2=26/30 (86.7%)  （续飞轮，R1 配置）$7.05
R3=25/30 (83.3%)  ship ×2    $4.61
R4=26/30 (86.7%)  noop（Evolver 烧穿）$5.71
```
- 终值 +6.7pp = +2 题，30 床噪声内，**不作分数主张**（smoke 目的=连通性）。
- rollout 合计 $28.91；元阶段 ≈ $195（Evolver 四轮 $150 占大头，Digester $29、Critic $15）；replay 6 次 ≈ $1。全程 ≈ $225。

## 3 · 船与闸门（M24 机制的第一批活体判词）

| ship | bucket | hit | 存在闸门 | scope | resolution |
|---|---|---|---|---|---|
| C-R1-01 | processor | 1/2 | **checked=True, direct** | ok | additive, pop=0, predicted_failing=2, **sub_res** |
| C-R1-02 | prompt | 2/3 | **checked=True, direct** | ok | modify, pop=6, predicted_failing=3, **sub_res** |
| C-R3-02 | processor | 2/3 | **checked=True, direct** | ok | additive, pop=0, predicted_failing=3, **sub_res** |
| C-R3-04 | prompt | 2/3 | **checked=True, direct** | ok | modify, pop=4, predicted_failing=3, **sub_res** |

- **存在闸门 4/4 答题**——replay 跑候选自己预测集中败 streak 最长的题（30–35 秒/次），签名以双形态 id 计数判 direct。M23 的 6/6 未答就此关闭。
- **四船全部 sub_resolution**：30 床阈值 6，预测集 2–3 题 < 阈值 → 记账只认预测题集（hit_rate），不认曲线——标注机制按设计工作。
- **零拒绝**：scope/存在两道闸门都没杀过船——它们是手术刀，本 smoke 没遇到该杀的形态（历史回放同样零假拒绝）。
- 预测命中合计 7/11 = 64%。

## 4 · 事件账（本 smoke 修掉的最后两个真 bug）

1. **gate replay 自锁**（R2 悬死 2h18m）：`with ThreadPoolExecutor` 的 `__exit__` = `shutdown(wait=True)`，超时抛出后反而死等挂死线程。修复 = 内层 `asyncio.wait_for`（真取消）+ 外层兜底 + `shutdown(wait=False)`；`test_hung_runner_times_out_and_passes_through` 钉住秒级返回。副作用（已知可接受）：真挂死线程漏到进程结束，收官后进程需手动清——冻结后清理项。
2. **U 定位器**：`base_dir` 在 journal 块里不在顶层 `sessions:` 键——smoke #5 里 replay 跑了、U 落盘、判词却 unavailable。修复 = 正则收集全部 `base_dir:` 逐个 `find_unfolded` + run 根 glob 兜底。
3. 续飞语义（记录）：`--start-round 2` 从 `R1/applied/merged.yaml` 恢复，被中断的 R2 evolve 整轮作废——正确且保守。

## 5 · motif 人口与泄漏账（跨轮首秀）

```
motif              R1  R3  R4      （failing 侧，30 床失败仅 4–9 题，人口小属预期）
empty_consumed      4   3   4
budget_no_commit    2   0   1
ungrounded_commit   1   1   1

M2-on-pass（运气/泄漏候选）：R1=7 → R3=7 → R4=11  （约占通过题 27–42%）
```

## 6 · 已知缺口（非本批 seam，进下批清单）

1. **归因仍全 joint**（loop_health DEGRADED）：4 船 11 个 graded task 全 joint。prompt 两船 joint 属定义正确；**两条 processor 船本可 direct/orphan**——账本回填路径没吃到 `check_signature_in_u` 的双形态修复（M23 的 direct 全来自 tools 船，processor 船在 M23 也全 joint，同源旧缺口）。下批：把双形态计数接到账本回填的 resolver。
2. **outcome 保真红灯**：digest-empty 11 vs U-empty 4——已知记录器缺口，冻结后修（Layer A′ 用 join 已绕开）。
3. **Evolver 烧穿复发**（R4 exit=error 0 候选，L0-R6 同款）——仪表批押后的"失败回退候选池"该上了。
4. 收官后进程不退（漏线程堵解释器退出）——teardown 清理，冻结后。

## 7 · 判定

**连通性验收通过。** 103 床战役（M24 正式臂）的技术前提全部就绪：
六个 smoke 迭代（6×2 ×5 + 30×5）把五层真 bug 剥完（stabilize 键 → slug 双形态 → 即兴键名 → 会话陪葬 → 定位器/超时自锁），每层都是诚实梯兜住（放行而非崩溃/误拒），每层有 commit + 测试钉住。

---

## 8 · 全量 log 补扫（验收后追加，08-20 深夜）

对两份 err.log 的全部 WARNING/ERROR 归类扫描 + out.log（0 警告）+ digest 内容抽查，新增两个发现：

### 8.1 R1 曾发生 ROLLBACK，且续飞把被撤的船装了回去（真缺口 #5）

- 官方回滚 17:44 触发：批 1=21 比 last_validated=24 低 3（`Δrate=-0.100 ≤ -0.05 AND Δcount=-3 ≤ -3`），撤 C-R1-01/02。
  **注意：30 床上 Δ=-3 本身在噪声包络内——这是"治理杀药"的回滚版实例。**
- 续飞从 `R1/applied/merged.yaml`（回滚**前**的合并配置）恢复 → 批 2–4 实际带着被撤的两船跑。
  分数 26/25/26 ≥ 24，未受害；但 **resume 无视 rollback 是真缺口**：正式臂若中断续飞，必须先核对
  audit.jsonl 的 rollback 事件再选恢复配置。
- 另证（grep 纠偏）：船资产 grep 不到 `file://` 不是 merge 失败——C-R1-01 ship 的是**内置**
  `StepCountdownProcessor(escalate_within=3)`（模块路径接线），C-R1-02/C-R3-04 是 prompt 模板替换。
  巧合值得记录：**环自己 ship 了 L0 那次 +10pp 的同款机制（StepCountdown）**。

### 8.2 IV-1 零锚 digest 17 份（已修）

- 根因：vendored 锚点正则只认反引号/方括号包裹的锚；零工具调用的 digest 没有 Layer A 表头锚，
  Digester 又用裸括号写锚 → 0 匹配。
- 对照（同一检查器）：官方格式 7–8% 零锚 vs Layer A′ 10–17%（30 易床零调用题更多，差值主要是床构成）。
- 修复：Layer A′ 的 motif/死链锚点加反引号（commit 已落），严格降低零锚率。

### 8.3 其余噪声定性

- Bing 抓取失败 ×13、Wikipedia 403 ×17：任务侧搜索抖动（serper 主路无碍），环境已知行为。
- `Task exception was never retrieved` ×12：replay 线程 loop 收尾的 httpx 噪声，主环无碍。
- IV-4 verdict 锚格式警告 ×1（R2，被弃轮）：候选自写锚不合契约，vendored 校验按设计拦截。
