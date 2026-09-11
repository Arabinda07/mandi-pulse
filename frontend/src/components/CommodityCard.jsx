import React, { useState } from 'react';
import { GroundTruthBadge } from './GroundTruthBadge';
import { AttributionDrawer } from './AttributionDrawer';
import { CommodityVectorIcon, AdvisorIcon } from './Icons';

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

  // Delta formatting based on mode
  const deltaValue = isHousehold ? commodity.day_change_rs : (commodity.day_change_rs * 100);
  const deltaUnit = isHousehold ? '/kg' : '/qtl';
  const deltaSign = deltaValue > 0 ? '+' : deltaValue < 0 ? '-' : '';
  const deltaNumber = isHousehold 
    ? Math.abs(deltaValue).toFixed(2) 
    : Math.round(Math.abs(deltaValue)).toLocaleString('en-IN');
  
  const pctText = commodity.day_change_pct !== undefined
    ? ` (${commodity.day_change_pct > 0 ? '+' : ''}${commodity.day_change_pct.toFixed(1)}%)`
    : '';

  const deltaText = deltaValue !== 0 
    ? `${deltaSign}₹${deltaNumber} ${deltaUnit}${pctText}` 
    : `±₹0.00 ${deltaUnit}`;

  const deltaClass = deltaValue > 0 ? 'up' : deltaValue < 0 ? 'down' : 'neutral';
  const drawerId = `attribution-drawer-${commodity.id}`;

  return (
    <article className="commodity-card" aria-label={`${commodity.name} price card`}>
      <div>
        {/* Card Header: Icon, Name, Variety, Status */}
        <div className="commodity-card-header">
          <div className="commodity-name-group">
            <div className="commodity-icon-box" aria-hidden="true">
              <CommodityVectorIcon id={commodity.id} fallback={commodity.icon} size={24} />
            </div>
            <div>
              <h3 className="commodity-title">{commodity.name}</h3>
              <div className="commodity-variety">{commodity.variety}</div>
            </div>
          </div>

          <div className={`status-pill ${commodity.status}`}>
            <span className="status-pill-dot" aria-hidden="true" />
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
              {deltaText} vs yesterday
            </span>
            <span className="trend-pill">
              {commodity.trend_signal}
            </span>
          </div>
        </div>

        {/* Actionable Shopping Advice */}
        <div className="shopping-advice">
          <span className="shopping-advice-icon" aria-hidden="true">
            <AdvisorIcon size={18} />
          </span>
          <div>
            <strong>Buying tip: </strong>
            <span>{commodity.advice}</span>
          </div>
        </div>
      </div>

      {/* Footer / Transparency & Attribution Action */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
          <GroundTruthBadge type={commodity.retail_provenance || 'empirical_dca'} />
          <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Verified APMC Mandi
          </span>
        </div>

        <button 
          type="button"
          className="attribution-trigger-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-controls={drawerId}
        >
          <span>{isExpanded ? 'Hide price breakdown' : 'Why is this price moving?'}</span>
          <span style={{ fontSize: '0.85rem' }} aria-hidden="true">{isExpanded ? '▴' : '▾'}</span>
        </button>

        {isExpanded && (
          <div id={drawerId}>
            <AttributionDrawer commodity={commodity} mode={mode} />
          </div>
        )}
      </div>
    </article>
  );
}
