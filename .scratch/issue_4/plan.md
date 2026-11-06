# Issue #4 Plan — Approved

## 状态与依据

用户“读取.scratch/issue_4中的需求，研究和设计文件，进入plan阶段”授权进入 Plan；后续“继续”延续该任务。用户随后回复“yes”，批准任务拆分与 GitHub 发布；Implement 已由用户后续明确授权；最终 Verify 已由用户于 2026-11-06 以“进入verify”明确授权；验收结果见 verification.md。

来源：GitHub #4（标题、正文及空评论列表已读取）、requirements.md、research.md、design.md、interfaces.md、ADR-001–007 与 status.md。当前 design.md 是本 Issue 已批准的规格，不另建重复 spec.md。以 S1–S67 最终修订为准；研究中的历史建议不是当前要求。

## 已确认事实、假设、问题与建议

- 已确认：环境与数据交付；六类地形；原生 ManagerBasedRLEnv 生命周期；初始支持组合仅 Newton MJWarp + Newton Warp renderer；不包含训练实现或性能收敛验收。
- 假设：实现时依赖仍兼容研究固定的 IsaacLab commit 346c74fe722ad371a6c663e3b384b3d172966d11。每个涉及原生扩展点的任务先检查实际版本和相关源码；变更导致契约不可实现时报告影响。
- 已批准：以下切片粒度、阻塞边与 GitHub 子工单发布（用户“yes”）。T 编号为稳定计划编号。
- 建议：先建立箱体的最小环境路径，再添加独立行为；每票包含接线、可观察结果、测试及文档，不安排全局“先写所有接口”的横向任务。没有证据要求单独大范围预重构。
- 文档歧义：design.md 验收表的“both initial supported backends”与其正文及 ADR-002 的单一组合表述不一致；本计划按明确批准的 ADR-002 单一组合安排，不扩展后端支持。该措辞应在文档同步时澄清。

## 已批准任务

每票拆分状态均为 Approved。以下为已批准发布内容；路径选择遵循已批准接口文档，工单正文不重复文件路径或代码。

### T01 — 箱体地形生成、导入与入口重置

**Blocked by:** 无。

**交付：** 注册任务能够使用指定箱体样本，从合法入口初始化 Go2，并通过原生 reset/step 运行有界检查；建立后续地形复用的已批准布局与导入链路。

- [ ] TerrainLayout、箱体 mesh、缓存命中/未命中、实际 difficulty 和世界变换一致；保留原生 meshes/origin 返回契约。
- [ ] 出生点与 mesh origin 分离，重置使用指定 tile 的安全入口及批准的姿态/关节抖动；非法配置明确报错。
- [ ] 验证 d=0/1、缓存一致性、放置变换、partial reset、注册与初始后端可加载性。
- [ ] 同步运行入口及地形契约说明；该切片仅验收生成/重置行为，不宣称完整任务完成。

追踪：R1/R6/R12/R15；S1/S2/S24/S32/S35/S48/S66；ADR-001/002/007。

### T02 — 箱体有效通过、落地确认与回合结束

**Blocked by:** T01。

**交付：** 箱体尝试仅在合法过门并完成有限落地确认后成功重置；绕行、基座碰撞和超时正确结束。

- [ ] 单一 ParkourAttemptState 原生 term；有序过门、回退清进度、高速跨门插值；重复读取/构造探测不重复推进。
- [ ] 0.2 s 窗口、姿态/速度/支持脚阈值和目标平面接触归属遵循规格；非目标支持、悬空越界不成功。
- [ ] 失败优先，terminated/truncated 可同时为真；手动/初始 reset 不伪造完成事件；边界信息不被清空缓冲别名污染。
- [ ] 合成轨迹覆盖边界情形；有界后端检查接触过滤、缺失接触点、正常/失败落地及部分重置。更新成功判定局限说明。

追踪：R10/R13–R19；S23/S35/S50–S52/S58；ADR-003/007。

### T03 — 沟壑跨越完整路径

**Blocked by:** T02。

**交付：** 沟壑生成、入口重置、双门通过和远端落地完成接入同一任务。

- [ ] 宽度/深度及地板侧壁碰撞、远端支持区与元数据一致；地板/侧壁支持不能计成功。
- [ ] d=0/1、越门回退、绕行、远端有效落地有独立证据；同步地形用法。

