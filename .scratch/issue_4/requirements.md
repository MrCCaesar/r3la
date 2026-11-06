# Issue #4 Requirements — Approved Explore

Stage approval: user “批准结束 Explore，进入 Research”. Later numbered resolutions
supersede earlier proposals; historical unapproved questions are retained below.

## Confirmed facts

Source: https://github.com/MrCCaesar/r3la/issues/4 (body and comments read).
User explicitly approved starting Explore with grill-with-docs.

- R1: Provide an IsaacLab 3.0 ManagerBasedRLEnv environment supporting SWAP reproduction.
- R2: Include parkour terrain and success-rate-based terrain and velocity-command curricula.
- R3: Match paper observations, rewards, events, terminations and parameters, subject to clarification of reproduction scope.
- R4: Noisy proprioceptive history, time-ordered; separate current velocity commands; current noiseless privileged observations for critic; depth images and terrain scans in target group.
- R5: Favor official APIs and examples; explicit approval for important architecture decisions; no production code during Explore.

## Assumptions — unapproved

- This issue delivers the environment and data needed by downstream training; world-model and runner implementation boundaries need confirmation.
- Paper-specific robot and experimental results may differ from the intended project target.

## Open questions — first frontier

- Q1: Which robot is the physical target, and how should deviations from the paper's Apollo platform be treated?
- Q2: Is the deliverable environment/data support only, or also world-model, runner and training implementation?
- Q3: What evidence constitutes acceptance: environment correctness and data contracts, or trained policy performance too?

## Deferred requirement branches

After target and scope settle: terrain coverage, success/failure definitions and edge cases, observation semantics, sensor realism, randomization and evaluation boundaries.

## Deferred technical decisions

Algorithms, module/API designs, tensor shapes, defaults and file layout belong to later approved stages.

## Evidence

- Paper: https://arxiv.org/pdf/2606.19928 — identifies Apollo as the experimental robot.
- Repository fact gathering in progress; existing code does not constitute approved requirements.

## Recommendations — unapproved

Resolve physical target, deliverable boundary and acceptance scope before detailed parameter reconciliation.

## Round 1 resolutions — Approved

Approval reference: user reply “1. yes 2. yes 3. yes”.
These decisions supersede the assumptions and open questions Q1–Q3 above.

- R6 / Q1: Unitree Go2 is the physical target. Reproduce SWAP task and observation semantics on Go2. Robot physical parameters must describe Go2; adaptations to paper task parameters require individual confirmation.
- R7 / Q2: Deliver environment and data outputs. World-model networks, training runner and training algorithms are outside this issue's implementation scope.
- R8 / Q3: Acceptance covers behavior, observation semantics and curriculum rules against approved requirements, with bounded-resource runtime verification. Convergence and paper performance records require separate experimental acceptance.

## Static repository evidence

- Existing task: R3la-SWAP-Parkour-UnitreeGo2 using ManagerBasedRLEnv.
- Existing terrain primitives: rails, gaps, pits, boxes, flat, random rough.
- Existing curriculum: terrain_levels_vel; custom curriculums.py is empty and success-rate curriculum is a TODO.
- Existing termination configuration: timeout and illegal base contact.
- These are observations of current code, not newly approved requirements.

## Round 2 questions — Proposed

- Q4: Cover box climbing, gap leaping, stairs, lateral slopes and irregular rock terrain, including unilateral tilted box/stair/gap and mirrored evaluation terrain? Exact Go2 dimensions remain deferred.
- Q5: Success means completing the designated terrain route without failure, including landing and ability to continue; crossing a boundary while falling is not success? Detailed observable criteria remain deferred.
- Q6: Terrain and command curricula share traversal success as the outcome; velocity tracking reward alone does not count as success? Adaptation algorithms remain deferred.

Evidence: SWAP sections IV.B and Fig. 3 describe terrain families and mirrored evaluation; paper defines success broadly as traversing target terrain. Landing/stability interpretation above is a project proposal, not an attributed paper definition.

