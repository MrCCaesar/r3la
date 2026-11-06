# Agent Instructions


## 1. Issue-Driven Workflow

- Every task starts from a GitHub Issue `#N`. Read its title, body, and comments with `gh issue view N --json title,body,comments,url`.
- Use the Issue as the initial requirements source, not as permission to implement.
- Keep all issue-specific working documents in `.scratch/issue_N/` (retain this path consistently).
- Before acting, read existing issue documents and `status.md`; resume the approved stage rather than restarting or skipping stages.
- User-approved decisions and specifications take precedence over earlier Issue text. If sources conflict, ask for clarification.

## 2. Stages and Decision Granularity

Follow **Explore → Research → Specify → Plan → Implement → Verify** in order.

| Stage | Decisions allowed | Defer / do not decide | Deliverable |
| --- | --- | --- | --- |
| **Explore** | **WHAT / WHY:** goals, functional scope, physical requirements, constraints, evaluation boundaries, acceptance intent | Algorithms, implementation methods, class/API design, parameter defaults, file layout | `requirements.md` |
| **Research** | **WHICH approaches are feasible:** investigate versions/APIs, compare alternatives, risks, evidence, minimal experiments (with approval) | Final interfaces, production architecture, unrelated feature expansion | `research.md`; proposed ADRs when relevant |
| **Specify** | **HOW the approved requirements will work:** select approved approach, architecture, module responsibilities, data contracts, configurations, measurable acceptance criteria | Production implementation, unapproved scope changes | `spec.md`, `interfaces.md`, accepted ADRs |
| **Plan** | **IN WHAT ORDER:** split approved design into bounded tasks, dependencies, test/documentation obligations | Redesign, speculative features, implementation outside the plan | `plan.md` |
| **Implement** | **EXECUTE:** implement only approved tasks and interfaces, add/update tests and documentation | Silently changing requirements, physics assumptions, interfaces, or architecture | Code, tests, synchronized documentation |
| **Verify** | **PROVE:** run tests, check acceptance criteria, report failures and deviations | Claiming unrun tests passed; redefining acceptance criteria to pass | `verification.md` |

- During **Explore**, ask requirement-level questions rather than embedding proposed solutions (e.g., ask whether post-excitation motion must be evaluated, not whether to hold the final trajectory frame for a chosen duration).
- Record premature technical questions as *deferred decisions* in the relevant document; revisit them at the appropriate stage.
- Discuss technical details early only when essential to clarify a requirement or establish feasibility; mark them as **unverified**, not approved design.
- At every stage, separate **confirmed facts**, **assumptions**, **open questions**, and **recommendations**. Ask a few high-impact, related questions at a time.
- Never advance to the next stage without explicit user approval. Approval of a stage does not implicitly approve every proposal within it.

## 3. Documentation and Decision Records

Maintain the following structure as applicable:


- Create documents when their stages begin; update them as decisions evolve. Mark each document or section **Draft**, **Proposed**, **Approved**, or **Superseded** where applicable.
- Record every significant architecture, physics-model, or technology decision in a separate ADR under `adr/`. Each ADR must include: context/problem, alternatives, decision and rationale, consequences/trade-offs, evidence, status, and approval reference. Do not mark an ADR **Accepted** without explicit user approval.
- In `interfaces.md`, define each public class/function/config/data contract with purpose, inputs/outputs, types/shapes, units, coordinate frames, defaults, constraints, error behavior, and compatibility expectations when applicable. Distinguish existing library APIs from project-proposed APIs.
- Trace requirements to design decisions, interfaces, implementation tasks, and tests using stable IDs where helpful.
- Approved contracts are authoritative for implementation. If changes are necessary, propose them and list their impact on dependent files; obtain approval before changing approved behavior.
- Keep documentation consistent with actual code and tests. Do not erase decision history; supersede old ADRs instead.

## 4. Engineering Rules

- Follow repository conventions and verify third-party APIs against the installed version or authoritative documentation.
- Keep changes within the approved task; avoid unrelated refactors or speculative features.
- Add relevant tests and record exact commands and outcomes. Never claim a test passed unless executed.
- Do not automatically commit, push, edit GitHub Issues, or post comments unless explicitly requested.

## 5. Communication and Handoffs

At the end of each stage or task, report:

1. Findings and work completed, with affected files.
2. Open questions, deferred decisions, and approval requests.
3. Tests performed (or not performed) and remaining risks.
4. Suggested next step **without executing it** until approved.

Keep `status.md` up to date so another agent session can resume from the approved state.

## 6. Isaac Lab Resource Safety

- **MUST** minimize resource usage during Isaac Lab simulations and tests to prevent OOM, system freezes, or crashes.
- Default to `--num_envs 2`, headless mode, and short, bounded runs.
- Check available RAM/VRAM before execution; increase workloads only when necessary and safe.
- Never run full-scale training or multiple simulations for routine verification.
- Stop immediately if resource exhaustion or system instability is detected.

## Agent skills

### Issue tracker

GitHub Issues；执行技能的 issue 操作前读取 `docs/agents/issue-tracker.md`。

### Triage labels

使用默认五类分诊标签；分诊前读取 `docs/agents/triage-labels.md`。

### Domain docs

采用 single-context 布局；探索领域代码前读取 `docs/agents/domain.md`。
