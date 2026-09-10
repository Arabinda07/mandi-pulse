import marimo

__generated_with = "0.23.15"
app = marimo.App(width="full")


@app.cell
def __():
    import sys
    from pathlib import Path
    import altair as alt
    import marimo as mo
    import polars as pl

    # Ensure src is discoverable
    root_path = Path(__file__).resolve().parent.parent
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

    from src.calendar import get_commodity_calendar_context
    from src.registry import MandiRegistry
    from src.warehouse import Warehouse

    wh = Warehouse(root_path / "data" / "agri_engine.db")
    reg = MandiRegistry()
    return Path, MandiRegistry, Warehouse, alt, get_commodity_calendar_context, mo, pl, reg, root_path, sys, wh


@app.cell
def __(mo):
    mo.md(
        r"""
        # Mandi Pulse — Analytical Research Workbench
        ### Quantitative Modeling: Arrival Shock Anomalies (Z-Scores), Spatial Dispersion & Lead-Lag Signals
        *Note: This notebook is strictly for quantitative model validation. Consumer frontend presentation is decoupled to the React client.*
        """
    )
    return


@app.cell
def __(mo, wh):
    # Dynamically fetch available states from the warehouse
    available_states = ["All India"] + wh.get_available_states()

    state_dropdown = mo.ui.dropdown(
        options=available_states,
        value="All India",
        label="State / Region:",
    )

    commodity_dropdown = mo.ui.dropdown(
        options={
            "Onion": "Onion",
            "Tomato": "Tomato",
            "Potato": "Potato",
        },
        value="Onion",
        label="Commodity:",
    )

    corridor_dropdown = mo.ui.dropdown(
        options={
            "Lasalgaon (Nashik) -> Azadpur (Delhi) [Onion]": "mandi_lasalgaon->mandi_azadpur",
            "Lasalgaon (Nashik) -> Vashi (Navi Mumbai) [Onion]": "mandi_lasalgaon->mandi_vashi",
            "Solapur (MH) -> Kolkata (Koley Market) [Onion]": "mandi_solapur->mandi_kolkata",
            "Kolar (Karnataka) -> Azadpur (Delhi) [Tomato]": "mandi_kolar->mandi_azadpur",
            "Kolar (Karnataka) -> Bangalore (Yeshwanthpur) [Tomato]": "mandi_kolar->mandi_bangalore",
            "Madanapalle (AP) -> Azadpur (Delhi) [Tomato]": "mandi_madanapalle->mandi_azadpur",
            "Agra (UP) -> Azadpur (Delhi) [Potato]": "mandi_agra->mandi_azadpur",
            "Agra (UP) -> Kolkata (Koley Market) [Potato]": "mandi_agra->mandi_kolkata",
            "Farrukhabad (UP) -> Azadpur (Delhi) [Potato]": "mandi_farrukhabad->mandi_azadpur",
        },
        value="Lasalgaon (Nashik) -> Azadpur (Delhi) [Onion]",
        label="Corridor:",
    )

    lookback_slider = mo.ui.slider(
        start=30,
        stop=180,
        step=15,
        value=90,
        label="Lookback (Days):",
    )

    mo.vstack([
        mo.md("### 🔍 Model Controls"),
        mo.hstack([commodity_dropdown, state_dropdown, corridor_dropdown, lookback_slider], justify="start", gap=2),
    ])
    return (
        available_states,
        commodity_dropdown,
        corridor_dropdown,
        lookback_slider,
        state_dropdown,
    )


@app.cell
def __(commodity_dropdown, state_dropdown, wh):
    # Fetch live clean market prices for the selected commodity & state
    selected_comm = commodity_dropdown.value or "Onion"
    selected_st = state_dropdown.value or "All India"

    live_df = wh.get_live_mandi_prices(
        commodity=selected_comm,
        state=selected_st if selected_st != "All India" else None,
        limit=500,
    )
    return live_df, selected_comm, selected_st


@app.cell
def __(get_commodity_calendar_context, mo, selected_comm):
    from datetime import date
    ctx = get_commodity_calendar_context(selected_comm, date.today())

    season_badge = f"🌾 **Crop Season**: `{ctx['crop_season']}` ({ctx['supply_phase']})"
    trend_badge = f"📊 **Price Expectation**: `{ctx['base_price_trend']}`"
    summary_text = ctx["season_summary"]

    fest_items = []
    for f in ctx["active_festivals"][:3]:
        stat_badge = (
            "🔴 Active Now"
            if f["status"] == "ACTIVE"
            else (f"🟡 In {f['days_offset']} days" if f["status"] == "UPCOMING" else "🟢 Concluded")
        )
        fest_items.append(f"• **{f['name']}** ({stat_badge}) — {f['description']}")

    fest_text = "\n".join(fest_items) if fest_items else "• *No holiday demand anomalies active this week.*"

    mo.md(
        f"""
        ### 🗓️ Seasonal & Cultural Drivers: **{selected_comm}**
        {season_badge} &nbsp;|&nbsp; {trend_badge}

        *{summary_text}*

        **Demand Anomaly Context**:
        {fest_text}
        """
    )
    return


