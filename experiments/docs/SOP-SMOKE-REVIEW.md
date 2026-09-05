# 冒烟轮审查 SOP

> 适用：`run_variant_pool` 的缩规模彩排（当前实例 `e2_dress`；未来 K=8 dress 同用此单）。
> 定位：**审管线，不审分数。** 冒烟轮三不看——分数高低（6 题 = 每题 16.7pp 粒度，纯噪声）、
> 退化签名（轮数太短）、fork/retire（K=1 结构上没有）。看见分数波动先查有没有 ship，
> 无 ship 而分数动 = 噪声，不是发现也不是故障。
> 所有命令从仓库根目录、Git Bash 执行；`TAG=e2_dress` 按实际替换。

```bash
TAG=e2_dress
RUN=recipe/gaia_evolver/runs/$TAG
LOG=recipe/gaia_evolver/runs/$TAG.console.log
```

---

## 0. 产物地图（实测布局，2026-08-10 对 e2_dress 核）

| 路径 | 是什么 | 审查用途 |
|---|---|---|
| `$RUN/pool_report.md` | 人读总报告 | **第一站**，§1 粗检全在这 |
| `$RUN/pool_report.json` | 同上机器版 | 提数 |
| `$RUN/comparison.json` | 逐轮 rounds 列表 | oracle_ceiling 的输入；逐轮分数/ship 核对 |
| `$RUN/pool_states.json`、`$RUN/R{n}/pool_state.json` | 池状态（全程/每轮） | ship/fork/retire 判定的原始依据 |
| `$RUN/experiment.lock.json` | 参数锁 | §2 参数核对 |
| `$RUN/data/task_history.jsonl` | 逐题**诊断**史（outcome/failure_category/implicated_components——**无 cost/steps/elapsed 字段**） | §3 归因；~~§4 记账~~（勘误①：记账真源见下行） |
| `$RUN/**/sessions/**/*_state.json` | attempt 级记账真源（键 `cumulative_cost_usd`/`cumulative_tokens`/`step`；按路径分 active_pool / candidate_gate / meta_workspace 三桶） | §4 记账抽查、§5 刻度①②、budget 定位 |
| `$RUN/data/rejected_candidates.jsonl` | 被拒候选 + 理由 | §3 候选问责 |
| `$RUN/R{n}/active_pool/V*/trajectories/` | 该轮上床轨迹（`<tid>.md`，attempt≥2 为 `<tid>.a2.md`） | §2 计数、§4 抽查 |
| `$RUN/R{n}/V*/pipeline_audit.json` | 该轮 meta 管线审计 | **零候选轮问责的第一现场** |
| `$RUN/R{n}/V*/pipeline/candidates/C-R{n}-XX/retry_XX/` | 每候选每重试的 meta 工作区 | §3 retry 消耗、空手取证 |
| `$RUN/V0/config.yaml` | 种子配置 | §2 不动产核对 |
| `$LOG` | 控制台全程 | fallback / early-stop / 崩溃取证 |

---

## 1. 五分钟粗检（只开 `pool_report.md`）

- [ ] 轮数齐：Per-round curve 行数 = `--num-rounds`
- [ ] 分母对：`tasks/denominator` = `--max-tasks`（全量时 = 103）
- [ ] `infra failures = 0`；非零则先去 `task_history.jsonl` 定位再往下走
- [ ] `budget exhaustion` 数值记下（≠0 不算失败，§4 要定位到题）
- [ ] lock 哈希存在（报告头部 `lock:`）
- [ ] **attempts 恒等式**（本 SOP 最重要的一条粗检）：

  ```
  attempts_total ?= Σ_轮 (该轮上床的配置数 × tasks × pass_k)
  ```

  用它反推**候选到底上没上床**。e2_dress 实例：36 = 3 轮 × 1 配置 × 6 题 × 2
  ⇒ 每轮只有 active V0 上床，**4 个候选零上床**。若候选各自全床评，R2 应多出 4×12=48。
- [ ] 分数波动解读：先看 `variants by round` 与 candidate 列。无 ship 而 pass@2 动
  （e2_dress: 1.00→0.83→1.00，variants [1,1,1]）= 单题噪声翻转，记录，不追。

---

## 2. 结构与参数完整性

- [ ] 每轮目录齐：`R0..R{n-1}/pool_state.json` 都在
- [ ] 轨迹计数逐轮 = 上床配置数 × tasks × pass_k：

  ```bash
  for r in $RUN/R*/; do
    echo "$r $(find $r -path '*trajectories*' -name '*.md' | wc -l)"
  done
  ```

- [ ] 参数锁核对（patience / seed / candidate_mode / pass_k 应与发射单一致）：

  ```bash
  grep -l 'candidate_mode' $RUN/*.json          # 先定位落在哪个 json
  python -c "import json,sys;d=json.load(open(sys.argv[1]));print({k:d[k] for k in d if k in ('patience','seed','candidate_mode','pass_k','concurrency')})" <上一步命中的文件>
  ```

