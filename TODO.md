# Flight Search Results Improvements - TODO List

**Created:** 2025-10-04
**Status:** In Progress

---

## Overview
Enhance the flight search results page with advanced filters and better display options to improve user experience and help users find the best flights.

---

## Tasks Checklist

### Phase 1: Filter Enhancements
- [x] **Task 1:** Add departure time filter
  - ✓ Morning (5:00 AM - 11:59 AM)
  - ✓ Afternoon (12:00 PM - 5:59 PM)
  - ✓ Evening (6:00 PM - 11:59 PM)
  - ✓ Night (12:00 AM - 4:59 AM)

- [x] **Task 2:** Add journey duration filter
  - ✓ Slider with min/max duration
  - ✓ Display duration range in hours/minutes
  - ✓ Auto-detect min/max from available flights

- [x] **Task 3:** Add airlines filter
  - ✓ Checkbox list of all airlines in results
  - ✓ Show airline name and IATA code
  - ✓ Display count of flights per airline
  - ✓ Dynamic population from flight data

- [x] **Task 4:** Add airports filter
  - ✓ Filter by layover/connection airports
  - ✓ Show airport IATA code and city name
  - ✓ Display count of flights per airport
  - ✓ Only show for multi-stop flights

- [x] **Task 5:** Add baggage filter
  - ✓ Carry-on only
  - ✓ Checked baggage included
  - ✓ 2+ checked bags
  - ✓ No baggage info (show all)

### Phase 2: Display Improvements
- [x] **Task 6:** Add self-transfer indicator
  - ✓ Badge/icon on flight cards
  - ✓ Tooltip explaining self-transfer
  - ✓ Highlight different airlines in same booking
  - ✓ Warning about baggage re-check

- [x] **Task 7:** Add Best/Cheapest/Fastest tabs
  - ✓ Summary cards at top of results
  - ✓ Quick navigation to best options (clickable)
  - ✓ Display price and time averages
  - ✓ Match reference image design

### Phase 3: UI/UX Enhancements
- [x] **Task 8:** Style filters sidebar
  - ✓ Collapsible filter sections
  - ✓ Smooth expand/collapse animations
  - ✓ Active filter count badges
  - ✓ Sticky sidebar on scroll

- [x] **Task 9:** Add clear all filters button
  - ✓ Reset all filters to default
  - ✓ Located in filter header
  - ✓ Resets all checkboxes and sliders

- [x] **Task 10:** Improve filter layout
  - ✓ Better spacing and alignment
  - ✓ Mobile responsive design
  - ✓ Touch-friendly checkboxes
  - ✓ Clean, modern styling

### Phase 4: Testing & Polish
- [x] **Task 11:** Test filter combinations
  - ✓ Verify all filters work together
  - ✓ Check edge cases (no results, single result)
  - ✓ Test with different search parameters
  - ✓ Validate performance with large result sets

- [x] **Task 12:** Add filter state persistence (Optional)
  - ✓ Remember filter selections in sessionStorage
  - ✓ Restore filters on page reload
  - ✓ Clear filters on new search

## B2B Multi-Tenant SaaS
- [x] Tenant data model & migrations (companies, memberships, policies, travel requests)
- [x] Dual RBAC: Ops roles + company roles with JWT tenant context
- [x] Company onboarding & management APIs (`/b2b/companies`, invites, admin listings)
- [x] Travel request workflow with manager/finance approvals (`/b2b/travel-requests`)
- [x] Regression tests for onboarding and approval paths (`tests/test_b2b.py`)
- [x] README updated with corporate travel docs
- [ ] Front-end/dashboard integration for new tenant flows
  - [x] Partner landing CTA and signup experience
  - [x] Partner dashboard shell (profile, team, travel requests, approvals)
  - [ ] Deep reporting & analytics views
- [ ] Monitoring & analytics for tenant activity

---

## Payments & FX (Pre-Production Strategy)

Goal: Charge customers in their local currencies while pricing from a USD base, applying a silent FX safety margin and settling in USD to pay Duffel directly.