@app.cell
def __(live_df, mo, selected_comm, selected_st):
    if live_df.is_empty():
        kpi_display = mo.md(f"*No live records found for {selected_comm} in {selected_st}. Try selecting 'All India'.*")
    else:
        prices = live_df["wholesale_price_rs_qtl"].to_list()
        max_p = max(prices)
        min_p = min(prices)
        med_p = float(live_df["wholesale_price_rs_qtl"].median() or 0.0)
        spread = max_p - min_p
        mandis_count = live_df.height

        costliest_row = live_df.sort("wholesale_price_rs_qtl", descending=True).row(0, named=True)
        cheapest_row = live_df.sort("wholesale_price_rs_qtl", descending=False).row(0, named=True)

        kpi_display = mo.hstack([
            mo.stat(
                label=f"National Median ({selected_comm})",
                value=f"₹{med_p:,.0f} / qtl",
                caption=f"≈ ₹{med_p/100:.1f} / kg (wholesale base)",
            ),
            mo.stat(
                label="Highest Mandi Price",
                value=f"₹{max_p:,.0f} / qtl",
                caption=f"{costliest_row['mandi_name']} ({costliest_row['state']})",
            ),
            mo.stat(
                label="Lowest Mandi Price",
                value=f"₹{min_p:,.0f} / qtl",
                caption=f"{cheapest_row['mandi_name']} ({cheapest_row['state']})",
            ),
            mo.stat(
                label="Spatial Dispersion Spread",
                value=f"₹{spread:,.0f} / qtl",
                caption=f"Gap: ₹{spread/100:.1f} / kg",
            ),
            mo.stat(
                label="Reporting Mandis",
                value=f"{mandis_count} Markets",
                caption=f"Region: {selected_st}",
            ),
        ], justify="space-between", gap=1)

    mo.vstack([
        mo.md(f"### 📈 Summary Metrics: **{selected_comm}** in **{selected_st}**"),
        kpi_display,
    ])
    return (
        cheapest_row,
        costliest_row,
        kpi_display,
        mandis_count,
        max_p,
        med_p,
        min_p,
        prices,
        spread,
    )


@app.cell
def __(mo, selected_comm, wh):
    attr_df = wh.get_attribution_reports(commodity=selected_comm, limit=3)
    if attr_df.is_empty():
        attribution_card = mo.md("")
    else:
        cards = []
        for r in attr_df.iter_rows(named=True):
            cards.append(mo.md(
                f"""
                #### {r['headline']}
                **Market**: {r['mandi_name']} ({r['state']}) &nbsp;|&nbsp; **Wholesale**: ₹{r['price_rs_kg']:.1f}/kg ({r['change_pct']:+.1f}%)  
                *{r['explanation']}*  
                `Season: {r['crop_season']}` &nbsp;•&nbsp; `Context: {r['cultural_context']}`
                """
            ))
        attribution_card = mo.vstack([
            mo.md(f"### 💡 Attribution Evaluator: **{selected_comm}**"),
            mo.hstack(cards, justify="start", gap=2),
        ])
    attribution_card
    return (attribution_card,)


@app.cell
def __(alt, live_df, mo, selected_comm):
    if live_df.is_empty():
        state_chart = mo.md("")
    else:
        pdf = live_df.to_pandas()

        state_summary = (
            live_df.group_by("state")
            .agg([
                pl.col("wholesale_price_rs_qtl").mean().round(1).alias("avg_price"),
                pl.col("wholesale_price_rs_qtl").min().alias("min_price"),
                pl.col("wholesale_price_rs_qtl").max().alias("max_price"),
                pl.col("mandi_name").count().alias("market_count"),
            ])
            .sort("avg_price", descending=True)
            .to_pandas()
        )

        bar = (
            alt.Chart(state_summary)
            .mark_bar(color="#3182ce", cornerRadiusEnd=4)
            .encode(
                x=alt.X("avg_price:Q", title="Average Wholesale Price (₹ / Quintal)"),
                y=alt.Y("state:N", title="State", sort="-x"),
                tooltip=["state", "avg_price", "min_price", "max_price", "market_count"],
            )
        )

        error_bars = (
            alt.Chart(state_summary)
            .mark_rule(color="#e53e3e", strokeWidth=2)
            .encode(
                x=alt.X("min_price:Q"),
                x2=alt.X2("max_price:Q"),
                y=alt.Y("state:N", sort="-x"),
            )
        )

        combined_chart = (
            alt.layer(bar, error_bars)
            .properties(
                title=f"State-Wise Wholesale Price Comparison & Spread Range ({selected_comm})",
                width="container",
                height=max(220, len(state_summary) * 22),
            )
        )

        state_chart = mo.ui.altair_chart(combined_chart)

    mo.vstack([
        mo.md("### 🗺️ Spatial Dispersion Across States"),
        state_chart,
    ])
    return bar, combined_chart, error_bars, pdf, state_chart, state_summary


