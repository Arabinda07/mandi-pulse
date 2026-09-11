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
- **Meteorological & Weather Shocks Engine**: Live Open-Meteo API (`archive-api.open-meteo.com` / `api.open-meteo.com` matching IMD gridded daily rainfall) integrated into `src/sources/weather.py`, `src/attribution.py`, and `data/agri_engine.db` via `mandi_weather_facts`. Dynamically attributes heavy rainfall ($\ge 15\text{mm}$, $\ge 30\text{mm}$) and extreme heat ($\ge 38^\circ\text{C}$, $\ge 40^\circ\text{C}$) to APMC price shocks.
- **Calendar Engine**: Hardcoded Kharif, Rabi, and Zaid crop seasons, plus major Indian festive demand windows (Navratri, Diwali, Eid, Pongal).
- **Datasette Read Engine**: Configured in `datasette/metadata.json` serving raw tables and canned queries.
- **Marimo Prototyping Notebook**: Located at `notebooks/volatility_engine.py`, displaying interactive Altair charts and market stats.

---

### 1.2 Exhaustive Ground Truth Gap Matrix (Current vs. Integrated)
The table below tracks every domain metric, its ground truth status, and the official government API or empirical source required to eliminate synthetic assumptions.

| Feature / Domain | Current Implementation in Frontend & Engine | Real World Reality | Verified Official API / Data Source | Status & Next Action |
| :--- | :--- | :--- | :--- | :--- |
| **Wholesale Mandi Arrivals & Prices** | Live paginated sync via `src/sources/datagov.py` connecting `api.data.gov.in` (Agmarknet). Ingested 1,664 live daily records across India for 11/09/2026. | Real APMC auctions trade daily across 2,400+ mandis with high-frequency arrival volumes and modal auction rates (₹/qtl). | **Open Government Data (OGD) Platform India (Agmarknet)** Resource ID `9ef84268-d588-465a-a308-a864a43d0070` via `https://api.data.gov.in`. | **🟢 LIVE INTEGRATED**: Paginated ingestion active in `src/sources/datagov.py` and `cmd_sync` with zero synthetic hash formulas. |
| **Retail Price Benchmark** | Real daily retail rates scraped directly from Department of Consumer Affairs Price Monitoring System (`https://fcainfoweb.nic.in/`). | Real retail rates are published daily across 555 reporting centers by the Department of Consumer Affairs (Tomato ₹39.19, Onion ₹53.10, Potato ₹22.80 as on 10/09/2026). | **Department of Consumer Affairs (DCA)** Price Monitoring System (PMS) at `https://fcainfoweb.nic.in/` (All India & Center-wise daily retail price reports). | **🟢 LIVE INTEGRATED**: Direct BeautifulSoup parser active in `src/sources/dca.py` (`dca_pms_live`), eliminating the synthetic 1.35x proxy. |
| **Day/Week Price Movements (`day_change_rs`, `week_change_pct`)** | Real-time window functions (`LAG OVER`) computed in SQLite view `v_live_price_deltas`. Exposes `day_change_rs_kg`, `day_change_pct`, and `week_change_pct` for all commodities and mandis. | Price velocity and momentum must be computed deterministically from consecutive daily trading observations. | **SQLite Analytical Window Functions** (`LAG(modal_price, 1) OVER (...)`, `LAG(modal_price, 7) OVER (...)`) computed across consecutive daily mandi/center facts. | **🟢 LIVE INTEGRATED**: Implemented in `v_live_price_deltas` and joined into `v_live_mandi_prices`, eliminating hardcoded delta placeholders. |
| **Early Signals & Trend Pills (`trend_signal`)** | Algorithmic signal engine joining farmgate arrival anomalies (ASA Z-scores from `corridor_stress_metrics`) and price deltas directly into `v_live_price_deltas` and `v_live_mandi_prices`. | Early warning signals must be algorithmic outputs driven by farmgate arrival anomalies (ASA Z-scores) with 10-14 day lead-lag. | **Algorithmic Signal Engine**: Evaluates `arrival_z_score` from `corridor_stress_metrics` ($\text{ASA} < -1.5\sigma \implies \text{Spike}$, $\text{ASA} > +1.0\sigma \implies \text{Cooling}$). | **🟢 LIVE INTEGRATED**: Dynamic trend signals (`Spike in ~10d`, `Cooling Down in ~7d`, `Stable Corridor`) computed directly in SQL views. |
| **Actionable Shopping Advice & Market Verdict** | Hardcoded static text strings in `fallbackData.js` (e.g., *"Lasalgaon arrivals dropped 38% due to unseasonal rain..."*). | Household advice must dynamically combine arrival shock severity, meteorological flags, and retail spread trends. | **Deterministic Rule-Based NLG Engine**: Formulates advice based on live facts (Origin Mandi + ASA Z + Weather Flag + DoD Delta). | **🔴 PENDING IMPLEMENTATION**: Build deterministic advice generator in `src/attribution.py` and expose via API. |
| **The Rupee Journey Breakdown** | Live corridor joins in `v_live_mandi_prices` linking terminal mandis to production origins (`origin_mandi_id`, `origin_mandi_name`, `origin_modal_price_rs_kg`, `origin_arrival_shock_z`, `corridor_stress_level`). | Real cost flow composed of origin APMC auction rate, statutory State Mandi Cess (1-2%), transit freight, and true retail spread. | **Active Corridor Joins** linking `daily_mandi_facts` (origin) to `daily_mandi_facts` (terminal) and `dca_retail_facts` (retail center). | **🟢 LIVE INTEGRATED**: Joined `v_corridor_attributions` and `v_origin_corridor_attributions` directly into `v_live_mandi_prices`. |
| **Bulk Mode Arbitrage & Package Sizing** | Hardcoded crate/sack sizes (`20kg crate`, `50kg sack`) with arbitrary 40x bulk multiplier in `BasketHero.jsx`. Syntax error in `datasetteClient.js` (`crateRate` undefined) forcing fallback. | APMC wholesale auctions trade in standardized packaging units with statutory hamali (handling ₹2-5/bag), weighment, and crate charges under State APMC Acts. | **State APMC Mandi By-Laws** (Maharashtra APMC Rules, Delhi APMC Act, KSAMB Regulations) codifying official packaging and handling charges. | **🔴 PENDING IMPLEMENTATION**: Fix `datasetteClient.js` undeclared variables; codify statutory hamali/weighment rates and remove arbitrary 40x hero multiplier. |
| **Weekly Kitchen Basket Weightings** | Fixed assumption: 1kg Tomato + 2kg Onion + 2kg Potato. | Real household consumption is benchmarked by national expenditure surveys. | **Ministry of Statistics & Programme Implementation (MoSPI)** Consumer Price Index (CPI 2024=100 Series) & Household Consumption Expenditure Survey (HCES 2023-24). | **🔴 PENDING CALIBRATION**: Calibrate basket quantities to official MoSPI urban household expenditure ratios (~1.5kg Potato, 1.2kg Onion, 1.0kg Tomato per weekly household unit). |
| **Logistics / Freight** | Static Haversine distance multiplied by fixed nominal Rs/km rate. | Real freight fluctuates with diesel prices, toll rates, truck availability, and seasonal demand. | **Petroleum Planning & Analysis Cell (PPAC)** daily metro diesel rates (`ppac.gov.in`) + **National Highways Toll Information System (NHTIS)** toll gazettes (`tis.nhai.gov.in`). | **🔴 PENDING INTEGRATION**: Ingest daily PPAC diesel prices + gazetted national highway toll plaza rates for active corridors. |
| **Weather & Crop Calamity Alerts** | Live Open-Meteo ERA5 / IMD reanalysis and forecast queries at mandi coordinates. | Weather impact requires real-time precipitation anomalies and heatwave detection. | **Open-Meteo Reanalysis & Forecast API** (`api.open-meteo.com` / `archive-api.open-meteo.com`). | **🟢 LIVE INTEGRATED**: Connected in `src/sources/weather.py`, `src/attribution.py`, and `mandi_weather_facts`. |
| **Statutory State APMC Cess** | Exact statutory formula: `Retail Spread = DCA Retail - (Wholesale + Statutory Cess + Freight)`. | Real cost flow composed of origin APMC auction rate, statutory State Mandi Cess (1-2%), Commission (Arhat), transit freight, and true DCA retail spread. | **State Agricultural Marketing Boards** (MSAMB, DAMB, KSAMB, UPSAMB gazettes) codified in `src/registry.py` & SQLite warehouse views (`v_live_mandi_prices`). | **🟢 LIVE INTEGRATED**: Codified MSAMB (1.05%), DAMB (2.0%), KSAMB (1.5%), UPSAMB (2.0%) directly into `MandiRecord` and warehouse views. |

