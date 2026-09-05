# M28 过夜作业 Runbook（08-26 02:40 起）

**本文件是今晚在飞任务的权威 SOP。compaction / 重连后先读它，再动手。**
上一代规则见 docs/ghx-m24-overnight-runbook.md（启动模式 line ~235、监控语法沿用）。

---

## 0. 状态快照（写于 08-26 02:40）

- **裁定**：论文证据白名单 = M22_L0_ghx0 + M26_100x16 + M26_100x16b + PROBE_*。M28 双种子是给每臂凑 ≥2 种子的正式战役。
- **预检五门**：①床✓ ②dry-run✓ ③网关探针✓（flash 3.1s / pro 0.7s）④全测试✓（2791 绿）⑤smoke：
  - **G6 smoke（bzzs1q8zu）：完成，绿**。R0 3/3 → R1 2/3，evolve ok；R1 decision.md 真 ship（cone_sigs、Level-2 round-trip、portfolio audit 全活体）；config 与 M26b 字节级一致；退出时 `Event loop is closed` = Windows asyncio 收尾噪声，无害。
  - **L0 smoke（b9chu9jul）：在飞**，02:32 时在 R1 evolve 应用 C-R1-01。等完成通知。
- 磁盘已清 15G（可用 50G）。smoke 目录 M28_smoke_L0 / M28_smoke_G6 = **非证据**，战役健康后可整目录删。
- 冻结线：**8-27 实验硬冻结**。按 103×3≈31min/轮 估计，16 轮 ≈ 10–14h，今晚 3 点起飞 → 明天下午前收官，赶得上。

## 1. 触发链

1. **等 b9chu9jul 通知** → L0 smoke 体检：curves.json 两条、R1 decision/summary 在、正文零 Traceback（收尾噪声不算）、**L0 臂特异性 = 无 graph_evidence 目录**（level 0 不该有）。
2. 两臂全绿 → **宣布 go** → 按 §2 错峰点火。任一红 → 停，查根因，不带病起飞。

## 2. 点火（错峰，禁串行——两臂必须同窗交错飞）

从 repo 根、`.venv312`，按 M24 runbook line ~235 的 Start-Process detached 模式（存活性已验证），**新日志文件名**，`-WindowStyle Hidden`：

**先 L0 臂**（无 GHX env）：
```
python recipe/gaia_evolver/run_meta_aegis_ghx.py --tasks recipe/gaia_evolver/data/webthinker_gaia_dev.json --max-tasks 0 --num-rounds 16 --k-all 1 --search-backend serper --no-early-stop --evolve-max-steps 400 --ghx-level 0 --model deepseek-v4-flash --meta-model deepseek-v4-pro --run-tag M28_L0_s2
```
日志：`m28_l0_s2_console.log` / `m28_l0_s2_err.log`。env 只设 `PYTHONUTF8=1`。

**隔 3–5 分钟，GHX 臂**：
```
python recipe/gaia_evolver/run_meta_aegis_ghx.py --tasks recipe/gaia_evolver/data/webthinker_gaia_dev_nopixel.json --max-tasks 0 --num-rounds 16 --k-all 1 --search-backend serper --no-early-stop --evolve-max-steps 400 --ghx-level 6 --runtime-policy --noop-audit 25 --model deepseek-v4-flash --meta-model deepseek-v4-pro --run-tag M28_GHX_s2
```
日志：`m28_ghx_s2_console.log` / `m28_ghx_s2_err.log`。env：`PYTHONUTF8=1` **加 `HARNESSX_GHX_FLIP_LEDGER=1`**（设→点火→立即清掉，别污染后续 shell）。

要点：`--max-tasks 0` 必须显式传（默认 1 的坑）；launcher 自动读 .env（setdefault）；两臂任务文件不同是刻意的（L0=103 题复刻 M22 床，GHX=100 题 nopixel 复刻 M26b 床）；`--k-all 1` 是已登记的改进偏差（M22 R0 当年 k=2）；床未改（#31 不先堵）。

## 3. 起飞后 10 分钟内体检

