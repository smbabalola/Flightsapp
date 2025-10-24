# API and Data Specs (MVP)

Base: FastAPI backend, Postgres (Alembic), Duffel (global content), Domestic consolidator (Nigeria) for local carriers, Paystack, WhatsApp Cloud API.

Endpoints (v1)
- POST /v1/search
  Body: { slices[{from,to,date,time_window?}], adults, children, infants, cabin, max_stops, bags_included }
  Returns: [{ offer_id, price{total,currency,ngn_equiv?}, slices[], baggage, refundability, changes, created_at }]
- POST /v1/offers/{offer_id}/price
  Returns: { price{total,currency,ngn_equiv?}, valid_until?, delta }
- POST /v1/book
  Body: { offer_id, passengers[{type,title,first,last,dob,passport{number_token,expiry,nationality}}], contacts{email,phone}, channel }
  Action: creates Quote, initializes Paystack; returns { payment_url, reference }
- POST /v1/orders/issue (internal)
  Body: { quote_id } → issues order & tickets; stores { pnr, etickets[] }
- GET /v1/trips/{id}
- POST /webhooks/paystack (signed, idempotent)
- GET/POST /webhooks/whatsapp (signed)

Data Model (simplified, worldwide)
- customers(id, email, phone, channel, external_id, created_at)
- travelers(id, customer_id FK, title, first, last, dob, nationality, doc_hash, doc_last4?, redress?)
- quotes(id, offer_id, price_minor, currency, ngn_snapshot_rate, email, phone, channel, status[awaiting_payment|paid|ticketed|expired], paystack_reference, raw_offer, created_at)
- payments(id, quote_id FK, provider, reference, amount_minor, currency, status[initialized|succeeded|failed|refunded], raw, created_at)
- trips(id, quote_id FK, supplier_order_id, pnr, etickets[], email, phone, created_at, raw_order)
- ancillaries(id, trip_id FK, type[seat|bag|meal], amount_minor, currency, details)
- audit_logs(id, event, actor[user_id|system], details JSON, created_at)
- users(id, email, name, role[agent|supervisor|finance|admin], hash_password, status)
- fees(id, rule JSON, flat_minor, percent)

Security & Compliance
- NDPA, GDPR principles; PCI-DSS via Paystack; never store PAN
- Field-level encryption or tokenization for passport numbers; avoid PII in logs
- Signed webhooks (Paystack HMAC-SHA512, WhatsApp X-Hub-Signature-256)

Acceptance Criteria (MVP)
- Search ≥3 offers <3s P95; reprice <2s P95
- /v1/book → Paystack link; quote in awaiting_payment
- On charge.success → tickets issued; WhatsApp + email within 60s
- Webhooks 401 on invalid signatures; idempotent under duplicates