追踪：R9/R15/R16；S37/S48–S52/S66。

### T04 — 普通阶梯完整路径

**Blocked by:** T02。

**交付：** Go2 从入口沿单向阶梯到实际残余平台，按真实平台内缩区域确认完成。

- [ ] 原生计数/残余尺寸、额外平台升高、holes 两种跨度与单 +X 路线符合契约；默认 N=10、平台 1×4 m。
- [ ] 参数变化重新计算门/支持/完成区，空区域拒绝；d=0/1 和有效/无效平台落地覆盖几何与任务链路。
- [ ] 更新阶梯参数及实际平台关系说明。

追踪：R9/R15/R16；S38/S39/S59–S64/S66。

### T05 — 倾斜阶梯与匹配镜像

**Blocked by:** T04。

**交付：** 倾斜踏面及其匹配镜像能生成、导入、重置并沿对应任务区域判定完成。

- [ ] 入口/平台保持水平；踏面剪切、首末边界变高及低侧闭合不被底面覆盖。
- [ ] 同一 canonical sample 同步反射 geometry 与 regions；两种 holes、d=0/1、连接面与支持区域有验证。
- [ ] 同步镜像使用及接缝验证记录；最终确定性评估入口在 T12 汇总。

追踪：R9 最终修订；S30/S41/S65/S66；ADR-001。

### T06 — 侧坡及镜像完整路径

**Blocked by:** T02。

**交付：** 指定横坡及匹配镜像经过入口、坡面与远端落地区完成任务。

- [ ] 分段横坡过渡、网格间距 ≤0.05 m、三角形内部高度误差 ≤0.001 m；镜像复用 canonical sample。
- [ ] 几何/门/支持面一致；d=0/1、合法通过及绕行有验证；同步坡面说明。

追踪：R9 最终修订；S30/S42/S49/S54/S66。

### T07 — 随机岩石网格完整路径

**Blocked by:** T02。

**交付：** 可复现的正高度网格障碍及远端落地区接入有效通过判定。

- [ ] 2×2 m、10×10 cells、正高度样本，无额外中心平台或刻意缝隙；缓存/mesh/layout 使用同一抽样。
- [ ] d=0/1、seed 重现、碰撞表面、双门与远端支持验证；同步随机地形说明。

追踪：R9/R15；S43/S44/S49/S66；ADR-001。

### T08 — 共享本体历史与规范动作路径

**Blocked by:** T01。

**交付：** 环境输入动作按 canonical 顺序驱动关节，返回同顺序的共享 noisy 五帧历史与独立 commands。

- [ ] proprio [N,210] 的特征/时间顺序、噪声范围及共享样本复用精确；初始/部分重置重复同一首帧。
- [ ] q_default+0.5*a、原始前次动作、无额外裁剪，明确坏输入失败；关节/足序映射一致。
- [ ] 无 terminal-only 观测；done 行属于新回合。数值及原生生命周期检查并同步消费者选取说明。

追踪：R4/R17/R22/R23；S9–S11/S18/S58/S66。

### T09 — 深度与高度扫描输出完整契约

**Blocked by:** T01。

**交付：** 环境返回经校准的深度、body/foot target 扫描及 critic 扫描，附有效性、时间和回合元数据。

- [ ] 深度 320×240、公制 image-plane、姿态轴向和有效 mask；已知平面检验校准。
- [ ] 扫描分辨率/顺序/基座 yaw、捕获时参考 Z 和射线范围符合契约；no-hit 为零+无效。
- [ ] 10 Hz target 原生持有、50 Hz critic；捕获 hook 内逐行复制，异步 partial reset 不改其他行样本。
- [ ] low-rate bundle 捕获身份一致，初始时间/年龄、reset 有效性和返回 key/shape 完整；不另设调度器。同步所有权与借用缓冲说明。

追踪：R4/R24；S13–S16/S27/S35/S53/S66；ADR-005/007。

### T10 — 实际动力学参数、干净状态与奖励

**Blocked by:** T08、T09。

**交付：** 启动随机化真正应用到 Go2，privilege/AMP 返回实际干净状态，16 项奖励按批准公式作用于步进。

