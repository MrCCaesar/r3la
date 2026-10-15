# Codex 工程化工作流（精简可复用版）

> 目标：用 Codex 完成软件开发任务时，确保“需求明确、修改可控、结果可验证、旧功能不被意外破坏”。

---

## 1. 先记住这 4 个文件

项目中建议长期维护：

```text
project/
├── AGENTS.md
├── REQUIREMENTS.md
├── TEST_PLAN.md
└── VERIFICATION.md
```

它们的关系是：

```text
AGENTS.md
    ↓ 规定 Codex 应该怎么工作
REQUIREMENTS.md
    ↓ 定义系统必须做到什么
TEST_PLAN.md
    ↓ 定义如何证明需求被满足
VERIFICATION.md
    ↓ 记录这一次实际验证出了什么
```

### 文件职责

| 文件 | 什么时候读 | 什么时候改 | 主要内容 |
|---|---|---|---|
| `AGENTS.md` | 每次任务开始 | 工作流程变化时 | Codex 的长期工作规则 |
| `REQUIREMENTS.md` | 设计和实现前 | 新增/修改需求时 | 可验证需求 |
| `TEST_PLAN.md` | 实现前、测试前 | 新增/修改验收方式时 | Requirement → Test 映射 |
| `VERIFICATION.md` | 任务结束时 | 每次任务执行后 | 实际测试、benchmark、风险、结论 |

---

# 2. 一次完整任务只走 6 步

```text
① 明确需求
   ↓
② 建立现状基线
   ↓
③ 设计验证方法
   ↓
④ 分析影响并实现
   ↓
⑤ 回归与验证
   ↓
⑥ 独立复核
```

下面每一步都说明：

- Codex 做什么
- 读什么文件
- 写什么文件
- 你应该给什么提示词
- 什么情况下才能进入下一步

---

# 3. 第一步：明确需求

## 目标

把：

```text
“我想增加一个功能”
```

变成：

```text
“什么输入下，系统必须表现成什么样，什么叫 PASS”
```

## Codex 读取

```text
README.md
现有代码
现有测试
相关 docs/
```

## Codex 写入

```text
REQUIREMENTS.md
```

## REQUIREMENTS.md 应写什么

每个需求至少包含：

```text
Requirement ID
Condition / Initial state
Stimulus / Input
Expected observable behavior
Acceptance threshold
Unknown / TBD
```

例如：

```markdown
### R3 - Terrain-aware rollout

Condition:
Terrain rollout is enabled.

Input:
Robot state + local elevation map.

Expected behavior:
Each rollout shall account for terrain height.

Acceptance:
The generated rollout must not penetrate the terrain by more than 2 mm.
```

如果阈值未知：

```text
TBD
```

不要让 Codex 自己编造。

## 这一步使用的“临时提示词”

> 下面内容是给 Codex 的一次性 prompt，不是写进 `REQUIREMENTS.md` 的正文。

```text
先不要修改业务代码。

阅读当前项目，并把我的目标拆成可验证需求。

对每条需求给出：
- Requirement ID
- 初始条件
- 输入/触发条件
- 可观察行为
- 验收标准
- 尚不明确的问题

不要替我猜测未知阈值；无法确定的标记为 TBD。

将确认后的结果写入 REQUIREMENTS.md。
```

## 进入下一步的条件

必须能回答：

```text
“如果实现正确，我能观察到什么？”
```

如果回答不了，需求还不够明确。

---

# 4. 第二步：建立现状基线

## 目标

在修改代码前，先固定：

```text
当前代码到底是什么行为
```

否则以后测试失败时，你无法判断：

```text
是 Codex 改坏了
还是原来就坏
```

## Codex 读取

```text
REQUIREMENTS.md
现有 tests/
现有 benchmarks/
现有 API
```

## Codex 不应修改

```text
production code
```

## Codex 产出

基线数据，例如：

```text
Build: PASS
Tests: 428 / 428 PASS

Benchmark:
mean = 4.8 ms
p95  = 5.6 ms

Reference output:
baseline/controller_output.json
```

必要时新增：

```text
characterization tests
baseline dataset
golden output
```

## 这一步使用的临时提示词

```text
在修改 production code 前建立 baseline。

执行：
1. 完整构建。
2. 运行现有测试。
3. 运行关键 benchmark。
4. 记录关键输入对应的当前输出。
5. 找出哪些旧行为必须保持不变。

如果缺少回归测试，先增加 characterization tests。

暂时不要修改业务实现。
```

## 为什么 Characterization Test 很重要

它不回答：

```text
“旧行为是否理想？”
```

而只回答：

```text
“旧代码当前到底怎么运行？”
```

这对 legacy code 很重要。

---

# 5. 第三步：设计验证方法

## 目标

建立：

```text
Requirement → Test → Pass/Fail Criterion
```

## Codex 读取

```text
REQUIREMENTS.md
baseline
现有测试
```

## Codex 写入

```text
TEST_PLAN.md
```

## TEST_PLAN.md 只写“怎么测”