### Gateway & Multi-Currency
- [ ] Decide gateway rollout: start with `Paystack` (existing), evaluate `Flutterwave` parity
- [ ] Enable multi-currency initialization (NGN, GHS, XOF, KES, ZAR, USD)
- [ ] Route payment channels by market (card/bank/USSD/mobile money as applicable)
- [ ] Add healthcheck for multi-currency endpoints and channel availability

### USD Base Pricing
- [ ] Introduce `BASE_PRICING_CURRENCY=USD` in settings
- [ ] Build FX service to convert USD → local currency in real time (with caching/fallback)
- [ ] Respect tenant/user display currency preference; default to market currency
- [ ] Add per-offer fields: `base_currency`, `display_currency`, `fx_rate_raw`, `fx_rate_effective`, `fx_source`

### FX Safety Margin (3–5%)
- [ ] Add `FX_SAFETY_MARGIN_PCT` env (default 4.0)
- [ ] Apply margin on top of live USD pair before formatting price
- [ ] Ensure rounding/psychological pricing rules (e.g., .99 or nearest 50)
- [ ] Log baseline vs. effective FX for audit (not visible to end users)

### Settlement & Reconciliation (USD)
- [ ] Record payments ledger in USD and local currency (dual-ledger entries)
- [ ] Configure USD settlement via Wise/Payoneer (ops runbook + credentials placeholders)
- [ ] Map Duffel billing to USD wallet; schedule payout workflow
- [ ] Reconciliation job: match gateway transactions → USD ledger → Duffel invoices

### Regional USD Collection (Later)
- [ ] Evaluate regional USD collection accounts once volume grows (per market)
- [ ] Compare fees/FX vs. current Wise/Payoneer setup; pick threshold to switch

### UX & Controls
- [ ] Show local currency prices everywhere; keep USD base invisible
- [ ] Admin override for margin per market/tenant
- [ ] Graceful degradation when FX API fails (fallback rate + banner for ops only)
 - [ ] Admin UI to manage: base currency, display currency, markup, booking fee, payment fee, FX safety margin
- [ ] Dashboard: user-selectable payment/display currency (limited to Paystack-supported)
  - [x] Added currency selector on `static/dashboard.html` saving to `/v1/ops/preferences`
  - [x] Search now includes `display_currency` from user preferences

### Testing & Monitoring
- [ ] Simulate FX volatility to validate safety margin and guardrails
- [ ] Verify gateway currency/channel combinations per market
- [ ] Add metrics: FX cache hit rate, rate age, margin distribution, refund parity
 - [ ] Daily audit log of FX raw vs effective rates used for pricing

---

## Engineering & CI/CD Recommendations

Adopt the following stack across pre-production and CI to improve reliability and speed:

- [ ] Browser automation: Playwright (e2e/regression for booking + payments)
- [x] Reporting: Playwright HTML report + Allure export
- [ ] Database: PostgreSQL (baseline already chosen)
- [ ] Containerization: Docker for dev/prod; Kubernetes Jobs for CI test runs
- [ ] CI/CD: GitHub Actions or GitLab CI pipelines (matrix for OS/Python)
- [x] Initial CI pipeline and Playwright smoke tests added (GitHub Actions)
- [ ] Pipeline artifacts: upload Playwright reports, logs, screenshots, videos
- [ ] Parallelize Playwright tests by shard to reduce wall time
- [ ] Seed data fixtures for e2e (offers, users, promo, pricing config)
- [ ] Ephemeral DB per run (Postgres in container) + alembic migrate

---

## Search Scope Rules

- [ ] Ignore domestic/local flights within the same country for now (show only international routes)
  - Enforce at search API: filter offer slices where origin.country == destination.country
  - Add a feature flag to re-enable domestic later
  - Env flag added: `IGNORE_DOMESTIC_ROUTES` (default false)


## Implementation Notes

### Data Structure
```javascript
// Filter state object
const filterState = {
  stops: ['direct', 'oneStop', 'twoPlus'],
  departureTime: ['morning', 'afternoon', 'evening', 'night'],
  duration: { min: 0, max: 1440 },
  airlines: ['BA', 'AA', 'DL'],
  airports: ['LHR', 'CDG', 'AMS'],
  baggage: ['carryOn', 'checked', 'multiple'],
  priceRange: 2000
};
```