- [ ] 双 python 垫片检查：每臂一对（venv 垫片 + 系统 worker），查 ParentProcessId 配对；**记 PID 进 §7**。误杀垫片 = 杀 run。
- [ ] `runs/M28_L0_s2/R0/config.yaml`、`runs/M28_GHX_s2/R0/config.yaml` 生成；G6 臂 processor 组对齐 M26b，L0 臂对齐 M22。
- [ ] base_url 只指 litellm 网关（合规只看 base_url）。
- [ ] R0 第一批任务 session 目录开始长文件。
- [ ] R0 curves 首条 total_tasks：L0=103、GHX=100。

## 4. 过夜监控

**哨兵**（background Bash 循环，每 10 min 查一次，触警即退出→回通知）：
- 停摆：任一 run 目录最新 mtime > **75 min** → 报警（先跑 scratchpad/gateway_probe.py 查网关，再看 err.log，**不许自动杀进程**）。
- err.log 出现 Traceback / ROLLBACK / StageP 异常模式 → 报警。
- 任一臂进程对消失而 curves.json 未到 16 条 → 报警。
- 心跳：每 ~3h 强制退出一次做例行轮界检查（重启哨兵续飞）。

**轮界例行**：curves.json 追条（pass/cost/evolve_status）；第一个 noop 域轮做 carried 账审计（M24 规矩）；单轮成本 > $150 记异常（M25 均值 ≈ $86/轮）。

**在飞禁令**：禁改任何被 import 的码；禁直连厂商端点；vendored harnessx/aegis/ 零字节；.env 值不打印；白名单 run 目录不许动。

## 5. 零干扰对（战役稳定后点，预算 ~$10–15，已在批准清单内）

两臂各自健康渡过 R0→R1 后起飞：10 题 × 3 rep × 2 臂，同窗交错，唯一差异 `HARNESSX_GHX_UNFOLD`，低并发（≤2）不扰战役。目的：补 ruling II 打掉的零干扰证据（CH1 Q2）。**未批**的两项别碰：notes 臂 ~$100、path-1 refeed ~$30。

## 6. 安静时段的两条工作流（优先级低于监控）

**6a. 论文逐章逻辑审计（用户 08-26 夜指令，主filler）**：对 THESIS-OUTLINE-V5.tex 全章（CH1–CH8+附录）做核查，产出 `experiments/docs/thesis/CHAPTER-VERIFY-0826.md`，每章简短 bullets 早晨交付。审计协议：
- 每章 \claim 是否只依赖它之前已建立的东西；章尾是否为下一章递刀（逻辑链 > 一切）。
- 每个数字/事实核对白名单台账（V4 F31–F40 + V3 F1–F30）；抓禁数残留（pre-M22、M24/M25 当证据、1.04 头条、τ²、M14 −9、E2 数字）。
- **用户裁定：结果不好没关系，分析必须优秀合理**——负结果按假设证伪科学写，禁对冲禁遮掩。
- CH2 bullets 已交用户待逐条意见，审计不改口径只记问题。

**6b. 免费离线数据活**：M26b 同配置翻转率（noop 轮）；白名单 F9 重算；药存活曲线表；majority@k 离线模拟；proof_stats.py 固化进 experiments/analysis。

## 7. 实时台账（边跑边填）

