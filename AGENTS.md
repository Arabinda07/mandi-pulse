# Mandi Pulse — Agent Guidelines

Mandi Pulse is a quantitative analytical engine tracking high-frequency wholesale mandi arrivals and prices across India to detect localized supply-chain shocks.

---

## Contextual Routing

Do not read full repository documentation before every edit. Consult specific documents only when relevant to your task:

- **Architectural Invariants & Domain Model**: See [`.specify/constitution.md`](file:///e:/food%20price%20monitor/.specify/constitution.md) when adding commodity feeds, changing database schemas (SQLite WAL mode), or modifying volatility calculations (`ASA`, `SPD`).
- **Ubiquitous Domain Vocabulary**: See [`CONTEXT.md`](file:///e:/food%20price%20monitor/CONTEXT.md) when naming entities (use *Mandi*, *Arrival*, *Modal Price*, *Retail Spread*; avoid generic terms like *market*, *volume*, *average price*).
- **Design Tokens & Frontend UI**: See [`DESIGN.md`](file:///e:/food%20price%20monitor/DESIGN.md) when styling components (Cabinet Grotesk, Slate surfaces `#0A0D12`, anti-slop guidelines, dual-mode Household vs. Bulk view).
- **Feature Specifications**: See [`.specify/specs/`](file:///e:/food%20price%20monitor/.specify/specs/) for active feature specs and tasks.

---

## Execution Permissions & Boundaries

You have autonomous permission for the following local workflows:
- **Local Testing**: Run `pytest` and test scripts against local fixtures. Diagnose failures caused by changes and rerun tests until passing without asking for approval at each step.
- **Specification Audits**: Run `python scripts/spec_audit.py` to verify spec and constitutional alignment.
- **SQLite Operations**: Verify database PRAGMAs (`PRAGMA journal_mode=WAL;`) and execute local queries without confirmation.

For destructive external actions (e.g. deleting remote git branches or modifying production keys), stop and confirm with the user first.

---

## Persistence & Definition of Done

Do not stop after a preliminary pass if the task requires end-to-end completion:
1. **Implement**: Make the requested code or documentation changes conforming to the deep module seams (`Warehouse`, `MandiRegistry`, `CommoditySource`, `VolatilityEngine`).
2. **Verify**: Run affected tests (`pytest tests/...`) and verify that no regressions were introduced.
3. **Summarize**: Briefly report the modified files and test verification results.
