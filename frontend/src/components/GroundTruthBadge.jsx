import React, { useState } from 'react';

/**
 * Ground Truth Transparency Badge
 * Article IV Non-Negotiable: All simulated metrics must be explicitly tagged.
 */
export function GroundTruthBadge({ type = 'empirical_dca' }) {
  const [showTooltip, setShowTooltip] = useState(false);

  const isEmpirical = type === 'empirical_dca' || type === 'empirical';

  let badgeLabel = '⚡ Estimated Benchmark';
  let badgeTitle = 'Data Reality Contract (Article IV)';
  let tooltipText = 'Constitutional Proxy: Retail price computed as (Wholesale Price / 100) × 1.35 standard urban logistics & distribution markup until DCA live feed connects.';

  if (isEmpirical) {
    badgeLabel = 'DCA Retail Benchmark';
    badgeTitle = 'Empirical Ground Truth (DCA PMD)';
    tooltipText = 'Official Daily Retail Price: Reported directly by the Department of Consumer Affairs (DCA) Price Monitoring Division (PMD) / Price Monitoring System (PMS) across target urban consumption centers.';
  } else if (type === 'transit') {
    badgeLabel = 'Transit Proxy';
    badgeTitle = 'Logistics Reality Contract';
    tooltipText = 'Constitutional Proxy: Inter-mandi freight calculated using nominal ₹/km over Haversine distance until FASTag & daily fuel API integration.';
  }

  return (
    <div 
      style={{ position: 'relative', display: 'inline-block' }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span className={`ground-truth-badge ${isEmpirical ? 'empirical' : ''}`} title={tooltipText}>
        <span>{isEmpirical ? '✓' : '⚡'}</span>
        <span>{badgeLabel}</span>
      </span>
      {showTooltip && (
        <div style={{
          position: 'absolute',
          bottom: 'calc(100% + 6px)',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '260px',
          background: 'var(--bg-surface-elev-2)',
          border: isEmpirical ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid var(--border-strong)',
          borderRadius: 'var(--radius-chip)',
          padding: '0.6rem 0.75rem',
          fontSize: '0.72rem',
          color: 'var(--text-secondary)',
          lineHeight: '1.4',
          zIndex: 100,
          boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
          pointerEvents: 'none',
        }}>
          <strong style={{ color: isEmpirical ? '#10B981' : 'var(--text-primary)', display: 'block', marginBottom: '0.2rem' }}>
            {badgeTitle}
          </strong>
          {tooltipText}
        </div>
      )}
    </div>
  );
}

