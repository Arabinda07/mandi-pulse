# System Status, Ground Truth & Frontend Specification

This document is the single source of truth for the Mandi Pulse project. It records the exact state of current data pipelines, mocks, formulas, missing data gaps, and approved frontend architecture decisions.

---

## 1. System Ground Truth (Current vs. Missing)

### 1.1 What Is Live and Functional Today
- **Warehouse**: Local SQLite database running in WAL mode at `data/agri_engine.db`.
- **Wholesale Mandi Data**: Daily arrivals (quintals) and modal prices (Rs/quintal) for **Tomato**, **Onion**, and **Potato** only.
- **Entity Resolution**: `src/registry.py` maps APMC market strings to 25 canonical mandis across 7 states, including geographic coordinates and official Local Government Directory (LGD) codes.
- **Statistical Volatility**:
  - Arrival Shock Anomaly (ASA): Z-score of weekly arrival volume compared to multi-year calendar-week historical averages.
  - Spatial Price Dispersion (SPD): Coefficient of variation across mandis for a given trading day.
- **Calendar Engine**: Hardcoded Kharif, Rabi, and Zaid crop seasons, plus major Indian festive demand windows (Navratri, Diwali, Eid, Pongal).
- **Datasette Read Engine**: Configured in `datasette/metadata.json` serving raw tables and canned queries.
- **Marimo Prototyping Notebook**: Located at `notebooks/volatility_engine.py`, displaying interactive Altair charts and market stats.

---

### 1.2 What Is Simulated or Hardcoded (Current Gaps)
The table below documents every synthetic calculation currently in place and the external API required to replace it.

| Feature / Domain | Current Implementation in Code | Real World Reality | Future API Target |
| :--- | :--- | :--- | :--- |
| **Retail Price** | Multiplied formula: `retail_equivalent_rs_kg = (wholesale_price / 100) * 1.35` | Urban retail markup varies from 30% to 150% depending on city, quality grade, and channel. | Department of Consumer Affairs (DCA) daily retail price feed, or local quick-commerce scrapers (Blinkit, Zepto). |
| **Logistics / Freight** | Static Haversine distance multiplied by fixed nominal Rs/km rate. | Real freight fluctuates with diesel prices, toll rates, truck availability, and seasonal demand. | FASTag toll congestion data, Indian Oil / HPCL daily diesel price APIs, or logistics broker indices (e.g. Rivigo / BlackBuck spot rates). |
| **Weather Events** | Hardcoded dates in `src/calendar.py` for past historical events (e.g. 2023 North India floods). | Weather impact requires real-time rainfall anomalies, unseasonal heatwaves, and hailstorm alerts. | India Meteorological Department (IMD) API or Open-Meteo historical/forecast APIs. |
| **Commodity Basket** | 3 items: Tomato, Onion, Potato (TOP). | Complete kitchen basket requires pulses (Tur/Chana dal), grains (Atta, Rice), cooking oil (Mustard, Palm), and milk. | Agmarknet / OGD Data.gov.in secondary commodity endpoints. |
| **Mandi Coverage** | 25 curated wholesale mandis. | India has 2,400+ APMC mandis and tens of thousands of rural periodic markets (haats). | Expanding `src/registry.py` with full LGD directory mapping. |

---

## 2. Frontend User Profile: Dual-Mode Architecture

### Decision 1: Target Audience & Primary Mode
- **Household Mode (Default)**:
  - Unit: Rs / kg.
  - Focus: Fair price indicator, 7-to-10 day trend forecast, simple "Buy Now or Wait" advice.
  - Basket: Standard weekly family vegetable basket (Tomato, Onion, Potato).
- **Bulk / Family Mode (Toggle)**:
  - Unit: Rs / quintal, box rates (e.g., 20 kg tomato crate, 50 kg onion sack).
  - Focus: Wholesale vs. retail savings gap. Shows whether traveling to a regional mandi or split-buying with neighbors pays off.
  - Addressed Problem: Resolves Problem #75 (Large families and small businesses paying full retail prices without volume discount transparency).

