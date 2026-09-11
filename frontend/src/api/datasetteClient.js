/**
 * Mandi Pulse - Datasette Headless API Client & Fallback Engine
 * Consumes SQLite WAL views served over Datasette REST API on :8001
 * Gracefully falls back to offline reference data if backend is not running.
 */

import { METRO_HUBS, REFERENCE_MARKET_DATA } from './fallbackData';
import { generateShoppingAdvice, generateBasketVerdict } from './adviceGenerator';

const METRO_MANDI_IDS = {
  delhi: 'mandi_azadpur',
  mumbai: 'mandi_vashi',
  bengaluru: 'mandi_bangalore',
  kolkata: 'mandi_kolkata',
  chennai: 'mandi_chennai',
};

export async function fetchMarketData(metroId = 'delhi') {
  const fallback = REFERENCE_MARKET_DATA[metroId] || REFERENCE_MARKET_DATA['delhi'];
  const targetMandiId = METRO_MANDI_IDS[metroId] || 'mandi_azadpur';

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2.0s timeout

    // Query specifically for the target terminal mandi
    let response = await fetch(`/agri_engine/v_live_mandi_prices.json?_shape=objects&mandi_id=${targetMandiId}&_size=30`, {
      signal: controller.signal,
      headers: { 'Accept': 'application/json' },
    });

    if (!response.ok) {
      // Fallback query without mandi_id filter
      response = await fetch('/agri_engine/v_live_mandi_prices.json?_shape=objects&_size=100', {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' },
      });
    }
    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        data: fallback,
        isLiveBackend: false,
        sourceLabel: 'Sample Data (Offline)',
      };
    }

    const json = await response.json();
    const rows = json.rows || [];

    if (rows.length === 0) {
      return {
        data: fallback,
        isLiveBackend: false,
        sourceLabel: 'Sample Data (Empty DB)',
      };
    }

    // Enrich commodities with empirical DCA retail benchmarks, wholesale prices, deltas, and corridor links
    const enrichedCommodities = fallback.commodities.map((comm) => {
      const match = rows.find(
        (r) =>
          r.commodity &&
          r.commodity.toLowerCase() === comm.id.toLowerCase()
      );
      if (match) {
        const wholesaleQtl = match.wholesale_price_rs_qtl || comm.wholesale_price_rs_qtl;
        const retailKg = match.retail_equivalent_rs_kg || comm.retail_equivalent_rs_kg;
        const packageSize = comm.package_size_kg || 20;
        const crateRate = Math.round((wholesaleQtl / 100) * packageSize);
        const retailBox = Math.round(retailKg * packageSize);
        const cessRsKg = match.statutory_cess_rs_kg !== undefined ? match.statutory_cess_rs_kg : (comm.rupee_journey?.statutory_cess_rs_kg || 0.5);

        // Exact Haversine distance between origin producing basin and destination terminal mandi
        let distanceKm = comm.rupee_journey?.distance_km || 400;
        if (match.latitude && match.longitude && match.origin_latitude && match.origin_longitude) {
          const lat1 = match.latitude * (Math.PI / 180);
          const lon1 = match.longitude * (Math.PI / 180);
          const lat2 = match.origin_latitude * (Math.PI / 180);
          const lon2 = match.origin_longitude * (Math.PI / 180);
          const dlat = lat2 - lat1;
          const dlon = lon2 - lon1;
          const a = Math.sin(dlat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon / 2) ** 2;
          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
          distanceKm = Math.round(6371 * c);
        }

        const updatedJourney = comm.rupee_journey ? {
          ...comm.rupee_journey,
          origin_mandi: match.origin_mandi_name || comm.rupee_journey.origin_mandi,
          distance_km: distanceKm,
          arrival_z_score: match.origin_arrival_shock_z !== undefined ? match.origin_arrival_shock_z : comm.rupee_journey.arrival_z_score,
          farmgate_rs_kg: match.origin_modal_price_rs_kg ?? Math.round((wholesaleQtl / 100) * 10) / 10,
          statutory_cess_pct: match.mandi_cess_pct ?? comm.rupee_journey.statutory_cess_pct,
          statutory_cess_rs_kg: cessRsKg,
          retail_margin_rs_kg: match.retail_spread_rs_kg ?? comm.rupee_journey.retail_margin_rs_kg,
          corridor_stress_level: match.corridor_stress_level || 'NORMAL',
        } : null;

        // Generate deterministic household shopping advice using live facts
        const nlgAdvice = generateShoppingAdvice({
          commodity: comm.id,
          terminalName: fallback.terminal_mandi,
          priceTodayRsKg: retailKg,
          dayChangeRsKg: match.day_change_rs ?? comm.day_change_rs ?? 0.0,
          weekChangePct: match.week_change_pct ?? comm.week_change_pct ?? 0.0,
          originName: match.origin_mandi_name || comm.rupee_journey?.origin_mandi,
          originArrivalShockZ: match.origin_arrival_shock_z !== undefined ? match.origin_arrival_shock_z : (comm.rupee_journey?.arrival_z_score || 0.0),
          weatherFlag: null,
        });

        if (updatedJourney && nlgAdvice.weatherContext) {
          updatedJourney.weather_context = nlgAdvice.weatherContext;
        }

        return {
          ...comm,
          wholesale_price_rs_qtl: wholesaleQtl,
          retail_equivalent_rs_kg: retailKg,
          retail_provenance: match.retail_provenance || 'empirical_dca',
          day_change_rs: match.day_change_rs !== undefined ? match.day_change_rs : comm.day_change_rs,
          day_change_pct: match.day_change_pct !== undefined ? match.day_change_pct : comm.day_change_pct,
          week_change_pct: match.week_change_pct !== undefined ? match.week_change_pct : comm.week_change_pct,
          trend_signal: nlgAdvice.trendSignal || match.trend_signal || comm.trend_signal,
          trend_status: nlgAdvice.trendStatus,
          status: nlgAdvice.status,
          status_label: nlgAdvice.statusLabel,
          advice: nlgAdvice.advice,
          crate_rate_rs: crateRate,
          retail_box_equivalent_rs: retailBox,
          bulk_savings_rs: Math.max(0, retailBox - crateRate),
          bulk_savings_pct: retailBox > 0 ? Math.round(((retailBox - crateRate) / retailBox) * 100) : comm.bulk_savings_pct,
          rupee_journey: updatedJourney || comm.rupee_journey,
        };
      }
      return {
        ...comm,
        retail_provenance: comm.retail_provenance || 'empirical_dca',
      };
    });

    // Recompute consolidated weekly kitchen basket total: 1kg Tomato + 2kg Onion + 2kg Potato
    let weeklyTotalRs = 0;
    enrichedCommodities.forEach((c) => {
      const kg = c.id === 'tomato' ? 1.0 : 2.0;
      weeklyTotalRs += c.retail_equivalent_rs_kg * kg;
    });
    weeklyTotalRs = Math.round(weeklyTotalRs * 10) / 10;

    // Weighted week-over-week change % across standard basket
    const totalWeightKg = 5.0; // 1kg + 2kg + 2kg
    let weightedWoWPct = 0;
    enrichedCommodities.forEach((c) => {
      const kg = c.id === 'tomato' ? 1.0 : 2.0;
      weightedWoWPct += (c.week_change_pct || 0) * (kg / totalWeightKg);
    });
    weightedWoWPct = Math.round(weightedWoWPct * 10) / 10;

    const basketVerdict = generateBasketVerdict(enrichedCommodities, weeklyTotalRs, weightedWoWPct);

    const updatedBasketHero = {
      ...fallback.basket_hero,
      weekly_total_rs: weeklyTotalRs,
      week_change_pct: weightedWoWPct,
      verdict: basketVerdict.verdict,
      verdict_status: basketVerdict.verdict_status,
    };

    return {
      data: {
        ...fallback,
        basket_hero: updatedBasketHero,
        commodities: enrichedCommodities,
      },
      isLiveBackend: true,
      sourceLabel: 'Live Agmarknet & DCA Data',
    };

  } catch (err) {
    // Graceful offline fallback
    return {
      data: fallback,
      isLiveBackend: false,
      sourceLabel: 'Sample Data (Offline)',
    };
  }
}
