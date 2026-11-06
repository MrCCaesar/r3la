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
