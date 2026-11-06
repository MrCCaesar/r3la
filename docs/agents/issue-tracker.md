# Issue tracker: GitHub

Issues and specifications live in MrCCaesar/r3la on GitHub.
Use the gh CLI from this repository.

## Read operations

- Read: gh issue view N --json title,body,comments,url
- List: gh issue list
- Verify target repository: gh repo view --json nameWithOwner

## Write operations

Follow AGENTS.md authorization requirements before creating,
editing, commenting on, labeling, or closing issues.
A skill's suggested write operation does not override those requirements.

For multiline issue or comment bodies, write the text to a temporary
file and pass --body-file.

## Working documents

Keep issue-specific documents in .scratch/issue_N/.
Read existing documents and status.md before resuming work.
These files support GitHub Issues; they are not a separate issue tracker.

## Pull requests as a triage surface

PRs as a request surface: no.
