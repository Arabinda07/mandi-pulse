---
name: speckit
description: Spec-Driven Development (SDD) workflow for Mandi Pulse. Use when creating, clarifying, planning, or auditing specs in .specify/.
---

# Mandi Pulse Spec Kit (`speckit`)

Use this skill when defining or auditing features using the **Spec-Driven Development (SDD)** lifecycle in [`.specify/`](file:///e:/food%20price%20monitor/.specify/).

---

## SDD Lifecycle Router

| Phase | Action | Reference & Artifacts |
| :--- | :--- | :--- |
| **1. Constitution** | Verify architectural and mathematical invariants | Read [`.specify/constitution.md`](file:///e:/food%20price%20monitor/.specify/constitution.md) |
| **2. Specify** | Define domain problem and user stories | Copy [`.specify/templates/spec-template.md`](file:///e:/food%20price%20monitor/.specify/templates/spec-template.md) to `.specify/specs/<feature>/spec.md` |
| **3. Clarify** | Probe edge cases (mandi holidays, arrival shocks) | Append to `Clarification Log` in `spec.md` |
| **4. Plan** | Technical design and schema changes | Copy [`.specify/templates/plan-template.md`](file:///e:/food%20price%20monitor/.specify/templates/plan-template.md) to `.specify/specs/<feature>/plan.md` |
| **5. Tasks** | Granular execution checklist with test targets | Copy [`.specify/templates/tasks-template.md`](file:///e:/food%20price%20monitor/.specify/templates/tasks-template.md) to `.specify/specs/<feature>/tasks.md` |
| **6. Analyze** | Traceability and pre-merge audit | Copy [`.specify/templates/checklist-template.md`](file:///e:/food%20price%20monitor/.specify/templates/checklist-template.md) to `.specify/specs/<feature>/checklist.md` |

---

## Core Guidelines

- **Focus on Outcomes First**: In `spec.md`, describe domain behavior and acceptance criteria; do not include SQL queries or Python implementation details.
- **Constitutional Alignment**: Ensure all new tables and modules adhere to SQLite WAL mode, canonical nomenclature (*Mandi*, *Arrival*, *Modal Price*), and deep module boundaries.
- **Traceability**: Before completing work, run `python scripts/spec_audit.py` to confirm that all requirements in `spec.md` map to concrete tasks and tests.
