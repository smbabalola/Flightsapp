# Deployment Options for Twitter DM Integration

Since ngrok isn't working on your network, here are alternative ways to get your bot online:

## Option 1: Localtunnel (Easiest Alternative to ngrok)

### Install
```bash
npm install -g localtunnel
```

### Run
```bash
# Terminal 1: Start your server (ensure DATABASE_URL is set for Postgres)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Start localtunnel
lt --port 8001
```

You'll get a URL like: `https://random-name-123.loca.lt`

Use this URL for Twitter webhooks: `https://random-name-123.loca.lt/webhooks/twitter`

## Option 2: Serveo (No Installation Required!)

```bash
# Terminal 1: Start your server (ensure DATABASE_URL is set for Postgres)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Start serveo tunnel
ssh -R 80:localhost:8001 serveo.net
```

You'll get a URL like: `https://random.serveo.net`

## Option 3: Cloudflare Tunnel (Free, Reliable)

### Install
```bash
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

### Run
```bash
# Terminal 1: Start your server (ensure DATABASE_URL is set for Postgres)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Start cloudflare tunnel
cloudflared tunnel --url http://localhost:8001
```

## Option 4: Deploy to Cloud (Production Ready)

### Render.com (Recommended - Free Tier)

1. Create account at https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repo (or deploy from URL)
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Add all your .env variables
5. Deploy!

You'll get: `https://your-app-name.onrender.com`

### Railway.app (Also Free Tier)

1. Go to https://railway.app
2. Click "Start a New Project"
3. Deploy from GitHub
4. Add environment variables from .env
5. Deploy!

### Vercel (Serverless)

Good for APIs, but might need adjustments for WebSocket/long-running processes.

## Option 5: Fix ngrok Connection

If you want to fix ngrok specifically:

### Check 1: Firewall
```bash
# Windows Firewall might be blocking
# Go to: Windows Security → Firewall & network protection → Allow an app
# Add ngrok.exe
```

### Check 2: Antivirus
Your antivirus might be blocking ngrok. Temporarily disable and test.

### Check 3: Corporate Network
If on a corporate network, ngrok might be blocked. Try:
- Using personal hotspot
- VPN
- Different network

### Check 4: ngrok Config
```bash
# Update ngrok
ngrok update

# Try different region
ngrok http 8001 --region eu
```

## Recommendation

**For Testing (Quick):**
- Use **localtunnel** or **serveo** (no account needed)

**For Production (Permanent):**
- Deploy to **Render** or **Railway** (free tier, always on)

## Example: Full Setup with Localtunnel

```bash
# 1. Install localtunnel
npm install -g localtunnel

# 2. Start server (ensure DATABASE_URL is set for Postgres)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 3. In another terminal, start tunnel
lt --port 8001

# 4. You'll get a URL, use it in Twitter Developer Portal:
# Webhook URL: https://your-url.loca.lt/webhooks/twitter

# 5. Test by sending DM to @sho87698
```

## After Deployment

1. Copy your public URL
2. Go to Twitter Developer Portal
3. Add webhook: `https://your-url/webhooks/twitter`
4. Twitter will send CRC challenge - your server will auto-respond
5. Send DM to @sho87698 to test!

## Testing Checklist

- [ ] Server running on port 8001
- [ ] Tunnel/deployment providing public HTTPS URL
- [ ] Twitter app permissions set correctly
- [ ] Webhook registered in Twitter Developer Portal
- [ ] OpenAI credits added to account
- [ ] Test DM sent to bot

Let me know which option you want to try!
