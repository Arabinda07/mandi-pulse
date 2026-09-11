import React from 'react';

/**
 * Footer Component
 * Public-interest civic transparency notice and methodology links.
 */
export function Footer({ currentMarket, onOpenModal }) {
  return (
    <footer className="site-footer">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <strong style={{ color: 'var(--text-primary)' }}>Mandi Pulse</strong>
          <span> · Daily wholesale prices and retail food costs.</span>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
          Market: <span style={{ color: 'var(--text-primary)' }}>{currentMarket?.terminal_mandi}</span> (LGD Code {currentMarket?.lgd_code || 'Verified'})
        </div>
      </div>

      <p style={{ fontSize: '0.75rem', lineHeight: '1.5', color: 'var(--text-muted)' }}>
        Data sources: Daily wholesale arrivals and prices from Agmarknet (Data.gov.in). Retail prices from the Department of Consumer Affairs (DCA). Arrival trends compare today's volume against 3-year seasonal averages.
      </p>

      <div className="footer-links">
        <button 
          type="button" 
          className="footer-link-btn" 
          onClick={() => onOpenModal('methodology')}
        >
          Methodology & Formulas
        </button>
        <button 
          type="button" 
          className="footer-link-btn" 
          onClick={() => onOpenModal('mandi-registry')}
        >
          25 APMC Mandi Registry
        </button>
        <a 
          href="https://data.gov.in" 
          target="_blank" 
          rel="noreferrer" 
          className="footer-link"
        >
          Data.gov.in ↗
        </a>
      </div>
    </footer>
  );
}
