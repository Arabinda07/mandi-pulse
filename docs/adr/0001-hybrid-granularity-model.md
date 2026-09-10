# 1. Bottom-up microdata roll-up for food inflation

We need to track food inflation and supply-chain volatility. We decided to make the daily Mandi-Commodity arrival and price record the atomic unit of the engine, aggregating it upwards into regional and national price indices, rather than ingesting top-down macro CPI series alone. While this increases data ingestion and storage volume by several orders of magnitude, Mandi arrival drops and wholesale price spikes precede consumer retail price inflation by 2 to 4 weeks, making raw microdata essential for lead-indicator modeling.
