# Issue #4 — 需求分析阶段证据

日期：2026-10-23。范围仅为读取项目、Issue、依赖源码及需求讨论；没有实施业务功能。

最终结果（当前阶段）：**PARTIALLY VERIFIED**。

已核查需求文档的结构、来源和工作区修改边界。需求仍在讨论中，包含用户明确保留的未决行为和参数；没有进行业务实现、仿真、训练、运行回归或性能验收。

## 本次影响范围

- `MUST CHANGE`：`.scratch/issue_04/REQUIREMENTS.md`，记录已确认范围、可验证需求和未决问题；本文件记录证据。
- `MUST CHANGE`（显式调用技能要求）：根 `GLOSSARY.md`，按 `grill-with-docs` 所调用的 `domain-modeling` 技能记录已澄清术语。
- `MAY CHANGE`：上述文档随用户答复继续更新。
- `MUST NOT CHANGE`：`src/`、`scripts/`、`tests/`、`config/`、依赖与锁文件、既有测试 oracle 和阈值。业务实现的影响分析留到需求和 TEST_PLAN 就绪后。

## 起始状态与修改隔离

- 项目 HEAD：`e3d3b3b2727f7bf49106b337c3bb92cddcadb8fa`。
- 起始工作区已有 `pyproject.toml`、`uv.lock` 修改，均由用户原有工作区带入。
- 起始及当前 `git diff --binary -- pyproject.toml uv.lock | sha256sum` 均为：
  `baf958e589c8d1f44be79cef2017f8ed7f508ca4b20943a5d23c64f7c0a94803`。
- `git diff --quiet -- src scripts tests config` 返回 0；未修改业务、脚本、测试或扩展配置。
- 起始没有 `.scratch/issue_04/REQUIREMENTS.md` 和 `TEST_PLAN.md`；本次仅进入需求阶段，未创建 TEST_PLAN。

## 核查记录

| 核查 | 结果 | 证据与限制 |
| --- | --- | --- |
| 读取 Issue #4 | PASS | `gh issue view 4 --repo MrCCaesar/r3la --json number,title,body,state,url,comments,labels,assignees` 成功；无评论，Issue 为 OPEN |
| 读取算法依赖 Issue | PASS | `gh issue view 1 --repo MrCCaesar/rsl_rl --json number,title,body,state,url,comments` 成功；读取时为 OPEN |
| 读取当前项目与有关配置 | PASS | README、AGENTS、任务注册、Go2 rough/flat、PPO/teacher/distillation、自定义 reward、现有注册测试均已读 |
| 核查频率机制 | PASS（源码） | `step_dt=sim.dt*decimation`、runner 逐环境步采样、传感器刷新与 RSSM 调用分别成立；来源和版本记录在 REQUIREMENTS.md |
| 用户确认追踪 | PARTIALLY VERIFIED | Q19–Q24 已确认五组、G1 四帧字段连接且保留历史轴、相对默认关节状态、G5 完整无噪声真值及框架首帧填充；actor 最终输入组织留给后续算法规范，不强制补第五帧。Q25/Q26 已确认失败类型及动作差分启动；Q28 确认按地形类型/难度分组统计；Q27a 已确认地形采样均值参考面，Q29 明确仅保留地形课程、去除速度课程 |
| 需求六字段与编号 | PASS | 只读解析识别 R04-001 至 R04-013 共 13 条；每条包含用户要求的六个字段，ID 无重复 |
| 文档空白与 diff | PASS | 文档逐行检查未发现尾随空格；`git diff --check` 返回 0；未跟踪文档另作内容和格式检查 |
| 工作区修改隔离 | PASS | 原有依赖 diff 哈希保持；业务目录 diff 为空 |
| 独立只读复核 | PASS（文档） | 单独 review 任务核查 13 条六字段、来源和未决项；本轮曾发现一处陈旧确认状态，修正并复核关闭；独立刷新规则也已复核 |
| RealSense 原理核查 | PASS（资料） | 官方几何白皮书明确 depth=Z；官方 SDK 记录时域同步限制，几何意义和同步分别讨论；用户据此确认 Q11a，Q11b 选择各传感器独立刷新 |
| 构建、业务测试、仿真、训练、数值/性能 | NOT VERIFIED | 本次没有改变业务代码，也没有进入实现或 TEST_PLAN 阶段；不以源码存在或文档通过替代运行证据 |

结构核查首次调用 `python` 时该命令不可用；改用 `python3` 后检查成功。未因此修改环境或依赖。

## 独立审阅证据

