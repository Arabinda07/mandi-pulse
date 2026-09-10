# Design System & Visual Specification: Mandi Pulse

## 0. Design Read

> **Reading this as:** Daily public-interest market utility for Indian households and volume buyers, with an editorial civic-transparency language, leaning toward modern utilitarian precision (Cabinet Grotesk + Geist Mono, Slate/Emerald palette, high data-trust, zero generic SaaS tropes).

---

## 1. The Three Dials

```
DESIGN_VARIANCE: 6   (Structured, asymmetric focal points, no cookie-cutter equal card grids)
MOTION_INTENSITY: 4  (Restrained, purposeful status micro-transitions, spring physics, zero decorative looping jank)
VISUAL_DENSITY: 6    (Glanceable data-compact cards, instant price readability, no wasteful airy fluff)
```

- **Variance Rationale**: Clean hierarchy with distinct emphasis between the primary Basket Hero, individual commodity price benchmarks, and the expandable supply-chain attribution drawer.
- **Motion Rationale**: Motion strictly serves data communication (state changes when switching metros, toggle animations between Household and Bulk mode, clear pill badges).
- **Density Rationale**: Everyday shoppers and bulk buyers want answers in 3 seconds on mobile. Numbers and tags must be legible without scrolling through endless empty padding.

---

## 2. Typography System

### Font Pairing
- **Display & Benchmark Prices**: `Cabinet Grotesk` (Variable, 700/800 weight)
  - Punchy, geometric, distinct, and authoritative. Gives numeric prices physical presence.
- **Body, Explanations & Labels**: `Geist` (400 regular, 500 medium, 600 semibold)
  - Engineered for high legibility, clean neutral geometry, and zero decorative noise.
- **Deltas, Units & Mandi Codes**: `Geist Mono` / `JetBrains Mono`
  - Used for `₹/kg`, `₹/qtl`, percentage changes (`+14.2%`), dates (`10 Sep 2026`), and LGD codes.

### Typographic Hierarchy
| Role | Font | Size / Line Height | Tracking | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Headline / Hero Price** | Cabinet Grotesk 800 | `36px md:48px` / `1.1` | `-0.03em` | Primary commodity prices (e.g. `₹32`) |
| **Basket Total** | Cabinet Grotesk 700 | `28px md:36px` / `1.15` | `-0.02em` | Weekly kitchen basket total |
| **Section Title** | Geist 600 | `18px md:20px` / `1.3` | `-0.01em` | Group headers ("Today's Price Pulse") |
| **Body / Advice** | Geist 400 | `14px md:15px` / `1.5` | `0` | Purchasing advice, attribution stories |
| **Pill / Metric Meta** | Geist Mono 500 | `12px md:13px` / `1.2` | `+0.02em` | Unit badges, deltas (`+₹2.50 today`) |
| **Caption / Attribution** | Geist 400 | `12px` / `1.4` | `0` | Mandi origin, reporting date |

---

## 3. Color Architecture & Tokens (Anti-Slop Palette)

### Core Principle
No purple or violet button glows. No dark-mesh gradient backgrounds. No beige-and-brass fake artisan pastels. The palette is rooted in agricultural trade reality: cool deep slate stone surfaces, crisp neutral text, and decisive semantic market signals.

### Color Tokens

#### Neutrals (Deep Slate & Surface Hierarchy)
```css
--bg-canvas:       #0A0D12;  /* Deep ground canvas */
--bg-surface:      #12161F;  /* Primary card surface */
--bg-surface-elev: #1A202C;  /* Hovered or elevated container */
--border-subtle:   #232B3B;  /* Structural 1px dividers */
--border-strong:   #344155;  /* Active card focus and interactive outlines */

--text-primary:    #F1F5F9;  /* High-contrast crisp foreground */
--text-secondary:  #94A3B8;  /* Labels, units, secondary descriptors */
--text-muted:      #64748B;  /* Captions, timestamps, inactive icons */
```

