/**
 * Mandi Pulse - Rule-Based NLG Shopping Advice & Market Verdict Generator
 * Synthesizes origin arrival shock (ASA Z-scores), weather flags from Open-Meteo,
 * and DoD/WoW price velocity into consumer-facing household buying recommendations.
 */

export function generateShoppingAdvice({
  commodity,
  terminalName,
  priceTodayRsKg,
  dayChangeRsKg = 0.0,
  weekChangePct = 0.0,
  originName = null,
  originArrivalShockZ = 0.0,
  weatherFlag = null,
}) {
  const comm = commodity ? commodity.charAt(0).toUpperCase() + commodity.slice(1) : 'Vegetable';
  const defaultOrigin = comm.toLowerCase() === 'onion' ? 'Lasalgaon' : comm.toLowerCase() === 'tomato' ? 'Kolar' : 'Farrukhabad';
  const origin = originName || defaultOrigin;

  let status = 'fair';
  let statusLabel = 'Fair Price';
  let trendSignal = '⚪ Steady price';
  let trendStatus = 'stable';
  let advice = '';
  let weatherContext = `Normal harvest weather and steady shipments from ${origin}.`;

  // 1. Severe Supply Contraction (Shock)
  if (originArrivalShockZ <= -1.5 || (weatherFlag && (weatherFlag.includes('Rain') || weatherFlag.includes('Inundation')))) {
    status = 'shock';
    statusLabel = 'Price Spike';
    trendSignal = '🔴 Rising in ~10 days';
    trendStatus = 'spike';

    if (weatherFlag && (weatherFlag.includes('Rain') || weatherFlag.includes('Inundation'))) {
      advice = `${weatherFlag} around ${origin} slowed arrivals. Wholesale prices rose ₹${Math.abs(dayChangeRsKg).toFixed(2)}/kg. Consider buying a few extra days of staples before retail markups peak.`;
      weatherContext = `${weatherFlag} reported across ${origin} growing areas.`;
    } else {
      advice = `Arrivals from ${origin} dropped sharply. Wholesale prices moved by ₹${dayChangeRsKg > 0 ? '+' : ''}${dayChangeRsKg.toFixed(2)}/kg. Buy your weekly supply early before prices rise.`;
      weatherContext = `Fewer trucks arriving at ${origin} yards.`;
    }
  }
  // 2. Moderate Pressure / Elevated Margin (Warning)
  else if (originArrivalShockZ <= -0.8 || weekChangePct >= 5.0 || dayChangeRsKg >= 1.5) {
    status = 'warning';
    statusLabel = 'High Margin';
    trendSignal = '🔴 Rising in ~10 days';
    trendStatus = 'spike';
    advice = `Arrivals from ${origin} are down and prices rose ${weekChangePct > 0 ? '+' : ''}${weekChangePct.toFixed(1)}% this week. Buying full crates directly saves on retail markups.`;
    weatherContext = `Slight shipping delays from ${origin}.`;
  }
  // 3. Supply Glut / Favorable Cooling Market (Fair / Cooling)
  else if (originArrivalShockZ >= 0.8 || weekChangePct <= -5.0 || dayChangeRsKg <= -1.5) {
    status = 'fair';
    statusLabel = 'Fair Price';
    trendSignal = '🟢 Falling in ~7 days';
    trendStatus = 'cooling';
    advice = `Supplies from ${origin} are strong and prices dropped ₹${Math.abs(dayChangeRsKg).toFixed(2)}/kg yesterday. Good time to buy as needed.`;
    weatherContext = `Clear roads and good harvest conditions across ${origin}.`;
  }
  // 4. Seasonal Equilibrium / Stable Corridor (Fair / Stable)
  else {
    status = 'fair';
    statusLabel = 'Fair Price';
    trendSignal = '⚪ Steady price';
    trendStatus = 'stable';
    advice = `Steady daily arrivals from ${origin} are keeping prices in ${terminalName} stable.`;
    weatherContext = `Normal harvest weather and steady shipments from ${origin}.`;
  }

  return {
    advice,
    status,
    statusLabel,
    trendSignal,
    trendStatus,
    weatherContext,
  };
}

export function generateBasketVerdict(commodities = [], weeklyTotalRs = 0.0, weekChangePct = 0.0) {
  const shocks = commodities.filter((c) => c.status === 'shock');
  const warnings = commodities.filter((c) => c.status === 'warning');
  const cooling = commodities.filter((c) => c.trend_status === 'cooling');

  let verdict = '';
  let verdictStatus = 'fair';

  if (shocks.length > 0) {
    const spikingNames = shocks.map((s) => s.name).join(' & ');
    const origins = [...new Set(shocks.map((s) => s.rupee_journey?.origin_mandi || 'key farmgate hubs'))].join(' and ');
    verdict = `Basket cost is up this week due to lower ${spikingNames} arrivals from ${origins}.`;
    verdictStatus = 'shock';
  } else if (warnings.length > 0) {
    const warnNames = warnings.map((w) => w.name).join(' & ');
    verdict = `Prices rose on ${warnNames} this week (+${Math.abs(weekChangePct).toFixed(1)}%), while other staples remained steady.`;
    verdictStatus = 'warning';
  } else if (cooling.length > 0) {
    const coolNames = cooling.map((c) => c.name).join(' & ');
    verdict = `Basket costs dropped this week as ${coolNames} supplies improved.`;
    verdictStatus = 'fair';
  } else {
    verdict = `Basket costs are steady at ₹${weeklyTotalRs.toFixed(1)} per week with normal seasonal supply.`;
    verdictStatus = 'fair';
  }

  return {
    verdict,
    verdict_status: verdictStatus,
  };
}
