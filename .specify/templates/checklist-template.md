# Quality & Traceability Checklist (`/speckit.analyze`)

> **Spec:** `[SPEC-XXX]`  
> **Auditor:** [Agent / Reviewer]  
> **Date:** [YYYY-MM-DD]  

---

## 1. Requirement Traceability Matrix

| Spec Requirement | Plan Section | Task ID | Test / Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| *Req 1: ...* | *Plan Sec 2.1* | `TASK-01` | *`pytest tests/...`* | `[Verified]` |
| *Req 2: ...* | *Plan Sec 2.2* | `TASK-03` | *Visual check / Test* | `[Verified]` |

---

## 2. Constitutional Invariant Audit

- [ ] **WAL Mode**: Is `agri_engine.db` verified to run in WAL mode with zero reader locks?
- [ ] **LGD Directory Codes**: Are all new mandis linked to official LGD codes?
- [ ] **Data Provenance**: Are synthetic fields explicitly tagged with `is_synthetic=1` or clearly noted?
- [ ] **Nomenclature Check**: Are any forbidden aliases (*market*, *supply*, *markup*, *average price*) present in code, schemas, or docs?
- [ ] **Design System Check**: Are colors, fonts, and responsive modes compliant with `DESIGN.md`?

---

## 3. Readiness Verdict
- [ ] **Ready to Merge**: All tasks completed, all tests passing, zero unapproved architectural drifts.
