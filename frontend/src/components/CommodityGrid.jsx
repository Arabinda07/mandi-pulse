import React from 'react';
import { CommodityCard } from './CommodityCard';

/**
 * CommodityGrid Component
 * Renders the responsive 3-column container for Tomato, Onion, and Potato.
 */
export function CommodityGrid({ commodities, mode }) {
  if (!commodities || commodities.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        No commodity data available for this market.
      </div>
    );
  }

  return (
    <section aria-label="Essential Commodities Price Monitor">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
          Tier 1 Kitchen Staples (TOP Index)
        </h3>
        <span className="font-mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Mode: {mode === 'household' ? 'Household Retail Benchmark (₹/kg)' : 'Wholesale Mandi Auction (₹/qtl)'}
        </span>
      </div>

      <div className="commodity-grid">
        {commodities.map((item) => (
          <CommodityCard key={item.id} commodity={item} mode={mode} />
        ))}
      </div>
    </section>
  );
}
