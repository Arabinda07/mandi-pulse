import React from 'react';

/**
 * Footer Component
 * Public-interest civic transparency notice and methodology links.
 */
export function Footer({ currentMarket }) {
  return (
    <footer className="site-footer">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <strong style={{ color: 'var(--text-primary)' }}>Mandi Pulse</strong>
          <span> — Public Interest Food Inflation & Supply-Chain Volatility Engine.</span>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
          Terminal Market: <span style={{ color: 'var(--text-primary)' }}>{currentMarket?.terminal_mandi}</span> (LGD Code: {currentMarket?.lgd_code || 'Verified'})
        </div>
      </div>

      <p style={{ fontSize: '0.75rem', lineHeight: '1.5', color: 'var(--text-muted)' }}>
        Data Source: Daily wholesale modal arrivals & prices aggregated from Agmarknet (Data.gov.in) APMC yards. Arrival Shock Anomalies (ASA) computed against 3-year seasonal calendar-week baselines. Retail benchmark estimates apply standard 35% urban logistics multiplier in compliance with Article IV of the project constitution.
      </p>

      <div className="footer-links">
        <a href="#methodology" className="footer-link">Methodology & Formulas (ASA / SPD)</a>
        <a href="#mandi-registry" className="footer-link">25 APMC Mandi Registry</a>
        <a href="#constitution" className="footer-link">Project Constitution (Spec-001)</a>
        <a href="https://data.gov.in" target="_blank" rel="noreferrer" className="footer-link">Data.gov.in (OGD India) ↗</a>
      </div>
    </footer>
  );
}
