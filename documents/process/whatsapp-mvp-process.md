# WhatsApp MVP – Booking Process

Goal: Enable end-to-end flight booking via WhatsApp for individuals worldwide (strong Nigeria support), using FastAPI backend, Duffel (global content), Paystack (primary), and basic agent takeover.

Scope (MVP)
- Channel: WhatsApp Cloud API only (worldwide itineraries: domestic and international)
- Flows: Search → Offers → Reprice → Book → Pay (Paystack) → Ticket → Confirmations (WhatsApp + email)
- Users: Shopper/Guest (U1), Agent (U3), Supervisor (U4 minimal), Admin (U5/U6 minimal)

Conversation States
- start → collect_search → show_offers → confirm_offer → collect_passengers → confirm_quote → payment_link_sent → awaiting_webhook → ticketed | failed

Happy Path
1) User: "LOS-ABV 2025-11-05, 1 adult"
2) Bot: Parse + normalize → POST /v1/search
3) Bot: Return top 3 with chips (price NGN + currency, baggage, stops) + rules summary
4) User: Selects #2 → Bot calls POST /v1/offers/{id}/price
5) If delta, bot asks to confirm new price; on confirm → POST /v1/book
6) Backend creates Quote + Paystack payment_url; bot sends payment link and reference
7) Paystack webhook charge.success → worker issues order (Duffel) → store PNR, e-tickets
8) Bot sends WhatsApp confirmation (PNR/e-tickets) + email

Edge/Exception Handling
- Price Delta > threshold: require explicit confirmation
- No inventory on issue: apologetic message + automatic reshop suggestions
- Payment timeout: mark quote expired; allow user to regenerate link
- Duplicate webhooks: idempotent by reference; no duplicate ticketing

Data Collected (PII minimal)
- Contact: email, phone (from WhatsApp when opt-in), channel external_id
- Passenger: title, first, last, dob, nationality, passport[hash/token, expiry]
- Compliance: NDPA/GDPR principles; do not log PII in plaintext

Signatures & Security
- Verify WhatsApp X-Hub-Signature-256
- Verify Paystack HMAC-SHA512 on webhook
- Store secrets in env/secret manager; RBAC for console

Observability
- Structured logs without PII; request_id per conversation
- Alerts: webhook failures, pricing mismatch, ticketing deadlines (<2h)

Acceptance Criteria
- See acceptance criteria in specs/API doc; WhatsApp flow must complete < 60s post payment for confirmations



