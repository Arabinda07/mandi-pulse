# Food Inflation & Supply-Chain Volatility Engine

A system for ingesting high-frequency wholesale and retail agricultural market data to detect localized supply-chain shocks and model lead indicators for headline food inflation.

## Language

**Mandi**:
A designated wholesale agricultural market yard operating under state APMC regulations where farmers auction produce to registered traders.
_Avoid_: Market, wholesale bazaar, yard

**Arrival**:
The physical volume of a specific commodity batch entering a Mandi on a reported date, typically recorded in quintals or metric tonnes.
_Avoid_: Supply, volume, shipment, influx

**Modal Price**:
The most frequent wholesale transaction price observed for a commodity batch in a Mandi on a trading day.
_Avoid_: Average price, median price, market rate

**Retail Spread**:
The price gap between the urban consumer retail price and the origin Mandi wholesale Modal Price for an identical commodity.
_Avoid_: Margin, markup, middleman cut

**Volatility Index**:
A statistical measure of localized price dispersion and arrival variance across Mandis within a defined spatial corridor.
_Avoid_: Risk score, price swing, instability metric

**Tier 1 Basket**:
The designated set of high-impact essential commodities (e.g., tomato, onion, potato, key pulses, and cereals) tracked daily with continuous historical backfills.
_Avoid_: Core list, priority crops, primary basket

**Tier 2 Basket**:
The broader agricultural catalog of secondary or niche commodities ingested on-demand or as periodic snapshot archives.
_Avoid_: Secondary crops, peripheral list, long-tail data

**Mandi Registry**:
The canonical dimension table mapping raw APMC market identifiers and aliases to standardized names, official administrative codes, and geographic coordinates.
_Avoid_: Market master, APMC list, location directory

**LGD Code**:
The official unique integer identifier assigned to an administrative unit (State, District, Sub-district) by the Ministry of Panchayati Raj's Local Government Directory.
_Avoid_: Census code, postal code, district ID

**Warehouse**:
The unified local SQLite database running in Write-Ahead Logging (WAL) mode that acts as the single source of truth for pipeline writes, Datasette exploration, and Marimo computations.
_Avoid_: Data lake, database cluster, central store

**Arrival Shock Anomaly**:
The standardized deviation of current weekly commodity arrival volume against historical multi-year seasonal baselines for that calendar week.
_Avoid_: Supply drop, volume slump, arrival deficit

**Spatial Price Dispersion**:
The coefficient of variation of wholesale Modal Prices across Mandis within a production-consumption corridor on a given trading day.
_Avoid_: Price variance, geographic spread, inter-mandi gap

**Bootstrap Seed**:
A pre-curated reference slice of master entities, geographic coordinates, and historical market observations used to immediately populate the Warehouse prior to live ingestion.
_Avoid_: Dummy data, sample records, mock dataset

**Commodity Source**:
An adapter satisfying the ingestion port to retrieve daily wholesale arrival and price observations from either local archives or remote APIs.
_Avoid_: Data fetcher, downloader, crawler