review 任务没有修改实现或文档。其首版结论为 `PASS`，范围限于文档事实和结构；明确说明没有执行仿真、训练或真实 RSSM 验收。核查包括：

- 13 条需求六字段完整，频率事实与当前源码一致。
- 世界模型采样边界归属、reset、相机及未知阈值保留为未决。
- `last_action` 为 wrapper 裁剪后、关节目标缩放前的最近已执行环境输入。
- 当前课程按 XY 位移升降级，没有独立跑酷成功谓词。
- `episode_length_buf` 可被 runner 随机初始化，不能天然当作相机时间基准。

增量复核结论同为 `PASS`：确认 Q4 的同频率未被误写成同相位或已选择光轴深度；Q5 的物理/动作基线、Q6 的奖励积分和 Q7 的单类区域均按用户答复记录；没有替用户补定参数。

### 继续讨论后的复核与纠正

- 在 Q14 确认初始化时刻后，review 曾报告 `FAIL`：确认列表一处仍写“初始化时刻继续讨论”，与详细需求冲突。
- 已将该处改为“初始化时刻已由 Q14 确认，历史初始化表示和填充方案继续讨论”。独立 reviewer 复查结论为 `PASS`，该缺陷关闭；没有改动业务实现、测试或验收阈值。
- reviewer 同时确认：Q10 的分组与 rsl_rl 提取职责、Q12 成功基本框架、Q13 逐项 TBD、Q14 逐环境相位及 Q11a 原生光轴 Z/米单位均按用户答复记录，13 条六字段齐全。
- Q11b 用户明确要求“各自刷新，不需要频率和时间配对”。据此取消跨组强制同频、同相位和逐帧时间配对候选要求。当时深度与重建高度图各自 10 Hz；Q34 后续明确将全部地形高度图观测改为 50 Hz，仅深度保留 10 Hz。该变更来自用户的需求澄清，不是为使测试通过。
- Q15a 已确认分别使用速度命令 c、已执行动作历史和本体感觉历史，不设“历史命令”独立概念。Q17 已确认终点触地条件，Q18 已确认任务失败 > 完成目标 > 仅超时，均已记录。
- Q16 用户要求重新确定环境与算法分别提供/实现哪些观测。随后 Q19 明确环境五组：本体感觉四槽历史、深度图、H_body/H_foot、command、全部特权信息；算法重新组织 RSSM、actor、critic 输入，环境继续定义奖励/终止/课程及任务内部历史。已用该决定替换先前仅单帧环境的候选。
- 对当前观测字段、actor/critic 映射、wrapper 裁剪、自动 reset 后动作清零及奖励内部历史需求做了只读源码核查；相关证据已写入需求文档。本轮未变更实现来适配候选方案。

### Q19–Q29 增量确认与事实核查

- 本地 `history_length=4` 总计四槽，append 当前样本后为当前及前三帧，最新样本在最后；没有默认的第五槽。Q20 明确环境四帧；论文 Table II 的 i=0…4 仅记录为来源事实，不作为本仓库第五槽或算法补帧要求。
- `concatenate_terms` 与 `flatten_history_dim` 分别控制字段连接和历史轴压平。二者均 False 可保持字段字典，每项 `(N,4,D_i)`；仅不压平时间轴也可连接为 `(N,4,sum(D_i))`。Q21 已选择字段连接且保留历史轴，即 concatenate_terms=True、flatten_history_dim=False，输出 (N,4,D)。
- 独立事实核查任务在实际虚拟环境用最小 CPU TensorDict 对象验证嵌套值 `(2,4,3)` 和 `(2,4,12)` 的形状可保持。这只验证容器结构，不是仿真环境或 SWAP runner 的集成验收。
- 已核查 `joint_pos_rel=q-default_q`、`joint_vel_rel=dq-default_dq`，Q22 已确认采用上述相对默认状态。资产配置引用远端 USD，本轮没有独立验证运行时关节数量/顺序，不将标准维数当作已验收事实。
- Q23 已确认 G5 完整 o_priv 当前真值且关闭该组观测噪声。Q24 已确认局部 reset 清空 G1 历史、首帧填满四槽、策略步追加、额外读取不推进；不新增环境有效长度协议。其他组噪声和预处理/归一化仍未确定。

- Q25 已确认三类任务失败：基座非法接触、跌落、离开允许运动区域；分别记录原因，检测几何与阈值继续 TBD。
- Q26 已确认动作差分项仅在真实动作历史足够后计算：第一步两个差分项为零，第二步仅一阶可计算，第三步起二阶可计算；不使用 G1 填充样本充当真实动作。该规则来自用户明确选择，不是修改测试阈值。

