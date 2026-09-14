import React, { useState, useEffect } from 'react';
import { Navigation } from './components/Navigation';
import { BasketHero } from './components/BasketHero';
import { CommodityGrid } from './components/CommodityGrid';
import { BulkSavingsCalculator } from './components/BulkSavingsCalculator';
import { Footer } from './components/Footer';
import { TransparencyModal } from './components/TransparencyModal';
import { fetchMarketData } from './api/datasetteClient';
import { METRO_HUBS } from './api/fallbackData';

export function App() {
  // Modal state for methodology and mandi registry
  const [activeModal, setActiveModal] = useState(null);

  // 1. Location state with localStorage persistence
  const [selectedMetro, setSelectedMetro] = useState(() => {
    return localStorage.getItem('mandi_pulse_metro') || 'delhi';
  });

  // 2. Dual-Mode state with localStorage persistence
  const [mode, setMode] = useState(() => {
    return localStorage.getItem('mandi_pulse_mode') || 'household';
  });

  // 3. Market data & backend status
  const [marketState, setMarketState] = useState({
    data: null,
    isLiveBackend: false,
    sourceLabel: 'Connecting to market data...',
    loading: true,
  });

  // Fetch market data when selected metro changes
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setMarketState(prev => ({ ...prev, loading: true }));
      const result = await fetchMarketData(selectedMetro);
      if (isMounted) {
        setMarketState({
          data: result.data,
          isLiveBackend: result.isLiveBackend,
          sourceLabel: result.sourceLabel,
          loading: false,
        });
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [selectedMetro]);

  // Persist selections
  const handleSelectMetro = (metroId) => {
    setSelectedMetro(metroId);
    localStorage.setItem('mandi_pulse_metro', metroId);
  };

  const handleToggleMode = (newMode) => {
    setMode(newMode);
    localStorage.setItem('mandi_pulse_mode', newMode);
  };

  const currentHub = METRO_HUBS.find(m => m.id === selectedMetro) || METRO_HUBS[0];
  const market = marketState.data;

  return (
    <div className="app-container">
      {/* Accessibility Skip Link (WCAG 2.4.1) */}
      <a href="#main-content" className="skip-link">
        Skip to market prices
      </a>

      <Navigation
        selectedMetro={selectedMetro}
        onSelectMetro={handleSelectMetro}
        mode={mode}
        onToggleMode={handleToggleMode}
        isLiveBackend={marketState.isLiveBackend}
        sourceLabel={marketState.sourceLabel}
      />

      <main 
        id="main-content" 
        className={`main-content ${marketState.loading ? 'is-loading' : ''}`}
        aria-busy={marketState.loading}
      >
        {marketState.loading && (
          <div className="loading-progress-bar" role="progressbar" aria-label="Loading terminal market data" />
        )}

        {market && (
          <>
            {/* Component 2: Weekly Kitchen Basket Hero */}
            <BasketHero heroData={market.basket_hero} mode={mode} reportingDate={market.reporting_date} />

            {/* Component 3: Tier 1 Commodities Grid */}
            <CommodityGrid commodities={market.commodities} mode={mode} />

            {/* Component 4: Bulk & Arbitrage Calculator (always available, expanded in bulk mode) */}
            <BulkSavingsCalculator commodities={market.commodities} />
          </>
        )}
      </main>

      <Footer 
        currentMarket={currentHub} 
        onOpenModal={(tabKey) => setActiveModal(tabKey)} 
      />

      {/* Methodology & Mandi Registry Modal */}
      <TransparencyModal
        isOpen={Boolean(activeModal)}
        activeTab={activeModal || 'methodology'}
        onClose={() => setActiveModal(null)}
        onSelectTab={(tabKey) => setActiveModal(tabKey)}
      />
    </div>
  );
}

export default App;
