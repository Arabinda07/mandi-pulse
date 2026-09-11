# Execution Tasks: SPEC-001 Dual-Mode Consumer Frontend & Ground Truth Gap Tracking

> **Spec Reference:** [`spec.md`](file:///e:/food%20price%20monitor/.specify/specs/001-ground-truth-and-dual-mode/spec.md)  
> **Plan Reference:** [`plan.md`](file:///e:/food%20price%20monitor/.specify/specs/001-ground-truth-and-dual-mode/plan.md)  
> **Status:** `Completed`  

---

## Task Execution Guidelines
1. Execute tasks in sequential order unless explicitly marked as parallelizable.
2. Check off each task immediately after automated test verification passes.
3. If an unforeseen architectural blocker arises, pause execution and update `plan.md`.

---

## Phase 1: Frontend Foundation & Design Tokens

- [x] `TASK-01`: **Scaffold Vite + React Project Structure**
  - **Action**: Initialized `frontend/` with React 19, Vite config with proxy, package.json, and HTML shell.
  - **Verification**: `npm run build` generates clean bundle in 619ms (< 80 kB gzipped).
  - **Spec Link**: Section 4 (Architectural Boundaries)

- [x] `TASK-02`: **Design System & Typography Token Setup**
  - **Action**: Created `frontend/src/index.css` implementing all tokens from `DESIGN.md`:
    - Canvas `#0A0D12`, Surface `#12161F`, Elevated `#1A202C`, Borders `#232B3B` / `#344155`.
    - Semantic Accents: Emerald `#34D399`, Amber `#FBBF24`, Red `#F87171`, Brand `#10B981`.
    - Web fonts: `Cabinet Grotesk`, `Geist`, `Geist Mono` with `tabular-nums`.
    - Single radius rule: `rounded-xl` (14px), `rounded-pill` (9999px), `rounded-chip` (8px).
  - **Verification**: Verified zero CSS linter warnings and responsive layout.
  - **Spec Link**: Section 5 (Visual UI & Layout Governance)

---

## Phase 2: Data Client & State Management

- [x] `TASK-03`: **Datasette REST API Client & Offline Fallback**
  - **Action**: Created `src/api/datasetteClient.js` and `src/api/fallbackData.js` containing real warehouse seed snapshot for Tomato, Onion, Potato across 25 APMC mandis.
  - **Verification**: Client seamlessly serves fallback reference data when `:8001` is offline, with clear connection badge.
  - **Spec Link**: Section 3 (Domain Metrics & Data Contracts)

- [x] `TASK-04`: **Dual-Mode & Location State Hook**
  - **Action**: Implemented application state managing:
    - Current Metro (Delhi NCR, Mumbai MMR, Bengaluru, Kolkata, Pune) persisted to `localStorage`.
    - Operational Mode: `Household (₹/kg)` vs `Bulk Buyer (₹/qtl)`.
  - **Verification**: State transitions trigger zero layout shifts; mode changes persist across reloads.
  - **Spec Link**: Section 2 (User Stories 1 & 2)

---

## Phase 3: Core UI Components

- [x] `TASK-05`: **Top Navigation & Utility Strip (`Navigation.jsx`)**
  - **Action**: Built brand header with warehouse freshness pulse dot, 5 metro quick chips with active indicators, and the segmented pill mode toggle.
  - **Verification**: All chips and toggles meet minimum 44x44px touch targets on mobile.
  - **Spec Link**: Section 2

- [x] `TASK-06`: **Weekly Kitchen Basket Hero (`BasketHero.jsx`)**
  - **Action**: Built consolidated family basket card (1kg Tomato + 2kg Onion + 2kg Potato) with week-over-week change delta and natural language advice verdict.
  - **Verification**: Values display in Cabinet Grotesk 700 with Geist Mono units.
  - **Spec Link**: Section 2 (User Story 1)

- [x] `TASK-07`: **Tier 1 Commodity Grid & Cards (`CommodityCard.jsx`, `CommodityGrid.jsx`)**
  - **Action**: Implemented responsive 3-column grid for Tomato, Onion, Potato displaying:
    - Primary benchmark price (`₹32/kg` in Household, `₹2,200/qtl` in Bulk).
    - Status badge (`Fair Price`, `Elevated`, `Severe Spike`).
    - Mini-trend pill (`🔴 Spike in ~10d` vs `🟢 Cooling Down`).
    - 1-line plain-language shopping advice.
    - Ground truth proxy badge (`Estimated Benchmark`) for synthetic retail markup.
  - **Verification**: Grid collapses gracefully to 1 column on mobile screens (< 768px).
  - **Spec Link**: Section 2 & Section 3.2

---

## Phase 4: Progressive Disclosure & Bulk Arbitrage

- [x] `TASK-08`: **Expandable Attribution Drawer ("The Rupee Journey") (`AttributionDrawer.jsx`)**
  - **Action**: Implemented 1-click disclosure showing:
    - Price journey: Farmgate APMC $\rightarrow$ Transit/Freight $\rightarrow$ Retail Margin.
    - Origin Mandi details with LGD code and distance.
    - Seasonal phase & weather context alert.
  - **Verification**: Expand/collapse animation tested with browser subagent.
  - **Spec Link**: Section 4 (Attribution Drawer)

- [x] `TASK-09`: **Bulk Arbitrage Calculator (`BulkSavingsCalculator.jsx`)**
  - **Action**: In Bulk Mode, displays packaging rates (20kg tomato crate, 50kg onion sack, 50kg potato sack) and computes the group-buying savings delta against urban retail equivalent.
  - **Verification**: Accurate savings percentage and net rupee difference calculated dynamically.
  - **Spec Link**: Section 2 (User Story 2)

---

## Phase 5: Verification, Accessibility & Audit

- [x] `TASK-10`: **Accessibility & Contrast Verification**
  - **Action**: Validated text contrast ratios meet WCAG AA/AAA standards (`13.8:1` for primary text), touch targets $\ge$ 44px, and clean keyboard navigation via browser subagent.
  - **Verification**: Zero console errors or warnings recorded.

- [x] `TASK-11`: **Constitutional & Spec Audit**
  - **Action**: Executed `python scripts/spec_audit.py` and `pytest`.
  - **Verification**: All spec packages verified (`[SUCCESS]`) and all pytest tests pass.

---

## Phase 6: Live Government Feeds, Analytical Views & Deterministic NLG Advice

- [x] `TASK-12`: **Real DCA Retail Web Scraping & Multiplier Elimination**
  - **Action**: Created `src/sources/dca.py` scraping official `fcainfoweb.nic.in` daily retail prices across 550+ reporting centers. Integrated into `Warehouse.record_daily_dca_prices()` and created `v_dca_retail_benchmarks`.
  - **Verification**: `pytest tests/test_dca.py` passes with real network and parsing tests.
  - **Spec Link**: Section 3.2 (Ground Truth Data Sourcing)

- [x] `TASK-13`: **Live Agmarknet Wholesale Mandi Ingestion**
  - **Action**: Refactored `src/sources/datagov.py` to target official OGD API resource `9ef84268` for live 2026 Agmarknet daily wholesale mandi records. Ingested 1,664 live records for `2026-09-11`.
  - **Verification**: Ingested facts verify in `daily_mandi_facts` with 0 unhandled commodity varieties.
  - **Spec Link**: Section 3.1 (Wholesale Mandi Data)

- [x] `TASK-14`: **Analytical SQL Views for Movements & Corridors**
  - **Action**: Implemented `v_live_price_deltas` with SQL window functions (`LAG(modal_price, 1)` and `LAG(modal_price, 7)`) in `src/warehouse.py`. Created `v_origin_corridor_attributions` and joined origin mandis, arrival shock anomaly $Z$-scores, and corridor stress into `v_live_mandi_prices`.
  - **Verification**: `pytest tests/test_warehouse.py` verifies delta calculations and corridor joins.
  - **Spec Link**: Section 3.3 (Corridor Stress & Window Delts)

- [x] `TASK-15`: **Deterministic Shopping Advice & Market Verdict Generator**
  - **Action**: Implemented rule-based NLG engine in `src/attribution.py` (`generate_shopping_advice`, `generate_basket_verdict`) and mirrored in `frontend/src/api/adviceGenerator.js`. Replaced all static advice in `frontend/src/api/fallbackData.js` and wired `frontend/src/api/datasetteClient.js` directly to live Datasette views.
  - **Verification**: `pytest tests/test_weather.py` passes unit tests for advice generation.
  - **Spec Link**: Section 2 (Household Buying Recommendations)

- [x] `TASK-16`: **Full End-to-End Browser & Test Suite Validation**
  - **Action**: Executed full pytest suite (32 tests), verified 100% Spec Kit audit, and verified live UI on `http://localhost:3000/` via browser subagent.
  - **Verification**: 32 passed in `33.64s`, 0 console errors, dynamic basket verdicts and price cards active.
