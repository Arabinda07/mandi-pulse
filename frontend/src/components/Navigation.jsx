import React from 'react';
import { METRO_HUBS } from '../api/fallbackData';

/**
 * Navigation Component
 * Top utility strip with brandmark, live pulse, 5 metro quick chips, and segmented mode toggle.
 */
export function Navigation({
  selectedMetro,
  onSelectMetro,
  mode,
  onToggleMode,
  isLiveBackend,
  sourceLabel
}) {
  return (
    <header>
      {/* Top Utility Strip */}
      <nav className="top-nav" aria-label="Main Navigation">
        <div className="brand-wrapper">
          <div className="brand-title">
            <span className="live-pulse-dot" title="Live data status" />
            <span>Mandi Pulse</span>
          </div>
          <span className="brand-badge">Daily Prices</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Data Source Status Badge */}
          <div 
            style={{ 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: '0.4rem', 
              fontSize: '0.75rem', 
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)' 
            }}
          >
            <span 
              style={{ 
                width: '6px', 
                height: '6px', 
                borderRadius: '50%', 
                background: isLiveBackend ? 'var(--brand-accent)' : '#94A3B8' 
              }} 
            />
            <span>{sourceLabel}</span>
          </div>

          <a 
            href="/datasette" 
            target="_blank" 
            rel="noreferrer"
            className="metro-chip"
            style={{ fontSize: '0.8rem', textDecoration: 'none' }}
          >
            Raw Data (Datasette) ↗
          </a>
        </div>
      </nav>

      {/* Controls Bar: Metro Selector + Segmented Mode Switcher */}
      <div className="controls-bar">
        {/* Metro Chips */}
        <div className="metro-chips-group" role="tablist" aria-label="Select city">
          {METRO_HUBS.map((metro) => {
            const isActive = selectedMetro === metro.id;
            return (
              <button
                key={metro.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={`metro-chip ${isActive ? 'active' : ''}`}
                onClick={() => onSelectMetro(metro.id)}
              >
                <span>{metro.name}</span>
              </button>
            );
          })}
        </div>

        {/* Dual Mode Switcher */}
        <div className="mode-toggle-container" role="group" aria-label="Select Pricing Mode">
          <button
            type="button"
            className={`mode-toggle-btn ${mode === 'household' ? 'active' : ''}`}
            onClick={() => onToggleMode('household')}
          >
            <span>Household</span>
            <span className="mode-toggle-unit">(₹/kg)</span>
          </button>
          <button
            type="button"
            className={`mode-toggle-btn ${mode === 'bulk' ? 'active' : ''}`}
            onClick={() => onToggleMode('bulk')}
          >
            <span>Bulk Buyer</span>
            <span className="mode-toggle-unit">(₹/qtl)</span>
          </button>
        </div>
      </div>
    </header>
  );
}
