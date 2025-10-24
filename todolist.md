# SureFlights UI/UX Improvement Checklist

## Progress: 20/35 Completed (57%)

**Latest Update:** 2025-10-04 - Added user registration, logo, and regional preferences

---

## ✅ Completed Tasks

### Phase 1: Quick Wins (5/5)
- [x] **Task 1:** Add baggage info and flight duration to results cards
- [x] **Task 2:** Show layover city/duration for multi-stop flights
- [x] **Task 3:** Add price breakdown (base fare + taxes + fees) to booking page
- [x] **Task 4:** Improve mobile responsiveness for results and admin tables
- [x] **Task 5:** Add inline validation instead of generic alerts

### Phase 2: Authentication & Password Reset (2/2)
- [x] **Task 6:** Implement password reset flow (Backend + Frontend)
- [x] **Task 7:** Add forgot password link to login page

### Phase 3: Booking Experience (4/4)
- [x] **Task 8:** Implement email confirmation sending after booking
  - ✓ Email service already implemented via notification service
  - ✓ Sends confirmation emails with PNR, e-tickets, and booking details
- [x] **Task 9:** Add WhatsApp booking confirmation with itinerary
  - ✓ WhatsApp Cloud API integration
  - ✓ Formatted message with booking reference, e-tickets, flight details
  - ✓ Includes route, airline, dates, times, passenger count, total amount
  - ✓ Clear next steps and instructions
  - ✓ Automatically sent after payment confirmation
- [x] **Task 10:** Add e-ticket download button to confirmation page
  - ✓ Download e-ticket as text file
  - ✓ Print-friendly itinerary
  - ✓ Share booking functionality
- [x] **Task 11:** Add 'Add to Calendar' option on confirmation
  - ✓ iCal format download
  - ✓ 24-hour flight reminder
  - ✓ Compatible with Google Calendar, Outlook, Apple Calendar

### Phase 4: Customer Self-Service (2/2)
- [x] **Task 12:** Create customer-facing cancellation request UI
  - ✓ Dedicated cancel-booking.html page
  - ✓ Load and display booking details
  - ✓ Cancellation reason dropdown with validation
  - ✓ Confirmation checkbox before submission
  - ✓ Success/error handling
  - ✓ Cancel button in dashboard (shows only for non-cancelled bookings)
  - ✓ Backend API integration (POST /v1/cancellations)
  - ✓ Email notification on request submission
- [x] **Task 13:** Add cancellation fee calculator
  - ✓ Real-time fee calculation (20% cancellation fee)
  - ✓ Clear breakdown showing original amount, fee, and refund
  - ✓ Visual display with color-coded sections
  - ✓ Currency-aware formatting

### Phase 5: Revenue & Conversion (2/2)
- [x] **Task 14:** Add promo code/discount system
  - ✓ PromoCode and PromoCodeUsage database models
  - ✓ Backend PromoCodeService with validation logic
  - ✓ API endpoints (POST /v1/promo-codes/validate)
  - ✓ Percentage and fixed amount discount types
  - ✓ Min purchase amount and max uses validation
  - ✓ Expiry date support
  - ✓ Customer-facing promo code input in booking flow
  - ✓ Real-time discount calculation and price update
  - ✓ Admin UI for creating and managing promo codes
  - ✓ Promo code deactivation feature
  - ✓ API router integration in main.py
- [x] **Task 15a:** User registration system
  - ✓ POST /auth/register endpoint with rate limiting
  - ✓ Password strength validation (min 8 characters)
  - ✓ Duplicate email check
  - ✓ Auto-assign customer role
  - ✓ Audit logging for registrations
- [x] **Task 15b:** SureFlights branding
  - ✓ Logo added to static/images directory
  - ✓ Updated all pages with actual logo (index, results, signup, login, dashboard)
  - ✓ Responsive logo sizing for different contexts
- [x] **Task 15c:** Regional preferences
  - ✓ Database migration for country and currency fields
  - ✓ Profile settings page with country/currency selector
  - ✓ Backend API endpoints (GET/PUT /v1/ops/users/preferences)
  - ✓ Audit logging for preference updates
  - ✓ Profile link added to navigation

---

## 🔥 High-Impact Features (In Progress)

### Revenue & Conversion
- [x] **Task 15:** Add payment method selection (card, bank, USSD)
  - Frontend booking form now presents card, bank transfer, and USSD options with clear selection states.
  - Booking API accepts a validated payment_method field and forwards it to Paystack metadata and channel filters.
  - Payments table now stores the chosen method for each initialized transaction via a new migration.