- **G6 smoke 终检（02:40 完成）：绿**。R0 3/3→R1 2/3，真 ship 裁决（cone_sigs/Level-2 round-trip/portfolio audit 全活体），config=M26b 字节级一致，退出仅 asyncio 收尾噪声。
- **L0 smoke**：02:07 起飞，R0 2/3（$1.78）；R1 任务 3/3 完成后 evolver 长审（400 步帽内正常），02:55 C-R1-01、03:10 C-R1-02 两候选出炉，持续活跃无停摆。等 decision+收官。
- **L0 smoke 终检（03:31 完成）：绿**。R0/R1 各 2/3，R1 evolve 全链后裁 noop（两候选+verdicts+decision 在），无 graph_evidence（臂特异性对），exit 0。五道门 5/5 全过，宣布 GO。
- **L0 臂点火 03:38:15**：shim **12712** / worker **3692**。103 题 ✓、level 0 零旗 ✓、ROUND 0/15 起跑、首 PASS 03:38:39。日志 `runs/M28_L0_s2.{out,err}.log`。
- **GHX 臂点火 03:40:35**：shim **23496** / worker **16392**。100 题 nopixel ✓、runtime-policy 空表 ✓、L6 十六旗 set+effective ✓、ROUND 0/15 起跑。日志 `runs/M28_GHX_s2.{out,err}.log`。已知良性噪声：WKD legacy-config note（M26b 同款）。
- 轮界记录：
  - **心跳①（06:45）双绿**：L0 = R0 51.5%($56.0)→R1 52.4%($50.5) evolve ok，R1 batch 05:32 起；GHX = R0 59.0%($45.6)→R1 53.0%($54.1) evolve ok，R1 batch 05:47 起。起点均在参考带内（L0 53/103 vs M22 种子 57；GHX 59/100 vs M26b R0 56）。夜段哨兵零警报（真值：停摆/进程检查活性正常；Traceback 比较因 count() 双写 bug 形同虚设——已修，基数初始化为当前值，哨兵已重启）。
  - **零干扰对 06:5x 点火 → 07:1x 双臂收官 = F43（Q2 闭合）**：两臂各 30/30 真完成；9/10 题向量逐位同（7 金丝雀 PPP=PPP、2 恒败 fff=fff）；分歧题=在案 flaky 金丝雀 3ff6b7a9（F33 23/24 缺口）挂在**无记录臂**；22/30 vs 24/30 噪声内且方向反于干扰。产物+读法=`runs/PROBE_ZIF/INDEX.md`；tex CH1 Q2/CH6 6.2 已回填。
