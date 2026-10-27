# Issue #4：四足跑酷参考高度计算调查

状态：源码调查完成；候选未获用户确认，不能视为需求冻结。日期：2026-10-23。未修改业务代码，未运行这些项目的训练或仿真。

## 结论

**局部地形采样均值有直接开源公式，但不能据此声称知名跑酷项目都启用了站高奖励。** Extreme Parkour 原版未列出高度跟踪奖励；Robot Parkour Learning 保留均值高度函数，但基类权重为零，核查的 field/jump/leap/crawl/tilt 配置未启用该项；SoloParkour 的高度下限属于约束，奖励本身没有目标高度跟踪。

因此，下面区分直接存在的公式、可以基于地形查询改造的方案，以及本轮未证实有开源采用的设计。数值仅说明上游实现，不直接成为 Go2 目标高度、网格、阈值或回退规则。

## 固定源码版本与核查范围

| 项目 | 固定提交 | 核查结果 |
|---|---|---|
| chengxuxin/extreme-parkour，ICRA 2024 作者原版 | `d2ffe27ba59a3229fad22a9fc94c38010bb1f519` | base/legged_robot.py 与基类、A1 parkour 配置；没有 `_reward_base_height`；奖励列表无高度项。 |
| ZiwenZhuang/parkour，CoRL 2023 作者原版 | `5e1f4136f7fec9dac2741add63ca58d32090666f` | base 高度函数、零权重删除逻辑、A1/Go1 field 及 jump/leap/crawl/tilt 配置、BarrierTrack 查询。高度函数存在不等于跑酷任务启用。 |
| Gepetto/SoloParkour，CoRL 2024 作者项目 | `b49594f8b7db3a18e04d1cc0c59f706dd5833921` | tasks/solo_parkour.py 的奖励、最低高度约束、足端高度查询。 |
| yobel-sungkooklee/extreme-quadruped-parkour，社区 IsaacLab 项目 | `f3bd09b0d3d1ba4b429ef4b9c7d04c31027b51b7` | 仅补查通用高度函数与 Go2 rough 配置；未完成其所有自定义跑酷任务的配置继承追踪，不作为已启用证据。不是 Extreme Parkour 作者原版。 |

## 候选 A：机身周围地形高度的均值

定义采样点集合 S，得到世界坐标地形高度 z_i；参考高度 `z_ref = mean(z_i)`，机身相对高度 `h = z_base - z_ref`。高度误差可以使用 `h - h_target`；本调查只讨论参考高度，不能自动用上游平方损失替换本项目已确认的论文奖励核。

