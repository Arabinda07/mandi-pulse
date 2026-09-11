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
      <div className="section-header-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
          Essential Kitchen Staples
        </h2>
        <span className="font-mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Mode: {mode === 'household' ? 'Household Retail (₹/kg)' : 'Wholesale Mandi (₹/qtl)'}
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