---

## 3. Technology Separation of Concerns & Role Boundaries

```
[ SQLite Warehouse (WAL) ]
            │
            ▼
[ Datasette Server (:8001) ] ──> Headless JSON REST API (zero custom backend boilerplate)
            │
      ┌─────┴────────────────────────────────────────────────┐
      ▼                                                      ▼
[ Marimo Notebook ]                                 [ React Web App ]
• STRICTLY Quantitative Research & Modeling         • 100% Owner of Consumer Frontend
• Arrival Shock Anomaly (ASA Z-scores)              • AIDA & Bento Layout Architecture
• Spatial Price Dispersion (CV math)                • Production Typography (Cabinet Grotesk)
• Warehouse & Pipeline Data Validation              • Micro-interactions & Tactile Hover Physics
• ZERO Consumer Frontend / HTML / UI Work           • Mobile-First Responsive Execution
```

1. **Datasette**: Headless database explorer and zero-code REST API layer. Serves JSON endpoints directly from SQLite views (`v_live_mandi_prices`, `v_active_corridor_stress`).
2. **Marimo**: Dedicated strictly to quantitative research, statistical formula testing, and pipeline data validation. **Marimo performs ZERO consumer frontend work.** It uses only native data-science tables and charts. It must never attempt to render consumer cards or application chrome.
3. **React Web Application**: Built in a dedicated session. Owns 100% of the consumer user interface, design system tokens, responsive layout, and interaction states. Consumes Datasette's JSON endpoints directly.

---

## 4. Frontend Design Decision Tree (Grilling Progress)

- [x] **Decision 1: Target User**: Dual-Mode (Household Rs/kg default + Bulk/Family wholesale toggle).
- [x] **Decision 2: Core Price Display & Status Tagging**:
  - Primary metric: Single central benchmark price (e.g., ₹32 / kg in Household Mode, ₹2,200 / qtl in Bulk Mode).
  - Change indicator: Day-over-day and week-over-week delta (e.g., `+₹2.50 vs yesterday`).
  - Situation tag: Color-coded badge (`Normal / Fair`, `Elevated (+15%)`, `Severe Spike (+40%)`).
  - Range transparency rule: If secondary range figures or spreads are shown on expansion, the UI must include an explicit legend explaining the origin (e.g. 10th–90th percentile mandi wholesale prices in the region + standard urban logistics markup).
- [x] **Decision 3: Geography & Location Scope**:
  - UI pattern: 5 quick metro chips (Delhi NCR, Mumbai MMR, Bengaluru, Kolkata, Pune) for 1-tap switching, plus a searchable district text field with auto-complete.
  - State persistence: Saved to `localStorage` so repeat visits immediately display the user's home region.
  - Data mapping: Resolves user location to the nearest terminal or consumption mandi in `src/registry.py`.
- [x] **Decision 4: Trend & Outlook Framing**:
  - UI pattern: Mini Trend Pill (`🔴 Spike Expected in ~10d`, `🟢 Cooling Down in ~7d`, `⚪ Stable`) placed alongside each commodity.
  - Actionable guidance banner: Direct household purchasing advice (e.g., *"Stock up your kitchen this week — Nashik wholesale arrivals are down 35% due to unseasonal rain."*).
  - Progressive disclosure: 1-click expander shows the lead-lag connection (origin mandi arrival slump vs destination mandi retail price).
- [x] **Decision 5: Visual UI & Layout Governance**:
  - **Deferred to Design Phase**: The actual visual layout, component styling, and motion will be designed using `/design-taste-frontend` and `/impeccable`.
  - **Anti-Default Guardrails**: No generic AI dashboards, no purple gradients, no cookie-cutter cards. Real typography, accessible contrast, purposeful motion, and deliberate composition.
  - **Interface Mode**: `Operate` (consumer utility) with `Persuade` clarity. Fast, glanceable, high data-trust.
