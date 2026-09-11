# Project Constitution: Mandi Pulse
**India Food Inflation & Supply-Chain Volatility Engine**

> **Status:** Active & Enforceable  
> **Version:** 1.0.0  
> **Governance:** Spec-Driven Development (GitHub Spec Kit Framework)  
> **Supersedes:** Informal conventions; binds all contributors, human reviewers, and AI coding agents.

---

## Preamble

Mandi Pulse is a quantitative, civic-transparency analytical engine and decision utility for Indian agricultural commodities. Its mission is to track high-frequency wholesale mandi arrivals and prices to detect localized supply-chain shocks, compute spatial price dispersion, and model leading indicators for consumer food inflation.

Every file created, line of code committed, and specification drafted in this repository must comply with the six articles of this Constitution.

---

## Article I: The Empirical Premise & Mathematical Standards

### Section 1.1: Core Empirical Premise
In India, wholesale arrival volume drops at primary farmgate APMC production hubs (e.g., *Lasalgaon* for onions, *Kolar* for tomatoes, *Agra* for potatoes) precede consumer retail price spikes and terminal wholesale inflation by **10 to 14 days** (and full CPI reflection by 2 to 4 weeks). The atomic unit of the engine is the daily **Mandi-Commodity arrival and modal price observation**, rolled upwards into corridor, regional, and national volatility metrics.

### Section 1.2: Volatility Invariants
All quantitative calculations must remain pure, deterministic, and isolated within `src/volatility.py`:
1. **Arrival Shock Anomaly (ASA)**:
   $$\text{ASA} = \frac{A_{t} - \mu_{\text{season}(w)}}{\sigma_{\text{season}(w)}}$$
   Where $A_t$ is weekly arrival volume and $\mu, \sigma$ are calculated against multi-year seasonal calendar-week baselines.
2. **Spatial Price Dispersion (SPD)**:
   $$\text{SPD} = \frac{\sigma_{\text{modal}}}{\mu_{\text{modal}}}$$
   Representing the Coefficient of Variation across production vs. consumption mandis within an active corridor.
3. **Corridor Friction**:
   Spread calculated as $(P_{\text{terminal}} - P_{\text{origin}})$ evaluated against transit distance and freight cost benchmarks.

---

## Article II: Ubiquitous Language & Nomenclature

To eliminate context rot and semantic drift, the following domain vocabulary is strictly enforced. Violations are considered bugs.

| Canonical Term | Definition | Strictly Forbidden Aliases |
| :--- | :--- | :--- |
| **Mandi** | Designated wholesale agricultural market yard operating under state APMC regulations where farmers auction produce to traders. | *Market, wholesale bazaar, yard, shop* |
| **Arrival** | Physical volume of a commodity batch entering a Mandi on a reported date (measured in quintals). | *Supply, volume, shipment, influx, input* |
| **Modal Price** | Most frequent wholesale transaction price observed for a commodity in a Mandi on a trading day (in ₹/quintal). | *Average price, median price, market rate, cost* |
| **Retail Spread** | Price gap between urban consumer retail price and origin Mandi wholesale Modal Price. | *Margin, markup, middleman cut, profit* |
| **Volatility Index** | Statistical metric of localized price dispersion and arrival variance across Mandis. | *Risk score, price swing, instability metric* |
| **Tier 1 Basket** | High-impact essential commodities (Tomato, Onion, Potato) tracked daily with multi-year backfill. | *Core list, priority crops, primary basket* |
| **Tier 2 Basket** | Secondary or niche commodities ingested on-demand or as periodic archives. | *Secondary crops, peripheral list, long-tail* |
| **Mandi Registry** | Curated dimension table mapping raw APMC strings to canonical names, LGD codes, and coordinates. | *Market master, APMC list, location directory* |
| **LGD Code** | Official unique integer identifier from Ministry of Panchayati Raj's Local Government Directory. | *Census code, postal code, district ID, pincode* |
| **Warehouse** | Unified local SQLite database in WAL mode serving pipeline writes, Datasette, and Marimo. | *Data lake, database cluster, central store* |
| **Bootstrap Seed** | Pre-curated reference slice of master entities and historical observations for offline use. | *Dummy data, sample records, mock dataset* |
| **Commodity Source**| Ingestion port/adapter interface retrieving daily arrival and price observations. | *Data fetcher, downloader, crawler, scraper* |

---

## Article III: Architectural Invariants & Deep Modules

Guided by ADRs 0001 through 0007, the codebase is strictly organized into deep modules with narrow, high-leverage interfaces:

### Section 3.1: SQLite WAL Mode (ADR 0004)
1. The primary datastore is `data/agri_engine.db`.
2. The database **must always operate in Write-Ahead Logging mode** (`PRAGMA journal_mode=WAL;`).
3. Concurrency contract: Background ETL writers append data without blocking read operations from Datasette (port `8001`) or reactive computations in Marimo (`notebooks/volatility_engine.py`).
4. In-process analytical queries in Marimo must use local file descriptors and zero-copy Polars scans rather than serializing data over HTTP JSON APIs.

