import React from 'react';

/**
 * AttributionDrawer Component
 * Progressive disclosure component displaying "The Rupee Journey" and supply chain factors.
 */
export function AttributionDrawer({ commodity, mode }) {
  const journey = commodity.rupee_journey;
  if (!journey) return null;

  const total = journey.farmgate_rs_kg + journey.transit_fee_rs_kg + journey.retail_margin_rs_kg;
  const farmPct = Math.round((journey.farmgate_rs_kg / total) * 100);
  const transitPct = Math.round((journey.transit_fee_rs_kg / total) * 100);
  const retailPct = 100 - farmPct - transitPct;

  return (
    <div className="attribution-drawer">
      {/* The Rupee Journey */}
      <div className="rupee-journey-container">
        <div className="journey-title">
          <span>The Rupee Journey (Cost Flow)</span>
          <span className="font-mono">₹{total.toFixed(1)} / kg</span>
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.5rem', fontFamily: 'var(--font-mono)' }}>
          Exact Formula: Retail Spread = DCA Retail − (Agmarknet Wholesale + Statutory Cess + Freight)
        </div>

        {/* Multi-segment stacked bar */}
        <div className="journey-bar-wrapper">
          <div className="journey-segment-farm" style={{ width: `${farmPct}%` }} title={`Farmgate: ₹${journey.farmgate_rs_kg} (${farmPct}%)`} />
          <div className="journey-segment-transit" style={{ width: `${transitPct}%` }} title={`Transit & Fees: ₹${journey.transit_fee_rs_kg} (${transitPct}%)`} />
          <div className="journey-segment-retail" style={{ width: `${retailPct}%` }} title={`Retail Spread: ₹${journey.retail_margin_rs_kg} (${retailPct}%)`} />
        </div>

        {/* Legend */}
        <div className="journey-legend">
          <div className="journey-legend-item">
            <span className="journey-dot journey-segment-farm" />
            <span>Wholesale: ₹{journey.farmgate_rs_kg.toFixed(1)} ({farmPct}%)</span>
          </div>
          <div className="journey-legend-item">
            <span className="journey-dot journey-segment-transit" />
            <span>Logistics & APMC Cess: ₹{journey.transit_fee_rs_kg.toFixed(1)} ({transitPct}%)</span>
          </div>
          <div className="journey-legend-item">
            <span className="journey-dot journey-segment-retail" />
            <span>Net Retail Spread: ₹{journey.retail_margin_rs_kg.toFixed(1)} ({retailPct}%)</span>
          </div>
        </div>
      </div>

      {/* Origin Mandi & Statistical Volatility Context */}
      <div className="mandi-meta-box">
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Origin APMC Mandi</span>
          <strong style={{ color: 'var(--text-primary)' }}>{journey.origin_mandi}</strong>
        </div>
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Transit Corridor</span>
          <span className="font-mono">{journey.distance_km} km freight distance</span>
        </div>
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Statutory State Mandi Cess</span>
          <span className="font-mono" style={{ color: 'var(--status-fair-text)', fontWeight: 600 }}>
            {journey.statutory_cess_label || 'State APMC Gazetted (1.05% - 2.0%)'}
          </span>
        </div>
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Arrival Shock (ASA)</span>
          <span 
            className="font-mono" 
            style={{ 
              color: journey.arrival_z_score < -1.0 ? 'var(--status-shock-text)' : 'var(--status-fair-text)',
              fontWeight: 600
            }}
          >
            {journey.arrival_z_score > 0 ? `+${journey.arrival_z_score}` : journey.arrival_z_score}σ (Z-Score)
          </span>
        </div>
        <div className="mandi-meta-row">
          <span style={{ color: 'var(--text-muted)' }}>Crop Cycle</span>
          <span>{journey.crop_season}</span>
        </div>
        <div style={{ marginTop: '0.35rem', paddingTop: '0.35rem', borderTop: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
          <span style={{ color: 'var(--text-muted)' }}>Weather & Farmgate Alert: </span>
          {journey.weather_context}
        </div>
      </div>
    </div>
  );
}
