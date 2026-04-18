# AI SI Project Team

Claude Code multi-subagent system that replicates an enterprise SI
(System Integration) project execution organization.

- Spec: `docs/superpowers/specs/2026-04-17-ai-si-team-design.md`
- Plan: `docs/superpowers/plans/2026-04-17-ai-si-team-build.md`

## Quick Start (once the system is in place)

1. As the client (user), drop a statement-of-work into
   `projects/<name>/00_kickoff/statement-of-work.md`.
2. Talk to the **project-manager** agent. PM is the single contact
   point; it orchestrates everything else.
3. At each stage gate, PM reports to you and waits for your approval.
4. When PM signals an audit is due, start a session with the
   **audit-team** agent (external auditor, isolated in `audit/`).

## Bootstrapping a new project

Before talking to `project-manager`, scaffold the project directory:

```bash
python3 scripts/bootstrap_project.py <project-name> --scale small|large
```

This creates `projects/<project-name>/` with the full stage directory tree,
seeds `00_kickoff/statement-of-work.md` from a template, and initializes
`project-state.md`, `RTM.md`, and supporting log files.

Next, fill in `00_kickoff/statement-of-work.md` with your actual SOW,
then invoke the `project-manager` agent.

## Agent Catalog

### Fixed-model agents (7)
- `project-manager` — Opus, xhigh, the user-facing orchestrator.
- `application-director` — Opus, xhigh, application track leader.
- `infrastructure-director` — Opus, xhigh, infrastructure track leader.
- `business-manager` — Sonnet, xhigh, schedule/cost/CR impact.
- `quality-assurance` — Sonnet, xhigh, quality criteria and QA report.
- `tester` — Sonnet, xhigh, UAT/IT/UT design & execution.
- `audit/audit-team` — Sonnet, xhigh, external auditor (independent).

### Dynamic-model agents (13 × 3 = 39)
Each role has `-opus`, `-sonnet`, `-haiku` variants. The upstream caller
picks the variant based on the task's difficulty (spec §2-3).

- `application-architect` (AA)
- `software-architect` (SWA)
- `technical-architect` (TA)
- `data-modeler`
- `part-leader` (activated in large-scale projects; has Agent tool)
- `backend-developer`, `batch-developer`, `web-developer`,
  `web-publisher`, `designer`
- `database-administrator` (DBA)
- `security-specialist`
- `infrastructure-engineer`

## Artifact Templates

See `.claude/agents/templates/artifacts/`. Every stage's expected
deliverables have a template with the required frontmatter and body
skeleton.

## Stage Gates

`.claude/agents/templates/stage-gates.md` lists the mandatory artifacts,
reviews, audits, and approvals required to close each stage.

## Validation Scripts

```bash
# Validate a single agent file
python3 scripts/validate_agent.py .claude/agents/project-manager.md

# Validate every agent file
python3 scripts/validate_agent.py $(ls .claude/agents/*.md)

# Re-derive the 39 dynamic variants from templates
python3 scripts/derive_dynamic_agents.py

# Run tests
python3 -m pytest tests/ -v
```

## Unresolved items (see spec §10)

- Sample project domain (for future meta-test E2E).
- Parallel-write file locking strategy (currently convention-only).
- Part-leader count in large mode (one vs. per-domain).
- Audit session kickoff UX (slash command vs. natural language).
