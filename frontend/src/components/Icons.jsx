import React from 'react';

/**
 * Mandi Pulse Vector Icon System
 * Standardized 24x24 scalable vector icons adhering to UI/UX Pro Max standards.
 * Eliminates platform-dependent emoji rendering (🍅, 🧅, 🥔, 💡, 📦).
 */

export function TomatoIcon({ size = 24, className = '', color = '#EF4444' }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Tomato Body */}
      <circle cx="12" cy="13.5" r="8" fill={color} fillOpacity="0.18" stroke={color} strokeWidth="1.75" />
      {/* Indentation line */}
      <path d="M12 5.5V11" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.6" />
      {/* Calyx & Stem */}
      <path d="M12 2.5V5.5" stroke="#10B981" strokeWidth="2" strokeLinecap="round" />
      <path d="M12 5.5L8.5 4.5M12 5.5L15.5 4.5M12 5.5L10 7.5M12 5.5L14 7.5" stroke="#10B981" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function OnionIcon({ size = 24, className = '', color = '#A855F7' }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Onion Bulb Shape */}
      <path 
        d="M12 3C8 8 5 11 5 15C5 18.866 8.13401 22 12 22C15.866 22 19 18.866 19 15C19 11 16 8 12 3Z" 
        fill={color} 
        fillOpacity="0.16" 
        stroke={color} 
        strokeWidth="1.75" 
        strokeLinejoin="round" 
      />
      {/* Inner Growth Rings */}
      <path d="M12 6C9.5 10 8 12.5 8 15.5C8 17.7 9.8 19.5 12 19.5C14.2 19.5 16 17.7 16 15.5C16 12.5 14.5 10 12 6Z" stroke={color} strokeWidth="1.2" strokeOpacity="0.5" />
      {/* Shoot Top */}
      <path d="M12 2V3.5" stroke="#10B981" strokeWidth="1.75" strokeLinecap="round" />
    </svg>
  );
}

export function PotatoIcon({ size = 24, className = '', color = '#F59E0B' }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Organic Potato Shape */}
      <path 
        d="M6 10C5 13.5 6 17 9 19C12 21 16.5 20.5 19 18C21.5 15.5 21 11.5 19.5 8.5C18 5.5 14.5 4 11 4.5C7.5 5 7 6.5 6 10Z" 
        fill={color} 
        fillOpacity="0.16" 
        stroke={color} 
        strokeWidth="1.75" 
        strokeLinejoin="round" 
      />
      {/* Dimple Eyes */}
      <circle cx="10" cy="9" r="1" fill={color} />
      <circle cx="15" cy="11" r="1.1" fill={color} />
      <circle cx="12" cy="15" r="0.9" fill={color} />
      <circle cx="16.5" cy="15.5" r="0.8" fill={color} />
    </svg>
  );
}

export function AdvisorIcon({ size = 18, className = '', color = 'var(--brand-accent)' }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path 
        d="M9 18H15M10 21H14M12 2C7.58172 2 4 5.58172 4 10C4 12.6522 5.28906 15.0065 7.28421 16.4718C7.72763 16.7974 8 17.3075 8 17.8546V18H16V17.8546C16 17.3075 16.2724 16.7974 16.7158 16.4718C18.7109 15.0065 20 12.6522 20 10C20 5.58172 16.4183 2 12 2Z" 
        stroke={color} 
        strokeWidth="1.8" 
        strokeLinecap="round" 
        strokeLinejoin="round" 
      />
      <path d="M12 6V11M10 9H14" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.6" />
    </svg>
  );
}

export function BulkCrateIcon({ size = 20, className = '', color = 'var(--brand-accent)' }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path 
        d="M21 8L12 3L3 8V16L12 21L21 16V8Z" 
        stroke={color} 
        strokeWidth="1.8" 
        strokeLinejoin="round" 
        fill={color}
        fillOpacity="0.12"
      />
      <path d="M12 3V21M3 8L12 13L21 8" stroke={color} strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M7.5 10.5L16.5 5.5" stroke={color} strokeWidth="1.4" strokeLinecap="round" strokeOpacity="0.7" />
    </svg>
  );
}

export function CommodityVectorIcon({ id, size = 26, fallback = null }) {
  switch (id) {
    case 'tomato':
      return <TomatoIcon size={size} />;
    case 'onion':
      return <OnionIcon size={size} />;
    case 'potato':
      return <PotatoIcon size={size} />;
    default:
      return fallback;
  }
}
