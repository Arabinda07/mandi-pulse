import React from 'react';
import { BulkCrateIcon, CommodityVectorIcon } from './Icons';

/**
 * BulkSavingsCalculator Component
 * Displays standard packaging rates (20kg crate, 50kg sack) and group-buying arbitrage savings.
 * Resolves Problem #75 for volume buyers and community split-buying.
 */
export function BulkSavingsCalculator({ commodities }) {
  if (!commodities || commodities.length === 0) return null;

  return (
    <section className="bulk-arbitrage-banner" aria-label="Bulk Purchasing Savings Calculator">
      <div style={{ maxWidth: '680px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
          <BulkCrateIcon size={22} color="var(--brand-accent)" />
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Bulk & Group Buying (Direct Mandi Rates)
          </h2>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
          Produce at wholesale mandis sells in full crates and sacks. Buying full crates directly or splitting with neighbors saves an average of <strong>25% to 28%</strong> compared to local shops and delivery apps.
        </p>
      </div>

      <div className="bulk-rates-grid">
        {commodities.map((c) => (
          <div key={c.id} className="bulk-rate-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                <CommodityVectorIcon id={c.id} fallback={c.icon} size={18} />
                <span>{c.name}</span>
              </span>
              <span className="bulk-rate-package">{c.packaging_type}</span>
            </div>

            <div className="bulk-rate-price font-mono">
              ₹{c.crate_rate_rs.toLocaleString('en-IN')}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.2rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Retail equivalent: ₹{c.retail_box_equivalent_rs}
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
