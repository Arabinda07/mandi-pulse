import React from 'react';

/**
 * BulkSavingsCalculator Component
 * Displays standard packaging rates (20kg crate, 50kg sack) and group-buying arbitrage savings.
 * Resolves Problem #75 for volume buyers and community split-buying.
 */
export function BulkSavingsCalculator({ commodities }) {
  if (!commodities || commodities.length === 0) return null;

  return (
    <section className="bulk-arbitrage-banner" aria-label="Bulk Purchasing and Arbitrage Savings Calculator">
      <div style={{ maxWidth: '680px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem' }}>
          <span style={{ fontSize: '1rem' }}>📦</span>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Bulk & Group-Buying Arbitrage (Direct APMC Dispatches)
          </h3>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
          Standard wholesale containers auction at APMC terminal mandis. Split-purchasing with neighbors or purchasing direct from wholesale yards saves an average of <strong>25% to 28%</strong> compared to quick-commerce and neighborhood retail markups.
        </p>
      </div>

      <div className="bulk-rates-grid">
        {commodities.map((c) => (
          <div key={c.id} className="bulk-rate-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {c.icon} {c.name}
              </span>
              <span className="bulk-rate-package">{c.packaging_type}</span>
            </div>

            <div className="bulk-rate-price font-mono">
              ₹{c.crate_rate_rs.toLocaleString('en-IN')}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.2rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Retail Eq: ₹{c.retail_box_equivalent_rs}
              </span>
              <span className="bulk-rate-savings">
                Save ₹{c.bulk_savings_rs} ({c.bulk_savings_pct}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