- [ ] 随机化范围/分布/生命周期、有效 P/D、质量/COM/共享材料回读正确，reset 不重抽 startup 参数；无 push。
- [ ] privilege [N,273]、命名 AMP 和高度有效性符合契约；高度全无效贡献为零且不触发 reset。
- [ ] S67 全部公式/权重、接触历史和 latest 区别、airtime 无低速门、dt 仅一次；动作一二阶差分从首步生效且部分重置隔离。
- [ ] 数值 fixtures 与有限后端回读验证；同步论文/Go2 适配及输出文档。

追踪：R3/R6/R14/R21；S17/S19/S20/S25/S26/S31/S33/S55–S58/S67；ADR-006。

### T11 — 独立课程驱动下一次尝试

**Blocked by:** T02。

**交付：** 结束尝试在原生 pre-reset 时更新地形成功率和速度跟踪统计，改变下一次分配/指令。

- [ ] 地形 last100/min20、0.8/0.3、逐级变更及最高级随机回低级；初始/手动 reset 不计数。
- [ ] q 累计包含终止物理步、按实际时长归一；≥1 s 的20次等权批次含失败；速度增减/清批次/范围符合规格。
- [ ] 同时结束按 env ID 排序；持久窗口跨 reset；只迁移结束行，迁移先于 spawn 与 command reset。
- [ ] 最小 CommandTerm 用原生周期保持整回合固定，更新只影响后续尝试；合成 family fixtures 验证隔离，无需等待六类 mesh 全部实现。
- [ ] 同步课程统计与日志语义。

追踪：R11/R17/R20；S5–S8/S21/S35；ADR-004/007。

### T12 — 六类任务集成与确定性评估交付

**Blocked by:** T03、T05、T06、T07、T10、T11。

**交付：** 现有任务 ID 提供完整训练环境配置与固定 family/level/command 的确定性评估；所有契约形成可复核验收记录。

- [ ] 默认10×20分配、4/4/2/4/4/2列、初始0..5、family固定和普通/倾斜阶梯独立统计。
- [ ] 评估关闭课程、噪声、随机动力学与抖动，保留行为定义；匹配镜像复用 canonical geometry。
- [ ] 串行逐类及镜像有界运行，验证最大阶梯高度、射线覆盖、低侧接缝、接触归属、partial reset、完整 observation keys 和边界。
- [ ] 核对原生 wrapper/timeout 兼容边界并记录，不实现 learner；所有 S67 验收行均有证据或明确失败。
- [ ] 同步使用文档及 verification.md，记录版本、确切命令、退出码、结果与剩余风险；不得以训练性能替代正确性验收。

追踪：R1–R24 经最终修订；S34/S45–S47/S58/S66/S67；全部 ADR。

## 执行与验证顺序

初始 frontier 为 T01；完成后 T02/T08/T09 可独立推进；T02 后开放地形扩展与 T11；T08/T09 后开放 T10；最后 T12 汇总。依赖表示交付物前置条件，不授权并行运行仿真或自动启动多个 agent。

每票先做无需仿真的确定性验证，再做必要的原生接线检查。配置、shape、bool 精确匹配；float32 公式 atol=rtol=1e-5，几何遵循更严格解析界限。运行前检查 RAM/VRAM，默认 headless、num_envs=2，一次一个有明确步数/超时上限的进程；实际启动命令根据实现入口记录，不捏造尚不存在的测试命令。两环境不足覆盖六类时显式逐类选择，不能依赖随机分配碰巧覆盖。

批准计划并授权 Implement 后，每票落实其测试；进入最终 Verify 阶段仍需显式批准。运行失败不能降低验收标准；需要改变已批准契约时先列依赖影响请求修订。

## 发布与交接

使用 GitHub Issues。拆分获批后依照 tracker 权限规则发布一票一 Issue，依赖优先顺序建立引用；验证可用的原生 blocking/sub-issue 操作后建立关系，标签 ready-for-agent。发布前必须获得用户对发布动作的明确授权；不编辑父 Issue 正文或关闭父 Issue。计划批准、发布批准与进入 Implement 分别记录。

TODO-01 深度噪声、TODO-02 OVPhysX、TODO-03 Isaac Sim PhysX 保留延期；训练 runner/model、AMP discriminator/dataset 不加入本计划。

