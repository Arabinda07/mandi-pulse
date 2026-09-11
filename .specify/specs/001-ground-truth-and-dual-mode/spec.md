# Feature Specification: Ground Truth Gap Tracking & Dual-Mode Consumer Interface

> **Spec ID:** `SPEC-001`  
> **Status:** `Approved`  
> **Author:** Architecture & Domain Team  
> **Created:** 2026-09-11  
> **Target Audience:** Household Shoppers, Volume Family Buyers, Quantitative Analysts  
> **Reference Document:** [`docs/GROUND_TRUTH_AND_FRONTEND_SPEC.md`](file:///e:/food%20price%20monitor/docs/GROUND_TRUTH_AND_FRONTEND_SPEC.md)

---

## 1. Problem Statement & "Why"

Urban Indian consumers face sudden price shocks for essential vegetables (Tomato, Onion, Potato) with zero forward visibility. Meanwhile, bulk family buyers and small food establishments pay full retail prices without realizing that regional mandi wholesale prices are substantially lower.

This specification governs:
1. **Dual-Mode Consumer Experience**: Bridging household decision-making (₹/kg, "Buy Now vs. Wait" advice) with bulk purchasing arbitrage (₹/quintal, box rates, group buying savings).
2. **Ground Truth Contract**: Maintaining absolute transparency regarding what data is empirically live (Agmarknet daily wholesale arrivals and modal prices) versus what is simulated (retail markup multiplier, Haversine freight, synthetic weather events).

---

## 2. User Stories & Core Behaviors

### User Story 1: Everyday Household Shopper
- **As an** urban household food buyer
- **I want to** check today's fair benchmark price and 7–10 day trend forecast in ₹/kg for Tomato, Onion, and Potato
- **So that** I know whether my local retail vendor/quick-commerce app is overcharging and whether to buy now or delay purchases.

#### Acceptance Criteria
- [ ] Prices default to **₹/kg** with single-decimal precision (e.g. `₹32.5/kg`).
- [ ] The interface displays an actionable status badge: *Fair Price*, *Elevated / Caution*, or *Severe Spike*.
- [ ] Provides a clear purchasing recommendation based on the Arrival Shock Anomaly ($Z$-score departure) 10–14 days prior.

### User Story 2: Bulk Buyer / Large Family Group
- **As a** large household or community organizer
- **I want to** toggle into Bulk Mode to view crate/sack rates and wholesale price deltas
- **So that** I can determine if traveling to an APMC mandi or split-purchasing with neighbors saves money.

#### Acceptance Criteria
- [ ] Immediate UI toggle without page reload between Household Mode and Bulk Mode.
- [ ] Displays prices in standard wholesale packaging units:
  - Tomato: 20 kg crate rate.
  - Onion: 50 kg sack rate.
  - Potato: 50 kg sack rate.
  - Raw wholesale: ₹/quintal.
- [ ] Computes the estimated "Arbitrage Savings Delta" comparing urban retail equivalent against mandi wholesale modal price.

---

## 3. Domain Metrics & Data Contracts

### 3.1: Live Empirical Baseline
- **Commodities**: Tier 1 Basket (Tomato, Onion, Potato).
- **Mandi Resolution**: 25 curated APMC wholesale mandis mapped via `src/registry.py` with official LGD codes.
- **Atomic Observation**: Daily arrivals (quintals) and modal prices (₹/quintal).
- **Derived Metrics**:
  - Arrival Shock Anomaly (ASA): Seasonal $Z$-score against calendar-week historical averages.
  - Spatial Price Dispersion (SPD): Inter-mandi coefficient of variation across production and consumption centers.

### 3.2: Synthetic Proxy Transition Matrix (Ground Truth)
All downstream UI components and APIs must display appropriate provenance badges for synthetic metrics until live feeds are connected:

| Metric | Current Synthetic Logic | Target Live API / Official Source | Status |
| :--- | :--- | :--- | :--- |
| **Wholesale Mandi Arrivals & Prices** | Live paginated sync connecting Agmarknet API via `api.data.gov.in` (1,664 live records ingested today) | Open Government Data (OGD) Agmarknet Resource `9ef84268-d588-465a-a308-a864a43d0070` via `api.data.gov.in` | `LIVE_INTEGRATED` |
| **Retail Benchmark Price** | Live daily scraping from Department of Consumer Affairs PMS (`https://fcainfoweb.nic.in/`) | Department of Consumer Affairs (DCA) Price Monitoring System (`https://fcainfoweb.nic.in/`) | `LIVE_INTEGRATED` |
| **Day/Week Price Deltas** | Windowed `v_live_price_deltas` view with `LAG OVER` computing exact DoD and WoW changes | SQLite window functions (`LAG() OVER ...`) on daily price facts | `LIVE_INTEGRATED` |
| **Early Signals & Shopping Advice** | Hardcoded static strings in `frontend/src/api/fallbackData.js` | Rule-based NLG engine evaluating origin ASA Z-scores, weather flags, and price velocity | `PENDING_ENGINE_IMPLEMENTATION` |
| **Freight Cost** | Fixed nominal ₹/km over Haversine distance | PPAC daily diesel prices (`ppac.gov.in`) + NHTIS toll gazette rates (`tis.nhai.gov.in`) | `PENDING_INTEGRATION` |
| **The Rupee Journey Cost Breakdown** | Active corridor joins in `v_live_mandi_prices` linking terminal mandis to production origins (`origin_mandi_id`, `origin_name`, `origin_arrival_shock_z`, `corridor_stress_level`) | State APMC statutory cess schedules (1-2%) + dynamic DCA retail spread + active corridor links | `LIVE_INTEGRATED` |
| **Weekly Kitchen Basket Weights** | Assumed 1kg Tomato + 2kg Onion + 2kg Potato | MoSPI Consumer Price Index (CPI 2024=100 Series) / HCES 2023-24 expenditure ratios | `PENDING_CALIBRATION` |
| **Bulk Mandi Handling & Packaging** | Scaled flat wholesale rate: `wholesale / 100 * box_kg` | APMC statutory hamali (₹2-5/bag) and standardized crate auction lots under State APMC Acts | `PENDING_INTEGRATION` |
| **Crop Calamities & Weather** | Live Open-Meteo ERA5 / IMD grid precipitation and temperature anomalies | Open-Meteo ERA5 / IMD grid live precipitation API (`src/sources/weather.py`) | `LIVE_INTEGRATED` |

---

## 4. Architectural Boundaries

### Included (In-Scope)
- Dual-mode toggle (Household ₹/kg vs Bulk ₹/qtl & box rates).
- Presentation of TOP commodities (Tomato, Onion, Potato).
- Clear attribution drawer showing Mandi origin, distance, and 10–14 day arrival trends.
- Datasette REST endpoints serving canned queries with sub-second response times.

### Excluded (Out-of-Scope)
- Tier 2 commodities (pulses, oilseeds, cereals) — deferred to `SPEC-002`.
- Direct payment checkout or logistics order fulfillment.
- Custom user accounts or authentication.

---

## 5. Clarification Log (`/speckit.clarify`)

| Question / Ambiguity | Decision | Decided By | Date |
| :--- | :--- | :--- | :--- |
| *Should Marimo handle the consumer frontend?* | *No. Marimo is strictly reserved for quantitative research and lead-lag chart prototyping. The consumer frontend must be an isolated, lightweight web app querying Datasette.* | Architecture Team | 2026-09-11 |
| *How should synthetic retail markup be communicated to users?* | *With a subtle "Estimated Retail Benchmark" indicator, with a tooltip explaining the 35% standard wholesale-to-retail multiplier until DCA feed integration.* | Product Team | 2026-09-11 |
