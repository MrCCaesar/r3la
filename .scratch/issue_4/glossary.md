# Go2 Parkour — Issue-local terminology

Confirmed terminology from Explore Q7–Q9. Kept with issue working documents;
root GLOSSARY.md has a pre-existing user deletion and is not restored here.

## Language

**子地形（Sub-terrain）**:
承载单个障碍的地形单元；分配到该子地形的环境以通过该障碍为任务目标。

**非法接触（Illegal contact）**:
本任务中触发接触类失败的基座碰撞。其他腿部连杆碰撞属于接触惩罚的对象。
_Avoid_: 将任意非足端接触统称为非法接触。

## Round 4 clarification

**障碍（Obstacle）**:
一个 IsaacLab 3.0 地形生成器 sub-terrain 所表示的完整任务地形，如一段阶梯、箱体或沟壑；不限定为单个几何构件。

“子地形”在本任务中对应上述 sub-terrain 单元，每个单元是一种障碍类型。


## Confirmed performance terminology — 2026-11-06

**耗时降低（Runtime reduction）**: 相同工作负载下，1−优化后耗时/基线耗时。
本次目标至少30%，即优化后不超过基线70%，分别用于观测与完整step。

**观测耗时（Observation time）**: 环境实际生成完整观测结果所需的时间。

**完整步耗时（Full-step time）**: 执行一次环境step直至结果可用的时间，
包含物理、传感器、奖励/终止、必要reset及观测计算，不包含策略推理。

**保持帧（Held-sample frame）**: 低频传感器本轮未采集新样本，使用上次有效
采集值；样本年龄仍随仿真时间增长。
