# 🇮🇳 India Food Inflation & Supply-Chain Volatility Engine

A quantitative analytical engine for detecting localized agricultural supply-chain shocks and modeling leading indicators for food inflation in India. Built with **SQLite in WAL mode**, interactive web exploration via **Datasette**, and reactive computational modeling in **Marimo**.

---

## 🎯 The Core Empirical Premise

In India, wholesale arrival volume drops at primary farmgate APMC production hubs (e.g. *Lasalgaon* for onions, *Kolar* for tomatoes, *Agra* for potatoes) **precede consumer retail and terminal wholesale price spikes by 10 to 14 days**.

This engine tracks:
1. **Arrival Shock Anomaly (ASA)**: Normalized departure ($Z$-score) against multi-year seasonal calendar-week baselines.
2. **Spatial Price Dispersion (SPD)**: Coefficient of Variation ($CV = \sigma / \mu$) across production vs. consumption Mandis.
3. **Corridor Friction & Arbitrage**: Price spreads and transit stress across designated trade routes (e.g., *Nashik $\rightarrow$ Azadpur/Delhi*).

---

## 🏗️ Architecture & Deep Modules

Guided by `/codebase-design` and documented across 7 Architectural Decision Records in [`docs/adr/`](docs/adr/):

* **`Warehouse` (`src/warehouse.py`)**: Local SQLite warehouse running in WAL mode (`PRAGMA journal_mode=WAL;`), providing high-concurrency non-blocking reads for Datasette and zero-copy Polars queries for Marimo.
* **`MandiRegistry` (`src/registry.py`)**: Curated entity resolution module mapping raw messy APMC strings to canonical markets, official Local Government Directory (**LGD**) district codes, and geographic coordinates.
* **`VolatilityEngine` (`src/volatility.py`)**: Pure mathematical and statistical functions for seasonal $Z$-scores and spatial dispersion.
* **`IngestionEngine` & Adapters (`src/ingest.py`, `src/sources/`)**: Decoupled via the `CommoditySource` port, supporting both offline bootstrap (`BootstrapSeedAdapter`) and live `api.data.gov.in` syncing (`DataGovInAdapter`).

---

## 🚀 Quick Start

### 1. Requirements & Setup

Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
```

### 2. Bootstrap the Local Warehouse

Populate the database with canonical Mandis, verified LGD codes, and initial historical observations for Tomato, Onion, and Potato:
```powershell
python -m src.cli bootstrap
```
*Output: Creates `data/agri_engine.db` with WAL mode, seeds 3,200+ facts, and materializes 1,800+ corridor stress metrics.*

---

## 🖥️ Interactive Exploration

### A. Launch Reactive Marimo Notebook

Run the reactive modeling interface with dynamic lead-lag charts, spatial dispersion curves, and KPI gauges:
```powershell
marimo edit notebooks/volatility_engine.py
```
*(Or run in presentation app mode: `marimo run notebooks/volatility_engine.py`)*

### B. Launch Datasette Web Explorer

Start Datasette to browse tables, run ad-hoc SQL, and explore pre-configured canned queries:
```powershell
datasette serve data/agri_engine.db --metadata datasette/metadata.json --port 8001
```
Open [http://localhost:8001](http://localhost:8001) in your browser:
* **Active Supply-Chain Shocks**: Instant view of corridors with severe arrival slumps and price spreads.
* **National Commodity Overview**: Daily average modal prices and total arrival volumes.
* **Mandi Master Registry**: Inspect canonical markets, LGD district codes, and coordinates.

---

## ⚙️ CLI Operations

### View Active Supply-Chain Stress Alerts
```powershell
python -m src.cli alerts --limit 10
```

### Ingest Live Daily Data (data.gov.in)
To query live data from the official Open Government Data (OGD) platform:
1. Register for a free API key on the real portal: [https://www.data.gov.in/user/register](https://www.data.gov.in/user/register)
2. View the official catalog entry: [Current Daily Price of Various Commodities from Various Markets (Mandi)](https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi)
3. Set your API key and run the sync:
```powershell
$env:DATA_GOV_IN_API_KEY = "your_actual_key_here"
python -m src.cli sync --commodity onion
```

*(Note: `api.data.gov.in` is the machine REST gateway; `www.data.gov.in` is the user registration portal.)*

### Run Automated Tests
```powershell
python -m pytest tests/ -v
```

---

## 📖 Architectural Decision Records (ADRs)

* [ADR 0001: Bottom-up microdata roll-up](docs/adr/0001-hybrid-granularity-model.md)
* [ADR 0002: Tiered commodity ingestion architecture](docs/adr/0002-tiered-commodity-basket.md)
* [ADR 0003: Curated Mandi Master Registry for spatial entity resolution](docs/adr/0003-curated-mandi-master-registry.md)
* [ADR 0004: Shared SQLite in WAL mode for Datasette and Marimo](docs/adr/0004-shared-sqlite-wal-architecture.md)
* [ADR 0005: Dual-pillar volatility metrics](docs/adr/0005-dual-pillar-volatility-metrics.md)
* [ADR 0006: Hybrid bootstrap seed and live delta ingestion](docs/adr/0006-hybrid-bootstrap-and-live-delta-pipeline.md)
* [ADR 0007: Deep modules and port-adapter seam for commodity sources](docs/adr/0007-deep-modules-and-source-seams.md)
* [CONTEXT.md](CONTEXT.md): Project Ubiquitous Language & Domain Glossary