---

### 1.3 Official Data Sources & API Verification Status

1. **Agmarknet Wholesale Mandi API (Live & Verified)**:
   * *Portal*: Open Government Data (OGD) Platform India (`https://data.gov.in`).
   * *Resource Endpoint*: `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`.
   * *Auth / Query*: `api-key` query param (active in `.env`), `filters[commodity]=Tomato` (or Onion, Potato), `limit=100`.
   * *Verification*: Successfully queried in live test returning real data for `11/09/2026` across APMCs (e.g. Baripada, Cuttack, Nagina) with exact modal prices.

2. **Department of Consumer Affairs (DCA) Price Monitoring System (Live & Verified)**:
   * *Portal*: Price Monitoring System (PMS), Ministry of Consumer Affairs (`https://fcainfoweb.nic.in/` / `consumeraffairs.nic.in/pmc/`).
   * *Data*: Daily retail and wholesale prices for 22+ essential commodities across 555 reporting centers.
   * *Verification*: Successfully fetched and parsed live bulletin for `10/09/2026` (All-India Retail: Tomato ₹39.19/kg, Onion ₹53.10/kg, Potato ₹22.80/kg).
   * *Action*: Replace the pseudo-empirical 1.35x formula in `src/sources/dca.py` with an automated daily ingestion parser for `fcainfoweb.nic.in`.

3. **Petroleum Planning & Analysis Cell (PPAC) Fuel Pricing (Verified)**:
   * *Portal*: PPAC, Ministry of Petroleum & Natural Gas (`https://ppac.gov.in` / `iced.niti.gov.in`).
   * *Data*: Daily Retail Selling Price (RSP) of High-Speed Diesel (HSD) across Delhi, Mumbai, Kolkata, Chennai, and state capitals.
   * *Action*: Ingest daily diesel rates to dynamically price ton-km freight.

4. **MoSPI CPI & HCES 2023-24 Household Basket Calibration (Verified)**:
   * *Portal*: Ministry of Statistics & Programme Implementation e-Sankhyiki (`https://esankhyiki.mospi.gov.in/` / `mospi.gov.in`).
   * *Data*: HCES 2023-24 consumption shares and CPI 2024=100 vegetable weights.
   * *Action*: Anchor kitchen basket to ~1.5kg Potato, 1.2kg Onion, 1.0kg Tomato per weekly household unit.

5. **Open-Meteo Meteorological API (Live & Integrated)**:
   * *Portal*: `https://api.open-meteo.com` / `https://archive-api.open-meteo.com`.
   * *Data*: Daily precipitation and max temperatures at mandi latitude/longitude coordinates.
   * *Status*: Already integrated and active in `src/sources/weather.py`.

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