- **心跳②（08:5x，由哨兵 Traceback 警报触发）**：警报=假阳性——GHX err.log 新增 5 个 Traceback 全为 **httpx/httpcore aclose 收尾噪声族**（对 litellm 已关闭连接的清理，M26 监控过滤过的同族），战役照跑。哨兵已加族过滤（按 Traceback 记录分割、不含 aclose 才算可疑；当前可疑=0）并重启。曲线：L0 = 51.5→52.4→**60.2**（R2，全 evolve ok）；GHX = 59.0→53.0→**58.0**（**R2=首 noop-scoped 轮**）。**首 noop carried 账当场审过**：25 fresh+75 carried、承接分 75/75==R1、steps 全 0、总分 58 对账 ✓（M24 铁律满足，无需停跑）。节奏 ~1.7–2h/轮 → 16 轮预计 08-27 早晨收官（仍在冻结日内）。
- **心跳③（11:58，静默心跳）**：L0 R0–R4 = 51.5/52.4/60.2/62.1ⁿ/60.2ⁿ（R3/R4=全床同配置重测窗，seed-2 F15 数据自动积累），进 R5；GHX R0–R4 = 59.0/53.0/58.0ⁿ/54.0ⁿ/58.0（noop 批费 $12.5/$18.6 省钱机制可见；R4 新 config 满批），进 R5。R3 carried 抽查全对（25+75/零错/54=54）。可疑 TB 双零。批面成本 5 轮 ~$466。预计两臂 8-27 凌晨—上午收官。
  - **心跳④（~15:10，静默心跳）**：L0 R0–R6 = 51.5/52.4/60.2/62.1ⁿ/60.2ⁿ/64.1/**60.2ⁿ**（R6 又一个全床同配置窗），进 R7；GHX R0–R7 = 59.0/53.0/58.0ⁿ/54.0ⁿ/58.0/62.0/57.0/**69.0**（R7 满批 $33，evolve ok——单轮新高，噪声包络内先不读大），进 R8。可疑 TB 双零、双进程对完好（12712/3692、23496/16392）。GHX 无新 noop 轮 → 无 carried 审计到期。哨兵重启（bk47j8zq6）。
  - **心跳⑤（~17:0x，哨兵被外部停掉后手动接班）**：L0 R0–R7 = …/64.1/60.2ⁿ/**65.0**（进 R8）；GHX R0–R9 = …/57.0/**69.0/67.0/64.0ⁿᶜ**（进 R10）。**R9 carried 账审过**：30 fresh（波动族>25 地板，R6–R8 高波动段全收）+70 carried、承接分 70/70==R8、steps/cost 全 0、总分 64 对账 ✓。顺产数据：R9 波动族重翻 11/30=36.7%，与 F41（M26b 汇总 41.6%）同向——种子 2 旁证，收官后并入 F41。可疑 TB 双零。哨兵重启（bdwe04oim）。
  - **心跳⑥（~20:1x，静默心跳）**：L0 收到 R9（R7 65.0 → R8 64.1ⁿ → R9 62.1ⁿ，两个全床同配置窗），进 R10，剩 6 轮；GHX 收到 R12（R10 66.0 → R11 67.0ⁿᶜ → **R12 73.0**——后半程走强 64→66→67→73，仍按包络纪律不读大），进 R13，剩 3 轮。**R11 carried 抽查全过**：25+75、承接分 75/75==R10、steps/cost 全 0、总分 67 对账 ✓；波动族重翻 13/25=52%（F41 种子-2 第二点，收官后并入）。可疑 TB 双零。哨兵重启（bc4t8jcto）。
  - **心跳⑦（~22:0x，哨兵两次被外部停，手动接班）**：GHX 收 **R13=71.0%ⁿᶜ**（后半程 66/67/73/71），进 R14，**剩 2 轮**；L0 仍在 R10（轮内正常写盘）。**R13 carried 抽查全过**：25+75、承接分 75/75==R12、steps/cost 全 0、总分 71 对账 ✓；波动族重翻 8/25=32%（F41 种子-2 第三点：36.7%/52%/32%，横跨 M26b 值 41.6%）。可疑 TB 双零。哨兵重启（b2bmozq0j）。
- 事故：（无；假阳性一次，已修哨兵；心跳④后哨兵一次被外部 kill，非战役事故）
- **写作线（03:10 前已完成并 commit）**：全 tex 逐章审计毕（CHAPTER-VERIFY-0826.md，脊柱紧、六处修改落地）；锥例白名单重导（n=33）；F9 混杂定性（±4σ/−1.5σ）；**F41 波动族持久性 41.6%**；**F42 majority@k 模拟（投票不治 wrong-closure）**；proof_stats 固化。commits：eaa3653、06aa3eb。哨兵脚本已备（scratchpad/watcher_m28.sh）。

## 9. 计划内暂停（08-26 ~23:00 用户令：下一轮后停所有，重启电脑）

**执行机制**：pause_m28.sh 自动等待并执行。**挂载方式=Start-Process 脱离进程**（会话内后台任务今晚屡被 Esc 杀掉，第一次挂载 bqlvwpiso 阵亡后改脱离式；bash 垫片链 PID 13236→40956）。**进度与"安全重启"信号写在 `runs/M28_pause_waiter.log`**，末行出现 `ALL DOWN — safe to reboot` 即可重启。逻辑——
- L0：等 R12 落盘（curves≥13 条）**且 R13/config.yaml 出现**（R12→R13 evolve 完整落地，元链无洞）→ 杀 M28_L0_s2 进程对。
- GHX：R15 是末轮，优先自然退出；若 16 条 curves 后终末 evolve 拖过 25 min 宽限 → 杀（16 轮分数已全在盘上，截掉的只是无人使用的最后一次审议，记档即可）。
- 哨兵已提前停掉（计划内杀进程不算事故）。
- **两臂全停后即可重启电脑**。自查命令（PowerShell）：`Get-CimInstance Win32_Process -Filter "Name like 'python%'" | ? { $_.CommandLine -match 'M28_' }` 无输出 = 安全。

**重启后续飞 SOP（L0 剩 R13–R15 三轮，~5.5h；GHX 无需续飞）**：
1. 若 R13 有残留批文件（`runs/M28_L0_s2/R13/raw|sessions` 里有东西），先删残留——R13 批会整轮重跑。
2. repo 根、`.venv312`、env 只设 `PYTHONUTF8=1`，Start-Process detached（M24 runbook line ~235 模式），**新日志名** `M28_L0_s2.resume.{out,err}.log`（-RedirectStandardOutput 会覆盖旧文件，不许复用旧名）：
```
python recipe/gaia_evolver/run_meta_aegis_ghx.py --tasks recipe/gaia_evolver/data/webthinker_gaia_dev.json --max-tasks 0 --num-rounds 16 --start-round 13 --k-all 1 --search-backend serper --no-early-stop --evolve-max-steps 400 --ghx-level 0 --model deepseek-v4-flash --meta-model deepseek-v4-pro --run-tag M28_L0_s2
```
3. 起飞后体检：双 python 对、R13 批在 103 题满床跑、curves.json 仍是接续写（13→14→…）。
4. **标签补记规则（resume 已知坑）**：`--start-round` 把恢复轮的 evolve_status 写死为 "ok"。核对 `R13/decision.md` 的真实裁决——若是 noop，**不改 curves.json 原文件**，在 `runs/M28_L0_s2/INDEX.md` 记一条"R13 evolve_status 真值=noop（resume 强制标 ok），F15/F41 窗口簿记按 decision.md 对齐"，分析脚本以 decision.md 为准。
5. 冻结线核算：早 8 点续飞 → 午后收官，仍在 8-27 冻结日内。

### §9-实况（08-26 23:30–23:45，与上面预案的偏差）
- **重启发生在暂停器触发之前**（waiter 日志空白）：被杀的是 L0 的 **R11→R12 evolve 中段**（非 R12 批）与 GHX 的 R15 批。
- **GHX 已于 00:27 以 `--start-round 15` 复飞末轮（勘误：此前一度误判截断）**。误判根因=拿字节哈希对比配置；真相（run_meta_aegis_ghx.py:538）：R{k}/applied/merged.yaml = 该轮末 evolve **commit 时刻**的合并 = 下一轮真配置，语义 diff 唯一差异 tracer.base_dir。复飞轮头 config hash 355910e0 与被杀前 R15 原配置字节级一致，C-R15-03 原样在跑，16/16 满编可期。详见 runs/M28_GHX_s2/INDEX.md 勘误段。**规则沉淀：本库一切配置等价性判定必须语义对比（yaml 解析、忽略 tracer.base_dir），字节哈希无效。**
- **L0 已于 23:38 以 `--start-round 12` 续飞**（非预案的 13）：seed=R11/config.yaml（resume 行在 .resume.err.log），R12 满床在跑，金丝雀首过。R11→R12 evolve 成 M26 型元链洞（一处）；R12 条目 evolve_status="ok" 为强制值，真相=同配置直跑，(R11,R12) 按同配置对读。详见 runs/M28_L0_s2/INDEX.md。
- 网关双模型探针 OK（flash 2.0s / pro 1.4s）。哨兵改 L0 专用（watcher_l0_resume.sh）。预计 R15 落盘 ~08-27 06:40。
- **GHX 收官（08-27 凌晨）：16/16 满编，R15=72.0%，进程自然退出（仅 asyncio ResourceWarning 噪声）**。终曲线 59.0/53.0/58.0ⁿ/54.0ⁿ/58.0/62.0/57.0/69.0/67.0/64.0ⁿ/66.0/67.0ⁿ/73.0/71.0ⁿ/72.0/72.0——终值 72.0%（=R14，复飞轮与被杀前趋势无缝），峰值 73.0%（R12）。
- L0 续飞首轮 R12=61.2% 落盘：与 R11=59.2% 差 +2 题，同配置对读数在包络内——续飞质量的活体旁证。剩 R13–R15。

## 8. 早晨汇报模板

战役状态（轮数/曲线/成本/事故）→ 零干扰对结果 → go/no-go 后续 → **回到写作：CH2 bullets 已交付待用户逐条意见，改完进 CH3**。

## 10. 08-27 追加战役（用户令二连）
- **M26b 补跑收官（16:40 前后）**：R14=62.0% / R15=67.0% 双满批（$41+$42），16/16 满编；(R13,R14) 复飞对翻转 18.0%/摆动 −4 = resume 等价性第三证。白名单升 **66 轮/5,813**。良性噪声族新增两员并入哨兵过滤：`ConnectionResetError/_call_connection_lost`、`wait_for`+`TimeoutError` 超时对。
- **M29 种子-3 双臂（16:46/16:47 起飞,用户令"再跑一遍16轮"）**：M29_L0_s3（103 床,level 0,shim 36376/worker 41424）+ M29_GHX_s3（100 nopixel,level 6+FLIP_LEDGER+runtime-policy+noop-audit 25,shim 8072/worker 17432）,命令逐项复刻 M28 §2,日志 `runs/M29_*.{out,err}.log`。起飞体检过（臂架构/双床/首批完成）。ETA 08-28 午后;收官后 = 2 臂 × 3 种子 × 16 轮,F15/F41 三点成线,F44 扩为 F44+F45 或并表。

## 11. 08-28 网关中断 → 复飞 + L0 床切 100（实况）
- 02:54 起 litellm 网关 SSL EOF，两臂任务 FAIL steps=0 cost=$0；04:3x 判杀两臂（"端点不健康就等"），污染轮隔离：L0 curves 截回 R0–R6（R7/R8 → `*_poisoned_gateway/`），GHX R11 → `R11_poisoned_gateway/`（curves R0–R10 未动）。恢复监视器脚本首版 exit 4 阵亡，改为人工重探。
- 14:5x 探针双模型 OK，14:59 双臂同窗复飞：L0 `--start-round 7`（seed R6/config.yaml）、GHX `--start-round 11`（seed R10/config.yaml），日志 `runs/M29_*.resume.{out,err}.log`，shim 37968/20792。
- **用户令"跑 100 题而不是 103"**：L0 臂自 R7 起改 `webthinker_gaia_dev_nopixel.json`（103 的有序子集，去 3 道 pixel 题），与 GHX 同床。M29_L0_s3 的跨轮读数一律按 100-子集从 task_history.jsonl 重算（R0–R6 分母 103 的 curves 数字不直接用）。细则见两臂 INDEX.md。
- 轮级监视器（Monitor 工具）已改指 `.resume.out.log` 重新上岗。
- **15:5x 勘误（GHX 臂）**：污染实为 R9–R11（R9/R10 各 25 道 fresh 全 cost=0；R8 末 evolve 断网出错）。杀停 14:59 复飞的 R11 谱系，清洗 task_history/audit/curves/journal 到 R≤8（备份齐），R9–R12 目录隔离，改 `--start-round 9`（预检以 R6/config.yaml≡R9/config.yaml 复位验证谱系）。**教训入 SOP：断网事故隔离必须逐轮核 fresh 行 cost_usd=0，不能只看杀停时的当前轮。** 细则见 M29_GHX_s3/INDEX.md。L0 臂 task_history 仍含被杀 R7/R8 的污染行（level 0 不读 volatile family，分析按 last-row-per-(task,round) 去重即可；收官后同法清洗备份）。

## 12. M29 种子-3 收官（08-29 02:5x L0 / 04:0x GHX）
- 两臂 16/16。L0_s3（100-子集）66→63，F15 类比 **19.5%**（117/600，6 窗=4 noop+2 crashed，摆动 −8..+5）；GHX_s3 57→76（峰 76），F41 类比 **31.5%**（51/162，6 noop 窗），carried 6/6 对账。三种子 F15：20.2 / 20.1 / 19.5；F41：41.6 / 37.7 / 31.5。
- 干净费用 $882 + $584；白名单新增评测 1,621 + 1,162。隔离数据不计。
- 记档：F45（STORY-V4 §2）、tex 1.8/5.1/6.3b/6.4/7.3/7.x/App C 改三种子、脚本 `experiments/analysis/audit_m29_seed3_flips.py`、两 INDEX.md 收官段。
- 崩溃家族（raw JSONL 含二进制 → evolve crashed）本战役 ×3（GHX R5→R6、L0 R8→R9、R12→R13）+ M26b ×1，收官后缺陷条目待修（写端转义/读端跳坏行）。
- SOP 沉淀：①断网隔离逐轮核 fresh 行 cost=0；②复飞前语义比对 seed；③resume 后清洗 task_history/audit/curves/journal 到干净前缀并留备份；④床切换只允许有序子集且读数按子集重算。
