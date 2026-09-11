# Implementation Plan: SPEC-001 Dual-Mode Consumer Frontend & Ground Truth Gap Tracking

> **Spec Reference:** [`spec.md`](file:///e:/food%20price%20monitor/.specify/specs/001-ground-truth-and-dual-mode/spec.md)  
> **Plan Status:** `Under Review`  
> **Constitutional Compliance:** [x] Passed all 6 Articles of `.specify/constitution.md`

---

## 1. Constitutional & Architectural Verification

Before proposing technical changes, verify adherence to non-negotiables:
- [x] **SQLite WAL Mode (Article III)**: The frontend acts purely as a read client over Datasette JSON endpoints (`http://localhost:8001/agri_engine/...`), executing zero write locks or database schema mutations.
- [x] **Deep Module Seam (Article III)**: Frontend is completely isolated in `frontend/` (Vite + React + Vanilla CSS), consuming decoupled REST endpoints or local offline fallback data. Marimo remains 100% untouched and reserved for statistical modeling.
- [x] **Data Reality & Zero Hidden Mocks (Article IV)**: All simulated metrics (1.35x retail multiplier, Haversine logistics) feature explicit `Estimated Benchmark (Synthetic Proxy)` indicators with explanatory popovers.
- [x] **Ubiquitous Language (Article II)**: Labels strictly use *Mandi*, *Arrival*, *Modal Price*, *Retail Spread*, *Tier 1 Basket*, and *LGD Code*.
- [x] **Dual-Mode UI & Anti-Slop System (Article V & `DESIGN.md`)**:
  - Exact token palette: Canvas `#0A0D12`, Surface `#12161F`, Borders `#232B3B`, Accents Emerald `#34D399`, Amber `#FBBF24`, Red `#F87171`.
  - Typography: `Cabinet Grotesk` (prices/heroes), `Geist` (body/labels), `Geist Mono` (units, deltas, codes with `tabular-nums`).
  - Strict 44x44px mobile touch targets, WCAG AAA contrast, and responsive layout.

---

## 2. Technical Architecture & Component Changes

```mermaid
graph TD
    subgraph Data Layer
        DB[(SQLite WAL: agri_engine.db)]
        DS[Datasette REST Engine :8001]
        DB --> DS
    end

    subgraph Consumer Frontend (Vite + React)
        API[Datasette Client + Fallback Mock]
        DS -.->|JSON REST| API
        Store[Metro & Dual-Mode State]
        API --> Store

        subgraph View Hierarchy
            Nav[Top Navigation & Metro Chips & Mode Switch]
            Hero[Weekly Basket Hero - TOP Index]
            Grid[Tier 1 Commodity Grid - Tomato, Onion, Potato]
            Drawer[Expandable Attribution Drawer - Rupee Journey]
            BulkCalc[Arbitrage & Box/Crate Calculator]
        end

        Store --> Nav
        Store --> Hero
        Store --> Grid
        Store --> Drawer
        Store --> BulkCalc
    end
```

### Technology Selection
* **Framework**: React 19 (via Vite) — ultra-fast HMR, lightweight bundle.
* **Styling**: Vanilla CSS Design Tokens (`src/index.css`) matching `DESIGN.md`. No Tailwind or CSS bloat; 100% custom-crafted design tokens.
* **Fonts**: `Cabinet Grotesk` + `Geist` + `Geist Mono` loaded via `@fontsource` or WebFont CDN with local fallbacks.
* **Icons**: Inline clean SVG micro-icons (zero heavy icon package dependencies).

### Proposed File Modifications & Additions

```
frontend/
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── index.css                     # Complete anti-slop design tokens & reset
│   ├── App.jsx                       # Root layout & state container
│   ├── main.jsx                      # App mounting
│   ├── types.js                      # JSDoc / Type declarations for Mandi & Prices
│   ├── api/
│   │   ├── datasetteClient.js        # Asynchronous fetcher for Datasette endpoints
│   │   └── fallbackData.js          # Constitutional bootstrap snapshot for offline use
│   ├── components/
│   │   ├── Navigation.jsx            # Brand, pulse dot, 5 metro chips, Mode Switcher
│   │   ├── BasketHero.jsx            # Weekly consolidated kitchen basket (TOP index)
│   │   ├── CommodityCard.jsx         # Benchmark price, status pill, advice, trend
│   │   ├── CommodityGrid.jsx         # 3-column responsive commodity container
│   │   ├── AttributionDrawer.jsx     # "The Rupee Journey" breakdown & weather context
│   │   ├── GroundTruthBadge.jsx      # Synthetic proxy tooltip & transparency indicator
│   │   └── BulkSavingsCalculator.jsx # Box & crate rate comparisons (Bulk Mode)
```

---

## 3. Data Integration & Endpoints

The frontend will consume Datasette's canned queries and tables:
1. `http://localhost:8001/agri_engine/v_live_mandi_prices.json?_shape=objects&_size=100`
2. `http://localhost:8001/agri_engine/v_price_movement_attribution.json?_shape=objects&_size=20`
3. `http://localhost:8001/agri_engine/v_active_corridor_stress.json?_shape=objects&_size=20`

**Resilience Contract**: If the Datasette local server is not running on `:8001`, the frontend automatically falls back to `fallbackData.js` (an exact export of the warehouse seed), displaying an unobtrusive *"Live Sync Disconnected — Displaying Cached Reference"* indicator in the utility strip.

---

## 4. Performance & Complexity Analysis

- **Bundle Size**: Under 90 KB gzipped (Zero heavy UI libraries).
- **First Contentful Paint (FCP)**: < 400ms on desktop, < 800ms on 4G mobile.
- **Interaction Latency**: Instantaneous client-side metro and mode switching with zero layout thrashing (`tabular-nums` used for all numerical values).
- **Accessibility**: Meets WCAG 2.1 AA and AAA for text contrast (`13.8:1` on primary text).

---

## 5. Risk Assessment & Rollback Plan

- **Risk**: User launches frontend without running Datasette on port 8001.
  - *Mitigation*: Seamless offline fallback dataset with visible status badge so the UI is immediately fully interactive and reviewable.
- **Risk**: Layout shift when switching between ₹/kg and ₹/quintal.
  - *Mitigation*: Strict fixed-width numerical slots with `tabular-nums` and CSS grid containment.
- **Rollback**: Frontend is completely isolated in `frontend/`; git revert on that folder restores repository state with zero impact on Python data pipelines.