## Round 2 resolutions — Approved

Approval reference: user reply “4. yes 5. yes, 但是如何定义成功，需要平衡成功的评判和代码实现难度；6. 地形课程以成功作为依据，速度课程以速度跟踪效果作为依据”.

- R9 / Q4: Include box climbing, gap leaping, stairs, lateral slopes and irregular rock terrain, plus unilateral tilted box/stair/gap and mirrored evaluation scenes. Dimensions and difficulty ranges remain open.
- R10 / Q5: Success represents completing the designated terrain route without failure, including necessary landing and continued locomotion capability. The operational definition must balance physical validity and implementation complexity; no detector, stability threshold or observation duration is approved.
- R11 / Q6: Terrain curriculum is based on traversal success. Velocity-command curriculum is based on velocity tracking performance. This explicitly replaces the proposed shared-success basis in Q6.

## Round 3 questions — Proposed

- Q7: Is the success assessment unit one complete assigned terrain route, potentially containing multiple obstacles, rather than independent success for each obstacle?
- Q8: Does timeout before successful completion count as an unsuccessful terrain attempt, while timeout alone is not a physical fall?
- Q9: Should non-foot contacts be distinguished by physical consequence, allowing useful brief leg/body contact during climbing while treating falls or inability to continue as failure? Exact allowed contacts require subsequent clarification.

## Deferred success-design trade-off

Compare simple traversal/landing criteria with richer stability criteria during Research, then approve a measurable definition during Specify. Preserve the requirement against counting an immediate post-crossing fall as success; report any proposed approximation and its limitations before approval.

## Round 3 resolutions — Approved

Approval reference: user reply to Q7–Q9.

- R12 / Q7: Each sub-terrain contains exactly one obstacle. An environment assigned to that sub-terrain succeeds by passing that obstacle. This replaces the proposed multi-obstacle route unit in Q7 and narrows references to a designated route in R10.
- R13 / Q8: Timeout does not count as success.
- R14 / Q9: Base collision is the only illegal-contact category. Other leg-link contacts incur the paper's contact penalties rather than directly causing reset. This specifies contact-triggered failure, not removal of timeout or any subsequently approved non-contact termination conditions.

## Round 4 questions — Proposed

- Q10: For stairs, lateral slopes and rock piles, does one obstacle mean one contiguous terrain feature (e.g. a staircase or a rock patch), rather than one step or one rock?
- Q11: Does passing retain R10's landing/continued-motion intent, so crossing the obstacle boundary while airborne is insufficient and an immediate failed landing is not success? Detector complexity, thresholds and timing remain deferred.
- Q12: Is the locomotion command scope forward speed only, with lateral/yaw command targets zero, rather than independently commanded lateral motion and turning? This is current-code behavior, not yet an approved requirement.

## Round 4 resolutions — Approved

Approval reference: user reply “10. 是的，一个障碍即为isaaclab3.0地形生成器中的一个sub terrain，每个sub terrain 是阶梯，箱子，gap等障碍中的一种 11. yes 12. yes”.

- R15 / Q10: The task obstacle unit is one IsaacLab 3.0 terrain-generator sub-terrain, containing one obstacle type such as stairs, box or gap. A staircase may contain multiple steps; one obstacle does not imply one isolated geometric primitive. This clarifies R12.
- R16 / Q11: Passing retains the necessary landing requirement. Crossing the far boundary while airborne and then falling on landing is not success. Operational criteria remain deferred, subject to R10's complexity constraint.
- R17 / Q12: Commands target forward speed only; lateral velocity and yaw angular velocity targets are zero. Necessary motion/path adjustments to pass an obstacle remain allowed; independent lateral/turning command tasks are outside scope.

## Round 5 questions — Proposed

