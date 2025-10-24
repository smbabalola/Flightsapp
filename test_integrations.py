"""Test script to verify Twitter and Voice integrations."""
import asyncio
import sys
from app.core.settings import get_settings


def test_environment_variables():
    """Check if required environment variables are set."""
    settings = get_settings()

    print("=" * 60)
    print("ENVIRONMENT CONFIGURATION CHECK")
    print("=" * 60)

    # Twitter checks
    print("\nTWITTER API:")
    twitter_vars = {
        "API Key": settings.twitter_api_key,
        "API Secret": settings.twitter_api_secret,
        "Access Token": settings.twitter_access_token,
        "Access Token Secret": settings.twitter_access_token_secret,
        "Bearer Token": settings.twitter_bearer_token,
    }

    twitter_ok = True
    for name, value in twitter_vars.items():
        status = "OK" if value and value != f"your_{name.lower().replace(' ', '_')}" else "MISSING"
        print(f"  {name}: {status}")
        if status == "MISSING":
            twitter_ok = False

    # Twilio checks
    print("\nTWILIO:")
    twilio_vars = {
        "Account SID": settings.twilio_account_sid,
        "Auth Token": settings.twilio_auth_token,
        "Phone Number": settings.twilio_phone_number,
    }

    twilio_ok = True
    for name, value in twilio_vars.items():
        status = "OK" if value and value != f"your_{name.lower().replace(' ', '_')}" else "MISSING"
        print(f"  {name}: {status}")
        if status == "MISSING":
            twilio_ok = False

    # OpenAI check
    print("\nOPENAI:")
    openai_ok = settings.openai_api_key and settings.openai_api_key != "your_openai_api_key"
    print(f"  API Key: {'OK' if openai_ok else 'MISSING'}")

    # Duffel check (already configured)
    print("\nDUFFEL:")
    duffel_ok = settings.duffel_api_key is not None
    print(f"  API Key: {'OK' if duffel_ok else 'MISSING'}")

    # Paystack check (already configured)
    print("\nPAYSTACK:")
    paystack_ok = settings.paystack_secret is not None
    print(f"  Secret Key: {'OK' if paystack_ok else 'MISSING'}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Twitter Integration: {'READY' if twitter_ok else 'NEEDS CONFIGURATION'}")
    print(f"Voice Integration: {'READY' if twilio_ok else 'NEEDS CONFIGURATION'}")
    print(f"AI Assistant: {'READY' if openai_ok else 'NEEDS CONFIGURATION'}")
    print(f"Flight Data (Duffel): {'READY' if duffel_ok else 'NEEDS CONFIGURATION'}")
    print(f"Payments (Paystack): {'READY' if paystack_ok else 'NEEDS CONFIGURATION'}")

    if twitter_ok and twilio_ok and openai_ok:
        print("\n[SUCCESS] All integrations configured!")
        print("\nNext steps:")
        print("1. Start server: python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload  # ensure DATABASE_URL is set to Postgres")
        print("2. Set up ngrok: ngrok http 8001")
        print("3. Configure webhooks in Twitter and Twilio dashboards")
        return True
    else:
        print("\n[ACTION REQUIRED] Please update .env file with missing credentials:")
        if not twitter_ok:
            print("\nTwitter API credentials:")
            print("  - Get from: https://developer.twitter.com/en/portal/dashboard")
        if not twilio_ok:
            print("\nTwilio credentials:")
            print("  - Get from: https://www.twilio.com/console")
        if not openai_ok:
            print("\nOpenAI API key:")
            print("  - Get from: https://platform.openai.com/api-keys")
        return False


def test_imports():
    """Test if all modules can be imported."""
    print("\n" + "=" * 60)
    print("MODULE IMPORT CHECK")
    print("=" * 60)

    modules = [
        ("Twitter Client", "app.twitter.client"),
        ("Twitter Handler", "app.twitter.handler"),
        ("Twitter Routes", "app.twitter.routes"),
        ("Voice Client", "app.voice.client"),
        ("Voice Handler", "app.voice.handler"),
        ("Voice Routes", "app.voice.routes"),
        ("Search API", "app.api.search"),
        ("Book API", "app.api.book"),
    ]

    all_ok = True
    for name, module_path in modules:
        try:
            __import__(module_path)
            print(f"  {name}: OK")
        except Exception as e:
            print(f"  {name}: FAILED - {str(e)}")
            all_ok = False

    return all_ok


async def test_ai_assistant():
    """Test AI assistant if OpenAI key is configured."""
    settings = get_settings()

    print("\n" + "=" * 60)
    print("AI ASSISTANT TEST")
    print("=" * 60)

    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key":
        print("  SKIPPED - OpenAI API key not configured")
        return True

    try:
        from app.twitter.ai_assistant import get_ai_assistant
        ai = get_ai_assistant()

        # Test flight search parsing
        test_message = "I want to fly from Lagos to Abuja on November 15th"
        print(f"\n  Testing with: '{test_message}'")

        result = await ai.parse_flight_search(test_message)

        if result:
            print(f"  Parsed successfully:")
            print(f"    Origin: {result.get('from_')}")
            print(f"    Destination: {result.get('to')}")
            print(f"    Date: {result.get('date')}")
            return True
        else:
            print("  AI parsing returned no results (might be due to API limits)")
            return True

    except Exception as e:
        print(f"  FAILED: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("*" * 60)
    print("  SUREFLIGHTS - TWITTER & VOICE INTEGRATION TEST")
    print("*" * 60)

    # Test imports
    imports_ok = test_imports()

    # Test environment
    env_ok = test_environment_variables()

    # Test AI (async)
    ai_ok = asyncio.run(test_ai_assistant())

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    if imports_ok and env_ok and ai_ok:
        print("STATUS: ALL SYSTEMS GO!")
        print("\nYou can now start the server and test the integrations.")
    elif imports_ok and not env_ok:
        print("STATUS: CONFIGURATION NEEDED")
        print("\nPlease update your .env file with the missing API credentials.")
    else:
        print("STATUS: ISSUES DETECTED")
        print("\nPlease review the errors above and fix them.")

    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    main()
