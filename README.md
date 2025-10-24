# SureFlights API

A FastAPI-based flight booking platform that integrates with Duffel (flight search) and Paystack (payment processing) to provide a complete end-to-end flight booking experience.

## Features

- **Flight Search**: Real-time flight search via Duffel API with mock fallback
- **Booking Management**: Quote creation and passenger data handling
- **Payment Processing**: Paystack integration with webhook support
- **Ticket Issuance**: Automated e-ticket generation after successful payment
- **Admin Operations**: Secure endpoints for trip management
- **Metrics & Monitoring**: Prometheus-compatible metrics endpoint
- **Rate Limiting**: Token bucket implementation for API protection
- **Idempotency**: Duplicate request prevention (in-memory + Redis support)
- **Request Tracking**: X-Request-ID propagation for distributed tracing
- **Currency Conversion**: NGN equivalent display for USD prices
- **B2B Corporate Travel**: Multi-tenant company onboarding, role-based approvals, and travel request workflows for corporate customers

## B2B Onboarding & Travel Requests

1. `POST /b2b/companies` � onboard a new corporate tenant and bootstrap the first company admin account.
2. Company admins invite managers, employees, and finance approvers via `POST /b2b/members/invite` and invitations are accepted with `POST /b2b/invitations/{token}/accept`.
3. Employees create draft travel requests with `POST /b2b/travel-requests` and optionally submit immediately.
4. Managers and finance approvers action requests through `/b2b/travel-requests/{id}/approve` or `/reject`, with policies controlling the required approval chain.
5. Admin dashboards and `/b2b/companies/me` expose tenant configuration, policies, and member management.

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite (dev) / PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **HTTP Client**: httpx
- **Payment**: Paystack
- **Flight API**: Duffel v2
- **Server**: Uvicorn

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd SureFlights

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Copy `.env` and configure:

```bash
# App
ENV=dev

# Database
DATABASE_URL=sqlite+pysqlite:///./sureflights.db

# Feature flags
USE_REAL_DUFFEL=true
USE_REAL_PAYSTACK=true
USE_REDIS_IDEMPOTENCY=false
LOG_LEVEL=INFO

# Integrations
DUFFEL_API_KEY=duffel_test_YOUR_KEY_HERE
PAYSTACK_SECRET=sk_test_YOUR_KEY_HERE
PAYSTACK_PUBLIC_KEY=pk_test_YOUR_KEY_HERE
PAYSTACK_BASE_URL=https://api.paystack.co

# FX rate (NGN per 1 USD)
FX_NGN_RATE=1650

# Admin auth
ADMIN_USER=admin
ADMIN_PASS=change_me

# Optional: Sentry
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.1

# Optional: Redis for idempotency
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Migration

```bash
# Run migrations
python -m alembic upgrade head

# Verify current revision
DATABASE_URL="sqlite+pysqlite:///./sureflights.db" python -m alembic current
```

### 4. Start Server

```bash
# Development (with auto-reload)
python -m uvicorn app.main:app --reload

# Production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server runs at: `http://127.0.0.1:8000`

## API Endpoints

### Public Endpoints

#### Health & Monitoring

- `GET /` - Root endpoint with feature flags
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics (request counts, latency)

#### Flight Operations

- `POST /v1/search` - Search flights
- `GET /v1/offers/{offer_id}/price` - Get offer pricing
- `POST /v1/book` - Create booking and initiate payment

#### Trip & Payment Info

- `GET /v1/trips/{trip_id}` - Get trip details (PNR, e-tickets)
- `GET /v1/payments/{reference}` - Get payment status

#### Webhooks

- `POST /webhooks/paystack` - Paystack payment webhook (HMAC verified)
- `POST /webhooks/whatsapp` - WhatsApp webhook verification

### Admin Endpoints (HTTP Basic Auth)

- `GET /v1/ops/trips` - List trips with filters
- `POST /v1/admin/fees` - Update fee configuration

## API Usage Examples

### 1. Search Flights

```bash
curl -X POST 'http://127.0.0.1:8000/v1/search' \
  -H 'Content-Type: application/json' \
  -d '{
  "slices": [{"from_": "LOS", "to": "ABV", "date": "2025-11-15"}],
  "adults": 1,
  "cabin": "economy",
  "max_stops": 1,
  "bags_included": true
}'
```

**Response:**
```json
[{
  "offer_id": "off_0000AyoI7WAkwWwtyrgQHy",
  "price": {
    "total": "65.27",
    "currency": "USD",
    "ngn_equiv": 107696
  },
  "slices": [{"from_": "LOS", "to": "ABV", "date": "2025-11-15"}],
  "baggage": null,
  "refundability": null,
  "changes": null,
  "created_at": "2025-10-02T20:47:28.110639"
}]
```

### 2. Book Flight