- Q28 已确认按地形类型和难度分别统计完整 episode，成功为正样本，任务失败及未成功超时为负样本，手动 reset/初始化中断不计成败。Q27a 已选择基座周围地形采样高度均值作为奖励参考面；采样范围、无效样本、沟底及腾空规则待定；Q29 明确仅保留地形课程、去除速度课程；保留 G4 速度命令自身配置待定。

- Q20–Q26 增量独立只读复核结论 PASS：review 核对四帧结构、相对关节状态、G5 真值、首帧填充、三类失败及动作差分真实历史规则，未发现陈旧冲突；13 条六字段及唯一 ID 完整。此结论限于文档，不代表功能通过。
- Q28/Q29 增量独立只读复核同为 PASS：分地形/难度统计与样本排除规则一致，全文未发现残留的强制速度课程或两课程耦合要求。

- Q27 只读事实核查：当前 rough 高度奖励使用扫描有限命中点 Z 均值，全未命中时参考退回零；论文未指定参考面提取方法。Q27a 用户随后选定地形采样均值定义；既有全未命中回退行为和扫描参数未自动纳入新环境。

RealSense 的持久来源位于 REQUIREMENTS.md；主要原理依据为 [官方几何白皮书 §2.3](https://dev.realsenseai.com/docs/projection-texture-mapping-and-occlusion-with-intel-realsense-depth-cameras/)、[SDK Frame Syncer](https://github.com/realsenseai/librealsense/blob/master/doc/frame_lifetime.md#frame-syncer)。D435/D455 主动双目仅作为原理示例，未据此选择设备或填入规格；其结构依据为 [D400 官方 datasheet](https://realsenseai.com/wp-content/uploads/dlm_uploads/2025/08/Intel-RealSense-D400-Series-Datasheet-August-2025.pdf)。研究未测试硬件或仿真相机。

详细只读研究与 review 工作笔记位于本会话临时文件 `/tmp/r3la-issue04-frequency-research.md`。该文件不是长期交付物；需求文件保留了源码定位和主要事实。

## 剩余问题与下一步

- 用户尚未确认所有时序和参数，REQUIREMENTS.md 明确为“讨论中，未冻结”。
- 现有注册测试 `tests/test_registration.py:15` 静态上断言不存在以 `r3la.tasks` 开头的环境配置入口，与当前注册入口需在后续基线阶段一并审查；本次没有运行该测试，也没有修改其预期。
- 需求文档完成讨论并确认冻结后，才能据此制定 TEST_PLAN；未确认的阈值或时序不得由后续实施者补猜。

## Q27 GitHub 跑酷源码调查

- 用户要求检索开源参考高度算法后，使用 research 技能的独立调查任务写入 [HEIGHT_REFERENCE_RESEARCH.md](HEIGHT_REFERENCE_RESEARCH.md)。固定三个作者项目提交，区分公式存在、配置实际启用、观测查询和约束用途；社区项目仅核查关键函数，未声称任务启用。
- 主任务独立对照 SoloParkour 的奖励/约束/足端查询，复查 Zhuang 均值公式及 Go2 field 配置、BarrierTrack 越界/沟壑生成，以及 Extreme 固定提交的三邻点查询。源码事实核对 PASS；候选的 Go2 适用性仍 PARTIALLY VERIFIED。
- Q27a 已确认基座周围地形采样高度均值作为参考面。研究仅补充依据，不补猜目标高度、网格或样本边界规则。未运行上游代码、仿真或训练。

## Q30–Q33 高度奖励边界

- 用户确认局部采样窗口以基座为中心并随偏航旋转；窗口尺寸、点距和射线量程尚未赋值。
- 用户确认均值仅纳入有效地形样本，地形生成器标记为沟壑内部的样本即使有实际命中也排除。全无有效样本时本步高度奖励项为零并记录原因；四足均无接触时该项为零。两种零值条件分别列入 R04-010 验收，不采用旧 rough 的全未命中世界高度回退。
- Q34 明确所有地形高度图观测 50 Hz，包括 G3 的 H_body/H_foot 和 G5 的 H_terrain；高度奖励每个策略步读取当时地形。该答复覆盖此前 G3 10 Hz 约定，深度 10 Hz 和 RSSM 10 Hz 仍各自独立；未运行仿真或奖励数值验证。
- 更新后结构检查确认 13 条需求及六字段完整，文档空白检查和 git diff --check 通过；业务目录 diff 为空，原有依赖差异哈希保持不变。
