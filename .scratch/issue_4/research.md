# Issue #4 Research — Proposed, ready for review

## 研究结论

源码层面存在实现路径，但当前环境尚不能视为满足已批准需求；未做运行验证。
证据固定到下文的本地 IsaacLab commit，避免把最新在线文档直接当成本地 API。

| 领域 | 已确认事实 / 影响 | 建议方向（未批准） |
| --- | --- | --- |
| 地形与出生点 | 内置箱体/阶梯原点可能在顶部；默认重置会绕过攀爬 | 明确入口、障碍、落地区与出口；比较包装原语和定向生成器 |
| 成功判定 | 位置越界不能证明落地；仅 tile 边界也不能阻止在 tile 内绕箱 | 有序通过条件 + 合法区域 + 有限落地确认；阈值不在本报告确定 |
| 地形课程 | 内置距离课程不是成功率课程 | 比较按类型/难度统计的窗口成功率与 EMA |
| 速度课程 | 命令指标结算晚于课程调用，日志归一化分母也不一定是实际尝试时长 | 比较实际尝试平均误差与平均跟踪得分，并明确采样生命周期 |
| 共享观测 | 单份 noisy history 与单份 depth 可由下游复用 | 优先复用官方 ObsManager；终止帧/重置需要单独处理 |
| 论文一致性 | 历史长度、接触数量、若干奖励语义与当前代码有差异 | 为每个量记录论文证据、Go2 适配和待批准缺项 |

### 推荐进入 Specify 后优先解决的选择

1. 地形路线与出生点方案，以及有限落地确认的能力边界。有限窗口不能保证未来永不摔倒。
2. 课程统计范围、实际尝试时长归一化，以及短暂失败回合对速度课程的影响。
3. 同一噪声样本和终止帧的数据生命周期；避免用 reset 后状态拼接前一回合的世界模型或 AMP 转移。
4. 奖励物理参考、关节/接触部位映射、传感器配置、随机化与 AMP 缺项的明确项目选择。

上述均为研究建议，不是自动接受的架构或接口。无需为了阶段切换提前选定全部参数。

## Status and scope

Explore approved; Research authorized by user: “批准结束 Explore，进入 Research”.
This document compares feasibility; it does not approve production architecture,
interfaces, parameter defaults or implementation. Requirements R1–R24 and TODO-01
in [requirements.md](requirements.md) govern this investigation.

## Evidence baseline

- GitHub issue #4 reread with `gh issue view 4 --json title,body,comments,url`; no comments.
- Local IsaacLab `VERSION`: 3.0.0; commit `346c74fe722ad371a6c663e3b384b3d172966d11`;
  `git -C ../IsaacLab status --short` returned no changes.
- Project resolves editable IsaacLab sources from `../IsaacLab` via
  [pyproject.toml](/home/sevnce-mr/r3la/pyproject.toml).
- These identify inspected source, not proof of the installed runtime or backend functionality.
- Current project contains pre-existing user changes. No production files changed in Research.

## Primary-source investigations

