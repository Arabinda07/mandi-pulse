# Feature Specification: [Feature Name]

> **Spec ID:** `SPEC-[###]`  
> **Status:** `Draft` | `Clarified` | `Approved` | `Implemented`  
> **Author:** [Author / Agent]  
> **Created:** [YYYY-MM-DD]  
> **Target Audience:** [Household / Bulk Buyer / Analyst / Pipeline Engineer]

---

## 1. Problem Statement & "Why"
*What specific user or domain problem does this feature solve? Why is it being built now?*
*(Reference specific user pain points, e.g. consumer price opacity, mandi spatial arbitrage, missing commodity feeds).*

---

## 2. User Stories & Core Behaviors

### User Story 1: [Primary Journey]
- **As a** [role / persona]
- **I want to** [action / capability]
- **So that** [tangible outcome / value]

#### Acceptance Criteria
- [ ] Criterion 1: Given [precondition], when [action], then [expected outcome].
- [ ] Criterion 2: ...

### User Story 2: [Secondary / Edge Journey]
- **As a** [role / persona]
- **I want to** [action / capability]
- **So that** [tangible outcome]

#### Acceptance Criteria
- [ ] Criterion 1: ...

---

## 3. Domain Metrics & Data Contracts
*Detail the explicit domain measurements, units, and formulas required.*

- **Commodity Target**: [e.g., Tomato / Onion / Potato / Tier 1 / Tier 2]
- **Operational Mode**: [Household (₹/kg) | Bulk (₹/quintal, box crates)]
- **Analytical Metrics**: [Arrival Shock Anomaly (Z-score) | Spatial Price Dispersion (CV) | Corridor Friction]
- **Data Provenance**: [Agmarknet Live | DCA Retail | Haversine Distance | Synthetic Proxy (Flagged)]

---

## 4. Edge Cases & Boundaries

### Included (In-Scope)
- [Explicit boundary 1]
- [Explicit boundary 2]

### Excluded (Out-of-Scope)
- [What this feature deliberately does NOT do]
- [Future extensions deferred to subsequent specs]

---

## 5. Clarification Log (`/speckit.clarify`)
*Record ambiguities and edge cases identified during the clarification phase.*

| Question / Ambiguity | Resolution / Decision | Decided By | Date |
| :--- | :--- | :--- | :--- |
| *e.g., How do we handle mandi market holidays?* | *Forward-fill previous day's modal price with stale flag* | [Spec Review] | [YYYY-MM-DD] |