- Q13: Once success is confirmed (including necessary landing), should the episode end and the environment reset for the next attempt?
- Q14: Should leaving the assigned sub-terrain sideways or bypassing the intended obstacle be unsuccessful, preventing adjacent terrain from providing a shortcut? Exact boundaries/detection remain deferred.
- Q15: Should velocity-curriculum tracking performance tolerate temporary acceleration/deceleration needed for takeoff, climbing and landing, evaluating overall attempt performance rather than requiring instantaneous tracking throughout? No metric, window or threshold is selected here.

## Round 5 resolutions — Approved

Approval reference: user reply “13. 是 14. 是 15. 是”.

- R18 / Q13: Confirmed successful completion ends the episode and resets the environment for the next attempt. Necessary landing is part of completion.
- R19 / Q14: Sideways departure from the assigned sub-terrain or bypass via adjacent terrain is unsuccessful; reaching the far side by a shortcut is not valid completion.
- R20 / Q15: Velocity curriculum evaluates overall tracking performance over an attempt and permits transient acceleration/deceleration needed for takeoff, climbing and landing. No instantaneous all-step tracking requirement; metric and thresholds remain deferred.

## Round 6 questions — Proposed

Paper evidence: https://arxiv.org/pdf/2606.19928, Table II and section III.D.1.
- Q16: Include environment-side data needed for AMP, while leaving discriminator, motion dataset and learned reward computation to the training task? Paper explicitly includes AMP beyond Table III rewards; do not claim complete reward reproduction from Table III alone.
- Q17: Follow Table II's separate consumer semantics: actor history includes previous actions; world-model proprioceptive encoder input contains angular velocity, gravity, command, joint position/velocity, excluding previous action. The issue's instruction to concatenate current proprioception with commands needs this selection clarified. Selection implementation belongs to runner; environment must supply the necessary distinguishable quantities.

## Round 6 resolutions — Approved

Approval reference: user approved Q16 and clarified Q17's shared noisy-data requirement.

- R21 / Q16: Include environment-side state data needed for AMP. Discriminator, reference-motion dataset and learned reward computation remain training-task responsibilities. Table III alone is not complete reproduction of paper rewards.
- R22 / Q17: For quantities requiring observation noise, the environment supplies one shared noisy sample per physical quantity per observation instant. Consumers that use the same quantity at that instant must receive exactly the same sampled value. Runner/model selects and combines these data for different modules; consumer-specific independently corrupted observation groups must not yield divergent measurements of the same instant.
- R22 clarifies R4 and R7: environment supplies noisy proprioceptive history as requested in the issue; runner/model selects current samples and assembles module inputs. No new requirement to move history storage out of the environment is inferred.
- Table II's actor-versus-encoder content difference remains the reference for downstream selection; it does not imply separately sampling noisy groups.

## Round 7 questions — Proposed

- Q18: Should the proprioceptive Decoder reconstruction target reuse the same noisy measurements as its corresponding Encoder input, rather than introduce an additional clean target stream?
- Q19: Should depth-image Encoder input and image reconstruction target share the same image, with no extra depth noise/dropout sensor model in this task unless subsequently supported by evidence and approved? Required geometric processing and invalid measurements still need later specification.

## Deferred verification

Inspect installed IsaacLab observation/noise/history behavior during Research to find a feasible way to preserve R22. User's statement about independent group noise is the motivation; no API-level experiment has been performed in Explore.

## Round 7 resolutions — Approved

Approval reference: user reply “18. yes 19. yes，但是将深度图添加噪声添加为todo”.

- R23 / Q18: Proprioceptive Decoder targets reuse the corresponding noisy measurements consumed by the Encoder. No additional clean proprioceptive reconstruction-target stream is required.
- R24 / Q19: Depth Encoder input and image Decoder reconstruction target share the same image. Initial scope excludes an additional depth-noise/dropout model; geometric semantics, necessary preprocessing and invalid-value handling remain to be specified.
- TODO-01: Add depth-image noise in subsequent work. This TODO is explicitly requested but does not authorize implementing a noise model now. Before implementation, clarify the corruption model and whether input/target share the same corrupted image; retain R24 until an approved change supersedes it.

