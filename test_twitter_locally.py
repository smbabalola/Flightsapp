"""Test Twitter DM flow locally without webhooks (for development)."""
import asyncio
from app.twitter.handler import get_twitter_handler
from app.twitter.session import get_session_manager


async def simulate_dm_conversation():
    """Simulate a Twitter DM conversation locally."""
    print("\n" + "=" * 60)
    print("TWITTER DM FLOW - LOCAL SIMULATION")
    print("=" * 60)
    print("\nThis simulates the conversation flow without requiring webhooks.")
    print("Testing with mock user ID: test_user_123")
    print("\n" + "=" * 60)

    handler = get_twitter_handler()
    test_user_id = "test_user_123"

    # Test 1: Start conversation
    print("\n[User] Sends: 'Hi'")
    try:
        await handler.handle_dm(test_user_id, "Hi")
        print("[Bot] Response sent (check logs above)")
    except Exception as e:
        print(f"[Error] {str(e)}")

    await asyncio.sleep(1)

    # Test 2: Search for flight
    print("\n[User] Sends: 'Flight from Lagos to Abuja on 2025-11-15'")
    try:
        await handler.handle_dm(test_user_id, "Flight from Lagos to Abuja on 2025-11-15")
        print("[Bot] Response sent (check logs above)")
    except Exception as e:
        print(f"[Error] {str(e)}")

    await asyncio.sleep(1)

    # Test 3: Check session state
    session_mgr = get_session_manager()
    session = await session_mgr.get_session(test_user_id)
    print(f"\n[Session State] Current state: {session.state}")
    if session.search_params:
        print(f"[Session State] Search params: {session.search_params}")
    if session.offers:
        print(f"[Session State] Found {len(session.offers)} flight offers")

    print("\n" + "=" * 60)
    print("NOTES:")
    print("=" * 60)
    print("1. The bot tries to send DMs but may fail without proper webhook setup")
    print("2. Check the logs above to see what the bot would send")
    print("3. If you see 'dm_sent' logs, the bot is working!")
    print("4. Session state is tracked correctly in memory")
    print("\nTo see actual DM responses, you need:")
    print("- OpenAI credits (for AI parsing)")
    print("- Webhook setup (for receiving real DMs)")
    print("=" * 60)


async def test_simple_flow():
    """Test a simple conversation flow."""
    print("\n" + "=" * 60)
    print("SIMPLE FLOW TEST")
    print("=" * 60)

    from app.twitter.client import get_twitter_client
    client = get_twitter_client()

    print("\nBot Account Info:")
    if client.me and client.me.data:
        print(f"  Username: @{client.me.data.username}")
        print(f"  User ID: {client.me.data.id}")
        print(f"  Name: {client.me.data.name}")

        print("\n[MANUAL TEST]")
        print("To test the bot manually:")
        print(f"1. Send a DM to @{client.me.data.username}")
        print("2. The message will arrive via webhook (when configured)")
        print("3. The bot will process it through the handler")
        print("4. The bot will send a response back")

    print("\n" + "=" * 60)


async def main():
    """Run local tests."""
    print("\n")
    print("*" * 60)
    print("  TWITTER DM - LOCAL TESTING")
    print("*" * 60)

    # Test basic info
    await test_simple_flow()

    # Simulate conversation
    print("\n\nWould you like to simulate a conversation? (y/n)")
    print("Note: This will show what WOULD happen, but won't send real DMs")

    # Auto-run for now
    print("[AUTO-RUNNING SIMULATION]")
    await simulate_dm_conversation()

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. Add credits to OpenAI account (for AI conversation)")
    print("2. Fix ngrok or use alternative tunnel (localtunnel, serveo)")
    print("3. Configure Twitter webhook")
    print("4. Send real DM to your bot to test end-to-end")
    print("\nOR")
    print("\nDeploy to a cloud platform with HTTPS (Render, Railway, Vercel)")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
