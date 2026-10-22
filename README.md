# R3LA

## Description

R3LA is a repository for reproducing and evaluating reinforcement learning algorithms for robotic systems.

Different algorithms are maintained in separate branches to keep implementations isolated and easy to compare.

## Repository Structure

A typical project structure is:

```text
r3-la/
├── config/         # Isaac Sim Extension config
├── docs/           # Documentation and design notes
├── scripts/        # Training, evaluation, and utility scripts
├── src/            # Source code
    ├── r3la/
        ├── tasks/  # Motion task definition
├── tests/           # Unit and integration tests
└── benchmarks/      # Performance and algorithm benchmarks
```

## Dependicies
Current Use Isaaclab 3.0.0EA version, which can be installed following [IsaacLab Installation](https://isaac-sim.github.io/IsaacLab/v3.0.0-EA/source/setup/installation/index.html#installation-method-uv)

Adding custom learning library with [Adding your own learning library](https://isaac-sim.github.io/IsaacLab/v3.0.0-EA/source/how-to/add_own_library.html)


## Branch Organization

Each branch contains the implementation of a specific reinforcement learning algorithm or experiment.

Please switch to the corresponding branch before building, training, or evaluating an algorithm.

# Codex 工程化工作流

> 目标：使用 Codex 完成软件开发任务时，确保需求明确、修改可控、结果可验证，并避免破坏已有功能。

## 工作流

一次非简单任务按以下 6 个阶段执行：

```text
① 明确需求
   ↓
② 建立基线
   ↓
③ 设计验证
   ↓
④ 影响分析与实现
   ↓
⑤ 验证与回归
   ↓
⑥ 独立复核
```

---

## 1. 明确需求

需求使用 GitHub Issue 记录。

### Issue 格式

```text
# Goal
# Requirements
# Constraints
# Acceptance Criteria
# Relevant files
# References
```

使用 `grill-with-docs` 进一步细化需求。

推荐提示词：

```text
先不要修改业务代码。

阅读当前项目和 GitHub Issue #xx，将目标拆分为可验证需求。

对每条需求给出：
- Requirement ID
- 初始条件
- 输入/触发条件
- 可观察行为
- 验收标准
- 尚不明确的问题

不要猜测未知阈值；无法确定的内容与我讨论后再确定。

将确认后的结果写入：
.scratch/issue_xx/REQUIREMENTS.md
```

---

## 2. 建立基线

对于优化、重构或行为敏感的修改，先记录当前实现的基线。

基线用于判断修改是否：

- 改善目标指标；
- 改变已有行为；
- 引入性能、数值或功能回归。

---

## 3. 设计验证方案

根据已确认的需求设计测试。

推荐提示词：

```text
阅读当前项目和 .scratch/issue_xx/REQUIREMENTS.md，
为每条可验证需求设计测试方案。

每条测试给出：
- 对应 Requirement ID
- 初始条件
- 输入/触发条件
- 可观察行为
- 验收标准
- Oracle
- Negative control

不要猜测未知阈值；无法确定的内容与我讨论后再确定。

将确认后的结果写入：
.scratch/issue_xx/TEST_PLAN.md
```

---

## 4. 影响分析与实现

修改代码前先执行 impact analysis。

推荐提示词：

```text
先进行 impact analysis，不要立即修改代码。

列出：
- directly affected modules
- indirectly affected modules
- public APIs
- shared state
- concurrency impact
- real-time impact

将相关内容分类为：
- MUST CHANGE
- MAY CHANGE
- MUST NOT CHANGE

随后只实施满足 REQUIREMENTS.md 所需的最小修改。

禁止：
- 无关重构
- 无关重命名
- 修改验收阈值以使测试通过
- 修改旧行为，除非 REQUIREMENTS.md 明确要求
```

---

## 5. 验证与回归

### 目的

确认实现真正满足需求，并且没有破坏已有功能。

验证应覆盖：

- 新需求是否满足；
- 现有功能是否回归；
- 性能、数值或实时性是否退化；
- 最终代码修改是否超出预期范围。

对于机器人、MPC 或实时系统，还应根据任务检查数值误差、延迟、抖动、内存分配、实时 deadline 和约束违反情况。

### 推荐提示词

```text
验证当前实现，不要继续开发新功能。

阅读：
- .scratch/issue_xx/REQUIREMENTS.md
- .scratch/issue_xx/TEST_PLAN.md
- baseline

逐条验证所有适用需求。

至少执行适用的：
- build
- existing tests
- new feature tests
- regression tests
- differential comparison
- benchmark
- git diff review

对于机器人、MPC、数值或实时相关代码，还应检查适用的：
- numerical regression
- latency
- p95 / p99 / max latency
- jitter
- memory allocation
- real-time deadline
- constraint violation

不要通过修改验收标准、测试 oracle 或预期结果使实现通过。

将每项验证记录为：
- Requirement ID
- verification method
- result: PASS / FAIL / NOT VERIFIED
- evidence
- remaining risks

将结果写入：
.scratch/issue_xx/VERIFICATION.md
```

---

## 6. 独立复核

实现完成后，不应仅以：

```text
all tests PASS
```

作为任务结束条件。

建议开启新的 Codex session，仅执行独立复核。

推荐提示词：

```text
不要修改代码。

作为 independent reviewer，检查：

- REQUIREMENTS.md 是否真正满足
- TEST_PLAN.md 是否覆盖关键需求
- test oracle 是否独立
- negative control 是否有效
- git diff 是否包含无关修改
- 是否存在旧功能回归
- 是否存在性能、数值、并发或实时性风险
- VERIFICATION.md 的结论是否有充分证据支持

最终结论只能是：

PASS
FAIL
PARTIALLY VERIFIED

每个结论必须附带证据。
```

---

## 核心原则

```text
Issue
  ↓
Requirements
  ↓
Baseline
  ↓
Test Plan
  ↓
Impact Analysis
  ↓
Minimal Implementation
  ↓
Verification
  ↓
Independent Review
```

实现代码不是任务完成的标准。

**需求满足、回归通过、验证证据充分，并完成独立复核，才算完成。**