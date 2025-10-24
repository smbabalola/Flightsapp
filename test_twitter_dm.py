"""Test Twitter DM integration without requiring OpenAI."""
import asyncio
from app.twitter.client import get_twitter_client


async def test_twitter_connection():
    """Test Twitter API connection."""
    print("\n" + "=" * 60)
    print("TWITTER API CONNECTION TEST")
    print("=" * 60)

    try:
        client = get_twitter_client()

        if client.me and client.me.data:
            print(f"\n[SUCCESS] Connected to Twitter API successfully!")
            print(f"  Bot User ID: {client.me.data.id}")
            print(f"  Bot Username: @{client.me.data.username}")
            print(f"  Bot Name: {client.me.data.name}")
            print("\nTwitter integration is ready!")
            return True
        else:
            print("\n[FAILED] Failed to authenticate with Twitter API")
            print("  Check your credentials in .env file")
            return False

    except Exception as e:
        print(f"\n[ERROR] Error connecting to Twitter: {str(e)}")
        print("\nPossible issues:")
        print("  1. Invalid API credentials")
        print("  2. API access level insufficient (need Elevated access for DMs)")
        print("  3. Bearer token or Access tokens incorrect")
        return False


async def send_test_dm():
    """Send a test DM to verify DM functionality."""
    print("\n" + "=" * 60)
    print("TWITTER DM TEST (OPTIONAL)")
    print("=" * 60)

    try:
        client = get_twitter_client()

        # Get bot's own user info
        if not client.me or not client.me.data:
            print("\n[FAILED] Cannot send test DM - bot not authenticated")
            return False

        print("\nTo test DM functionality:")
        print(f"1. Send a DM to your bot account (@{client.me.data.username})")
        print("2. The bot will respond via webhook (once configured)")
        print("\nSkipping automated DM test (requires recipient user ID)")

        return True

    except Exception as e:
        print(f"\n[ERROR] Error in DM test: {str(e)}")
        return False


def check_webhook_requirements():
    """Check webhook setup requirements."""
    print("\n" + "=" * 60)
    print("WEBHOOK SETUP CHECKLIST")
    print("=" * 60)

    print("\nFor Twitter DM integration to work, you need:")
    print("\n1. [DONE] Twitter API credentials (configured in .env)")
    print("   - API Key")
    print("   - API Secret")
    print("   - Access Token")
    print("   - Access Token Secret")
    print("   - Bearer Token")

    print("\n2. [TODO] Twitter API Access Level")
    print("   - Go to: https://developer.twitter.com/en/portal/dashboard")
    print("   - Your app needs 'Elevated' access for Account Activity API")
    print("   - Apply for Elevated access if you have 'Essential' only")

    print("\n3. [TODO] Account Activity API Subscription")
    print("   - Go to: https://developer.twitter.com/en/portal/products/premium")
    print("   - Subscribe to 'Account Activity API' (Sandbox tier is FREE)")
    print("   - This allows DM webhooks")

    print("\n4. [TODO] Webhook URL Configuration")
    print("   - You need a public HTTPS URL for webhooks")
    print("   - For local testing: Use ngrok")
    print("     $ ngrok http 8001")
    print("   - Register webhook: https://your-ngrok-url/webhooks/twitter")

    print("\n5. [TODO] OpenAI API Key (for AI conversation)")
    print("   - Get from: https://platform.openai.com/api-keys")
    print("   - Add to .env: OPENAI_API_KEY=sk-...")
    print("   - Required for intelligent conversation handling")


async def main():
    """Run all Twitter tests."""
    print("\n")
    print("*" * 60)
    print("  TWITTER DM INTEGRATION - CONNECTION TEST")
    print("*" * 60)

    # Test connection
    connected = await test_twitter_connection()

    if connected:
        # Test DM capability
        await send_test_dm()

    # Show setup requirements
    check_webhook_requirements()

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)

    if connected:
        print("\n[SUCCESS] Twitter API connection successful!")
        print("\nTo enable Twitter DM bookings:")
        print("\n1. Get OpenAI API key and add to .env")
        print("2. Apply for Twitter Elevated access (if needed)")
        print("3. Subscribe to Account Activity API (free)")
        print("4. Start server:")
        print('   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload  # ensure DATABASE_URL is set to Postgres')
        print("5. Set up ngrok: ngrok http 8001")
        print("6. Register webhook in Twitter Developer Portal")
        print("7. Test by sending DM to your bot")
    else:
        print("\n[FAILED] Twitter API connection failed")
        print("\nPlease check your credentials in .env file")

    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