### Payments & FX (Pre-Production)
- [ ] **Task P1:** Integrate multi-currency gateway support
  - Paystack first (existing integration), evaluate Flutterwave parity
  - Enable NGN, GHS, XOF, KES, ZAR, USD where supported
  - Route channels per market (card/bank/USSD/mobile money)
- [ ] **Task P2:** USD base pricing with real-time FX
  - Add `BASE_PRICING_CURRENCY=USD`
  - FX service: USD → local conversion with cache and fallback
  - Respect user/tenant display currency; default to market
- [ ] **Task P3:** Silent FX safety margin (3–5%)
  - `FX_SAFETY_MARGIN_PCT` env (default 4%)
  - Apply on top of live rates; round sensibly
  - Audit: store `fx_rate_raw` vs `fx_rate_effective`
- [ ] **Task P4:** USD settlement and Duffel payouts
  - Dual-ledger: store local and USD amounts per payment
  - Settle via Wise/Payoneer; map Duffel billing to USD wallet
  - Reconciliation job across gateway → USD ledger → Duffel invoices
- [ ] **Task P5:** Regional USD collection (scale-up)
  - Evaluate per-market USD collection accounts at volume thresholds
  - Compare fees/FX vs. current setup; define switch criteria

### Search & Discovery
- [ ] **Task 16:** Implement multi-city trip support
- [ ] **Task 17:** Add flexible date search (+/- 3 days)
- [x] **Task 17a:** Add advanced flight search filters (See TODO.md)
  - ✓ Departure time filters (morning, afternoon, evening, night)
  - ✓ Journey duration filter with slider
  - ✓ Airlines filter with checkboxes (dynamically populated)
  - ✓ Airports filter for connections (dynamically populated)
  - ✓ Baggage filter (carry-on, checked, multiple bags, no info)
  - ✓ Self-transfer indicator badge with tooltip
  - ✓ Best/Cheapest/Fastest summary tabs (clickable)
  - ✓ Collapsible filter sections with animations
  - ✓ Clear all filters button
  - ✓ Responsive design for mobile/tablet/desktop

---

## 📊 Dashboard & Admin Improvements

### User Dashboard
- [ ] **Task 18:** Add trip status timeline to user dashboard
- [ ] **Task 19:** Segregate upcoming vs past trips in dashboard
- [ ] **Task 20:** Add notifications center to user dashboard
- [ ] **Task 21:** Add save passenger details for future bookings

### Admin Dashboard
- [ ] **Task 22:** Add revenue analytics charts to admin dashboard
- [ ] **Task 23:** Add real-time booking notifications to admin
- [ ] **Task 24:** Add export functionality to admin for trips (CSV/Excel)

---

## 🎨 Polish & UX Enhancements

### Visual Improvements
- [ ] **Task 25:** Add empty state for results page instead of redirect
- [ ] **Task 26:** Add loading skeleton for better UX
- [ ] **Task 27:** Improve theme toggle consistency across all pages
- [ ] **Task 28:** Add trust badges and security indicators

---

## 📄 Legal & Compliance

- [ ] **Task 29:** Create Terms of Service page
- [ ] **Task 30:** Create Privacy Policy page

---

## Implementation Notes

### High-Impact Priorities (Next 10 Tasks)
1. Password reset flow (Tasks 6-7)
2. Email/WhatsApp confirmations (Tasks 8-9)
3. Confirmation page enhancements (Tasks 10-11)
4. Customer cancellation (Tasks 12-13)
5. Promo codes (Task 14)
6. Payment methods (Task 15)
7. Multi-city search (Task 16)
8. Flexible dates (Task 17)
9. Trip status timeline (Task 18)
10. Dashboard segmentation (Task 19)

### Technical Dependencies
- **Email system**: Requires SMTP configuration or email service integration
- **WhatsApp**: Already have whatsapp_notifier.py, needs template improvements
- **Promo codes**: Requires new database models and validation logic
- **Multi-city**: Backend search service enhancement needed
- **Analytics charts**: Consider Chart.js or similar library

### Business Impact Ranking
- 🔥 **Critical**: Tasks 6-9, 12-15 (Customer trust, conversion, revenue)
- ⚡ **Important**: Tasks 10-11, 16-19 (User experience, retention)
- 📈 **Nice-to-have**: Tasks 20-28 (Polish, convenience)
- 📋 **Compliance**: Tasks 29-30 (Legal requirements)

---

**Last Updated:** 2025-10-04
**Current Focus:** High-Impact Features (Tasks 6-17) + Flight Search Filters (Task 17a - see TODO.md)
