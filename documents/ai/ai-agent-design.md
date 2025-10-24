# AI Booking Agent – Design

Objective: AI assistant that understands natural-language flight intents on WhatsApp (worldwide coverage) and orchestrates the backend search/booking/ticket flows safely.

Architecture
- Channel adapter: WhatsApp webhook → message router
- Orchestrator: state machine managing conversation states and slots
- Intent parsing: rule-based + LLM hybrid (optional) with deterministic fallbacks
- Tools/Actions: call FastAPI endpoints (/v1/search, /v1/offers/{id}/price, /v1/book)
- Handover: escalation to human agent when confidence low or exceptions occur

State & Slots
- Required: origin, destination, date(s), pax (adults/children/infants), cabin, bags
- Optional: time window, preferred airlines, refundable-only
- Booking details: passenger names, DOB, nationality, passport numbers (masked), contacts

Safety & Guardrails
- Confirm parsed itinerary before booking actions
- Re-confirm on any price change
- Never echo full passport/card data
- Idempotency on quote creation and payment

Evaluation & Tuning (MVP)
- Seed intents with regex + examples (LOS-ABV, 2025-11-05, 1 adult)
- Add global IATA lexicon (e.g., JFK, LHR, DXB, LOS, ABV, PHC) and Nigeria emphasis
- Measure: time-to-3-offers, conversion rate, fallbacks to human

Handover Protocol
- Trigger on: low intent confidence, supplier error, payment issues, schedule change
- Provide agent context: conversation transcript (sanitized), parsed search, top offers, quote status

Roadmap
- Phase 2: richer NER, multi-city, rebooking automation
- Phase 3: proactive disruption handling, loyalty personalization