### Airlines Detection
```javascript
function getUniqueAirlines(offers) {
  const airlines = new Set();
  offers.forEach(offer => {
    const segments = offer.slices?.[0]?.segments || [];
    segments.forEach(seg => {
      if (seg.marketing_carrier) {
        airlines.add(JSON.stringify({
          code: seg.marketing_carrier.iata_code,
          name: seg.marketing_carrier.name
        }));
      }
    });
  });
  return Array.from(airlines).map(a => JSON.parse(a));
}
```

### Self-Transfer Detection
```javascript
function hasSelfTransfer(segments) {
  if (segments.length < 2) return false;

  for (let i = 0; i < segments.length - 1; i++) {
    const currentCarrier = segments[i].marketing_carrier?.iata_code;
    const nextCarrier = segments[i + 1].marketing_carrier?.iata_code;

    if (currentCarrier !== nextCarrier) {
      return true;
    }
  }
  return false;
}
```

---

## Dependencies
- CSS updates for new filter styles
- JavaScript updates for filter logic
- Session storage for filter persistence

---

## Progress Tracking
- **Total Tasks:** 12
- **Completed:** 12
- **In Progress:** 0
- **Remaining:** 0

## Summary of Implementation

All core features have been successfully implemented:

1. **Best/Cheapest/Fastest Summary Tabs** - Displays top 3 flight options with prices and durations
2. **Departure Time Filter** - Morning, Afternoon, Evening, Night time slots
3. **Journey Duration Filter** - Slider to filter flights by total travel time
4. **Airlines Filter** - Checkboxes for all airlines with flight counts
5. **Connection Airports Filter** - Filter by layover airports
6. **Baggage Filter** - Filter by baggage allowance (carry-on, checked, multiple)
7. **Self-Transfer Badge** - Warning indicator when connecting flights use different airlines
8. **Collapsible Filter Sections** - Clean, organized sidebar with expand/collapse functionality
9. **Clear All Filters** - One-click reset button
10. **Responsive Design** - Mobile-friendly layout with proper grid system

## Files Modified

- `static/results.html` - Added filter UI and JavaScript logic
- `static/styles.css` - Added CSS for all new components
- `todolist.md` - Updated with Task 17a reference
- `TODO.md` - This file (detailed task tracking)

---

## Recent Additions (2025-10-04)

### User Registration & Logo Implementation
- [x] **Fix user registration endpoint** - Added POST /auth/register endpoint for new user signups
- [x] **Add SureFlights logo** - Copied logo to static/images/ and updated all HTML pages
- [x] **Regional preferences** - Added country and currency selection in user profiles

### Regional Preferences Feature
- [x] **Database migration** - Added `country` and `preferred_currency` columns to users table (0009_user_preferences)
- [x] **Profile settings page** - Created profile.html with country/currency selector UI
- [x] **Backend API endpoints** - Added GET/PUT `/v1/ops/users/preferences` endpoints
- [x] **Navigation updates** - Added profile link to dashboard and other pages

### Files Modified/Created
- `app/auth/routes.py` - Added registration endpoint
- `static/images/logo.png` - Added SureFlights logo
- `static/index.html`, `results.html`, `signup.html`, `login.html`, `dashboard.html` - Updated with logo
- `static/profile.html` - **New file** for user profile settings
- `alembic/versions/0009_user_preferences.py` - **New migration** for preferences
- `app/api/users.py` - Added preferences GET/PUT endpoints
- `alembic/versions/0006_password_reset_tokens.py` - Fixed revision reference

---

**Last Updated:** 2025-10-24

## Recent Updates (2025-10-24)

### Frontend Modernization & Testing Complete
- [x] **Modernized frontend is live** - All filter and UI improvements deployed and tested
- [x] **Testing foundation established** - Comprehensive test coverage for quality assurance and regression prevention
- [x] **Filter state persistence** - User filter preferences saved and restored across sessions
- [x] **Full filter integration testing** - All filters validated to work correctly together
