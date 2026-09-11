## 📋 Spec Reference

- **Spec ID / Link**: Closes `.specify/specs/[SPEC_DIR]/spec.md`
- **Task IDs**: `TASK-[XX]`, `TASK-[YY]` from `tasks.md`

---

## 🎯 Description of Changes

<!-- Provide a concise summary of what was added, modified, or fixed in this pull request. -->

---

## 🏛️ Constitutional Compliance Checklist

Before requesting review or merging, you must verify adherence to [`.specify/constitution.md`](.specify/constitution.md):

- [ ] **Article I (Empirical & Math Standards)**:
  - Quantitative metrics (ASA, SPD, Corridor Friction) remain deterministic and pure in `src/volatility.py`.
- [ ] **Article II (Ubiquitous Language)**:
  - Strict terminology is used. No forbidden aliases (*market*, *supply*, *average price*, *markup*, *pincode*).
- [ ] **Article III (Architectural Invariants & Deep Modules)**:
  - SQLite WAL mode is preserved (`PRAGMA journal_mode=WAL;`).
  - Read queries remain non-blocking for Datasette and Marimo.
  - Spatial entities are resolved via `MandiRegistry` with verified LGD codes.
  - Ingestion changes implement the `CommoditySource` port seam.
- [ ] **Article IV (Data Reality & Ground Truth)**:
  - Zero unflagged mocks. Any synthetic calculation or heuristic multiplier is explicitly tagged as `synthetic`.
- [ ] **Article V (Consumer Design & UX)**:
  - If frontend changes are included: respects the Dual-Mode UI (Household ₹/kg vs Bulk ₹/qtl), anti-slop color tokens, and Cabinet Grotesk + Geist typography.
- [ ] **Article VI (AI Agent Governance & SDD Workflow)**:
  - Changes trace directly to an approved Spec, Plan, and Task in `.specify/specs/`.

---

## 🧪 Verification & Testing

<!-- What commands were run to verify these changes? -->

```powershell
pytest
```

- [ ] All tests passing with zero regressions
- [ ] Datasette / Marimo queries tested locally (if applicable)