## 本阶段验证

只进行了文档读取、GitHub只读查询和计划一致性检查；没有运行仿真、训练或生产测试。现有工作区改动保持原状。任务粒度/依赖已获批准，原生接触点与私有传感器 hook 的运行可行性仍待实现期验证。

## GitHub 发布结果 — 已核验

批准依据：用户在拆分与发布请求后回复“yes”。使用 to-tickets 技能发布。

| 计划 | GitHub 工单 | 阻塞于 |
| --- | --- | --- |
| T01 | [#5 箱体地形生成、导入与入口重置](https://github.com/MrCCaesar/r3la/issues/5) | 无 |
| T02 | [#6 箱体有效通过、落地确认与回合结束](https://github.com/MrCCaesar/r3la/issues/6) | #5 |
| T03 | [#7 沟壑跨越完整路径](https://github.com/MrCCaesar/r3la/issues/7) | #6 |
| T04 | [#8 普通阶梯完整路径](https://github.com/MrCCaesar/r3la/issues/8) | #6 |
| T05 | [#9 倾斜阶梯与匹配镜像](https://github.com/MrCCaesar/r3la/issues/9) | #8 |
| T06 | [#10 侧坡及镜像完整路径](https://github.com/MrCCaesar/r3la/issues/10) | #6 |
| T07 | [#11 随机岩石网格完整路径](https://github.com/MrCCaesar/r3la/issues/11) | #6 |
| T08 | [#12 共享本体历史与规范动作路径](https://github.com/MrCCaesar/r3la/issues/12) | #5 |
| T09 | [#13 深度与高度扫描输出完整契约](https://github.com/MrCCaesar/r3la/issues/13) | #5 |
| T10 | [#14 实际动力学参数、干净状态与奖励](https://github.com/MrCCaesar/r3la/issues/14) | #12、#13 |
| T11 | [#15 独立课程驱动下一次尝试](https://github.com/MrCCaesar/r3la/issues/15) | #6 |
| T12 | [#16 六类任务集成与确定性评估交付](https://github.com/MrCCaesar/r3la/issues/16) | #7、#9、#10、#11、#14、#15 |

已通过 GitHub GraphQL 回读核对全部正文、标题、父工单 #4、ready-for-agent 标签及原生阻塞边。父工单正文和状态未修改。Implement 已获授权；当前进度见 implementation.md 和 status.md。

## Implementation progress

T01–T12 / #5–#16: implementation complete; checks passed, ready for unified user
review. GitHub issues remain open; final Verify stage has not begun. Published
acceptance checkboxes above are retained as issue content, not marked as user
acceptance. See implementation.md and verification.md (Draft) for commands,
141-test results,17 bounded native cases and production camera visibility limitation.
User requested completion of all tickets before review; no per-ticket reapproval.
Camera mount/visibility changes remain subject to a separate explicit decision.


## User geometry correction — 2026-11-06

User authorized equal Y widths for holes=True stair treads/platforms and an
unblended transverse planar ramp (ordinary ramp rotated 90°). ADR-008 supersedes
the earlier conflicting width/transition details. Implemented layout/mesh,
regions, cache revision, regression tests and native probe expectations; see
verification.md for executed checks. Other geometry parameters remain unchanged.


## Camera debug-output extension — 2026-11-06

User requested RGB and other camera output types for debugging. HeldDepthCamera
now accepts additional native Newton Warp output types alongside the required
distance_to_image_plane. Native Camera owns output allocation/type validation;
extras are read via camera.data.output with native buffer lifetime, and must be
cloned for retention. The held SensorSample and training observations still
contain only metric image-plane depth with existing masks/cadence/episode rules.
Defaults remain depth-only; RGB-only debug cameras use native CameraCfg. No
backend or calibration/mount change is included. Examples: docs/parkour.md.


Ground-aligned slope follow-up (2026-11-06): user approved the current angle/joins
and requested minimum height z=0. Updated analytic heights, prism, cache revision
3 and regressions; 159 tests and native slope probe passed. Camera mount .35 m
was user-modified and visibility user-confirmed; synchronized documentation/test
expectation without further mount edits. See verification.md.
