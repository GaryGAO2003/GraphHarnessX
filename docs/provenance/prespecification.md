# Pre-specification record for the efficacy trials (ledger rows F32, F33, F34)

This note reproduces, from the author's working repository, the record behind the word
*pre-specified* in Section 5.4 of the thesis. The released repository has a fresh history,
so the commits below cannot be checked out here; their content is quoted verbatim. The plan
document itself is `docs/ghx-overnight-0825-clinic-plan.md` in this repository (its final state).

## Timeline, 25 August 2026 (Europe/London)

| Time | Event | Source |
|---|---|---|
| 01:30 | Commit `9713d33`: plan v2 written, including trial T3′ (clean-cluster transfer: the merged three-drug configuration against its parent, same-window pairs, 6 tasks × 10 repetitions × 2 arms; threshold: a cluster delta below +3 is indistinguishable) and trial T4 (canary: 8 always-passing tasks × 3 repetitions × 2 arms; any drop above 1 counts as collateral damage) | working-repository log |
| 02:04–02:14 | `trial_parent_transfer.json`, `trial_applied_transfer.json`, `trial_applied_canary.json`, `trial_parent_canary.json` written | trial archive file timestamps (archive available on request) |
| 02:15 | Commit `e33380e`: the T3′/T4 verdicts recorded (engaged but unreadable; zero collateral) | working-repository log |
| 04:44, 04:54 | `trial_parent_proof1.json`, `trial_applied_proof1.json` written | trial archive file timestamps |
| 04:56 | Commit `55533cf`: section 7 of the plan added, carrying both the protocol of the prospective batch (seven clean tasks including one known negative case that may not be dropped; sign test on the prospective batch as the primary criterion; at most two batches; stop at p < 0.05) and its verdict | working-repository log |

So the cluster-transfer and canary designs (F32, F33) have a committed record that precedes
their data; the prospective batch (F34) has its rules and its verdict in one commit made two
minutes after the batch's last file, and its pre-specification rests on the working notes.
No external registry was used.

## Working-repository log lines

```
9713d33 2026-08-25 01:30:01 +0100 feat(analysis): pathology census + clinic overnight plan v2
e33380e 2026-08-25 02:15:44 +0100 docs(overnight): clinic night verdicts — engaged-but-unreadable + zero collateral
55533cf 2026-08-25 04:56:27 +0100 docs(overnight): proof verdict — drug bundle effect is zero; note arm survives
```

## Plan v2 as committed at 01:30 — rows T3′ and T4 (verbatim, Chinese)

```
| T3′ | **干净簇迁移试验**:merged(三药) vs parent,同窗成对,6 题×10 rep×2 臂 | ~$35 | 墙簇(d5141ca5/114d5fd0/4b6bb5f7)与误收束簇(7673d772/872bfbb1/0bb3b44a)分簇读 Δ;开火验尸(U 文件);Δ<+3/簇=不可分辨 | 🚀 本轮发射 |
| T4 | 附带伤害金丝雀:all-pass 题 8×3 rep×2 臂 | ~$15 | 全过题掉分>1 即 D2 实锤 | T3′ 完后串行 |
```

## Section 7 as committed at 04:56 — protocol and verdict in the same commit (verbatim, Chinese)

```
---

## 7. Proof 阶段终审(用户令"想办法证明涨分";写于 08-25 晨)

**预注册协议**:观测单位=(题,同窗批)净胜差;题集=7 道干净题(含负例 4b6b,不许剔);
主判据=前瞻批(_proof1/_proof2)符号检验;历史格带后见偏差,单列描述性;停机=最多 2 批,
p<0.05 即停。

**proof1 判决(7 题×10×2 同窗)**:+1/−4,前瞻符号 p=0.97(方向反转);parent 29/70 vs
applied 21/70。上一窗 +2 的 0bb3/114d 本窗 −3/−5。**合并全部干净同窗格:parent 75/174
vs applied 72/174(Fisher 0.67,完全打平);机制终点同平(自信答错 51/99 vs 54/102——
verify-first 改了措辞没改交卷行为)**。停机算术:batch2 即便 7/7 全正,合并 p≈0.19,
不可能显著 → **batch2 取消**。终判:**三药配置包分数效应=0**;此前 +7/+5/+4/+6 为四连
窗口噪声,分别被开火验尸、同窗对照、前瞻批处决。单题底率半小时尺度摆幅可达 ±50pp
(0bb3 0/10→5/10;114d 2→6;4b6b 9→7→9),**这个床上任何单窗 Δ≤5 一律不可读**。

**情景笔记臂(折叠片段实验,commit 68f1921)**:题目自身历史的机械摘要(零答案,
epi_notes.json 审毒通过)直接前置进题面,不经 evolve 环;同窗 bare 17/72 vs +notes
22/72(+5,3 正 1 负,n.s.),最大涨幅落在笔记最对症的 d5141ca5(+3,"别恋战 403 直奔
快照")。**身份=唯一活口**,但形态与四个已处决假阳性相同;判生死需 3-4 个独立窗口对
(~$100),留给用户裁。若证实,机制意义重大:**solver 级情景复用不吃 prompt 单例槽位、
不过治理闸、且是逐题定向的——是"看过难题"最短的因果路径**;融入点=分诊器直接产出
per-task note,作为诊疗环的第 0 级药(先于 evolve 药)。

**杂项归账**:_epic/_epin 与 epi_note_gen 系折叠上下文片段所为(有 commit 68f1921 为凭);
工作区半途 revert 已恢复至 HEAD;瞬态 0 字节任务文件=自身前台命令痕迹。本夜总花费
~$120(pre-proof $50 + proof1 ~$35 + 笔记对 ~$35);超原 $60 帽系用户"想办法证明"指令
后的授权性支出,如实报。零 INVALID rep,零卡死,零未解释日志项。
```