```bash
curl -X POST 'http://127.0.0.1:8000/v1/book' \
  -H 'Content-Type: application/json' \
  -d '{
  "offer_id": "off_0000AyoI7WAkwWwtyrgQHy",
  "passengers": [{
    "type": "adult",
    "title": "Mr",
    "first": "John",
    "last": "Doe",
    "dob": "1990-01-01",
    "passport": {
      "number_token": "A12345678",
      "expiry": "2030-01-01",
      "nationality": "NG"
    }
  }],
  "contacts": {
    "email": "test@example.com",
    "phone": "+2348012345678"
  },
  "channel": "api"
}'
```

**Response:**
```json
{
  "payment_url": "https://checkout.paystack.com/64jamicyuuvi97x",
  "reference": "REF_64DE5BB6DAA0",
  "quote_id": 3
}
```

### 3. Simulate Payment Webhook (Testing)

```bash
# Generate signature using scripts/gen_paystack_sig.ps1
curl -X POST 'http://127.0.0.1:8000/webhooks/paystack' \
  -H 'Content-Type: application/json' \
  -H 'X-Paystack-Signature: <computed_signature>' \
  -d '{
  "event": "charge.success",
  "data": {
    "reference": "REF_64DE5BB6DAA0",
    "status": "success",
    "amount": 6527000,
    "currency": "NGN"
  }
}'
```

### 4. Get Trip Details

```bash
curl -X GET 'http://127.0.0.1:8000/v1/trips/1'
```

**Response:**
```json
{
  "id": 1,
  "pnr": "PNR42DAA0",
  "etickets": ["ET6DAA0001", "ET6DAA0002"],
  "email": "test@example.com",
  "phone": "+2348012345678"
}
```

### 5. Admin Operations

```bash
# List trips (requires admin credentials)
curl -X GET 'http://127.0.0.1:8000/v1/ops/trips?limit=10' \
  -u admin:change_me
```

## Architecture

```
app/
├── api/                    # API endpoints
│   ├── v1/                # Version 1 endpoints
│   │   ├── search.py      # Flight search
│   │   ├── bookings.py    # Booking creation
│   │   ├── trips.py       # Trip retrieval
│   │   ├── payments.py    # Payment status
│   │   ├── ops.py         # Admin operations
│   │   └── admin.py       # Admin configuration
│   ├── health.py          # Health check
│   ├── metrics.py         # Prometheus metrics
│   └── root.py            # Root endpoint
├── core/                  # Core functionality
│   ├── settings.py        # Configuration
│   ├── auth.py            # Admin auth
│   ├── logging.py         # Request ID middleware
│   ├── metrics.py         # Metrics collection
│   ├── errors.py          # Error handling
│   └── sentry.py          # Sentry integration
├── db/                    # Database
│   └── session.py         # Session management
├── integrations/          # External APIs
│   ├── duffel_client.py   # Duffel flight API
│   ├── paystack_client.py # Paystack payment API
│   ├── whatsapp_notifier.py
│   └── email_notifier.py
├── models/                # SQLAlchemy models
│   └── models.py          # Quote, Payment, Trip
├── repositories/          # Data access layer
│   ├── repos.py           # Quote, Payment repos
│   └── trips_repo.py      # Trip repository
├── services/              # Business logic
│   ├── search_service.py  # Flight search logic
│   └── booking_service.py # Booking logic
├── utils/                 # Utilities
│   ├── fx.py              # Currency conversion
│   ├── idempotency.py     # Duplicate prevention
│   ├── ratelimit.py       # Rate limiting
│   ├── retry.py           # Retry logic
│   └── security.py        # HMAC verification
├── webhooks/              # Webhook handlers
│   └── routes.py          # Paystack webhook
├── workers/               # Background tasks
│   └── ticketing_worker.py # Ticket issuance
└── main.py                # App entry point
```

## Database Schema

### Quotes
- `id` (PK)
- `offer_id` - Duffel offer identifier
- `price_total`, `price_currency` - Pricing
- `paystack_reference` - Payment reference
- `status` - Quote status (pending, paid, cancelled)
- `raw_offer` - JSON of original offer

### Payments
- `id` (PK)
- `reference` - Paystack reference
- `amount`, `currency` - Payment amount
- `status` - Payment status (pending, succeeded, failed)
- `raw` - JSON of webhook payload

### Trips
- `id` (PK)
- `quote_id` (FK) - Associated quote
- `supplier_order_id` - Duffel order ID
- `pnr` - Booking reference
- `etickets` - CSV of e-ticket numbers
- `etickets_json` - JSON array of e-tickets
- `email`, `phone` - Contact info
- `raw_order` - JSON of order details

## Feature Flags

