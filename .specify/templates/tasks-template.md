# Execution Tasks: [Feature Name]

> **Spec Reference:** `[Link to spec.md]`  
> **Plan Reference:** `[Link to plan.md]`  
> **Status:** `Pending` | `In Progress` | `Completed`  

---

## Task Execution Guidelines
1. Execute tasks in sequential order unless explicitly marked as parallelizable.
2. Check off each task immediately after automated test verification passes.
3. If an unforeseen architectural blocker arises, pause execution and update `plan.md`.

---

## Phase 1: Preparation & Foundation

- [ ] `TASK-01`: **Data/Schema Setup**
  - **Action**: Create or migrate SQLite tables/indices.
  - **Verification**: `python -c "import sqlite3; ..."`
  - **Spec Link**: Section 3

- [ ] `TASK-02`: **Registry / Entity Resolution Seed**
  - **Action**: Register any new canonical mandis with LGD codes and coordinates.
  - **Verification**: `pytest tests/test_registry.py`
  - **Spec Link**: Section 3

---

## Phase 2: Core Domain & Engine Logic

- [ ] `TASK-03`: **Implement Mathematical / Volatility Logic**
  - **Action**: Add pure analytical formulas to `src/volatility.py`.
  - **Verification**: `pytest tests/test_volatility.py`
  - **Spec Link**: Section 2 (Acceptance Criteria)

- [ ] `TASK-04`: **Ingestion / Adapter Update**
  - **Action**: Implement or update `CommoditySource` adapter.
  - **Verification**: `pytest tests/test_ingest.py`
  - **Spec Link**: Section 2

---

## Phase 3: Integration & Presentation

- [ ] `TASK-05`: **Datasette / Canned Query Configuration**
  - **Action**: Update `datasette/metadata.json` with new queries.
  - **Verification**: Validate JSON syntax and test Datasette query response.
  - **Spec Link**: Section 2

- [ ] `TASK-06`: **Frontend / Marimo Integration**
  - **Action**: Connect UI/Notebook to new queries.
  - **Verification**: Verify visual rendering and toggle interactions.
  - **Spec Link**: Section 2 (User Stories 1 & 2)

---

## Phase 4: Final Validation & Constitutional Audit

- [ ] `TASK-07`: **Run Full Test Suite & Linting**
  - **Action**: Execute `pytest -v`.
  - **Verification**: Zero test failures.

- [ ] `TASK-08`: **Constitutional Sign-off**
  - **Action**: Audit committed files against `.specify/constitution.md`.
  - **Verification**: Pass `/speckit.analyze`.
