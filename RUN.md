Run with: uvicorn app.main:app --reload

Environment
- Copy .env.example to .env and fill secrets (DATABASE_URL, PAYSTACK_SECRET, WHATSApp tokens)
- Or export as environment variables


Logging: Set LOG_LEVEL and send X-Request-ID to propagate tracing.


Idempotency: Set USE_REDIS_IDEMPOTENCY=true and REDIS_URL to enable Redis-backed keys.


Feature flags: USE_REAL_DUFFEL/USE_REAL_PAYSTACK toggle real API calls. Provide DUFFEL_API_KEY and PAYSTACK_SECRET (+ PAYSTACK_PUBLIC_KEY).


Paystack: Set USE_REAL_PAYSTACK=true and PAYSTACK_SECRET/PAYSTACK_PUBLIC_KEY to use live/sandbox initialize endpoint.


Duffel: Set USE_REAL_DUFFEL=true and DUFFEL_API_KEY to use real search. The client calls /air/offer_requests and /air/offers/{id}.


FX: Set FX_NGN_RATE to compute ngn_equiv for prices.
