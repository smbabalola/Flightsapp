"""
Test script for cancellation flow.

Tests:
1. Request a cancellation for a trip
2. Check cancellation status
3. Process cancellation (admin)
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8001"

def test_cancellation_flow():
    print("=" * 60)
    print("CANCELLATION FLOW TEST")
    print("=" * 60)

    # Test 1: Request cancellation
    print("\n1. Requesting cancellation for trip_id=1...")
    response = requests.post(
        f"{BASE_URL}/v1/cancellations",
        json={
            "trip_id": 1,
            "reason": "Change of plans"
        }
    )

    if response.status_code == 200:
        cancellation = response.json()
        print(f"   ✅ Cancellation requested successfully!")
        print(f"   Cancellation ID: {cancellation['cancellation_id']}")
        print(f"   PNR: {cancellation['pnr']}")
        print(f"   Status: {cancellation['status']}")

        cancellation_id = cancellation['cancellation_id']
    elif response.status_code == 400:
        print(f"   ℹ️  Trip not found or already cancelled: {response.json()['detail']}")
        print("   This is expected if no trips exist yet.")
        return
    else:
        print(f"   ❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return

    # Test 2: Check cancellation status
    print(f"\n2. Checking cancellation status...")
    response = requests.get(f"{BASE_URL}/v1/cancellations/{cancellation_id}")

    if response.status_code == 200:
        status = response.json()
        print(f"   ✅ Status retrieved successfully!")
        print(f"   Status: {status['status']}")
        print(f"   Refund Amount: {status.get('refund_amount', 'Pending calculation')}")
    else:
        print(f"   ❌ Failed to get status: {response.status_code}")
        print(f"   Response: {response.text}")

    # Test 3: Admin processing (via direct service call since it requires auth)
    print(f"\n3. Admin processing (simulated)...")
    print("   📝 Admin would process this via /admin/cancellations interface")
    print("   This will:")
    print("      - Cancel with Duffel API")
    print("      - Calculate refund amount")
    print("      - Update trip/quote status")
    print("      - Send confirmation email/SMS")

    print("\n" + "=" * 60)
    print("CANCELLATION FLOW TEST COMPLETE")
    print("=" * 60)
    print("\nNEXT STEPS:")
    print("1. Visit http://127.0.0.1:8001/admin/cancellations")
    print("   (Login: admin / change_me)")
    print("2. Click 'Process' to confirm the cancellation")
    print("3. Customer will receive refund confirmation email")

if __name__ == "__main__":
    try:
        test_cancellation_flow()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("   Please ensure the server is running on http://127.0.0.1:8001")
        print("   Run: python -m uvicorn app.main:app --port 8001")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
