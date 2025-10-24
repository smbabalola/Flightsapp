# Twitter & Voice Integration Setup Guide

This guide explains how to set up and test the new Twitter DM and Twilio Voice integrations for SureFlights.

## Prerequisites

1. **Twitter Developer Account** (You mentioned you already have this)
2. **Twilio Account** (Sign up at https://www.twilio.com)
3. **OpenAI API Key** (For conversational AI)

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Twitter Setup

1. Go to your Twitter Developer Portal (https://developer.twitter.com/en/portal/dashboard)
2. Create a new app or use existing app
3. Go to "Keys and Tokens" section
4. Copy the following credentials to your `.env` file:

```env
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
```

5. Set up Account Activity API:
   - Go to "Products" > "Premium" > "Account Activity API"
   - Subscribe to the Sandbox tier (free)
   - Create a webhook environment
   - Set webhook URL: `https://yourdomain.com/webhooks/twitter`

6. Test the CRC (Challenge Response Check):
```bash
curl -X GET "https://yourdomain.com/webhooks/twitter?crc_token=test"
```

### 2. Twilio Setup

1. Sign up at https://www.twilio.com
2. Go to Console Dashboard
3. Copy your Account SID and Auth Token to `.env`:

```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

4. Get a phone number:
   - Go to "Phone Numbers" > "Buy a Number"
   - Choose a number with Voice capabilities
   - Add to `.env`:

```env
TWILIO_PHONE_NUMBER=+1234567890
```

5. Configure Voice webhook:
   - Go to your phone number settings
   - Set "A Call Comes In" webhook to: `https://yourdomain.com/webhooks/voice/incoming`
   - Set HTTP POST

### 3. OpenAI Setup

1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
```

## Testing

### Test Twitter DM Flow

1. Start the server (ensure DATABASE_URL points to Postgres):
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

2. Send a DM to your Twitter bot account:
   - "Hi" - Should receive welcome message
   - "Flight from Lagos to Abuja on 2025-11-15" - Should search flights
   - Reply with number (1-5) to select flight
   - Provide passenger details
   - Reply "confirm" to complete booking

### Test Voice Call Flow

1. Ensure server is running (same as above)

2. Call your Twilio phone number

3. Follow the voice prompts:
   - Say origin city (e.g., "Lagos")
   - Say destination city (e.g., "Abuja")
   - Say travel date (e.g., "tomorrow" or "November 15th")
   - Listen to flight options
   - Say option number (e.g., "option 2")
   - Say passenger name (e.g., "John Doe")
   - Booking confirmed, SMS sent with payment link

## Webhook Endpoints

### Twitter Webhooks
- `GET /webhooks/twitter` - CRC validation
- `POST /webhooks/twitter` - DM events

### Voice Webhooks
- `POST /webhooks/voice/incoming` - Incoming call handler
- `POST /webhooks/voice/collect-origin` - Origin collection
- `POST /webhooks/voice/collect-destination` - Destination collection
- `POST /webhooks/voice/collect-date` - Date collection
- `POST /webhooks/voice/select-flight` - Flight selection
- `POST /webhooks/voice/collect-passenger` - Passenger info
- `POST /webhooks/voice/status` - Call status updates

## Architecture

### Twitter Integration
- **Client** (`app/twitter/client.py`) - Twitter API v2 client for DM operations
- **Session Manager** (`app/twitter/session.py`) - In-memory conversation state
- **AI Assistant** (`app/twitter/ai_assistant.py`) - OpenAI-powered natural language understanding
- **Handler** (`app/twitter/handler.py`) - Main conversation flow orchestration
- **Routes** (`app/twitter/routes.py`) - Webhook endpoints

### Voice Integration
- **Client** (`app/voice/client.py`) - Twilio client for voice and SMS
- **Session Manager** (`app/voice/session.py`) - In-memory call state
- **AI Assistant** (`app/voice/ai_voice.py`) - Speech-to-intent processing
- **Handler** (`app/voice/handler.py`) - Voice conversation flow with TwiML
- **Routes** (`app/voice/routes.py`) - Twilio webhook endpoints

## Deployment Notes

1. **Use HTTPS**: Both Twitter and Twilio require HTTPS webhooks in production
2. **Set up ngrok for local testing**:
   ```bash
   ngrok http 8001
   ```
   Then use the ngrok URL for webhook configuration

3. **Environment Variables**: Ensure all API keys are properly set in production

4. **Monitoring**: Check logs for conversation flow and errors:
   ```python
   logger.info("dm_received", sender_id=sender_id, text=message_text)
   ```

## Troubleshooting

### Twitter Issues
- **CRC fails**: Check that Twitter API secret is correct
- **No DM received**: Verify webhook is registered and Account Activity API subscription is active
- **Bot doesn't respond**: Check logs for errors, verify OpenAI API key

### Voice Issues
- **Call doesn't connect**: Verify Twilio phone number webhook URL
- **Speech not recognized**: Check OpenAI API key, ensure clear speech input
- **No SMS received**: Verify Twilio account has SMS capabilities

### General Issues
- **Import errors**: Run `pip install -r requirements.txt`
- **Database errors**: Run migrations: `python -m alembic upgrade head` (with `DATABASE_URL` set to Postgres)
- **Rate limiting**: Adjust rate limits in respective handlers

## Next Steps

1. **Add persistent storage**: Move from in-memory sessions to Redis/database
2. **Enhanced NLP**: Fine-tune AI prompts for better understanding
3. **Multi-language support**: Add Nigerian Pidgin, Yoruba, Hausa, Igbo
4. **Voice customization**: Use Twilio's voice options for local accents
5. **Analytics**: Track conversation metrics and conversion rates
