# Twitter DM Bot Setup - Step by Step

## ✅ COMPLETED
1. **Server is running** on port 8001
   - Health check: http://localhost:8001/health
   - Status: All integrations healthy (Duffel ✅, Paystack ✅)

2. **ngrok is running**
   - Tunneling to port 8001

## 🔄 NEXT STEPS

### Step 1: Get Your ngrok URL

Look at your ngrok terminal. You should see something like:

```
Forwarding    https://abc-123-xyz.ngrok-free.app -> http://localhost:8001
```

**Copy that HTTPS URL!** You'll need it in the next steps.

Example: `https://abc-123-xyz.ngrok-free.app`

---

### Step 2: Fix Twitter App Permissions ⚠️ CRITICAL

**This is blocking DM functionality - must fix!**

1. Go to: https://developer.twitter.com/en/portal/dashboard

2. Click on your app

3. Go to **"Settings"** tab

4. Scroll to **"App permissions"**

5. Click **"Edit"**

6. Select: **"Read and Write and Direct Messages"**

7. Click **"Save"**

8. **IMPORTANT:** Go to **"Keys and tokens"** tab

9. Under "Access Token and Secret", click **"Regenerate"**

10. Copy the NEW tokens:
    - New Access Token
    - New Access Token Secret

11. Update your `.env` file:
    ```env
    TWITTER_ACCESS_TOKEN=your_new_token_here
    TWITTER_ACCESS_TOKEN_SECRET=your_new_secret_here
    ```

12. Restart the server (Ctrl+C and run `start.bat` again)

---

### Step 3: Subscribe to Account Activity API (FREE)

1. Go to: https://developer.twitter.com/en/portal/products

2. Find **"Premium"** section

3. Click on **"Account Activity API"**

4. Click **"Subscribe"** for **Sandbox** tier (FREE)
   - 15 webhooks
   - Unlimited DMs
   - Perfect for testing

5. If prompted, create a "Dev environment"
   - Name: `sureflights-dev` (or anything you like)
   - Choose: Account Activity API / Sandbox

---

### Step 4: Register Your Webhook

1. Go to: https://developer.twitter.com/en/account/environments

2. Find your dev environment (e.g., `sureflights-dev`)

3. Click **"Add webhook URL"**

4. Enter:
   ```
   https://YOUR-NGROK-URL/webhooks/twitter
   ```

   Example:
   ```
   https://abc-123-xyz.ngrok-free.app/webhooks/twitter
   ```

5. Click **"Add"**

6. Twitter will send a CRC challenge
   - Your server will automatically respond ✅
   - You should see "Valid" status

**Check Server Logs:**
You should see:
```
[info] twitter_crc_validated
```

---

### Step 5: Subscribe Your Bot Account

1. Still in the webhook environment

2. Find **"Subscriptions"** section

3. Click **"Add subscription"** or **"Subscribe"**

4. Select your bot account: **@sho87698**

5. Click **"Subscribe"**

6. Status should show: "Subscribed ✅"

---

### Step 6: Add OpenAI Credits (For AI Conversation)

**Current issue:** Quota exceeded

1. Go to: https://platform.openai.com/account/billing

2. Click **"Add payment method"**

3. Add a card and deposit $5-10

4. Your API key will start working immediately

**Note:** Without credits, the bot can't understand flight search requests intelligently. It will fall back to basic responses.

---

### Step 7: Test Your Bot! 🎉

Send a DM to **@sho87698** on Twitter:

**Test 1: Greeting**
```
Hi
```
Expected: Welcome message

**Test 2: Flight Search**
```
Flight from Lagos to Abuja on 2025-11-15
```
Expected: Flight options (1-5)

**Test 3: Select Flight**
```
1
```
Expected: Request for passenger details

**Test 4: Passenger Info**
```
Name: John Doe
Email: john@example.com
Phone: +2348012345678
DOB: 1990-01-15
```
Expected: Booking summary

**Test 5: Confirm**
```
confirm
```
Expected: Payment link!

---

## Monitoring

Watch your server terminal for logs:

```bash
# Good signs:
[info] dm_received sender_id=... text=...
[info] dm_sent user_id=...
[info] flight_search origin=LOS destination=ABV

# Issues:
[error] dm_send_error error='403 Forbidden'  # App permissions not fixed
[error] ai_parse_error error='429'           # OpenAI no credits
```

---

## Troubleshooting

### "CRC validation failed"
- ✅ Server running? Check: http://localhost:8001/health
- ✅ ngrok running? Check ngrok terminal
- ✅ Correct webhook URL? Should end with `/webhooks/twitter`

### "403 Forbidden" on DM
- ❌ App permissions not set to "Read and Write and Direct Messages"
- ❌ Forgot to regenerate tokens after changing permissions
- ❌ Old tokens still in `.env` file

### "Bot doesn't respond"
- ❌ Webhook not "Valid" status
- ❌ Bot account not subscribed
- ❌ Server errors (check logs)

### "429 Quota exceeded"
- ❌ No OpenAI credits
- Add credits at: https://platform.openai.com/account/billing

---

## Quick Reference

| Item | Value |
|------|-------|
| Bot Username | @sho87698 |
| Bot User ID | 1974310868901851136 |
| Server | http://localhost:8001 |
| Webhook Path | /webhooks/twitter |
| Full Webhook URL | https://[ngrok-url]/webhooks/twitter |

---

## Current Status Checklist

- [x] Server running on port 8001
- [x] ngrok tunnel active
- [x] Twitter API connected
- [ ] App permissions: "Read and Write and DM" ⚠️
- [ ] Access tokens regenerated ⚠️
- [ ] Account Activity API subscribed
- [ ] Webhook registered and valid
- [ ] Bot account subscribed
- [ ] OpenAI credits added
- [ ] End-to-end DM test successful

---

## Need Help?

Check the logs in your server terminal. Most issues will show up there with clear error messages.

**Server is healthy and ready!** Just need to complete the Twitter setup steps above. 🚀
