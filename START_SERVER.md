# Starting the Server for Twitter DM Integration

## Current Status
✅ ngrok is running!

## Step-by-Step Guide

### 1. Check Your ngrok URL
In your ngrok terminal, you should see something like:
```
Forwarding    https://abc123xyz.ngrok-free.app -> http://localhost:8001
```

Copy that HTTPS URL (e.g., `https://abc123xyz.ngrok-free.app`)

### 2. Start the Server

Open a **NEW terminal** (keep ngrok running in the other one) and run:

```bash
# Ensure DATABASE_URL points to Postgres (in .env or environment)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3. Test the Server

In a third terminal (or browser), test that it's working:

```bash
curl http://localhost:8001/health
```

Should return: `{"status":"healthy"}`

### 4. Configure Twitter Webhook

Now go to Twitter Developer Portal:

**URL:** https://developer.twitter.com/en/portal/dashboard

#### 4.1 Check App Permissions (IMPORTANT!)
1. Click on your app
2. Go to "Settings" → "App permissions"
3. Make sure it's set to: **"Read and Write and Direct Messages"**
4. If you changed this, go to "Keys and tokens" and **regenerate** your access tokens
5. Update `.env` with the new tokens

#### 4.2 Subscribe to Account Activity API
1. Go to https://developer.twitter.com/en/portal/products
2. Find "Account Activity API"
3. Subscribe to **Sandbox** tier (FREE)
4. You'll get 15 webhooks and unlimited DMs for testing

#### 4.3 Set Up Webhook Environment
1. Go to https://developer.twitter.com/en/account/environments
2. Click "Set up dev environment" (or similar)
3. Choose "Account Activity API / Sandbox"
4. Name it something like "sureflights-dev"
5. Click "Complete setup"

#### 4.4 Add Webhook URL
1. In the environment you just created, click "Add webhook URL"
2. Enter your ngrok URL + webhook path:
   ```
   https://your-ngrok-url.ngrok-free.app/webhooks/twitter
   ```
   For example: `https://abc123xyz.ngrok-free.app/webhooks/twitter`
3. Click "Add"
4. Twitter will send a CRC challenge → Your server will auto-respond ✅
5. If successful, you'll see "Valid" status

#### 4.5 Subscribe to Account Events
1. Still in the webhook environment
2. Find "Subscriptions" section
3. Click "Add" or "Subscribe"
4. Choose your bot's account (@sho87698)
5. Click "Subscribe"

### 5. Test the Bot!

Now send a Direct Message to **@sho87698**:

**Test Message 1:**
```
Hi
```
Expected response: Welcome message

**Test Message 2:**
```
Flight from Lagos to Abuja on 2025-11-15
```
Expected response: Flight search results (if OpenAI has credits)

### 6. Monitor Logs

Watch your server terminal for logs:
```
[info] dm_received sender_id=... text=...
[info] dm_sent user_id=...
```

### Troubleshooting

**"CRC validation failed"**
- Check that server is running on port 8001
- Check that ngrok is forwarding to localhost:8001
- Check server logs for errors

**"403 Forbidden" when sending DM**
- App permissions not set correctly
- Access tokens not regenerated after permission change
- Update tokens in `.env` and restart server

**"429 Quota exceeded" (OpenAI)**
- Add credits at https://platform.openai.com/account/billing
- Need at least $0.50 credit

**No response from bot**
- Check webhook is "Valid" in Twitter portal
- Check subscription is active
- Check server logs for errors
- Restart server if needed

### Quick Reference

**Your Bot:** @sho87698
**Webhook URL:** `https://[your-ngrok-url]/webhooks/twitter`
**Server:** http://localhost:8001
**Health Check:** http://localhost:8001/health

## Next Steps After Testing

Once working:
1. Consider deploying to Render/Railway for permanent URL
2. Add more Nigerian airport codes if needed
3. Test complete booking flow with payment
4. Monitor conversation success rate
5. Improve AI prompts based on user feedback