| Flag | Description | Default |
|------|-------------|---------|
| `USE_REAL_DUFFEL` | Use live Duffel API vs mock | `false` |
| `USE_REAL_PAYSTACK` | Use live Paystack API vs mock | `false` |
| `USE_REDIS_IDEMPOTENCY` | Redis-based idempotency vs in-memory | `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `ENV` | Environment (dev/staging/prod) | `dev` |

## Rate Limiting

Token bucket implementation:
- **Default**: 5 requests per 60 seconds per IP
- **Overflow**: Returns `429 Too Many Requests`
- **Reset**: Tokens refill at 1 per 12 seconds

## Idempotency

Prevents duplicate requests using `idempotency_key`:
- **In-memory**: Default, 5-minute TTL
- **Redis**: Set `USE_REDIS_IDEMPOTENCY=true`
- Returns cached response for duplicate keys within TTL

## Monitoring

### Metrics Endpoint

`GET /metrics` returns Prometheus format:

```
# HELP sureflights_requests_total Requests by endpoint and status
# TYPE sureflights_requests_total counter
sureflights_requests_total{endpoint="/v1/search",status="200"} 12
sureflights_requests_total{endpoint="/v1/book",status="200"} 3

# HELP sureflights_endpoint_latency_ms_total Total latency by endpoint (ms)
# TYPE sureflights_endpoint_latency_ms_total counter
sureflights_endpoint_latency_ms_total{endpoint="/v1/search"} 8420
```

### Request Tracking

All requests include `X-Request-ID` header for distributed tracing.

## Testing

### Unit Tests

```bash
pytest tests/
```

### Manual E2E Test

```bash
# 1. Search
curl -X POST http://127.0.0.1:8000/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"slices":[{"from_":"LOS","to":"ABV","date":"2025-11-15"}],"adults":1}'

# 2. Book (use offer_id from search)
curl -X POST http://127.0.0.1:8000/v1/book \
  -H 'Content-Type: application/json' \
  -d '{...booking payload...}'

# 3. Simulate webhook (use reference from book)
curl -X POST http://127.0.0.1:8000/webhooks/paystack \
  -H 'X-Paystack-Signature: ...' \
  -d '{...webhook payload...}'

# 4. Get trip
curl http://127.0.0.1:8000/v1/trips/1
```

## Deployment

### Production Checklist

1. **Environment Variables**
   - Set `ENV=prod`
   - Configure `SENTRY_DSN` for error tracking
   - Use PostgreSQL: `DATABASE_URL=postgresql://...`
   - Set `USE_REDIS_IDEMPOTENCY=true`
   - Update `ADMIN_PASS` to strong password

2. **Database**
   - Run migrations: `python -m alembic upgrade head`
   - Set up PostgreSQL connection pooling
   - Enable database backups

3. **Security**
   - Enable HTTPS
   - Rotate API keys regularly
   - Use secret management (AWS Secrets Manager, etc.)
   - Set up WAF/DDoS protection

4. **Monitoring**
   - Configure Sentry for error tracking
   - Set up Prometheus/Grafana for metrics
   - Enable application logging
   - Set up uptime monitoring

5. **Scaling**
   - Use Redis for idempotency at scale
   - Deploy multiple instances behind load balancer
   - Configure database replicas for reads

## Troubleshooting

### Server won't start

**Error**: `ModuleNotFoundError`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error**: `Duffel API version unsupported`
```bash
# Solution: Check duffel_client.py uses "Duffel-Version": "v2"
```

### Database issues

**Error**: `No such table: quotes`
```bash
# Solution: Run migrations
python -m alembic upgrade head
```

**Error**: `sqlite3.ProgrammingError: Error binding parameter`
```bash
# Solution: Ensure JSON data is serialized with json.dumps() for SQLite
```

### API errors

**429 Too Many Requests**
- Wait 60 seconds for rate limit reset
- Or adjust rate limiting in `app/utils/ratelimit.py`

**401 Unauthorized (admin endpoints)**
- Check `ADMIN_USER` and `ADMIN_PASS` in `.env`
- Verify HTTP Basic Auth credentials

**422 Unprocessable Entity**
- Validate request JSON matches API schema
- Check required fields are present

### Webhook testing

**Error**: `Invalid signature`
```bash
# Solution: Use scripts/gen_paystack_sig.ps1 to generate correct HMAC signature
# Or disable verification in dev by setting PAYSTACK_SECRET=""
```

## Development

### Adding a new endpoint

1. Create endpoint in `app/api/v1/your_endpoint.py`
2. Add router to `app/api/v1/__init__.py`
3. Include in `app/main.py` if needed
4. Add tests in `tests/`

### Creating a migration

```bash
# Auto-generate migration
python -m alembic revision --autogenerate -m "description"

# Edit migration file in migrations/versions/
# Apply migration
python -m alembic upgrade head
```

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.

Updates:
- Added cabin-class selection to search flow (passed through API).
- Added light/dark theme toggle with saved preference.
- Booking now requires login before proceeding to payment.