不要写实际运行结果。

推荐结构：

```markdown
## T4 - Terrain penetration test

Validates:
R3

Initial condition:
Robot starts above flat terrain.

Stimulus:
Enable terrain-aware rollout.

Observable:
Minimum foot/terrain clearance.

Pass criterion:
penetration <= 2 mm

Oracle:
Independent geometry calculation

Negative control:
Disable terrain collision handling.
The test must FAIL.
```

---

# 6. 测试本身也必须被验证

这是非常关键的一步。

不能只验证：

```text
正确实现 → PASS
```

还必须验证：

```text
错误实现 → FAIL
```

## 每个关键测试至少检查三件事

```text
1. Requirement traceability
2. Independent oracle
3. Negative control
```

### Requirement traceability

这个测试到底验证哪条需求？

```text
T4 → R3
```

### Independent oracle

测试的 expected result 不要直接调用 production code 得到。

错误示例：

```cpp
EXPECT_EQ(actual, productionHelper(input));
```

如果 `productionHelper()` 本身错了：

```text
实现错
测试也错
→ PASS
```

更可靠的 oracle：

```text
解析解
独立 reference implementation
高保真 simulator
golden dataset
实验数据
旧版本 baseline
```

### Negative control

故意制造错误：

```text
关闭 terrain handling
```

正确测试应该：

```text
FAIL
```

如果仍然 PASS：

```text
测试本身不可信
```

---

# 7. 第四步：影响分析并实现

## 目标

新增功能时，只修改真正需要修改的部分。

## Codex 读取

```text
AGENTS.md
REQUIREMENTS.md
TEST_PLAN.md
baseline
相关源码
```

## 修改前先做 Impact Analysis

要求 Codex 区分：

```text
MUST CHANGE
MAY CHANGE
MUST NOT CHANGE
```

例如：

```text
MUST CHANGE
- rollout.cpp

MAY CHANGE
- test_rollout.cpp

MUST NOT CHANGE
- actuator interface
- state estimator API
```

## 临时提示词

```text
先进行 impact analysis，不要立即修改代码。

列出：
- directly affected modules
- indirectly affected modules
- public APIs
- shared state
- concurrency impact
- real-time impact

分类为：
MUST CHANGE
MAY CHANGE
MUST NOT CHANGE

随后只实施满足 REQUIREMENTS.md 所需的最小修改。

禁止：
- 无关重构
- 无关重命名
- 修改验收阈值来让测试通过
- 修改旧行为，除非 REQUIREMENTS.md 明确要求
```

---

# 8. 新功能应优先可隔离

如果可能：

```text
旧路径
和
新路径
```

应可明确区分。

例如：

```cpp
if (config.enable_terrain_rollout) {
    useTerrainAwareRollout();
} else {
    useOriginalRollout();
}
```

这样可以验证：

```text
feature disabled
→ old behavior unchanged

feature enabled
→ new requirement satisfied
```

这比直接替换旧逻辑更安全。

---

# 9. 第五步：验证和回归

## Codex 读取

```text
REQUIREMENTS.md
TEST_PLAN.md
baseline
```

## Codex 执行

至少包括：

```text
build
existing tests
new feature tests
regression tests
differential comparison
benchmark
git diff review
```

## 对机器人 / MPC 项目还应检查

```text
numerical regression
latency
p95 / p99 / max latency
jitter
memory allocation
real-time deadline
constraint violation
```

## Codex 写入

```text
VERIFICATION.md
```

---

# 10. VERIFICATION.md 写“证据”，不是写计划

推荐结构：

```markdown
# VERIFICATION.md

## R3 - Terrain-aware rollout

Status:
VERIFIED

Tests:
T4, T5

Negative control:
PASS
(disabling terrain handling causes T4 to fail)

Baseline comparison:
feature disabled:
max control error = 2.1e-8

Performance:
before = 4.8 ms
after  = 5.0 ms

Acceptance:
performance regression < 5%

Result:
PASS

Remaining risk:
Not yet tested on physical robot.
```

---

# 11. 新需求必须同时定义“允许变”和“不允许变”

不要简单说：

```text
“新增功能但不要影响旧代码”
```

而应该明确：

| 场景 | 是否允许变化 |
|---|---|
| 新功能启用 | 允许 |
| 新功能关闭 | 不允许 |
| Public API | 通常不允许 |
| 旧配置文件 | 尽量兼容 |
| 旧 regression dataset | 不允许 |
| 性能 | 允许在明确阈值内变化 |

例如：

```text
Terrain enabled:
behavior MAY change

Terrain disabled:
behavior MUST remain unchanged
```

---

# 12. 最推荐的 Requirement/Test 映射

维护一个简单矩阵即可：

```text
Req   Test     Oracle        Negative control   Status
R1    T1       analytical    M1                 VERIFIED
R2    T2,T3    baseline      M2                 VERIFIED
R3    T4       simulator     M3                 VERIFIED
R4    T5       benchmark     overload           VERIFIED
R5    -        -             -                  UNVERIFIED
```

