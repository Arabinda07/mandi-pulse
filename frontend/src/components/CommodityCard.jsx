import React, { useState } from 'react';
import { GroundTruthBadge } from './GroundTruthBadge';
import { AttributionDrawer } from './AttributionDrawer';

/**
 * CommodityCard Component
 * Displays benchmark prices, volatility signals, shopping advice, and expandable attribution.
 */
export function CommodityCard({ commodity, mode }) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Price formatting based on active mode
  const isHousehold = mode === 'household';
  const displayPrice = isHousehold 
    ? `₹${commodity.retail_equivalent_rs_kg.toFixed(1)}` 
    : `₹${commodity.wholesale_price_rs_qtl.toLocaleString('en-IN')}`;
  const displayUnit = isHousehold ? '/ kg' : '/ qtl';

  // Delta formatting
  const deltaText = commodity.day_change_rs > 0
    ? `+₹${commodity.day_change_rs.toFixed(2)}`
    : commodity.day_change_rs < 0
    ? `-₹${Math.abs(commodity.day_change_rs).toFixed(2)}`
    : '±₹0.00';

  const deltaClass = commodity.day_change_rs > 0 ? 'up' : commodity.day_change_rs < 0 ? 'down' : 'neutral';

  return (
    <article className="commodity-card" aria-label={`${commodity.name} price card`}>
      <div>
        {/* Card Header: Icon, Name, Variety, Status */}
        <div className="commodity-card-header">
          <div className="commodity-name-group">
            <div className="commodity-icon-box" aria-hidden="true">
              {commodity.icon}
            </div>
            <div>
              <h2 className="commodity-title">{commodity.name}</h2>
              <div className="commodity-variety">{commodity.variety}</div>
            </div>
          </div>

          <div className={`status-pill ${commodity.status}`}>
            <span style={{ fontSize: '0.65rem' }}>●</span>
            <span>{commodity.status_label}</span>
          </div>
        </div>

        {/* Benchmark Price Section */}
        <div className="price-display-section">
          <div className="price-row">
            <span className="benchmark-price numeric-data">{displayPrice}</span>
            <span className="price-unit">{displayUnit}</span>
          </div>

          <div className="price-submeta">
            <span className={`price-delta ${deltaClass} price-delta`}>
              {deltaText} vs yday
            </span>
            <span className="trend-pill">
              {commodity.trend_signal}
            </span>
          </div>
        </div>

        {/* Actionable Shopping Advice */}
        <div className="shopping-advice">
          <strong>Advisor: </strong>
          {commodity.advice}
        </div>
      </div>

      {/* Footer / Transparency & Attribution Action */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <GroundTruthBadge type={commodity.retail_provenance || 'empirical_dca'} />
          <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>

            LGD Verified APMC
          </span>
        </div>

        <button 
          type="button"
          className="attribution-trigger-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          <span>{isExpanded ? 'Hide supply chain attribution' : 'Why is this price moving?'}</span>
          <span style={{ fontSize: '0.85rem' }}>{isExpanded ? '▴' : '▾'}</span>
        </button>

        {isExpanded && <AttributionDrawer commodity={commodity} mode={mode} />}
      </div>
    </article>
  );
}