@app.cell
def __(
    commodity_dropdown,
    corridor_dropdown,
    lookback_slider,
    wh,
):
    raw_corridor = corridor_dropdown.value or "mandi_lasalgaon->mandi_azadpur"
    if "->" in raw_corridor:
        origin_id, term_id = raw_corridor.split("->", 1)
    else:
        origin_id, term_id = "mandi_lasalgaon", "mandi_azadpur"

    comm_id = (commodity_dropdown.value or "Onion").lower()

    corridor_raw = wh.get_corridor_timeseries(comm_id, origin_id, term_id)
    if not corridor_raw.is_empty():
        sorted_c = corridor_raw.sort("reported_date", descending=False)
        tail_len = min(sorted_c.height, lookback_slider.value)
        corridor_df = sorted_c.tail(tail_len)
    else:
        corridor_df = corridor_raw

    dispersion_df = wh.get_spatial_dispersion_timeseries(comm_id)
    return (
        comm_id,
        corridor_df,
        corridor_raw,
        dispersion_df,
        origin_id,
        raw_corridor,
        sorted_c,
        tail_len,
        term_id,
    )


@app.cell
def __(alt, corridor_df, mo):
    if corridor_df.is_empty():
        lead_lag_view = mo.md("*Insufficient corridor observations to plot lead-lag series.*")
    else:
        c_pdf = corridor_df.to_pandas()
        base = alt.Chart(c_pdf).encode(x=alt.X("reported_date:T", title="Reported Date"))

        arrival_chart = base.mark_area(
            opacity=0.30,
            color="#2b6cb0",
        ).encode(
            y=alt.Y("origin_arrival:Q", title="Farmgate Inflow Volume (Tonnes)"),
            tooltip=["reported_date", "origin_arrival"],
        )

        terminal_price_chart = base.mark_line(
            color="#c53030",
            strokeWidth=2.8,
        ).encode(
            y=alt.Y("terminal_price:Q", title="Terminal Modal Price (₹/quintal)"),
            tooltip=["reported_date", "terminal_price", "price_spread", "spread_pct"],
        )

        lead_lag_combined = (
            alt.layer(arrival_chart, terminal_price_chart)
            .resolve_scale(y="independent")
            .properties(
                title="Lead-Lag Dynamics: Farmgate Arrival Slump Preceding Terminal Price Spikes",
                width="container",
                height=320,
            )
        )

        lead_lag_view = mo.ui.altair_chart(lead_lag_combined)

    mo.vstack([
        mo.md("### ⚡ Strategic Corridor Lead-Lag Analysis"),
        lead_lag_view,
    ])
    return (
        arrival_chart,
        base,
        c_pdf,
        lead_lag_combined,
        lead_lag_view,
        terminal_price_chart,
    )


@app.cell
def __(live_df, mo):
    mo.md("### 📋 Warehouse Observation Records")
    if live_df.is_empty():
        table_out = mo.md("*No records.*")
    else:
        display_cols = [
            "reported_date",
            "commodity",
            "state",
            "district",
            "mandi_name",
            "wholesale_price_rs_qtl",
            "retail_equivalent_rs_kg",
            "min_price_rs_qtl",
            "max_price_rs_qtl",
            "intraday_spread_rs_qtl",
        ]
        clean_view = live_df.select([c for c in display_cols if c in live_df.columns]).to_pandas()
        clean_view.rename(
            columns={
                "reported_date": "Date",
                "commodity": "Commodity",
                "state": "State",
                "district": "District",
                "mandi_name": "Mandi Market",
                "wholesale_price_rs_qtl": "Wholesale Modal (₹/qtl)",
                "retail_equivalent_rs_kg": "Retail Base (₹/kg)",
                "min_price_rs_qtl": "Min (₹/qtl)",
                "max_price_rs_qtl": "Max (₹/qtl)",
                "intraday_spread_rs_qtl": "Spread (₹)",
            },
            inplace=True,
        )
        table_out = mo.ui.table(clean_view, pagination=True, page_size=15)

    table_out
    return clean_view, display_cols, table_out


if __name__ == "__main__":
    app.run()
