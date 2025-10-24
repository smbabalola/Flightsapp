"""Register Twitter webhook for Account Activity API."""
import requests
from requests_oauthlib import OAuth1
import os
from dotenv import load_dotenv

load_dotenv()

# Your credentials from .env
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Your ngrok webhook URL
WEBHOOK_URL = "https://unopiated-michel-magically.ngrok-free.dev/webhooks/twitter"

# Environment name (you'll need to create this first in Twitter Developer Portal)
ENV_NAME = "dev"  # or whatever you named it

def register_webhook():
    """Register webhook with Twitter Account Activity API."""

    # OAuth1 authentication
    auth = OAuth1(
        API_KEY,
        API_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )

    # API endpoint
    url = f"https://api.twitter.com/1.1/account_activity/all/{ENV_NAME}/webhooks.json"

    # Payload
    data = {
        "url": WEBHOOK_URL
    }

    print("=" * 60)
    print("REGISTERING TWITTER WEBHOOK")
    print("=" * 60)
    print(f"\nEnvironment: {ENV_NAME}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"\nSending request to Twitter...")

    # Make request
    response = requests.post(url, auth=auth, data=data)

    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        print("\n✓ SUCCESS! Webhook registered!")
        print(f"\nResponse:")
        print(response.json())
        return True
    else:
        print("\n✗ FAILED!")
        print(f"\nError Response:")
        print(response.text)

        # Common errors
        if response.status_code == 401:
            print("\nIssue: Authentication failed")
            print("- Check your API credentials in .env")
            print("- Make sure you regenerated tokens after changing permissions")
        elif response.status_code == 403:
            print("\nIssue: Forbidden")
            print("- App permissions might not be correct")
            print("- Make sure: 'Read and Write and Direct Messages'")
        elif response.status_code == 409:
            print("\nIssue: Webhook already registered")
            print("- You might need to delete the old one first")
        elif "Too many" in response.text:
            print("\nIssue: Too many webhooks")
            print("- Sandbox tier allows only 1 webhook")
            print("- Delete existing webhook first")

        return False

def get_webhooks():
    """List existing webhooks."""
    auth = OAuth1(
        API_KEY,
        API_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )

    url = f"https://api.twitter.com/1.1/account_activity/all/{ENV_NAME}/webhooks.json"

    print("\n" + "=" * 60)
    print("CHECKING EXISTING WEBHOOKS")
    print("=" * 60)

    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        webhooks = response.json()
        if webhooks:
            print(f"\nFound {len(webhooks)} webhook(s):")
            for i, wh in enumerate(webhooks, 1):
                print(f"\n{i}. ID: {wh['id']}")
                print(f"   URL: {wh['url']}")
                print(f"   Valid: {wh['valid']}")
                print(f"   Created: {wh['created_timestamp']}")
        else:
            print("\nNo webhooks registered yet.")
        return webhooks
    else:
        print(f"\nError: {response.status_code}")
        print(response.text)
        return []

def delete_webhook(webhook_id):
    """Delete a webhook."""
    auth = OAuth1(
        API_KEY,
        API_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )

    url = f"https://api.twitter.com/1.1/account_activity/all/{ENV_NAME}/webhooks/{webhook_id}.json"

    response = requests.delete(url, auth=auth)

    if response.status_code == 204:
        print(f"\n✓ Webhook {webhook_id} deleted successfully!")
        return True
    else:
        print(f"\n✗ Failed to delete webhook")
        print(response.text)
        return False

def subscribe_app():
    """Subscribe to user's account events."""
    auth = OAuth1(
        API_KEY,
        API_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )

    url = f"https://api.twitter.com/1.1/account_activity/all/{ENV_NAME}/subscriptions.json"

    print("\n" + "=" * 60)
    print("SUBSCRIBING TO ACCOUNT EVENTS")
    print("=" * 60)

    response = requests.post(url, auth=auth)

    if response.status_code == 204:
        print("\n✓ Successfully subscribed to account events!")
        print("\nYour bot can now receive DMs!")
        return True
    else:
        print(f"\n✗ Failed to subscribe")
        print(f"Status: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    print("\n")
    print("*" * 60)
    print("  TWITTER WEBHOOK REGISTRATION")
    print("*" * 60)

    # Step 1: Check existing webhooks
    existing = get_webhooks()

    # Step 2: If webhooks exist, ask to delete
    if existing:
        print("\n" + "=" * 60)
        print("OPTIONS")
        print("=" * 60)
        print("\n1. Delete existing webhook and register new one")
        print("2. Keep existing webhook")
        print("\nNote: Sandbox tier only allows 1 webhook")

        choice = input("\nEnter choice (1 or 2): ").strip()

        if choice == "1":
            for wh in existing:
                delete_webhook(wh['id'])
            print("\nNow registering new webhook...")
            register_webhook()
        else:
            print("\nKeeping existing webhook.")
    else:
        # Step 3: Register webhook
        register_webhook()

    # Step 4: Subscribe to events
    print("\n")
    subscribe_app()

    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext step: Send a DM to @sho87698 to test!")
    print("=" * 60)
    print("\n")
