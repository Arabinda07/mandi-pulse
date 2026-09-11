---
name: speckit
description: Spec-Driven Development (SDD) workflow for Mandi Pulse based on GitHub Spec Kit. Use when specifying, planning, auditing, or executing features against the project constitution and architectural invariants.
---

# Mandi Pulse Spec Kit Skill (`speckit`)

Use this skill to guide and enforce **Spec-Driven Development (SDD)** across the `mandi-pulse` repository. 

Whenever you are tasked with creating a feature, modifying schemas, adding commodity feeds, or building consumer interfaces, follow this contract-first methodology before writing code.

---

## The Spec Kit Lifecycle

```
1. CONSTITUTION    ──> Read `.specify/constitution.md` for non-negotiable invariants
2. SPECIFY         ──> Define "What" & "Why" in `.specify/specs/<name>/spec.md`
3. CLARIFY         ──> Resolve edge cases and log decisions in `Clarification Log`
4. PLAN            ──> Design "How" in `.specify/specs/<name>/plan.md`
5. TASKS           ──> Generate granular checklist in `.specify/specs/<name>/tasks.md`
6. IMPLEMENT       ──> Write code, run tests, verify against tasks
7. ANALYZE         ──> Audit traceability and constitutional compliance
```

---

## Command Workflows

### 1. `/speckit.constitution`
**Purpose**: Audit an incoming request or existing code against the project constitution.
- Open and read [`.specify/constitution.md`](file:///e:/food%20price%20monitor/.specify/constitution.md).
- Verify the 5 core checks:
  1. **SQLite WAL Mode**: Is the database operating with `PRAGMA journal_mode=WAL;`?
  2. **Ubiquitous Language**: Are terms like *Mandi*, *Arrival*, *Modal Price*, *LGD Code*, and *Retail Spread* used correctly? (No "market", "volume", "average price").
  3. **Deep Module Seam**: Are changes behind `Warehouse`, `MandiRegistry`, `VolatilityEngine`, or `CommoditySource`?
  4. **Data Reality**: Are synthetic proxies (retail markup, Haversine freight) explicitly tagged?
  5. **UI Standard**: Does the design follow the dual-mode architecture (Household vs Bulk) and anti-slop tokens?

### 2. `/speckit.specify <feature-name>`
**Purpose**: Draft a new feature specification.
- Create a directory: `.specify/specs/<feature-name>/`.
- Copy `.specify/templates/spec-template.md` to `.specify/specs/<feature-name>/spec.md`.
- Fill out the Problem Statement, User Stories with Acceptance Criteria, Domain Metrics, and Explicit Boundaries.
- **Rule**: Never include SQL queries, Python classes, or UI implementation specifics in `spec.md`. Focus 100% on domain behavior and user outcomes.

### 3. `/speckit.clarify <feature-name>`
**Purpose**: Probe the specification for edge cases and unstated assumptions.
- Check:
  - What happens during APMC mandi trading holidays or weekend closures?
  - What happens if an arrival drops by 80% due to rain vs a true supply shock?
  - How are new or unmapped APMC strings handled?
- Document the resolutions in the `Clarification Log` section of `spec.md`.

### 4. `/speckit.plan <feature-name>`
**Purpose**: Generate the technical implementation plan.
- Copy `.specify/templates/plan-template.md` to `.specify/specs/<feature-name>/plan.md`.
- Detail the SQLite schema changes, deep module interface updates, Datasette query definitions, and performance constraints.
- Perform the Constitutional Verification checklist at the top of `plan.md`.

### 5. `/speckit.tasks <feature-name>`
**Purpose**: Break the plan into sequential, atomic execution tasks.
- Copy `.specify/templates/tasks-template.md` to `.specify/specs/<feature-name>/tasks.md`.
- Structure tasks into chronological phases: Preparation $\rightarrow$ Domain Engine $\rightarrow$ Presentation $\rightarrow$ Validation.
- Ensure every task has a verifiable test command (e.g. `pytest tests/...`).

### 6. `/speckit.analyze <feature-name>`
**Purpose**: Pre-merge traceability and quality audit.
- Copy `.specify/templates/checklist-template.md` to `.specify/specs/<feature-name>/checklist.md`.
- Map each requirement from `spec.md` to its corresponding task in `tasks.md` and test in `tests/`.
- Ensure zero orphaned requirements and zero unapproved architectural drifts.