- [ ] 种子配置未被原地改动：`diff $RUN/V0/config.yaml $RUN/R0/active_pool/V0/config.yaml`
- [ ] 进程善终：`grep LAUNCHER_EXIT $LOG` 存在且 code=0（ResourceWarning 噪声可忽略）。
  **勘误③兜底**：非 launcher 启动的 run 无此记录——以"三轮产物齐（R* 目录 + pool_report 双格式）
  且日志尾无真实 Traceback（`I/O operation on closed pipe` 类拆卸噪声除外）"替代判定，并在记录里注明"善终为推断"。

---

## 3. meta 三元出活率（冒烟轮的主审对象）

- [ ] 每轮候选数（report 的 candidate 列 + 目录数）：

  ```bash
  for r in $RUN/R*/; do echo "$r $(find $r -maxdepth 4 -type d -name 'C-R*' | wc -l)"; done
  ```

- [ ] **零候选轮逐轮问责**：candidate=none 的轮，开该轮 `V*/pipeline_audit.json`，
  必须能回答"digester/planner/evolver 哪一级没出活、为什么"。答不出来 = F3。
- [ ] retry 消耗率：`find $RUN -type d -name 'retry_*' | wc -l`，除以候选总数。
  接近 `--evolve-retry` 上限 = meta 模型在这个栈上勉强出活，全量前要处置。
- [ ] fallback 计数（LLM 级失败回落确定性实现）：

  ```bash
  grep -c 'llm_digester_fell_back' $LOG; grep -c 'llm_planner_fell_back' $LOG
  ```

- [ ] commit-bounce / 空手 end_turn 触发次数：`grep -ci 'bounce' $LOG`（关键词以实际日志为准）
- [ ] 被拒候选每条有 reason：`wc -l $RUN/data/rejected_candidates.jsonl` + 抽 2 条读 reason 字段
- [ ] **候选归宿全部说清**：生成数 = ship 数 + rejected 数 + 悬置数（run 在该轮终止）。
  ⚠ K=1 下 ship 不改变 variants 计数（覆盖同名谱系），**不能**从 variants 列推断有没有 ship，
  以 `pool_state.json` / `comparison.json` 为准。

---

## 4. 评测与记账正确性

- [ ] 抽 2 题人工核 judge：开 `R{n}/active_pool/V0/trajectories/<tid>.md`，
  读最终答案 vs `task_history.jsonl` 里该题的判分，人工同意才算过
- [ ] budget exhaustion 定位到题：在 `task_history.jsonl` 里找 cap 触发的 attempt，
  判断 `--max-cost 120`（假价、每 attempt 各自一顶）是否被正常任务误触
- [ ] 步数分布：数全 20 步截断的 attempt 占比（卡上限 = 题做不完；冒烟可容忍，全量要记录）
- [ ] masking gap 记录：pass@2 − pass@1（§7.1，pass@2 会掩盖单 attempt 退步）
- [ ] **外部集成覆盖与搜索后端身份**（每个声明的外部依赖至少被真实踩过一次）：

  ```bash
  grep -rli 'websearch' $RUN/R*/active_pool/V*/trajectories/ | wc -l   # WebSearch 覆盖轨迹数
  grep -ci 'SERPER_API_KEY' recipe/gaia_evolver/runs/${TAG}_launch.cmd # key 真进了 env
  grep -c 'Serper search failed' $LOG                                  # serper 硬失败数
  grep -rl 'SEARCH UNAVAILABLE' $RUN/R* --include='*.md' | wc -l       # 静默降级下限
  ```

  ⚠ 盲点：`serper` 后端在 key 缺失或空结果时**静默**回落内建链
  （`serper_search.py:128-135`），产物层证明不了单次调用的后端身份。
  要可证明，用 `--search-backend serper_only`（降级全显式：ERROR/WARNING +
  3 次重试 + 诚实空答案，永不碰内建链）。

---

## 5. 成本刻度提取（冒烟轮最值钱的产出，四个数）

| # | 量 | 来源 | e2_dress 填入 |
|---|---|---|---|
| 1 | 每 attempt 均值 token / 假价 / 墙钟 | `task_history.jsonl` 聚合 | |
| 2 | 每轮 meta 开销（digester+planner+evolver×候选×retry+critic） | meta_workspace / 日志 | |
| 3 | 候选上床范围（§1 恒等式的结论） | attempts 恒等式 | 零上床 |
| 4 | retry 消耗率 | §3 | |

外推公式（全量单臂）：

```
内层体量 ×= (103/6) × (16/3) ≈ 92     # V0 床评部分
meta体量 ×= 16/3 ≈ 5.3
全臂报价 = 92×(彩排内层成本) + 5.3×(彩排 meta 成本)，再 ×3 seeds
墙钟 ≈ attempts_total × 均值时长 / concurrency(10)
```