## Explore review — Proposed complete

The user has individually approved R6–R24, in addition to the issue requirements R1–R5 as clarified by those decisions. Explore as a whole and transition to Research still require explicit approval.

### Confirmed delivery boundary

Go2 parkour environment on IsaacLab 3.0, environment observations and AMP-supporting data, conventional paper reward terms, resets/termination, terrain and velocity curricula, and mirrored evaluation terrain support. World-model/AMP networks, training runner, reference motion dataset, convergence and performance-record reproduction are outside this issue's implementation/acceptance scope.

### Confirmed task behavior

One obstacle type per sub-terrain; stairs may contain multiple steps. Valid traversal includes necessary landing. Confirmed success ends the episode; timeout and bypass are unsuccessful. Base collision is the only illegal contact; leg-link collisions are penalized instead of directly resetting. Terrain curriculum uses success; velocity curriculum uses overall velocity tracking with dynamic-maneuver transients allowed. Commands target forward velocity with zero lateral/yaw targets.

### Confirmed data behavior

Noisy proprioception is sampled once and shared across consumers, with history available. Runner/model composes module inputs. Proprioceptive reconstruction uses the same noisy measurement. Privileged critic observations are current and noiseless. Depth input/reconstruction use one shared image; terrain scans are reconstruction targets. AMP environment data are included; details require source investigation.

### Research questions and deferred decisions

- Reconcile paper, available author materials and installed IsaacLab source; distinguish reported values from missing information and Go2-specific adaptations.
- Verify terrain primitives can express approved types, single sub-terrain traversal and mirrored evaluation without unapproved geometry simplifications.
- Compare physically meaningful, low-complexity success/landing and bypass criteria; no threshold or detector approved yet.
- Investigate success-based terrain and tracking-based velocity curriculum alternatives; no update formula or threshold approved yet.
- Verify shared observation noise, history/reset behavior and sensor timing against installed APIs; no interfaces or data shapes approved yet.
- Reconcile reward, contact-link, randomization/event and AMP state requirements with authoritative evidence. Missing values require proposals, not silent defaults.
- Assess supported physics/sensor combinations and bounded verification feasibility; existing backend configuration is not evidence that all backends work.

### Verification performed and limitations

Read-only repository inspection, GitHub issue retrieval, paper and official documentation reading. No simulation, training, numerical tests or API experiments were run. Existing code is evidence of current behavior, not an approved design. No significant architecture or physics-model choice has been accepted; no ADR is marked Accepted.

## Specify clarification: terminal export scope — Approved amendment

User explicitly removed terminal clean AMP/critic retention after removing
terminal noisy proprioceptive retention. R21's normal AMP data support remains;
it does not require terminal snapshots. Environment exports ordinary observations
and boundary information; runner/model handles episode boundaries and avoids
cross-reset training pairs. This supersedes Specify S10's earlier terminal-state
requirements, not the approved curriculum's pre-reset outcome processing.

## Specify scope amendment — tilted terrain families

User explicitly limited tilted/mirrored variants to slopes and stairs in S30.
This supersedes R9's prior tilted box/stair/gap list. Ordinary box/gap/rock terrain
remains; no added tilted box/gap/rock variants. Side slopes use their native
transverse angle, not an additional tilt applied on top. S29 changed top platforms
to 1.5x1.5 m with 0.15 m inward completion margin.


## User geometry correction — 2026-11-06

User authorized equal Y widths for holes=True stair treads/platforms and an
unblended transverse planar ramp (ordinary ramp rotated 90°). ADR-008 supersedes
the earlier conflicting width/transition details. Implemented layout/mesh,
regions, cache revision, regression tests and native probe expectations; see
verification.md for executed checks. Other geometry parameters remain unchanged.