- [Observation lifecycle and sensor data](#observation-lifecycle-and-sensor-data).
- [Terrain, success and curricula](#terrain-success-and-curricula).
- [Paper, rewards, randomization and AMP](#paper-rewards-randomization-and-amp).

Each investigation separates source facts from proposed approaches and unresolved details.

## Observation lifecycle and sensor data

Scope: R4, R21–R24. Read-only source investigation; no implementation, imports, experiments, simulations or tests. Findings apply to local IsaacLab commit `346c74fe722ad371a6c663e3b384b3d172966d11` (`git -C ../IsaacLab rev-parse HEAD`; `git -C ../IsaacLab status --short` was empty). This is evidence about that checkout, not a claim about every IsaacLab 3.0 release. Project files are the current working tree. Parent task supplied approval to research; earlier Explore status records are historical. Direct `gh issue view 4 --json title,body,comments,url` failed with network connection error; approved issue requirements were read from requirements.md.

Sources below use repository-relative paths; `../IsaacLab/` means `/home/sevnce-mr/IsaacLab/`. Line references identify inspected source, not runtime validation.

### Confirmed source facts

#### One noisy sample and clean critic

- `../IsaacLab/source/isaaclab/isaaclab/managers/observation_manager.py:348–373,422–451`: `compute()` computes every group again, then assigns `_obs_buffer`. It is not a memoized physical-instant sample lookup. Each configured noisy term invokes its noise callback separately. Duplicating a physical quantity into several corrupted groups therefore does not enforce shared noise.
- The existing project has one noisy `proprio` group, separate current `commands`, a dictionary `target`, and current `privilege`: `src/r3la/tasks/velocity/config/Unitree/parkour_env_cfg.py:353–458`. Actor history includes angular velocity, projected gravity, relative joint position/velocity and previous actions. A downstream consumer can use the last time slice of this same returned history for encoder/decoder quantities without drawing noise again. That is a feasible interpretation of R22–R23, not an approved final tensor contract.
- The privileged group disables corruption at project config line 450. Although its angular-velocity term declares noise at lines 421–424, the manager sets term noise to `None` when group corruption is disabled (`observation_manager.py:655–657`). Thus that declaration does not make the current critic noisy. Privileged history is not enabled.
- Processing order is callback, tensor processors, noise, clipping, scaling, delay, history (`observation_manager.py:422–490`). Noise ranges refer to values before clipping/scaling. History stores the resulting measurement, so past noisy frames are retained, not re-corrupted when read.

#### History order, reset and observation timing

- Local `ObservationGroupCfg.history_order="time"` exists and supports a flattened group reshaped as batch × history × combined features (`../IsaacLab/source/isaaclab/isaaclab/managers/manager_term_cfg.py:303–325`). Conditions are positive group history length, concatenation, flattened history and concatenate dimension -1. Current project already sets history length 4 and `history_order="time"` (project config lines 62,371–376). These current values are not paper reproduction approvals.
- CircularBuffer stores oldest to newest; reset clears selected rows; their first subsequent append fills the whole history with that first measurement (`../IsaacLab/source/isaaclab/isaaclab/utils/buffers/circular_buffer.py:105–110,146–208`). Thus startup/reset padding repeats one sample, including one noise draw, rather than synthesizing several independently noisy past states. Selected resets preserve other environments' history.
- `compute(update_history=False)` still executes callbacks and noise, but initialized history terms return the already stored history without adding the new measurement (`observation_manager.py:434–487`). Repeated calls can consume RNG and recompute non-history outputs even while history does not move. Construction probes observation outputs for dimensions (`observation_manager.py:665–666`), so any proposed stateful sampler must tolerate probing.
- RL step increments counters, computes terminations/rewards, optionally records observations, optionally computes `extras["final_obs"]`, resets done environments, updates commands/interval events, then calls `compute(update_history=True)` for returned observations (`../IsaacLab/source/isaaclab/isaaclab/envs/manager_based_rl_env.py:229–284`). Returned observations of done rows are new-episode observations. `compute_final_obs` defaults to false (`manager_based_rl_env_cfg.py:47`).
- **Critical inferred terminal-history gap:** the optional final-observation call uses the default `update_history=False` (RL env lines 247–249). For initialized history terms, the terminal frame is therefore not appended; final proprio history ends at the prior recorded frame, while ordinary current terms read the terminal state. Enabling the flag alone cannot be treated as a synchronized terminal world-model/AMP transition contract. This conclusion follows directly from the two code paths; no runtime test was run.
- Reset invokes curriculum before scene reset and reset events; then observation/action/reward managers reset (`manager_based_rl_env.py:382–409`). A sampler keyed only by the global step counter would collide between terminal and post-reset observations in that same step. Episode/reset identity must be considered if a cache approach is later selected.

#### Depth and scans

- Current camera uses 320 × 240, 0.1 s update period, RGB plus image-plane depth, NewtonWarp renderer, and offset quaternion `(0,0,0,0)` (`src/r3la/tasks/velocity/config/Unitree/parkour_env_cfg.py:134–145`). The zero quaternion is not a valid unit rotation; intended Go2 pose/FOV/calibration need specification and eventual validation. Existing values are not evidence of paper agreement.
- Target contains one depth term using `mdp.image_depth` (project config lines 341–350). The local class defaults to image-plane depth, normalization enabled, invalid values replaced by zero, no range rescaling, channels last and one frame; absent optional rescaling it returns metric depth (`../IsaacLab/source/isaaclab/isaaclab/envs/mdp/observations.py:467–514`). Consequently current default “normalize” does not imply unit-interval depth. Same input/target can be obtained by sharing this returned image. Adding separate calls/groups is unnecessary for R24.
- Sensor sample clock and due-data behavior are explicit (`../IsaacLab/source/isaaclab/isaaclab/sensors/sensor_base.py:214–236`). A depth sample may be held across policy steps; same-image input/target does not establish synchronization with every proprioception instant. Camera reset explicitly invalidates its buffers (`sensors/camera/camera.py:649–672`), unlike the generic sensor reset contract of retaining reset data until positive-time update (`sensor_base.py:186–212`). Actual post-reset render freshness is backend-dependent and untested.
- RL step's post-reset rerender path is conditional on rendering enabled, RTX sensors and rerender count (RL env lines 254–257). Generic sensor reset comments must not be used to conclude every camera returns zero after reset, or every renderer refreshes identically.
- `height_scan` computes sensor world z minus ray-hit world z minus offset (`envs/mdp/observations.py:293–300`). It is not automatically a gravity-aligned body-frame geometric surface model. The target config clips scans to [-1,1] (project lines 315–339). Missing-hit infinities can become saturated values; NaN behavior and validity masks remain to specify. Foot scans use per-foot yaw alignment and offsets; body and terrain scans use base yaw alignment (project lines 146–258). Paper-required frame, window, resolution and invalid-value semantics still require reconciliation.

#### AMP feasibility and joint ordering

- Current `is_contact` thresholds the norm of **normal** contact forces, not total forces (`src/r3la/tasks/velocity/mdp/observations.py:16–32`). `ContactSensorCfg` has optional pose, contact-point and friction tracking flags, but no normal-force opt-in (`../IsaacLab/source/isaaclab/isaaclab/sensors/contact_sensor/contact_sensor_cfg.py:30–46`). The normal-force API returns a proxy whose `.torch` shape is environment × body × 3 (`../IsaacLab/source/isaaclab_newton/isaaclab_newton/sensors/contact_sensor/contact_sensor_data.py:143–154`). Its optional return type still warrants initialized-backend validation; `track_friction_forces=False` alone does not disable the normal-force quantity. Normal versus total force thresholds must be explicit in the later contact contract.

- Existing observation groups have no AMP output contract (project lines 454–458). The installed humanoid AMP example obtains joint position/velocity, reference-body pose/velocities and key-body positions from articulation data, then builds an AMP history (`../IsaacLab/source/isaaclab_tasks/isaaclab_tasks/contrib/humanoid_amp/humanoid_amp_env.py:60–77,210–232`). This demonstrates accessible state quantities, not a Go2/SWAP feature definition. Its newest-first history at index 0 differs from ObservationManager's oldest-first order; do not copy ordering implicitly.
- Data-only support is feasible without introducing a discriminator or motion loader into this issue. Go2 body selection, coordinate transformations, transition timing, absolute versus relative joints and reference-data compatibility must be selected in Specify using paper/author evidence. AMP clean state should not silently reuse corrupted policy measurements.
- **Current ordering risk:** actions explicitly preserve `_SYMMETRY_JOINT_NAMES` order (project config lines 298–303), whereas joint observation SceneEntityCfg instances omit `preserve_order` (lines 363–368,396–398,432–438). The library defaults it to false and passes it to `find_joints` (`../IsaacLab/source/isaaclab/isaaclab/managers/scene_entity_cfg.py:110–121,175–196`). Named lists alone do not prove action/joint feature correspondence. Actual resolved ordering needs verification before a public contract is approved.

### Alternatives and recommendations — Proposed, not approved design

1. **Expose one canonical noisy history and one canonical depth output; downstream selects views.** Uses existing official manager capabilities, satisfies shared sample requirements on normal steps with minimal custom machinery, and retains clean critic. Requires documented feature/time ordering, reset padding and terminal handling; cannot obtain a synchronized terminal history by merely turning on the current final-obs flag.
2. **Introduce a project-owned sampler/cache with explicit observation and reset identity.** Can provide consistent values to multiple groups and define terminal snapshots. More lifecycle complexity: shape probing, repeated reads, recorder calls, partial resets, command/event timing, history ownership and sensor sampling clocks all require tests. A global-step-only cache is insufficient.
3. **Separate independently corrupted actor/encoder/decoder groups.** Official APIs permit this, but it fails approved R22–R23 and should not be selected.

Prefer investigating alternative 1 first, then the narrowest lifecycle adaptation needed for terminal data if that data contract is approved. No final architecture/interface or terminal convention is selected by this research document. Retain TODO-01 for later depth corruption; implement no noise model now.

### Open questions and deferred Specify decisions

- Exact Go2 feature order, tensor shapes, history duration/frequency, reset padding policy and unit/scaling/noise values; confirm which paper values transfer unchanged.
- Terminal observation and transition requirements for world-model and AMP consumers: capture at termination before reset, mask, history inclusion and sensor frame age. Decide how interval perturbations and command resampling define an observation instant.
- Camera orientation/FOV/near/far clipping, image size/preprocessing, invalid-depth encoding and per-image sampling metadata; target scan frames and missing-hit treatment.
- Exact AMP state set and reference-data compatibility; this is data scope only, with no training algorithm or dataset implementation.
- Later verification must test shared-value equality across consumers, chronological feature layout, partial resets, one-step terminal transitions, clean critic, same depth target/input, joint order and sensor freshness. These tests have not been run.

### Investigation commands and outcome

Read AGENTS.md, docs/agents/domain.md, docs/agents/issue-tracker.md, requirements.md and status.md. GLOSSARY.md and ADR directories were absent. Inspected source with `rg`, `nl -ba` and `sed`; `git -C ../IsaacLab rev-parse HEAD` and `git -C ../IsaacLab status --short` succeeded. GitHub issue read failed due to network. No production files changed. No tests or simulations performed; backend capability and dynamic correctness remain unverified. Next stage requires explicit approval; this document supplies Research evidence only.


## Terrain, success and curricula

Status: Draft research findings; alternatives and recommendations are **Proposed**, not approved design. No production changes or experiments. Requirements R9–R20 govern this investigation. Parent session reports explicit approval to enter Research; older status entries awaiting transition are historical.

### Evidence scope / confirmed facts

Static source inspected in `../IsaacLab`, HEAD `346c74fe722ad371a6c663e3b384b3d172966d11`, clean working tree when inspected. This establishes the behavior of this local checkout, not all distributions called “IsaacLab 3.0”. Paths below are relative to repository root; `IL` abbreviates `../IsaacLab/source/isaaclab/isaaclab` and `ILT` abbreviates `../IsaacLab/source/isaaclab_tasks/isaaclab_tasks`. These are local primary-source citations. Sub-agent's `gh issue view 4 --json title,body,comments,url` failed to connect; approved local requirements were read, and parent notified. No authoritative-source web claims are made here.

#### Existing project gaps

- `src/r3la/labs/terrains/parkour_terrain_cfg.py:6` defines 10 m tiles with rails, ring gaps, pits, central boxes, flat and heightfield random roughness. Stairs, lateral slopes and explicit irregular rocks/tilted/mirrored variants are not represented by this list. Current values are existing code, not approved Go2 geometry.
- `src/r3la/tasks/velocity/config/Unitree/parkour_env_cfg.py:645` has timeout and base-contact terminations; `:656` uses `terrain_levels_vel` and has a success-curriculum TODO. `:715` enables generator curriculum when the curriculum term exists; play overrides `:761` randomize terrain assignment and reduce the grid.
- Stock `ILT/core/velocity/mdp/curriculums.py:23` promotes on radial XY displacement exceeding half tile length, demotes on insufficient command-scaled travel, then calls importer `update_env_origins`. This is neither traversal/landing success nor an empirical success-rate curriculum. Sideways displacement can promote it.

#### Generator and origin semantics: critical feasibility constraint

- `IL/terrains/terrain_generator.py:235` assigns one terrain configuration per column when curriculum is enabled. Row difficulty is `(row + uniform_random)/num_rows`, remapped to the configured difficulty range (`:251`). Adjacent columns can contain the same type; rows are difficulty bins, not exact fixed difficulty values.
- Sub-terrain function returns meshes and **one origin**, `IL/terrains/terrain_generator.py:381`. Both receive `(-size_x/2, -size_y/2, 0)` translation, then placement by tile row/column (`:334`), then a global centering translation (`:181`). The stock return contract does not carry task entry, obstacle footprint, completion or landing-zone metadata.
- `IL/terrains/terrain_importer.py:337` uses generated origins for environment assignment. `:381` initializes random terrain levels and assigns columns across environment IDs; `terrain_types` is a column index, not necessarily an obstacle-family enum. `:360` updates rows without changing columns, clips below zero, and **randomizes the row when advancing beyond the hardest level**. This last behavior must not be silently mistaken for saturating at maximum difficulty.
- The root reset implementation adds default robot pose, `env.scene.env_origins` and configured random displacement (`IL/envs/mdp/events.py:1282`). Therefore origin is operationally a spawn anchor, and is not necessarily the geometric center of the tile at ground height.
- Stock box origin is at the central box **top**, `IL/terrains/trimesh/mesh_terrains.py:546`; stairs origin is at the summit (`:141`); pit origin is at pit bottom (`:484`); ring gap origin is central platform (`:588`). Existing center spawning on a box does not require climbing it. Moving spawn to an approach zone without correcting vertical placement can also put Go2 above/below the surface.
- Consequently a detector using `root_x - env_origin_x > tile_length/2` cannot universally encode obstacle completion, especially if origins are changed to approach positions. Tile frame, spawn frame, obstacle bounds and landing bounds must be distinguished in Specify. Curriculum changes require selecting corresponding geometry metadata before the next spawn.

#### Terrain feasibility comparison

| Required family | Available local primitive | Fit and unresolved adaptation |
| --- | --- | --- |
| Stairs | Mesh pyramid stairs (`mesh_terrains.py:49`) and heightfield pyramid stairs (`height_field/hf_terrains.py:155`) | Stair construction exists, but stock shape rises from all sides to a central platform. A directed staircase route requires explicit entry/exit interpretation or custom geometry. |
| Box climbing | `mesh_terrains.py:489` | Central box on full tile floor is reusable geometry. Center-top spawning must change for climbing. Corridor/footprint rules must reject going around the box within the same tile. |
| Gap | `mesh_terrains.py:551` | Stock gap surrounds a central island on all four sides, not a single transverse ditch. Center-to-outside route crosses once; edge-to-edge route crosses twice. One sub-terrain of one type permits multiple features, but which route reproduces intended task remains open. |
| Lateral slope | Pyramid slope (`height_field/hf_terrains.py:85`) | Stock pyramid is not a uniform transverse bank. A dedicated heightfield/mesh can encode a lateral slope; full-tile rigid rotation would also tilt approach/landing surfaces and boundaries unless carefully constructed. |
| Irregular rocks | Repeated objects (`mesh_terrains.py:744`); custom callable object type accepted (`:784`); random grid (`:243`) | Repeated boxes/cylinders/cones and a protected central platform exist. They are not evidence of irregular rock morphology. Custom mesh objects/heightfields are feasible extension seams; their fidelity needs approval. Random roughness must not silently substitute for rocks. |
| Unilateral tilted box/stair/gap | No directly matching listed primitive | Custom terrain function can compose/transform meshes through the stock `(difficulty, cfg) -> (meshes, origin)` seam. Need define whether tilt applies to obstacle, support surface, landing surface or entire route. |
| Mirrored evaluation | Mesh or heightfield geometry can be reflected | Mirror geometry, route/landing metadata, initial pose and relevant orientation conventions together. Merely negating commands is not a mirrored scene. Reflection changes mesh winding; verify collision normals/mesh integrity later. |

Sources for table are `IL/terrains/` plus indicated path. Alternatives: (A) wrap existing primitives and explicitly constrain routes, minimizing geometry work but retaining pyramid/ring shapes; (B) custom directed terrain generators using stock mesh/import machinery, more geometry validation but more direct control over approach/obstacle/landing zones; (C) mesh-file terrain (`mesh_terrains.py:714`), useful for fixed evaluation assets but weak for continuous procedural difficulty without asset variants. None selected.

### Success/landing detector alternatives — Proposed

R16 rules out boundary crossing alone. R19 rules out leaving tile sideways and bypass; checking tile bounds alone does **not** reject circling a central box inside the same tile.

1. **Far-side position only:** simplest but invalid for R16; counts airborne crossings and subsequent failed landings. Reject as sole detector.
2. **Far-side position plus one instantaneous foot contact:** inexpensive, but a front foot may brush the edge while the body falls. Net foot force can be wall contact rather than supporting contact. A single frame does not establish continued capability.
3. **Ordered traversal gate(s), bounded route corridor, then bounded landing confirmation:** first enter the valid approach/obstacle region, remain within the legal corridor, reach a designated landing region with enough body/foot clearance, and sustain acceptable support/uprightness for a short confirmation interval without base contact or bypass. Uses a few per-environment flags/timers and existing state/contact data. This is the leading simplicity/validity compromise, **not approved**. A condition requiring every foot down simultaneously may wrongly reject ordinary gait; intermittent gait contacts need deliberate aggregation. Exact support count, duration, uprightness, landing clearance and speed conditions remain open.
4. **Extended post-obstacle locomotion test / dynamic stability estimator:** stronger evidence of ability to continue but longer episodes, more thresholds, and more false negatives during valid maneuvers. Capture-point/support-polygon criteria are not automatically valid on dynamic Go2 jumping and irregular contact. Probably unnecessary unless simpler detector fails approved acceptance cases.

All finite confirmation windows approximate future capability; none guarantees the robot will never fall later. Explicitly approve this limitation and a reproducible “immediate landing failure” time/space horizon. A short forward advance in the landing region can strengthen continued-motion evidence, but must not be adopted without approving its geometric/time cost.

Proposed detector invariants for later tests: success impossible before traversing the required region; airborne far-side crossing alone fails; failed landing never increments success; within-tile circling and adjacent-tile detours fail; allowed leg contact does not itself terminate; base contact wins over simultaneous completion; timeout cannot yield success; completed attempt contributes only once. Terminal precedence on exact timeout/completion coincidence must be specified (conservative failure precedence is recommended).

A route corridor must leave sufficient room for approved lateral path adjustments (R17). It should not silently turn the task into exact centerline tracking. Shape-dependent gates or obstacle-spanning barriers may be needed to reject within-tile shortcuts without excluding legitimate motion. Body-center containment versus body/feet containment is also a deferred accuracy/complexity choice.

### Curriculum alternatives — Proposed

#### Terrain curriculum, R11

- **Binary promotion/demotion after each completed attempt:** minimal state, easy interpretation, but noisy and not explicitly a measured success rate. Accept only if user agrees it meets the issue's success-rate intent.
- **Windowed success rate per type/level (and possibly per environment):** counts completed attempts, promotes above one threshold, demotes below another, holds between; minimum sample count prevents one-event jumps. Transparent and suited to empirical rate requirement, but adds window/count state and choice of grouping.
- **Exponentially smoothed success rate:** bounded state and responsive, but sensitivity to decay, initialization and update order; asynchronously completed attempts need count-aware aggregation.

Recommend comparing window/count-based rate with EMA in Specify, retaining built-in row/origin migration where its top-level recycling behavior is approved. Only terminated actual attempts contribute; startup/manual resets and duplicate manager callbacks must not count. Timeout/bypass/base failure are unsuccessful attempts. Pooling all families can hide difficult-family failures; per-family/level statistics are a plausible proposal. With a small environment count, global column sampling can omit families entirely; verification should explicitly select families rather than rely on random assignments.

#### Velocity curriculum, R20

- **Mean tracking error over actual attempt:** easy physical interpretation (forward error in m/s, yaw error in rad/s if included), naturally tolerates transient deviations when mean remains acceptable. Absolute, squared/RMS or normalized error are alternatives; squared error penalizes jump transients more strongly. Include lateral/yaw tracking only as explicitly chosen components, since targets are zero.
- **Mean bounded tracking reward over actual attempt:** convenient reuse of reward calculations and smooth bounded quality metric. Must remove reward weight/time scaling and divide by actual attempt duration, not maximum episode duration. Ties the curriculum to reward shape/scale unless separately defined.
- **Fraction of time under instantaneous error threshold:** can permit occasional transients, but depends on another threshold and can over-penalize legitimate maneuver phases. Requiring every frame to satisfy tracking violates approved R20.

Recommend actual-attempt mean error or bounded tracking score; no metric/threshold selected. Short failed attempts can look excellent, and longer approaches can dilute poor obstacle tracking. Minimum usable duration and whether short/failure attempts are excluded, included, or prevented from promotion must be decided. Gating on traversal success would add a dependency not implied by R11/R20; do not silently adopt it. Curriculum range changes during asynchronous resets should affect the intended next commands only; global range vs per-family/per-environment range is open. Command resampling within an attempt is also open; any score must compare each sample to the command in force for that physical transition.

### Manager order / metric traps — confirmed facts and implications

- `IL/envs/manager_based_rl_env.py:230`: increment counters, compute terminations, compute rewards; `:244`: reset finished environments; `:274`: update commands; `:281`: final observations. Therefore reward accumulation includes the terminal transition.
- `_reset_idx` at `:382` runs curriculum first (`:389`), then scene reset and reset events (`:391`), then observation/action/reward/curriculum/command/event/termination manager resets (`:402`–`:420`). Curriculum can inspect terminal state and reward accumulators **before** spawn/migration/reset clearing. A success term's state must survive until consumed. Initial/manual reset also uses this lifecycle, requiring an actual-attempt guard.
- `IL/managers/termination_manager.py:152` computes each term and ORs results; it does not resolve success versus failure precedence. `get_term` (`:181`) exposes individual results. `reset` (`:129`) resets class-based term state, but this checkout does not simply clear every done tensor there; do not rely on implicit clearing when handling startup/manual reset.
- `IL/managers/reward_manager.py:143` computes weighted term values; `:150` adds weight × dt-scaled values to episode sums. Reset log at `:116` divides by **maximum** episode seconds. This logged value is not a whole-attempt mean for successful early termination.
- **Local command implementation is especially important:** `IL/envs/mdp/commands/velocity_command.py:85` has finalized `error_vel_xy`, `error_vel_yaw`, and `success_rate` metrics, with private running sums. `:123` accumulates errors and `:133` finalizes means only during command reset; then base reset logs/clears metrics. Curriculum runs **before** that finalization, so reading public finalized metrics during curriculum does not provide the just-ended attempt. Its `success_rate` means thresholded velocity tracking, not parkour success, and writes shared log `Metrics/success_rate` (`:152`). Logging requires disambiguation to avoid misreporting traversal success.
- `IL/managers/command_manager.py:146` calls `_update_metrics` in command compute. Because env command compute occurs after autoreset, command metrics naturally include post-reset samples and exclude the just-terminal physical state from the ended episode. Reusing these accumulators blindly will not exactly measure all action transitions of the attempt. A task metric accumulated pre-reset, or deliberate command extension with verified timing, is a feasible alternative. No API/interface selected.

### Assumptions, open questions, recommendations

Assumptions: standard manager step/reset path is retained; explicit geometric metadata is feasible alongside stock terrain import; contact sensors can supply an adequate proxy for landing after later validation. These are feasibility assumptions, not approved architecture.

Open questions for Specify: route meaning for central/pyramid/ring primitives; exact bank/tilt/mirror definitions; Go2-safe geometry/difficulty; origin/spawn/landing geometry; completion clearance/confirmation and failure precedence; bounds vs legitimate lateral adjustment; curriculum statistics scope/window/thresholds/top-level policy; velocity metric/duration/short-failure treatment/command resampling. No defaults are selected.

Recommended next work after Research approval: resolve the high-impact geometry and detector alternatives, then document contracts and Proposed ADRs in Specify. Do not implement until the staged approvals permit it.

### Verification record

Executed read-only `cat`, `rg`, `sed`, `nl`, `git -C ../IsaacLab rev-parse HEAD`, `git -C ../IsaacLab status --short`; source checkout was clean. GitHub read failed with connection error. No simulation, training, Python import, numerical experiment or runtime test was performed. Only this research Markdown artifact was written. Static feasibility does not prove terrain collision quality, landing classification accuracy, API runtime compatibility or curriculum training performance.


## Paper, rewards, randomization and AMP

Status: Draft Research evidence, 2026-11-05. No design choices approved here.
Scope: R3, R6, R14, R21 and parameter provenance. Read-only source inspection;
no simulation, imports, experiments, production edits or tests.

### Confirmed evidence and source limits

The [SWAP PDF](https://arxiv.org/pdf/2606.19928), v1, was read through the web
reader; page 5 screenshot was requested to cross-check Table III. The
[project website](https://swap-parkour.github.io/) was inaccessible through the
web tool; shell curl failed DNS resolution. No author-linked implementation was
verified. This does **not** establish that no implementation exists. `gh issue
view 4 --json title,body,comments,url` also failed network access in this worker;
the parent owns the issue read, and the approved issue-local requirements were read.

Compact paper evidence (all from the linked PDF; consult the indicated original
tables rather than treating this note as a replacement): Table II specifies five
actor frames; Table I specifies eight thigh/shank flags. Table III uses
roll²+pitch², collision threshold zero, σ=0.15, σh=σo=0.1, desired height 0.6 m;
air-time has no displayed command gate. Section III.D adds AMP transition pairs
and expands velocity to 3 m/s. Figure 2 gives 50/10 Hz. Section IV.B uses boxes
≤1.9 m, gaps ≤3 m, stairs 0.23 m, slopes ≤60°. Table IV's Apollo is 72 kg.
Missing reproducibility details include AMP feature schema/dataset/weight,
randomization ranges, noise distributions, actuator/action settings, stance
thresholds, exact terrain construction and operational success detection.

Local dependency snapshot: `/home/sevnce-mr/IsaacLab`, HEAD
`346c74fe722ad371a6c663e3b384b3d172966d11`, clean `git status --short` at inspection.
These are facts about the installed checkout, not a claim about a released API.

### Local reward findings

Source keys:

- [Task configuration](../../../src/r3la/tasks/velocity/config/Unitree/parkour_env_cfg.py).
- [Project rewards](../../../src/r3la/tasks/velocity/mdp/rewards.py).
- [Installed reward APIs](/home/sevnce-mr/IsaacLab/source/isaaclab/isaaclab/envs/mdp/rewards.py).
- [Installed locomotion rewards](/home/sevnce-mr/IsaacLab/source/isaaclab_tasks/isaaclab_tasks/core/velocity/mdp/rewards.py).

| Item | Verified local behavior | Implication / question for Specify |
| --- | --- | --- |
| Tracking | Both terms use `std=sqrt(0.15)`; library divides squared error by `std**2`. Linear and angular velocities are body-frame. | Denominator matches the cited value; frame must be documented. |
| Orientation | `flat_orientation_l2` sums squared projected-gravity x/y. | Different formula from the cited orientation row; equivalence cannot be claimed at large parkour tilt. |
| Height | Height penalty uses root world z against 0.4 m, without scanner. Stance adds average finite terrain-scan z to 0.4 m. | Two height references coexist. Elevated platforms and terrain-grid origins change the first penalty independently of body clearance. Choose a physical reference explicitly. |
| Stance | Scalar tilt from `atan2(norm(g_xy), -g_z)`; command thresholds 0.1; contact threshold 1 N. Its default contact selector is every sensor body, while configuration does not pass a foot-only selector. | `.all()` therefore requires all selected links, not demonstrably four feet. Correct selector and orientation definition need review. |
| Contacts | Thigh/calf selector; count uses max normal-force norm across sensor history, threshold 1 N. | Threshold, temporal aggregation and normal-versus-total force require documented choices; anatomical mapping needs verification. |
| Air-time | Official helper multiplies first-contact air-time sum by planar command norm >0.1. | Extra command gate must be reviewed against the cited table. |
| Stumble | Project helper sums feet whose current horizontal total force exceeds four times absolute vertical total force. | No extra minimum-force threshold. Availability of total force differs by backend. |
| Abduction, power | Hip-joint deviation from authored defaults is squared; power sums absolute torque × velocity. | Meaningful Go2 mapping exists; resolved joint ordering still requires tests. |
| Smoothness | Stateful action second difference is disabled for first two calls after reset. | Initial-history convention is a project behavior needing acceptance. |
| Scaling | Installed RewardManager multiplies total weighted reward by step dt, currently 0.02 s. | Confirm convention before comparing raw logged magnitudes or mixing downstream learned rewards. |

Reward timing source: [RewardManager](/home/sevnce-mr/IsaacLab/source/isaaclab/isaaclab/managers/reward_manager.py:125).
Contact semantics source: [base contact data](/home/sevnce-mr/IsaacLab/source/isaaclab/isaaclab/sensors/contact_sensor/base_contact_sensor_data.py:197).
The latter documents a normal-force fallback for Isaac Sim PhysX 6.1, while
[Newton data](/home/sevnce-mr/IsaacLab/source/isaaclab_newton/isaaclab_newton/sensors/contact_sensor/contact_sensor_data.py:83)
exposes normal plus friction. Backend equivalence is not established by static inspection.

### Randomization and Go2 facts

Current configuration, not approved parameter provenance:

- Startup foot materials: static friction [0.4,1.2], dynamic [0.3,1.0],
  restitution [0,0.1], 64 buckets. Startup base COM ranges in metres:
  x/y ±0.05, z ±0.01. Base mass is log-uniform scaling [0.9,1.1].
- Reset pose x/y ±0.5 m and yaw ±3.14 rad, all six velocity components ±0.5;
  joint-position scale [0.5,1.5], zero joint velocity. Push interval [10,15] s
  sets x/y velocity within ±0.5 m/s. Reset force/torque ranges are zero.
- No actuator-gain randomization event is configured. The observation helper
  reads existing actuator/controller gains; reading a value does not randomize it.
- `randomize_shared_material` samples one material per environment, applies it
  to selected foot shapes, and caches values. Newton uses one friction sampled
  from the static range for both cached friction columns; its dynamic range is
  not sampled. PhysX paths use material buckets. It depends on private native
  fields (`_impl`, binding maps); Kamino explicitly raises unsupported.

Sources: [events configuration](../../../src/r3la/tasks/velocity/config/Unitree/parkour_env_cfg.py:461),
[material implementation](../../../src/r3la/tasks/velocity/mdp/events.py),
[gain reader](../../../src/r3la/tasks/velocity/mdp/observations.py:35).
The [installed gain randomizer](/home/sevnce-mr/IsaacLab/source/isaaclab/isaaclab/envs/mdp/events.py:635)
supports add/scale/absolute operations with uniform/log-uniform/Gaussian sampling
and distinguishes controller ownership. This is a feasible official candidate,
not an approved range or cadence.

[Installed Go2 asset configuration](/home/sevnce-mr/IsaacLab/source/isaaclab_assets/isaaclab_assets/robots/unitree.py:154)
authored initial root z is 0.4 m; it is not a measured standing-clearance result.
DC motor limits hip/thigh/calf are 23.7/23.7/45.43 N·m and
30.1/30.1/15.70 rad/s; stiffness 25, damping 0.5; self collisions disabled.
The asset references `Robots/Unitree/Go2/go2.usd`. Mass/inertia and geometric
dimensions in that USD were not measured here. Task action scale is 0.5 with
default-pose offset. These settings must remain distinguished from verified
hardware specifications and paper settings.

### Assumptions — not approved

- Existing task numbers are provisional carryovers until given provenance or
  accepted as project choices. Matching reward weights alone does not establish
  reproduction of effective reward behavior.
- Go2 nominal root height is only a candidate input to height-target selection.
  Scaling obstacle dimensions by body size alone has not established feasibility.

### Recommendations and open questions — deferred to Specify

1. Preserve the original Table III as authoritative reference, and document each
   chosen approximation, force definition and Go2 adaptation independently.
2. Resolve height reference and stance foot selection before accepting reward
   behavior. Select backend before claiming force-based penalty equivalence.
3. Approve randomization distributions/cadences and reset pose relative to the
   assigned obstacle. Full-yaw reset needs reconciliation with forward-only routes.
4. R21 needs a downstream-compatible AMP state schema, frame, joint order and
   consecutive-state timing. Candidate raw fields can be researched, but naming
   an invented feature vector “SWAP AMP input” would be unsupported. Ensure
   terminal state pairs are not replaced by next-episode reset states.
5. Record exact Go2 asset identity, dimensions and actuator assumptions before
   selecting terrain ranges and height targets; no Apollo performance goal is
   implied by R6/R8.
6. Existing history length 4 and thigh-only critic contacts must be reconciled
   with the cited table; current R22/R23 shared-noise semantics remain authoritative.

No automatic fixes or parameter selections were made. Suggested next step:
review these evidence gaps alongside the other Research notes, then explicitly
approve entering Specify with identified project choices.


## Backend and verification evidence

### Confirmed facts

Current task defaults to Newton MJWarp and explicitly selects NewtonWarpRendererCfg;
it also declares alternative physics presets. These declarations do not establish
working backend combinations. See [task config](/home/sevnce-mr/r3la/src/r3la/tasks/velocity/config/Unitree/parkour_env_cfg.py:87).

The renderer advertises image-plane depth, but missing rays default to zero,
whereas RTX background may be infinity. A backend-neutral depth contract therefore
requires explicit invalid-value handling. See
[renderer configuration](/home/sevnce-mr/IsaacLab/source/isaaclab_newton/isaaclab_newton/renderers/newton_warp_renderer_cfg.py:58).

Contact-force semantics are version-dependent: the base contact data documentation
states that Newton, OVPhysX and Isaac Sim PhysX 6.2+ expose normal plus friction
forces, while PhysX 6.1 falls back to normal forces with a warning. This matters for
horizontal/vertical force ratios in stumble rewards. See
[contact data contract](/home/sevnce-mr/IsaacLab/source/isaaclab/isaaclab/sensors/contact_sensor/base_contact_sensor_data.py:24).

Newton contact initialization explicitly requires `total_force_friction` in its
underlying sensor. Source compatibility must be checked against the actual installed
Newton version before claiming a successful runtime. See
[initialization](/home/sevnce-mr/IsaacLab/source/isaaclab_newton/isaaclab_newton/sensors/contact_sensor/contact_sensor.py:390).

The project's shared-material randomizer samples one value set per environment,
uses private backend implementation fields, treats Newton as having one friction
coefficient, and explicitly rejects Kamino. See
[material randomizer](/home/sevnce-mr/r3la/src/r3la/tasks/velocity/mdp/events.py:18).

The only current test, despite its registration name, asserts absence of registry
entries whose environment-config entry points start with `r3la.tasks`. It does not
prove successful registration or task behavior. See
[existing test](/home/sevnce-mr/r3la/tests/test_registration.py:14).

### Recommendations — unapproved

Start verification with one explicitly selected physics/renderer combination;
consider existing Newton MJWarp/Warp a candidate, not an established working
baseline. Alternative presets require their own evidence. Do not promise
multi-backend physical equivalence.

Avoid selecting success/contact/depth thresholds until source semantics and a
bounded runtime check are reconciled. Preserve approved physical meaning rather
than accepting a backend's incidental defaults as requirements.

### Assumptions and open questions

Runtime dependency resolution, assets, camera rendering and material writes have
not been exercised. Future checks must first inspect available RAM/VRAM, use
headless mode and at most two environments by default, and run serially with a
short explicit bound. Research experiments need explicit approval under AGENTS.md.

## Validation performed

Read-only source inspection, issue retrieval and primary-source reading only.
No simulation, training, imports of simulation packages, or numerical experiment.
A later implementation verification plan must cover episode outcomes, reset order,
noise sample identity, history alignment, finite sensor outputs, reward semantics,
and curriculum updates, rather than treating import success as sufficient.

## Candidate verification obligations — not executed

| Requirement | Evidence needed after design approval |
| --- | --- |
| R10, R12–R19 traversal/landing | Passing, airborne crossing, failed landing, timeout, bypass, simultaneous success/failure, and reset cases |
| R11, R20 curriculum | Terrain changes follow success statistics; speed changes follow duration-normalized tracking evidence, including short episodes and transient maneuvers |
| R4, R22–R24 data | Shared noisy sample identity, correct history order, reset isolation, clean critic, shared image target/input |
| R21 AMP | Valid consecutive state pairs at episode boundaries, once the required state content is sourced and approved |
| R3, R6 paper/Go2 | Numeric reward checks and an explicit paper-vs-Go2 parameter ledger, including units, frames and contact mappings |
| R9, R15 terrain | Per-type start/obstacle/landing/exit geometry and mirrored equivalents |

These are recommended coverage categories, not new acceptance thresholds. Runtime
checks must be approved and bounded; this research does not certify feasibility
through execution.

## Specify follow-up: default reset history and terminal data

Status: source facts confirmed; terminal contract alternatives under review.
Prompt: user approved S9 contents/order but requested native history padding, and
questioned terminal proprio history while requiring AMP terminal state.

At inspected commit 346c74fe722ad371a6c663e3b384b3d172966d11:

- CircularBuffer.reset clears selected storage to zero and resets push counts
  (`../IsaacLab/source/isaaclab/isaaclab/utils/buffers/circular_buffer.py:146`).
- First append detects zero push count and backfills the complete history from
  that one new sample (`circular_buffer.py:195`). The buffer returned to consumers
  after this append contains repeated first observations, not leading zeros.
- ObservationManager applies noise before append, then concatenates time-major
  frames (`../IsaacLab/source/isaaclab/isaaclab/managers/observation_manager.py:434`,
  `:469`, `:495`). Thus repeated reset slots share the same noisy draw.
- On done steps, ManagerBasedRLEnv optionally computes final observations before
  reset without history append, then resets and computes normal output with history
  append (`../IsaacLab/source/isaaclab/isaaclab/envs/manager_based_rl_env.py:244`,
  `:281`). Existing final history therefore ends at the prior sample; it must not
  be labelled as synchronized terminal proprioception.
- RSL-RL wrapper forwards timeouts for non-finite-horizon tasks but does not itself
  guarantee consumer-specific terminal latent/state alignment
  (`../IsaacLab/source/isaaclab_rl/isaaclab_rl/rsl_rl/vecenv_wrapper.py:155`).

No experiment or simulation was run. Source behavior is explicit; runtime checks
remain part of later approved verification.

### Terminal-history usefulness — inference and alternatives

Actor does not select another action for an ended attempt, so an additional full
terminal actor-history stack is not intrinsically required. This differs from
terminal current measurements: a world-model learner may use the final valid
transition/reconstruction, and timeout value evaluation may need terminal critic
state with a compatible external latent. Details depend on the future runner's
chosen loss masks and finite/infinite-horizon semantics, not on observation shape
alone. These are reasoning implications, not claims that a training implementation
has been inspected or validated.

Alternative A (recommended, pending approval): no terminal history append/export;
export one terminal current noisy proprioceptive sample and corresponding command
separately, plus terminal clean critic/AMP state, sensor data with age and valid
boundary masks. Normal post-reset history follows native backfill. Shared-noise
identity still applies: one terminal sample is reused by all consumers requiring
it. This preserves information without an extra five-frame terminal stack.

Alternative B: omit terminal proprioceptive measurements entirely and have the
runner mask affected final WM transitions/reconstruction targets. Simpler output,
but discards potentially useful landing/failure transitions; timeout bootstrapping
with a WM-conditioned critic needs an explicit compatible convention. This is not
automatically wrong, but cannot be assumed equivalent to retaining terminal data.

Do not mistake prior history from the stock final_obs call for a terminal current
sample. Do not substitute next-episode initial data into the ended transition.
Neither alternative is approved by this research addendum.

### Paper timing reconciliation and user decision

Rechecked SWAP equations (7)–(9): posterior conditions on o_t and reconstruction
uses (o_t, H_wm_t) at the same indexed time. H_wm is an auxiliary target, not an
Encoder input. Source: https://arxiv.org/pdf/2606.19928, section III.B.
This does not mandate collecting the pre-reset terminal state as another WM input.
User's selected workflow excludes that extra WM sample, so no extra terminal
proprio sample/history is needed. Earlier recommendation A is superseded for this
project. Clean terminal AMP/critic data and explicit boundaries remain required.
Do not describe the chosen workflow as universally rendering terminal data useless.
No simulator experiment performed.

### Final terminal-export scope amendment

User subsequently removed clean terminal AMP/critic export too. Earlier research
recommendations to retain such snapshots are not the selected design. Consumers
use normal observations and episode boundaries; pairs requiring unexported
terminal states are not available, and reset states must not substitute for them.
This is a project data-scope choice, not evidence about all AMP or actor-critic
algorithms. Timeout bootstrap remains a separate compatibility question.

## Specify S14 follow-up — native sensor schedule and reset

Status: static evidence; no runtime check. User requested default behavior research
before choosing synchronization; S15/S16 data contracts are approved.

### Confirmed default scheduling

- InteractiveSceneCfg.lazy_sensor_update defaults True; InteractiveScene.update
  advances each sensor clock. Sensor data properties lazily refresh due results.
  Sources: ../IsaacLab/source/isaaclab/isaaclab/scene/interactive_scene_cfg.py:97;
  interactive_scene.py:459; sensors/sensor_base.py:214,471.
- Due clocks are per environment. Kernel advances simulation time; an uncaptured
  sensor or elapsed time >= update_period-1e-6 becomes outdated on positive dt.
  On capture, last-update time becomes current sensor time and elapsed resets.
  Source: sensors/kernels.py:10,36. Equal periods plus aligned initial captures
  and reads support normal-step alignment; there is no universal atomic bundle.
- Generic reset clears timing; importantly, Camera.reset and BaseRayCaster.reset
  additionally invalidate derived results. Their next data access can recompute
  without advancing physical time. Sources: sensors/camera/camera.py:649;
  sensors/ray_caster/base_ray_caster.py:108. Therefore generic SensorBase comments
  about cached cleared values must not be applied to camera/ray subclasses alone.
- Default Newton RayCaster is NewtonRaycastSensor, which inherits BaseRayCaster
  reset and reads live BVH data. Source: isaaclab_newton/sensors/ray_caster/
  __init__.pyi and newton_raycast_sensor.py:232,255,336. Existing global_world_only
  configuration restricts ray queries to global geometry rather than robot bodies.

### Configuration and backend caveats

CameraCfg.update_latest_camera_pose defaults False; Camera._prepare_camera refreshes
pose only when enabled, otherwise advances frame bookkeeping. Newton Warp consumes
CameraData poses in update_camera. A moving body-mounted camera requires explicit
pose refresh review; setting equal sensor periods alone is insufficient. Sources:
sensors/camera/camera_cfg.py:107; camera.py:745; isaaclab_newton/renderers/
newton_warp_renderer.py:548. Reset calls scene sensor reset before root-reset events,
so the pose read during sensor reset is not by itself evidence of post-event pose.
Source: envs/manager_based_rl_env.py:389–399.

Default APIs offer update(dt, force_recompute=True), but this refreshes outdated
rows; it does not force every non-due row into a fresh capture. Private invalidation
is a separate operation. Prefer native scheduling over duplicating a clock.

### Newton partial-reset rendering scope — source-derived risk

Camera preparation and SensorBase bookkeeping are per-row, but render_context's
render_into_camera call does not forward an environment mask to the renderer
(isaaclab/isaaclab/renderers/render_context.py:335–372). NewtonWarp tiled update
uses full camera transform/output arrays (isaaclab_newton/isaaclab_newton/renderers/
newton_warp_renderer.py:609–649) and aliases pixel outputs to camera buffers
(:666–671). Therefore a subset-triggered render can change non-due rows without
updating their sample bookkeeping. This is a static scope mismatch requiring a
bounded partial-reset test, not an executed runtime failure report.

Newton scene-data state retrieval invokes forward/FK without advancing physics
(isaaclab_newton/isaaclab_newton/physics/newton_scene_data.py:113–126). Camera sensor reads can render without
adding a simulation step. The existing step-reset rerender loop is RTX-specific,
not the NewtonWarp camera refresh mechanism.

Revised S14 proposal: use native update_period/lazy scheduling and subclass reset
invalidation; explicitly enable update_latest_camera_pose for the moving camera.
Expose immutable held target snapshots updated only for rows whose native capture
bookkeeping indicates a valid new sample, preventing renderer-wide writes from
changing other rows' exported samples. Use native sample timing/reset identity;
do not invent a second schedule. Confirm with two-environment partial reset and
capture-age checks later, before claiming correctness. No experiment run now.

Related S16 integration caveat: ray_alignment='yaw' uses the attached parent's
yaw; foot attachment alone does not implement approved base-yaw foot grids.
Need a narrowly scoped adapter or ray-origin/orientation composition in Specify,
not silent adoption of each foot's yaw. Source: ray_caster_cfg.py:49–59.

## Specify integration follow-up — proposed narrow extension seams

Static investigation only; no experiments, imports or production edits.

- TerrainGenerator samples actual d before `_get_terrain_mesh`, then calls
  `_add_sub_terrain` with row/column. Cached mesh loading skips cfg.function, so
  function side effects cannot supply dependable task metadata. Override these
  hooks narrowly and share a pure seed/config/difficulty layout builder. Sources:
  ../IsaacLab/source/isaaclab/isaaclab/terrains/terrain_generator.py:250,298,350.
- TerrainImporter holds generator only as a local during construction, but calls
  public import_mesh with its final mesh. An in-memory mesh.metadata table can be
  extracted by a small subclass while preserving native constructor/import flow.
  This is a project handoff proposal, not serialized OBJ metadata. Source:
  terrains/terrain_importer.py:89,229; terrain_generator_cfg.py:31.
- Immediate per-row camera copy belongs inside the capture hook, before another
  subset-triggered render can overwrite aliases. Camera's scalar-hook override
  disables native batching automatically. Sources: sensors/camera/camera.py:350,
  :753; isaaclab_newton/renderers/newton_warp_renderer.py:609.
- Newton ray scanner pose hook can compose reference-body translation with a
  separately registered base orientation before using the native yaw ray kernel;
  retains query/reset clocks. Sources: isaaclab_newton/sensors/ray_caster/
  newton_raycast_sensor.py:74,306; isaaclab/sensors/ray_caster/kernels.py:90.
- Term classes are constructed separately per configured term. One owner plus
  public term-config lookup avoids duplicate state machines. Native curriculum
  runs before reset events and manager clears, enabling pre-reset record consumption.
  Sources: isaaclab/managers/manager_base.py:411; termination_manager.py:228;
  envs/manager_based_rl_env.py:232,381.

Paths above are within /home/sevnce-mr/IsaacLab/source/<package>/ as appropriate;
all refer to the previously pinned commit. Proposed API names/contracts are in
interfaces.md; adoption requires S35 approval. Precise geometry and reward edge
policies remain separate choices.

## S36 follow-up: installed staircase holes semantics

Static source check: terrains/trimesh/mesh_terrains_cfg.py MeshPyramidStairsTerrainCfg
sets holes=False by default. mesh_terrains.py pyramid_stairs_terrain lines 49–141
builds four directional flights. With holes=True, directional tread spans use
platform_width and border meshes are omitted; other areas have no steps. With False,
tread spans shrink toward the center and optional border meshes are generated.
This is a topology change, not merely a generic numeric stair-width parameter.
The final center box dimensions are computed from residual terrain size/step count;
copying the function verbatim does not guarantee our exact approved top dimensions
and riser count. Proposed adaptation must preserve those independent contracts.
No runtime test performed.

## S43 follow-up: installed random_grid_terrain compatibility

Source inspection only, no simulation/import experiment: local
source/isaaclab/isaaclab/terrains/trimesh/mesh_terrains.py random_grid_terrain
(lines approximately 243–380), mesh_terrains_cfg.py MeshRandomGridTerrainCfg.

Confirmed compatible primitives: square constant-width cells, independent uniform
height perturbations with flat tops, difficulty-interpolated amplitude, adjacent
cells when holes=False, meshes/origin return convention.

Direct reuse fails approved contracts:
- amplitude h is interpolated from grid_height_range, then tops sample U[-h,h],
  not U[0,h]. Config range (0.02,0.20) controls amplitude, not sample endpoints.
- size=(2,2), grid_width=0.20 gives 10 cells per axis and zero border remainder;
  the implementation raises RuntimeError for border_width<=0 (strictly positive
  border required), despite its docstring mentioning only negative borders.
- center platform is added unconditionally, default width 1 m, top at h; no explicit
  disable flag. platform_width=0 would create degenerate geometry, not a supported
  disable API to adopt. Origin is center at h.
- using full task size=(10,10) would fill the tile, rather than confine roughness
  to the approved 2 x 2 m patch with separate approach/exit areas.
- implementation uses torch RNG and chooses CUDA whenever available; project
  integration must deliberately preserve accepted seed/cache determinism and
  resource constraints, not infer them merely from calling the function.

Recommendation S44: adapt the upstream construction pattern locally under approved
src/r3la/labs/terrains, permit exact tiling, sample positive heights, omit platform,
and compose task tile through shared layout. No upstream edits. User has approved
geometry (S43), not yet this concrete adaptation recommendation.

## S45/S46 source verification

terrain_importer_cfg.py defines max_init_terrain_level. terrain_importer.py
_compute_env_origins clamps it to num_rows-1 and samples torch.randint(0,
max_init_level+1), so value 5 with ten rows means indices 0..5 inclusive. The cap
applies only at initialization. terrain_generator.py _generate_curriculum_terrains
normalizes proportions and assigns columns using cumulative proportions and
index/num_cols+0.001. Ten columns realize approved proportions as 2,2,1,2,2,1.
Importer distributes environment types across columns separately, so exact column
ratios do not guarantee exact ratios for arbitrary num_envs. Static source review.

## Landing support attribution source follow-up

Newton ContactSensorData.contact_pos_w exposes aggregate per-body/per-filter
world contact positions, enabled by track_contact_points and nonempty filters.
Missing tracking/filter configuration yields None; sensor initialization warns
when tracking is requested without filters. Source: isaaclab_newton/sensors/
contact_sensor/contact_sensor_data.py:249 and contact_sensor.py:418. This is not
an individual contact mesh-face ID. S52 proposes target-surface geometric checks
on these aggregates with explicit integration tests; no runtime guarantee made.

## S60/S61 native staircase count and platform check

Re-read mesh_terrains.py pyramid_stairs_terrain lines 76–82 and 129–141. Count is
min of both dimension floor divisions by 2*step_width, then +1. Center mesh XY is
terrain_size-2*num_steps*step_width, not platform_width exactly. Highest ordinary
tread is num_steps*step_height; center platform is (num_steps+1)*step_height.
For size10,border0,platform_width1.5,step_width0.30, arithmetic gives count15,
center width1.0. These are illustrative inputs, not an approved border/default
obstacle footprint. No runtime experiment performed.
