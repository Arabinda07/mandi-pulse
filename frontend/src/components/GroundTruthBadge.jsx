import React, { useState } from 'react';

/**
 * Ground Truth Transparency Badge
 * Article IV Non-Negotiable: All simulated metrics must be explicitly tagged.
 * Fully keyboard accessible (Tab, Focus, Hover, Escape).
 */
export function GroundTruthBadge({ type = 'empirical_dca' }) {
  const [showTooltip, setShowTooltip] = useState(false);

  const isEmpirical = type === 'empirical_dca' || type === 'empirical';

  let badgeLabel = '⚡ Estimated Retail';
  let badgeTitle = 'Estimated Retail Price';
  let tooltipText = 'Estimated from wholesale mandi prices plus typical 35% transport and retail distribution costs.';

  if (isEmpirical) {
    badgeLabel = 'DCA Retail Benchmark';
    badgeTitle = 'Official Retail Price (DCA)';
    tooltipText = 'Official daily retail price collected by the Department of Consumer Affairs across urban markets.';
  } else if (type === 'transit') {
    badgeLabel = 'Estimated Transport';
    badgeTitle = 'Estimated Transport Cost';
    tooltipText = 'Trucking freight estimated using driving distance between origin and terminal mandis.';
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setShowTooltip(false);
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setShowTooltip((prev) => !prev);
    }
  };

  return (
    <div 
      style={{ position: 'relative', display: 'inline-block' }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onFocus={() => setShowTooltip(true)}
      onBlur={() => setShowTooltip(false)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-haspopup="dialog"
      aria-expanded={showTooltip}
      aria-label={`${badgeTitle}: ${badgeLabel}. Press Enter or Space for methodology details.`}
      className="ground-truth-wrapper"
    >
      <span className={`ground-truth-badge ${isEmpirical ? 'empirical' : ''}`}>
        <span aria-hidden="true">{isEmpirical ? '✓' : '⚡'}</span>
        <span>{badgeLabel}</span>
      </span>
      {showTooltip && (
        <div 
          role="tooltip"
          id="truth-tooltip"
          style={{
            position: 'absolute',
            bottom: 'calc(100% + 8px)',
            left: '50%',
            transform: 'translateX(-50%)',
            width: '280px',
            background: 'var(--bg-surface-elev-2)',
            border: isEmpirical ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid var(--border-strong)',
            borderRadius: 'var(--radius-chip)',
            padding: '0.65rem 0.85rem',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            lineHeight: '1.45',
            zIndex: 100,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            pointerEvents: 'none',
          }}
        >
          <strong style={{ color: isEmpirical ? '#10B981' : 'var(--text-primary)', display: 'block', marginBottom: '0.25rem' }}>
            {badgeTitle}
          </strong>
          {tooltipText}
        </div>
      )}
    </div>
  );
}