### Section 3.2: Spatial Entity Resolution (ADR 0003)
1. Raw market text from incoming data sources must never be written directly to `fact_mandi_daily`.
2. Every market entity must be resolved through `MandiRegistry` (`src/registry.py`), mapping to a verified LGD district code, canonical name, and latitude/longitude coordinates.
3. Unmatched mandis must be logged to a quarantine staging table until aliases are reviewed and registered.

### Section 3.3: Port-and-Adapter Seams (ADR 0006, 0007)
1. All data ingestion must implement the `CommoditySource` protocol (`src/sources/base.py`).
2. Two canonical adapters are maintained:
   - `BootstrapSeedAdapter`: Self-contained, offline-executable, local-substitutable adapter for zero-friction setup, local testing, and CI pipelines.
   - `DataGovInAdapter`: External production sync adapter connecting to `api.data.gov.in` (Agmarknet).
3. Code modules must never invoke raw `requests` or `urllib` calls outside of concrete adapter classes.

---

## Article IV: Data Reality & Ground Truth Contract

The integrity of this analytical system depends on complete transparency regarding data provenance:

### Section 4.1: The Zero-Hidden-Mocks Rule
Under no circumstances may synthetic calculations, heuristic multipliers, or simulated models masquerade as live empirical facts. 

### Section 4.2: Current Known Proxies & Transition Boundaries
All simulated metrics must be explicitly tagged as `synthetic` in schemas and APIs:
- **Retail Prices**: Current proxy is `(wholesale_price / 100) * 1.35`. Any change or display must clearly label this until the Department of Consumer Affairs (DCA) live feed or quick-commerce scrapers are integrated.
- **Logistics & Freight**: Current proxy is static Haversine distance multiplied by fixed nominal ₹/km. Must be explicitly flagged until dynamic diesel and FASTag APIs are connected.
- **Weather & Crop Calamity**: Past historical events in `src/calendar.py` are hardcoded. Must be upgraded via Open-Meteo or IMD weather feeds.

---

## Article V: Consumer Design & UX Guardrails

### Section 5.1: Dual-Mode Architecture
All user interfaces must support two primary operational modes:
1. **Household Mode (Default)**:
   - **Unit**: ₹/kg.
   - **Focus**: Fair price indicator, 7–10 day trend forecast, consumer purchasing guidance ("Buy Now vs. Wait").
   - **Scope**: Kitchen staples (Tomato, Onion, Potato).
2. **Bulk / Family Mode**:
   - **Unit**: ₹/quintal and standard wholesale containers (e.g., 20 kg tomato crate, 50 kg onion sack).
   - **Focus**: Wholesale vs. retail savings delta, break-even distance calculations for direct-mandi purchasing, group buying arbitrage.

### Section 5.2: Anti-Slop Visual System
1. **Palette**: Rooted in agricultural reality and slate stone. Absolutely no generic AI purple/violet glows, no dark-mesh gradient soups, and no decorative pastel fluff.
   - Canvas: `#0A0D12`
   - Surface: `#12161F`
   - Border Subtle: `#232B3B`
   - Semantic Signals: Emerald (`#34D399`), Amber (`#FBBF24`), Rose (`#F87171`).
2. **Typography**:
   - Display & Headline Prices: `Cabinet Grotesk` (700/800).
   - Body & Explanations: `Geist` (400/500/600).
   - Units, Mandi Codes, Deltas: `Geist Mono` / `JetBrains Mono`.
3. **Information Density**: High density, mobile-first glanceability (instant answer in under 3 seconds).

---

## Article VI: AI Agent Governance & Spec-Driven Workflow

All AI coding agents interacting with this repository must strictly adhere to the GitHub Spec Kit lifecycle:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 1. Spec      │ ──> │ 2. Clarify   │ ──> │ 3. Plan      │ ──> │ 4. Tasks     │ ──> │ 5. Implement │
│ (.specify/   │     │ (Resolve     │     │ (Architecture│     │ (Atomic      │     │ (Clean Code  │
│  specs/*)    │     │  Ambiguity)  │     │  & Seams)    │     │  Checklist)  │     │  & Tests)    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

1. **No Vibe Coding**: Agents must never write or refactor substantive features without an approved specification in `.specify/specs/`.
2. **Constitutional Compliance**: Every implementation plan must contain a "Constitutional Check" validating adherence to SQLite WAL rules, deep module seams, ubiquitous language, and ground-truth transparency.
3. **Traceability**: Every code pull request or commit must link directly to an existing Spec and Task ID.
4. **Non-Breaking Invariants**: Modifications that alter existing ADRs require authoring a new ADR in `docs/adr/` and an amendment to this Constitution.
