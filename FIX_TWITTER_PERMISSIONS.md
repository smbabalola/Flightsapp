# Fix Twitter App Permissions for DM

## The Problem
Your Twitter app doesn't have permission to send Direct Messages. You're getting:
```
403 Forbidden - Your client app is not configured with the appropriate oauth1 app permissions
```

## The Solution

### Step 1: Go to Twitter Developer Portal
1. Visit: https://developer.twitter.com/en/portal/dashboard
2. Click on your app (the one you got the API keys from)

### Step 2: Enable DM Permissions
1. Click on your app name
2. Go to "Settings" tab
3. Scroll down to "App permissions"
4. Click "Edit"
5. Change permissions to **"Read and Write and Direct Messages"**
6. Click "Save"

### Step 3: Regenerate Access Tokens
**IMPORTANT:** After changing permissions, you MUST regenerate tokens!

1. Go to "Keys and tokens" tab
2. Find "Access Token and Secret" section
3. Click "Regenerate" (or "Revoke and Regenerate")
4. Copy the NEW tokens
5. Update your `.env` file with the new tokens:
   ```
   TWITTER_ACCESS_TOKEN=new_token_here
   TWITTER_ACCESS_TOKEN_SECRET=new_secret_here
   ```

### Step 4: Verify Access Level
1. Still in the Twitter Developer Portal
2. Check if you have "Essential" or "Elevated" access
3. For Account Activity API (webhooks), you need **"Elevated" access**
4. If you only have "Essential", apply for Elevated access (free, instant approval usually)

### Step 5: Test Again
After updating the tokens, run:
```bash
python test_twitter_locally.py
```

You should no longer see the "403 Forbidden" error.

## Important Notes

- **App Permissions**: Must be "Read and Write and Direct Messages"
- **Access Level**: Must be "Elevated" for webhooks
- **Tokens**: Must regenerate after changing permissions
- **Account Activity API**: Subscribe to sandbox tier (free)

## Checklist

- [ ] App permissions set to "Read and Write and Direct Messages"
- [ ] Access tokens regenerated after permission change
- [ ] New tokens updated in `.env` file
- [ ] Access level is "Elevated" (not just "Essential")
- [ ] Account Activity API sandbox subscription active

## After Fixing

Once permissions are fixed, you'll be able to:
1. ✅ Send DMs from your bot
2. ✅ Receive DMs via webhooks
3. ✅ Full two-way conversation with customers

## Still Having Issues?

Common problems:
1. **Forgot to regenerate tokens** - Must do this after changing permissions!
2. **Using old tokens** - Make sure `.env` has the NEW tokens
3. **Wrong access level** - Need Elevated, not Essential
4. **No Account Activity API** - Subscribe to sandbox tier
