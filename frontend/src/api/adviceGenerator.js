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
  let trendSignal = '⚪ Stable Corridor';
  let trendStatus = 'stable';
  let advice = '';
  let weatherContext = `Normal seasonal climate and steady dispatches across ${origin} agricultural belt.`;

  // 1. Severe Supply Contraction (Shock)
  if (originArrivalShockZ <= -1.5 || (weatherFlag && (weatherFlag.includes('Rain') || weatherFlag.includes('Inundation')))) {
    status = 'shock';
    statusLabel = 'Severe Spike';
    trendSignal = '🔴 Spike in ~10d';
    trendStatus = 'spike';

    if (weatherFlag && (weatherFlag.includes('Rain') || weatherFlag.includes('Inundation'))) {
      advice = `${weatherFlag} in ${origin} farming belt disrupted arrivals (ASA ${originArrivalShockZ > 0 ? '+' : ''}${originArrivalShockZ.toFixed(2)}σ). Wholesale prices up ₹${Math.abs(dayChangeRsKg).toFixed(2)}/kg—buy 3-5 day weekly buffer before retail markups peak.`;
      weatherContext = `${weatherFlag} recorded across ${origin} producing basin.`;
    } else {
      advice = `${origin} arrivals contracted sharply (${originArrivalShockZ > 0 ? '+' : ''}${originArrivalShockZ.toFixed(2)}σ shock). Daily wholesale moved by ₹${dayChangeRsKg > 0 ? '+' : ''}${dayChangeRsKg.toFixed(2)}/kg—stock weekly cooking essentials early.`;
      weatherContext = `Arrival contraction at ${origin} dispatch yards.`;
    }
  }
  // 2. Moderate Pressure / Elevated Margin (Warning)
  else if (originArrivalShockZ <= -0.8 || weekChangePct >= 5.0 || dayChangeRsKg >= 1.5) {
    status = 'warning';
    statusLabel = 'Elevated Margin';
    trendSignal = '🔴 Spike in ~10d';
    trendStatus = 'spike';
    advice = `${comm} arrivals from ${origin} down ${Math.abs(originArrivalShockZ).toFixed(1)}σ with prices up ${weekChangePct > 0 ? '+' : ''}${weekChangePct.toFixed(1)}% WoW. Consider purchasing bulk crate lots to bypass intermediary retail markups.`;
    weatherContext = `Moderate dispatch variability in ${origin}; transit corridors experiencing slight friction.`;
  }
  // 3. Supply Glut / Favorable Cooling Market (Fair / Cooling)
  else if (originArrivalShockZ >= 0.8 || weekChangePct <= -5.0 || dayChangeRsKg <= -1.5) {
    status = 'fair';
    statusLabel = 'Fair Price';
    trendSignal = '🟢 Cooling Down in ~7d';
    trendStatus = 'cooling';
    advice = `Abundant arrivals flowing smoothly from ${origin} (DoD ₹${dayChangeRsKg > 0 ? '+' : ''}${dayChangeRsKg.toFixed(2)}/kg). Favorable market conditions—buy only what you need for daily consumption.`;
    weatherContext = `Favorable harvest conditions and clear highway transit across ${origin} belt.`;
  }
  // 4. Seasonal Equilibrium / Stable Corridor (Fair / Stable)
  else {
    status = 'fair';
    statusLabel = 'Fair Price';
    trendSignal = '⚪ Stable Corridor';
    trendStatus = 'stable';
    advice = `Steady daily arrivals from ${origin} maintaining normal price equilibrium in ${terminalName} (${weekChangePct > 0 ? '+' : ''}${weekChangePct.toFixed(1)}% WoW). Stable cooking budget.`;
    weatherContext = `Normal seasonal climate and steady dispatches across ${origin} agricultural belt.`;
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
    verdict = `Vegetable basket elevated due to ${spikingNames} supply contraction at ${origins}.`;
    verdictStatus = 'shock';
  } else if (warnings.length > 0) {
    const warnNames = warnings.map((w) => w.name).join(' & ');
    verdict = `Moderate upward pressure on ${warnNames} (${weekChangePct > 0 ? '+' : ''}${weekChangePct.toFixed(1)}% WoW); stable supplies on remaining staples.`;
    verdictStatus = 'warning';
  } else if (cooling.length > 0) {
    const coolNames = cooling.map((c) => c.name).join(' & ');
    verdict = `Kitchen basket easing across ${coolNames} (${weekChangePct > 0 ? '+' : ''}${weekChangePct.toFixed(1)}% WoW); prices favorable for household staples.`;
    verdictStatus = 'fair';
  } else {
    verdict = `Kitchen basket steady at ₹${weeklyTotalRs.toFixed(1)}/week; all strategic supply corridors operating in normal seasonal equilibrium.`;
    verdictStatus = 'fair';
  }

  return {
    verdict,
    verdict_status: verdictStatus,
  };
}