看这张表就能知道：

```text
哪些需求真正有证据
哪些只有测试文件
哪些还没有验证
```

---

# 13. 第六步：独立复核

最好不要让实现任务在：

```text
“所有测试 PASS”
```

后立刻结束。

再开一个 Codex session，让它只做 reviewer。

## Reviewer 读取

```text
原始任务
AGENTS.md
REQUIREMENTS.md
TEST_PLAN.md
VERIFICATION.md
git diff
```

## Reviewer 不应修改代码

它只回答：

```text
PASS
FAIL
PARTIALLY VERIFIED
```

并指出证据和遗漏。

## 临时提示词

```text
不要修改代码。

作为 independent reviewer，检查：

- REQUIREMENTS.md 是否真的被满足
- TEST_PLAN.md 是否覆盖关键需求
- test oracle 是否独立
- negative control 是否有效
- 当前 git diff 是否包含无关修改
- 是否存在旧功能回归
- 是否存在性能、数值、并发、实时性风险
- VERIFICATION.md 的结论是否被证据支持

最终给出：

PASS
FAIL
PARTIALLY VERIFIED

每个结论必须附证据。
```

---

# 14. AGENTS.md 中真正应该长期写什么

`AGENTS.md` 只保存稳定规则，不保存某一次任务的具体 prompt。

建议包含：

```markdown
# AGENTS.md

## Required workflow

For non-trivial changes:

1. Read REQUIREMENTS.md.
2. Read TEST_PLAN.md.
3. Establish baseline before changing behavior-sensitive code.
4. Perform impact analysis.
5. Implement the smallest necessary change.
6. Run existing tests and new tests.
7. Run regression and benchmark checks.
8. Record evidence in VERIFICATION.md.

## Test integrity

Do not weaken tests only to make implementation pass.

Changes to:
- acceptance thresholds
- expected outputs
- test fixtures
- test oracles

must be independently justified.

## Completion policy

Do not claim completion unless:
- applicable requirements pass;
- regression checks pass;
- verification evidence exists;
- remaining unverified items are reported explicitly.
```

---

# 15. 哪些内容是“文件内容”，哪些是“临时 Prompt”

这是最容易混淆的地方。

## 应长期写进项目文件的内容

```text
AGENTS.md
→ 长期工作规则

REQUIREMENTS.md
→ 系统需求

TEST_PLAN.md
→ 测试规范

VERIFICATION.md
→ 实际验证记录
```

## 不应该长期写进这些文件的内容

类似：

```text
“先不要改代码”
“请阅读整个项目”
“列出 MUST CHANGE / MAY CHANGE”
“现在作为 reviewer”
```

这些是：

```text
一次任务中的 Codex Prompt
```

它们应该直接发给 Codex，而不是长期保存为需求正文。

---

# 16. 一张图看完整工作流

```text
                   ┌───────────────┐
                   │   AGENTS.md   │
                   │ 长期工作规则   │
                   └───────┬───────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ REQUIREMENTS.md │
                  │ 什么叫做正确     │
                  └───────┬─────────┘
                          │
                          ▼
                  ┌─────────────────┐
                  │   TEST_PLAN.md  │
                  │ 如何证明正确     │
                  └───────┬─────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
      Baseline / Regression      New Implementation
             │                         │
             └────────────┬────────────┘
                          ▼
                  Run tests/benchmark
                          │
                          ▼
                 ┌─────────────────┐
                 │ VERIFICATION.md │
                 │ 实际证据与结论   │
                 └────────┬────────┘
                          │
                          ▼
                 Independent Review
```

---

# 17. 最小可执行模板

如果你不想维护复杂流程，至少保持下面四件事：

```text
1. REQUIREMENTS.md
   写清“必须做到什么”

2. TEST_PLAN.md
   写清“怎么证明做到”

3. Baseline
   修改前记录旧行为

4. VERIFICATION.md
   修改后记录真实证据
```

然后要求 Codex 永远遵守：

```text
先理解
→ 再修改
→ 再验证
→ 最后才宣布完成
```

---

# 18. 最终完成判据

一个任务只有满足以下条件才算真正完成：

```text
NEW REQUIREMENT       PASS
EXISTING TESTS        PASS
REGRESSION            PASS
NUMERICAL CHECK       PASS
PERFORMANCE           PASS
API COMPATIBILITY     PASS
DIFF REVIEW           PASS
UNVERIFIED ITEMS      EXPLICITLY REPORTED
```

对于机器人和实时系统，再增加：

```text
SIMULATION VALIDATION
TARGET HARDWARE VALIDATION
REAL-TIME DEADLINE CHECK
```

---

# 19. 最重要的判断标准

不要问：

```text
“Codex 是否说任务完成了？”
```

而应该问：

```text
“REQUIREMENTS.md 中每条需求，
是否都能在 VERIFICATION.md 中找到
独立、可重复的验证证据？”
```

如果不能，就还不能认为任务已经被完整验证。
