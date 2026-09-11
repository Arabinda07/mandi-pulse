import React from 'react';

/**
 * BasketHero Component
 * Asymmetric hero card calculating consolidated weekly kitchen staples (1kg Tomato + 2kg Onion + 2kg Potato).
 */
export function BasketHero({ heroData, mode }) {
  if (!heroData) return null;

  const isHousehold = mode === 'household';
  const totalDisplay = isHousehold
    ? `₹${heroData.weekly_total_rs.toFixed(2)}`
    : `₹${(heroData.weekly_total_rs * 40).toLocaleString('en-IN')}`; // 40x weekly scaling for volume families/institutions
  
  const unitDisplay = isHousehold ? 'weekly family basket' : 'bulk order (40x)';

  const isUp = heroData.week_change_pct > 0;
  const deltaColor = isUp ? 'var(--status-shock-text)' : 'var(--status-fair-text)';
  const deltaText = isUp ? `+${heroData.week_change_pct}% vs last week` : `${heroData.week_change_pct}% vs last week`;

  const verdictBg = heroData.verdict_status === 'shock'
    ? 'var(--status-shock-bg)'
    : heroData.verdict_status === 'warning'
    ? 'var(--status-warn-bg)'
    : 'var(--status-fair-bg)';

  const verdictBorder = heroData.verdict_status === 'shock'
    ? 'var(--status-shock-border)'
    : heroData.verdict_status === 'warning'
    ? 'var(--status-warn-border)'
    : 'var(--status-fair-border)';

  const verdictColor = heroData.verdict_status === 'shock'
    ? 'var(--status-shock-text)'
    : heroData.verdict_status === 'warning'
    ? 'var(--status-warn-text)'
    : 'var(--status-fair-text)';

  return (
    <section className="basket-hero-card" aria-label="Weekly Kitchen Basket">
      <div className="basket-title-group">
        <div className="basket-eyebrow">
          <span>Weekly Staples</span>
          <span>•</span>
          <span>Early Price Alert</span>
        </div>
        <h1 className="basket-headline">
          The Essential Kitchen Basket
        </h1>
        <p className="basket-composition">
          {heroData.composition}
        </p>
        <div 
          className="basket-outlook-strip" 
          style={{ background: verdictBg, borderColor: verdictBorder }}
        >
          <span className="outlook-badge" style={{ color: verdictColor }}>
            ● Outlook:
          </span>
          <span className="outlook-text">
            {heroData.verdict}
          </span>
        </div>
      </div>

      <div className="basket-metric-group">
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Estimated Total Cost
        </span>
        <div className="basket-price-row">
          <span className="basket-total-price numeric-data">{totalDisplay}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginTop: '0.35rem' }}>
          <span className="price-delta font-mono" style={{ color: deltaColor, fontSize: '0.85rem' }}>
            {deltaText}
          </span>
          <span className="basket-total-unit">({unitDisplay})</span>
        </div>
      </div>
    </section>
  );
}