#### Semantic Market Accents
```css
/* Normal / Fair Price / Cooling Trend */
--status-fair-bg:     rgba(16, 185, 129, 0.12);
--status-fair-border: rgba(16, 185, 129, 0.35);
--status-fair-text:   #34D399;  /* Emerald 400 */

/* Elevated Price / Watching Trend */
--status-warn-bg:     rgba(245, 158, 11, 0.12);
--status-warn-border: rgba(245, 158, 11, 0.35);
--status-warn-text:   #FBBF24;  /* Amber 400 */

/* Severe Supply Shock / Price Spike Incoming */
--status-shock-bg:    rgba(239, 68, 68, 0.14);
--status-shock-border:rgba(239, 68, 68, 0.40);
--status-shock-text:  #F87171;  /* Red 400 */

/* Brand / Interactive Accent */
--brand-accent:       #10B981;  /* Clear agricultural emerald */
--brand-accent-hover: #059669;
```

---

## 4. Component Structure & Information Flow

### Component 1: Top Navigation & Utility Strip
- **Brand Title**: `Mandi Pulse` (left-aligned, clean, with a 6px live status dot indicating warehouse freshness).
- **Location Selector**: 5 quick chips (`Delhi NCR`, `Mumbai`, `Bengaluru`, `Kolkata`, `Pune`) + search button.
- **Mode Toggle**: Segmented pill switch: `[ Household (₹/kg) | Bulk Buyer (₹/qtl) ]`.

### Component 2: The Weekly Basket Hero (TOP Index)
- Asymmetric card displaying the consolidated price for standard family consumption (1kg Tomato + 2kg Onion + 2kg Potato).
- Clear numeric total with week-over-week delta and shopping verdict (*"Stable week for cooking essentials"*).

### Component 3: Commodity Grid (Tomato, Onion, Potato)
- **3-column responsive grid** on desktop (`grid-cols-1 md:grid-cols-3 gap-5`), single-column on mobile.
- **Each card contains**:
  1. Commodity icon/name + local variety badge.
  2. Large Cabinet Grotesk benchmark price (`₹32` with `/kg` unit in mono).
  3. Status Tag (`Fair Price` in emerald pill, or `Elevated` in amber).
  4. Mini Trend Pill (`🔴 Spike in ~10d` or `🟢 Cooling Down`).
  5. 1-line plain-language shopping advice: *"Nashik arrivals dropped 35% this week. Stock up before Monday."*
  6. 1-click bottom disclosure: *"Why is this price moving?"*

### Component 4: Expandable Attribution Drawer
- Triggered on card expansion:
  - **The Rupee Journey**: Visual progress bar showing Farmgate price (₹14) $\rightarrow$ Transport & Mandi fees (₹5) $\rightarrow$ Retail margin (₹13).
  - **Harvest & Weather Context**: Active seasonal phase (e.g. *Late Kharif harvest delay*) and natural-language weather impact.

---

## 5. Craft Floor & Quality Invariants (`/impeccable`)

1. **Touch Target Size**: Every chip, toggle, and expandable button has a minimum hit target of `44x44px` on mobile screens.
2. **Contrast Accessibility**: All text against background meets WCAG AA standards:
   - Primary text (`#F1F5F9` on `#12161F`): **13.8:1** (passes AAA).
   - Status text (`#34D399` on `rgba(16,185,129,0.12)` + `#12161F`): **5.4:1** (passes AA).
3. **Button Label Integrity**: Button text must never wrap on any viewport.
4. **Single Radius Rule**: All card containers use `rounded-xl` (12px), interactive buttons and pills use `rounded-full`, and internal chips use `rounded-lg` (8px). No sharp squares mixed arbitrarily with circles.
5. **No Layout Shifts**: Numeric values render with `tabular-nums` (`font-mono` where applicable) to prevent jitter when switching modes or locations.