直接代码：Robot Parkour Learning 的 `_reward_base_height` 先对 `root_z - measured_heights` 求均值，再计算与目标的平方误差。[高度公式](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/envs/base/legged_robot.py#L1732-L1735)

启用情况：其基类 `base_height = -0.`，初始化奖励时删除零权重；A1/Go1 的 field、jump/leap/crawl/tilt 配置未发现非零 `base_height`。所以这是仓库中保留的通用候选，不能写成已验证的跑酷高度奖励。[基类权重](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/envs/base/legged_robot_config.py#L132-L157)、[删除零权重](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/envs/base/legged_robot.py#L1208-L1227)、[Go1 field](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/envs/go1/go1_field_config.py#L116-L139)、[Go1 jump](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/envs/go1/go1_jump_config.py#L86-L110)、[Go1 leap](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/envs/go1/go1_leap_config.py#L90-L114)

采样方式：周围点随基座 yaw 旋转，再加基座位置，交给 terrain 查询；不是接触足筛选，也不是只查机身正下方。BarrierTrack 按 XY 查询单个 heightfield 单元，越界返回负无穷。[采样变换](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/envs/base/legged_robot.py#L1587-L1610)、[地形查询](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/utils/terrain/barrier_track.py#L1839-L1854)

边界：源码没有对高度奖励中的非有限值过滤，也没有“腾空暂停奖励”门控。BarrierTrack 沟壑通过降低 heightfield 形成，因此采到坑底会降低均值；不是 ray miss。全越界会产生负无穷参考值，直接套该高度函数会出现无穷误差，不能把它当作已有可靠回退。[沟壑生成](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/utils/terrain/barrier_track.py#L487-L533)

社区 IsaacLab 仓库也存在同一参考思想：传入 sensor 时，将 ray_hits 的 Z 均值加到 target_height；不传 sensor 时直接跟踪世界 Z。此函数没有 finite 过滤；本次仅核实函数，未证明自定义跑酷配置启用它。[社区函数](https://github.com/yobel-sungkooklee/extreme-quadruped-parkour/blob/f3bd09b0d3d1ba4b429ef4b9c7d04c31027b51b7/source/isaaclab/isaaclab/envs/mdp/rewards.py#L100-L122)

还需区分查询高度与碰撞几何：BarrierTrack 的 leap 生成支持 fake_offset，并可修改供查询的高度场以让 oracle 提前起跳；因此不能默认任意上游观测高度图都是真实碰撞表面。[生成逻辑](https://github.com/ZiwenZhuang/parkour/blob/5e1f4136f7fec9dac2741add63ca58d32090666f/legged_gym/legged_gym/utils/terrain/barrier_track.py#L510-L528)

工程推论：均值可平滑局部粗糙地形，但采样窗口跨越箱体边缘、台阶或沟壑时，参考值会随采到的高低表面比例变化；它不是实际支撑面。需另外确认窗口/位置、无效值规则、是否允许坑底参与，以及腾空时是否仍计算。这些均为待决策项。

## 候选 B：基座正下方的地形高度

定义 `z_ref = terrain_height(x_base, y_base)`，`h = z_base - z_ref`。这是基于开源地形点查询的改造候选；本轮未找到以上作者项目把它直接用于目标站高奖励的证据。

可复用的查询范式：Extreme Parkour 在查询点附近取三个 heightfield 网格值的最小值；越界先夹到边界；平面返回零，无地形配置报错。该函数目前用于地形测量，**其奖励列表没有高度跟踪项**。[三邻点最小值查询](https://github.com/chengxuxin/extreme-parkour/blob/d2ffe27ba59a3229fad22a9fc94c38010bb1f519/legged_gym/legged_gym/envs/base/legged_robot.py#L1166-L1202)、[启用奖励列表](https://github.com/chengxuxin/extreme-parkour/blob/d2ffe27ba59a3229fad22a9fc94c38010bb1f519/legged_gym/legged_gym/envs/base/legged_robot_config.py#L293-L317)

边界/工程推论：基座越过台阶边缘时参考值会跳变；腾空越沟时可能跟踪坑底；如果采用真实 mesh raycast，则无命中与无限深沟要另定规则。原 heightfield 查询的边界夹取不是“ray miss 回退”，不能直接移植成 miss 约定。它比区域均值更局部，但不等于支撑足所在表面。

## 候选 C：足端地形或接触支撑面的参考高度

本轮直接证据是“足端离地高度”，不是“基座相对接触支撑面”。SoloParkour 在四个足端 XY 处取 heightfield 的三个邻值最小值，计算 `foot_z - terrain_z`；不按接触力筛掉摆动足。[SoloParkour 足端高度](https://github.com/Gepetto/SoloParkour/blob/b49594f8b7db3a18e04d1cc0c59f706dd5833921/tasks/solo_parkour.py#L1519-L1541)

将足下地形高度汇总成机身参考面、仅使用接触足、拟合支撑平面，都是需要我们另外定义的改造。本轮未证明上述项目采用了这套机身高度奖励。不能将“足端查询函数存在”写成“开源已用接触面站高奖励”。

工程推论：足下地形汇总可能受摆动足跨障影响；按接触足筛选可关联实际支撑，但腾空时没有样本，一足/两足接触无法唯一拟合一般平面，前后足跨台阶时也没有天然唯一水平高度。需确认足集合、聚合/拟合方法、退化和零接触处理、测量垂直高度还是法向距离。所有阈值保持 TBD。

## 不能混同的实现：世界 Z 最低安全界

SoloParkour 的总奖励只包含速度项和 survival bonus，没有目标站高跟踪。它的 `min_base_height` 是直接使用世界 `root_states[:,2]` 的约束，并受 ceilings 条件门控；不是相对局部地形的高度奖励。[奖励](https://github.com/Gepetto/SoloParkour/blob/b49594f8b7db3a18e04d1cc0c59f706dd5833921/tasks/solo_parkour.py#L738-L757)、[高度约束](https://github.com/Gepetto/SoloParkour/blob/b49594f8b7db3a18e04d1cc0c59f706dd5833921/tasks/solo_parkour.py#L822-L832)、[约束注册](https://github.com/Gepetto/SoloParkour/blob/b49594f8b7db3a18e04d1cc0c59f706dd5833921/tasks/solo_parkour.py#L890-L899)

SoloParkour 的 `base_height_target` 还用于归一化/截断高度观测，不能据此断言它训练了目标高度奖励。[高度观测](https://github.com/Gepetto/SoloParkour/blob/b49594f8b7db3a18e04d1cc0c59f706dd5833921/tasks/solo_parkour.py#L618-L620)

## 面向 Issue #4 的候选比较与待确认项

| 候选 | 开源证据层级 | 对箱体/台阶/沟壑的关键影响 | 需明确后才能验收 |
|---|---|---|---|
| A 周围采样均值 | 直接高度奖励公式存在；本次核查的作者跑酷任务未启用 | 混合高低表面；沟底降低均值；会在空中继续变化 | 样本范围、无效值、沟底是否纳入、腾空规则 |
| B 正下方查询 | 查询存在；改作机身奖励是本项目设计 | 过边缘跳变；越沟时可能读坑底 | 查询几何、miss、越界、腾空规则 |
| C 足下/接触支撑参考 | 足端离地查询存在；汇总成机身参考面尚无直接证据 | 可关联支撑，但跨台阶、少接触和腾空均有歧义 | 足集合、聚合/拟合、零接触/退化回退、高度方向 |

建议先讨论 A 与 C 的任务含义：如果希望奖励表示“机身相对周围地形的平均净空”，A 最接近直接开源公式；如果希望表示“机身相对当前支撑地面的站高”，C 更贴合该定义，但要承担明确接触和腾空规则的额外设计。B 可作为更局部的基线。此建议是工程判断，不是上述项目训练性能的对比结论。

## 验证与限制

- 使用固定提交阅读源码，查找函数、配置和调用链；没有以 README 中的概括替代公式与启用检查。
- Extreme 和 Zhuang 已获取源码快照；Solo 关键源码由主 agent 独立复核；社区实现仅取关键单文件，未完成任务继承链。
- 未测运行效果、训练收敛、IsaacLab 兼容性、耗时或 Go2 合适站高。未把任何候选或阈值写成已确认需求。
- 调查结果：**PARTIALLY VERIFIED**。源码公式和上述配置事实已核实；候选对本项目的适用性及边界行为仍需选择和验证。
