# Quick Start Checklist - Twitter & Voice Integration

## 📋 Pre-Launch Checklist

### 1. ✅ Dependencies (DONE)
- [x] Installed tweepy
- [x] Installed twilio
- [x] Installed openai
- [x] Updated requirements.txt

### 2. 🔑 API Credentials (TODO - You Need To Do This)

#### Twitter API
- [ ] Create/Access Twitter Developer Account
- [ ] Create new App or use existing
- [ ] Get API Key & Secret
- [ ] Get Access Token & Secret
- [ ] Get Bearer Token
- [ ] Update `.env` with Twitter credentials

#### Twilio
- [ ] Sign up at https://www.twilio.com
- [ ] Copy Account SID
- [ ] Copy Auth Token
- [ ] Purchase phone number with Voice capability
- [ ] Update `.env` with Twilio credentials

#### OpenAI
- [ ] Get API key from https://platform.openai.com
- [ ] Update `.env` with OpenAI key

### 3. 🌐 Webhook Setup (TODO)

#### For Local Testing (Recommended First)
- [ ] Install ngrok: `npm install -g ngrok` or download from ngrok.com
- [ ] Start ngrok: `ngrok http 8001`
- [ ] Copy ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`)

#### Twitter Webhook Configuration
- [ ] Go to Twitter Developer Portal
- [ ] Navigate to Account Activity API
- [ ] Subscribe to Sandbox (free tier)
- [ ] Create webhook environment
- [ ] Add webhook URL: `https://your-ngrok-url.ngrok.io/webhooks/twitter`
- [ ] Twitter will send CRC challenge - server will auto-respond
- [ ] Subscribe to user events (your bot account)

#### Twilio Webhook Configuration
- [ ] Go to Twilio Console
- [ ] Navigate to Phone Numbers
- [ ] Click your purchased number
- [ ] Under "Voice & Fax":
  - Set "A Call Comes In" to `https://your-ngrok-url.ngrok.io/webhooks/voice/incoming`
  - Set HTTP POST
- [ ] Save configuration

### 4. 🧪 Testing (TODO)

#### Test Twitter DM
- [ ] Start server: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload` (ensure `DATABASE_URL` points to Postgres)
- [ ] Send DM to your bot: "Hi"
- [ ] Verify welcome message received
- [ ] Send: "Flight from Lagos to Abuja on 2025-11-15"
- [ ] Verify flight options received
- [ ] Reply with number (1-5)
- [ ] Verify passenger info request
- [ ] Provide passenger details
- [ ] Reply "confirm"
- [ ] Verify booking confirmation

#### Test Voice Call
- [ ] Ensure server is running
- [ ] Call your Twilio number
- [ ] Verify greeting plays
- [ ] Say "Lagos" when asked for origin
- [ ] Verify destination prompt
- [ ] Say "Abuja" when asked for destination
- [ ] Say "tomorrow" when asked for date
- [ ] Listen to flight options
- [ ] Say "option 1" to select
- [ ] Say passenger name when prompted
- [ ] Verify booking confirmation
- [ ] Check for SMS with payment link

### 5. 📊 Monitoring (Ongoing)

- [ ] Check server logs for errors
- [ ] Monitor OpenAI API usage (costs)
- [ ] Monitor Twilio usage (costs)
- [ ] Track conversation success rates
- [ ] Review failed bookings

## 🚨 Troubleshooting Quick Reference

### Twitter Issues
| Issue | Solution |
|-------|----------|
| CRC validation fails | Verify TWITTER_API_SECRET in .env |
| No DM received | Check Account Activity API subscription status |
| Bot doesn't respond | Check logs, verify OpenAI API key |

### Voice Issues
| Issue | Solution |
|-------|----------|
| Call doesn't connect | Verify webhook URL in Twilio console |
| No voice response | Check TwiML generation in logs |
| Speech not recognized | Ensure clear audio, check OpenAI key |
| No SMS received | Verify phone number has SMS capability |

### General Issues
| Issue | Solution |
|-------|----------|
| Import errors | Run `pip install -r requirements.txt` |
| Database errors | Run migrations |
| Server won't start | Check .env configuration |

## 🎯 Production Deployment Checklist

- [ ] Get production domain with HTTPS
- [ ] Update Twitter webhook to production URL
- [ ] Update Twilio webhook to production URL
- [ ] Set production API keys in .env
- [ ] Enable monitoring/logging (Sentry configured)
- [ ] Set up Redis for session persistence
- [ ] Configure auto-scaling if needed
- [ ] Set up backup/disaster recovery
- [ ] Document operational procedures
- [ ] Train support team on new channels

## 📞 Support Channels Matrix

| Channel | Status | Use Case |
|---------|--------|----------|
| WhatsApp | ✅ Existing | Customer bookings |
| Twitter DM | ✅ NEW | Social media bookings |
| Voice Call | ✅ NEW | Phone bookings |
| Web | ✅ Existing | Online bookings |

## 🎉 Launch Ready!

Once you complete the TODO items above, you'll have:
- ✅ Twitter DM booking bot
- ✅ Voice call booking system
- ✅ AI-powered conversation handling
- ✅ SMS notifications
- ✅ Multi-channel booking platform

**Next Steps:**
1. Complete API credential setup
2. Configure webhooks
3. Test thoroughly
4. Launch to users!
