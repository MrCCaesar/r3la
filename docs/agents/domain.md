# Domain docs

## Layout and reading rules

This repository uses a single-context layout.

Before exploring domain code, read root GLOSSARY.md if present,
then relevant decisions in docs/adr/ and the current issue's
.scratch/issue_N/adr/ directory.

If a domain document is absent, continue exploration.
Create domain documents when terms or decisions are resolved,
following AGENTS.md approval requirements.

## Vocabulary

Use terms defined in GLOSSARY.md.
Identify unresolved terminology for later domain modeling.

## Decision records

Keep issue-specific ADRs in .scratch/issue_N/adr/, as required
by AGENTS.md. Read docs/adr/ for repository-wide decisions if present.
Moving or promoting an ADR requires an explicit approved decision;
preserve its approval reference and history.

Surface conflicts with existing ADRs before proposing a change.
Mark an ADR Accepted only after explicit user approval.
