import React from 'react';

/**
 * AttributionDrawer Component
 * Progressive disclosure component displaying "The Rupee Journey" and supply chain factors.
 */
export function AttributionDrawer({ commodity, mode }) {
  const journey = commodity.rupee_journey;
  if (!journey) return null;

  const isHousehold = mode === 'household';
  const total = journey.farmgate_rs_kg + journey.transit_fee_rs_kg + journey.retail_margin_rs_kg;
  const farmPct = Math.round((journey.farmgate_rs_kg / total) * 100);
  const transitPct = Math.round((journey.transit_fee_rs_kg / total) * 100);
  const retailPct = 100 - farmPct - transitPct;

  const displayTotal = isHousehold 
    ? `₹${total.toFixed(1)} / kg` 
    : `₹${Math.round(total * 100).toLocaleString('en-IN')} / qtl`;

  const farmgateDisplay = isHousehold
    ? `₹${journey.farmgate_rs_kg.toFixed(1)} / kg`
    : `₹${Math.round(journey.farmgate_rs_kg * 100).toLocaleString('en-IN')} / qtl`;

  const transitDisplay = isHousehold
    ? `₹${journey.transit_fee_rs_kg.toFixed(1)} / kg`
    : `₹${Math.round(journey.transit_fee_rs_kg * 100).toLocaleString('en-IN')} / qtl`;

  const retailDisplay = isHousehold
    ? `₹${journey.retail_margin_rs_kg.toFixed(1)} / kg`
    : `₹${Math.round(journey.retail_margin_rs_kg * 100).toLocaleString('en-IN')} / qtl`;

  return (
    <div className="attribution-drawer">
      {/* Price Breakdown */}
      <div className="rupee-journey-container">
        <div className="journey-title">
          <span>Where Your Money Goes ({isHousehold ? 'Per Kilogram' : 'Per Quintal'})</span>
          <span className="font-mono">{displayTotal}</span>
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.5rem', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
          Breakdown: Retail price = Mandi wholesale + Market cess + Freight + Retail margin
        </div>

        {/* Multi-segment stacked bar */}
        <div className="journey-bar-wrapper">
          <div className="journey-segment-farm" style={{ width: `${farmPct}%` }} title={`Wholesale: ${farmgateDisplay} (${farmPct}%)`} />
          <div className="journey-segment-transit" style={{ width: `${transitPct}%` }} title={`Transport & Cess: ${transitDisplay} (${transitPct}%)`} />
          <div className="journey-segment-retail" style={{ width: `${retailPct}%` }} title={`Retail Margin: ${retailDisplay} (${retailPct}%)`} />
        </div>

        {/* Legend */}
        <div className="journey-legend">
          <div className="journey-legend-item">
            <span className="journey-dot journey-segment-farm" />
            <span>Farmgate wholesale: {farmgateDisplay} ({farmPct}%)</span>
          </div>
          <div className="journey-legend-item">
            <span className="journey-dot journey-segment-transit" />
            <span>Transport & cess: {transitDisplay} ({transitPct}%)</span>
          </div>
          <div className="journey-legend-item">
            <span className="journey-dot journey-segment-retail" />
            <span>Retail margin: {retailDisplay} ({retailPct}%)</span>
          </div>
        </div>
      </div>

      {/* Origin Mandi & Statistical Volatility Context */}
      <div className="mandi-meta-box">
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Origin mandi</span>
          <strong style={{ color: 'var(--text-primary)' }}>{journey.origin_mandi}</strong>
        </div>
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Transport distance</span>
          <span className="font-mono">{journey.distance_km.toLocaleString('en-IN')} km</span>
        </div>
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>State mandi cess</span>
          <span className="font-mono" style={{ color: 'var(--status-fair-text)', fontWeight: 600 }}>
            {journey.statutory_cess_label || 'State APMC Gazetted (1.05% - 2.0%)'}
          </span>
        </div>
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Arrival volume trend</span>
          <span 
            className="font-mono" 
            style={{ 
              color: journey.arrival_z_score < -1.0 ? 'var(--status-shock-text)' : 'var(--status-fair-text)',
              fontWeight: 600
            }}
          >
            {journey.arrival_z_score > 0 ? `+${journey.arrival_z_score}` : journey.arrival_z_score}σ ({journey.arrival_z_score < -1.0 ? 'Low arrivals' : journey.arrival_z_score > 1.0 ? 'Heavy arrivals' : 'Normal'})
          </span>
        </div>
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Harvest season</span>
          <span>{journey.crop_season}</span>
        </div>
        <div style={{ marginTop: '0.35rem', paddingTop: '0.35rem', borderTop: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
          <span style={{ color: 'var(--text-muted)' }}>Weather note: </span>
          {journey.weather_context}
        </div>
      </div>
    </div>
  );
}