⚠ **定价前置条件**：候选评测时点的语义必须先弄清（见 §6 F4）。若全量运行里候选
要上床（每轮 +4×103×2 attempts），内层另有一个 ~4× 分支，报价差 4 倍。

---

## 6. GO / NO-GO 门

**PASS（全部满足才 GO 全量）**

1. §2 结构完整、参数锁与发射单一致、LAUNCHER_EXIT=0
2. §1 attempts 恒等式成立**且每一项可解释**
3. ≥1 轮产出满编 4 候选，且每个候选归宿说得清
4. 零候选轮在 `pipeline_audit.json` 里有可读死因
5. fallback 率 < 50%（三元名义上是 llm，老回落等于没在跑论文形态）
6. infra failures = 0 或逐条可解释
7. §5 四个刻度数全部提取成功

**失败分级**

| 级 | 判据 | 处置 |
|---|---|---|
| F1 管线死 | 中途崩、轮目录缺、EXIT≠0 | 修复后整轮重跑 |
| F2 meta 出活不足 | 多轮零候选且 audit 归因于模型空手 / fallback≥50% | 调 `--evolve-retry`、审 prompt/brief、或换 meta 模型；重跑冒烟 |
| F3 记账缺失 | audit/lock/history 字段缺，无法问责 | 修代码，重跑冒烟 |
| F4 语义未明 | 候选评测时点说不清（gate 前拒？下轮才 apply？） | **读 `pipeline_audit.json` + 代码定位，不重跑**；弄清前禁止给全量报价 |

**再说一次**：分数低、分数波动，都不在失败判据里。

---

## 7. 审查记录模板

```markdown
## 冒烟审查记录 — <TAG>
- 审查人/日期：
- commit / lock 哈希：
- §1 粗检：PASS / FAIL（恒等式：attempts=___ = ___）
- §2 结构参数：PASS / FAIL
- §3 出活率：候选 __/轮均，retry 率 __%，fallback __次，零候选轮死因：__
- §4 记账：抽查 __题同意 __题；budget 触发：__；20 步截断率 __%
- §5 刻度：attempt=__tok/__$/__s；meta/轮=__$；候选上床：__；全臂报价=__$，墙钟=__h
- 裁定：GO / NO-GO(F_)
- 遗留：
```

---

## 附：e2_dress 首次套用的即时发现（2026-08-10，未做完整审查）

1. **R1 候选 = none**——R0 零候选是设计使然（lock 里 `baseline_round_policy:
   R0_settled_active_only_evolution_starts_R1`，R0 只坐实基线、演化从 R1 起）；
   要问责的只有 R1，死因待开 `R1/V0/pipeline_audit.json`（§3）
2. ~~attempts=36 ⇒ 候选零上床~~ **勘误①（2026-08-10 完整审查改判）**：36 恒等式只覆盖
   active 池；候选床评在 candidate-gate **独立记账**（`R2/V0/candidate_gate/C-R2-04/` 12 条
   attempt 轨迹 = 1 候选 × 6 题 × pass@2）。真实归宿 4/4 说清：C-R2-01 提案层拒
   （bucket missing + 无预测翻转）、C-R2-02 meta 140.8s 空手、C-R2-03 证据门拒——三个
   零上床；C-R2-04 上床后 SEESAW_REGRESSION 拒（improved=[]）。**F4 闭案**：候选评测 =
   同轮 settlement 前 candidate_gate，无悬置；全量报价候选项 = `存活率×4×103×2`（本次存活率 1/4）
3. **6 题全是 GAIA Level 1**——`--max-tasks 6` 切片偏斜；全量（=0）无此问题，但后续冒烟建议按 level 分层抽样
4. ~~budget exhaustion ×2 撞 max-cost 假价顶~~ **勘误（完整审查定位）**：无 attempt 撞
   cost cap（near-cap 0）——两次 exhaustion 是 active 池里的 **20 步截断**（步预算耗尽），
   即内层截断率 2/48=4% 的那两条；meta 会话另有 7/19 撞步顶（37%，另记）

> **完整审查记录：`experiments/docs/REVIEW-e2_dress-AUG10.md`**（GO 裁定 + 四条遗留：
> 分层抽样、SOP 勘误、墙钟刻度源、搜索栈平价/Serper 静默缺席）。
5. 分数 1.00→0.83→1.00 且 variants 恒 [1,1,1]：教科书式单题噪声翻转，无需处理（§1 解读规则的实例）
6. **serper 用上了，但有 2 次静默降级**——key 在 env（launcher 核实）、console 零
   `Serper search failed`、key 实测活（HTTP 200）；2 条轨迹含 `[SEARCH UNAVAILABLE]`
   = serper 空结果静默落内建链后全链失败。项目裁定（serper_search.py:178）本就是
   "内建链不可用、永不该服务查询"⇒ **全量改 `--search-backend serper_only`**，
   两臂同值，进冻结包
