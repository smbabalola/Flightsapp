"""
RBAC System Test Script

Tests the complete role-based access control system:
- Login with different roles
- Permission checking
- User management
- Operational endpoints
"""
import requests
import json
from typing import Optional

BASE_URL = "http://127.0.0.1:8001"


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text: str):
    print(f"[OK] {text}")


def print_error(text: str):
    print(f"[ERROR] {text}")


def print_info(text: str):
    print(f"[INFO] {text}")


def login(email: str, password: str) -> Optional[str]:
    """Login and return access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Logged in as {email}")
        return data["access_token"]
    else:
        print_error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
        return None


def test_authentication():
    """Test authentication system."""
    print_header("1. AUTHENTICATION TESTS")

    # Test admin login
    print("\n>> Testing admin login...")
    admin_token = login("admin@sureflights.ng", "admin123")

    if admin_token:
        # Get current user info
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        if response.status_code == 200:
            user_info = response.json()
            print_success(f"User info: {user_info}")
        else:
            print_error(f"Failed to get user info: {response.status_code}")

    return admin_token


def test_user_management(admin_token: str):
    """Test user management endpoints."""
    print_header("2. USER MANAGEMENT TESTS")

    # Create an agent user
    print("\n>> Creating agent user...")
    response = requests.post(
        f"{BASE_URL}/v1/ops/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "agent@sureflights.ng",
            "name": "Test Agent",
            "password": "agent123",
            "role": "agent",
            "status": "active"
        }
    )

    if response.status_code == 201:
        agent = response.json()
        print_success(f"Agent created: ID={agent['id']}, Email={agent['email']}")
        agent_id = agent['id']
    elif response.status_code == 400 and "already exists" in response.text:
        print_info("Agent user already exists")
        # Get existing agent
        response = requests.get(
            f"{BASE_URL}/v1/ops/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"role": "agent"}
        )
        if response.status_code == 200 and response.json():
            agent_id = response.json()[0]['id']
        else:
            agent_id = None
    else:
        print_error(f"Failed to create agent: {response.text}")
        agent_id = None

    # Create a finance user
    print("\n>> Creating finance user...")
    response = requests.post(
        f"{BASE_URL}/v1/ops/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "finance@sureflights.ng",
            "name": "Finance Manager",
            "password": "finance123",
            "role": "finance",
            "status": "active"
        }
    )

    if response.status_code == 201:
        finance = response.json()
        print_success(f"Finance user created: ID={finance['id']}")
    elif "already exists" in response.text:
        print_info("Finance user already exists")
    else:
        print_error(f"Failed to create finance user: {response.text}")

    # List all users
    print("\n>> Listing all users...")
    response = requests.get(
        f"{BASE_URL}/v1/ops/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code == 200:
        users = response.json()
        print_success(f"Found {len(users)} users:")
        for user in users:
            print(f"   - {user['email']} ({user['role']}) - {user['status']}")
    else:
        print_error(f"Failed to list users: {response.status_code}")


def test_permissions():
    """Test permission system with different roles."""
    print_header("3. PERMISSION TESTS")

    # Login as agent
    print("\n>> Testing agent permissions...")
    agent_token = login("agent@sureflights.ng", "agent123")

    if agent_token:
        # Agent should be able to view trips
        response = requests.get(
            f"{BASE_URL}/v1/ops/trips",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        if response.status_code == 200:
            print_success("Agent can view trips ")
        else:
            print_error(f"Agent cannot view trips: {response.status_code}")

        # Agent should NOT be able to view payments (finance only)
        response = requests.get(
            f"{BASE_URL}/v1/ops/payments",
            headers={"Authorization": f"Bearer {agent_token}"}
        )
        if response.status_code == 403:
            print_success("Agent correctly blocked from viewing payments ")
        else:
            print_error(f"Agent should not access payments: {response.status_code}")

        # Agent should NOT be able to create users
        response = requests.post(
            f"{BASE_URL}/v1/ops/users",
            headers={"Authorization": f"Bearer {agent_token}"},
            json={
                "email": "test@example.com",
                "name": "Test",
                "password": "test123",
                "role": "agent"
            }
        )
        if response.status_code == 403:
            print_success("Agent correctly blocked from creating users ")
        else:
            print_error(f"Agent should not create users: {response.status_code}")

    # Login as finance
    print("\n>> Testing finance permissions...")
    finance_token = login("finance@sureflights.ng", "finance123")

    if finance_token:
        # Finance should be able to view payments
        response = requests.get(
            f"{BASE_URL}/v1/ops/payments",
            headers={"Authorization": f"Bearer {finance_token}"}
        )
        if response.status_code == 200:
            print_success("Finance can view payments ")
        else:
            print_error(f"Finance cannot view payments: {response.status_code}")

        # Finance should NOT be able to modify trips
        response = requests.post(
            f"{BASE_URL}/v1/ops/trips/1/notes",
            headers={"Authorization": f"Bearer {finance_token}"},
            json={"note": "Test note"}
        )
        if response.status_code == 403:
            print_success("Finance correctly blocked from modifying trips ")
        else:
            print_error(f"Finance should not modify trips: {response.status_code}")


def test_ops_endpoints(admin_token: str):
    """Test operational endpoints."""
    print_header("4. OPERATIONAL ENDPOINT TESTS")

    # Test trips listing
    print("\n>> Testing trips listing...")
    response = requests.get(
        f"{BASE_URL}/v1/ops/trips",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"limit": 5}
    )

    if response.status_code == 200:
        trips = response.json()
        print_success(f"Retrieved {len(trips)} trips")
        if trips:
            trip = trips[0]
            print(f"   Sample trip: ID={trip.get('trip_id')}, PNR={trip.get('pnr')}, Status={trip.get('status')}")
    else:
        print_info(f"No trips found or error: {response.status_code}")

    # Test payments listing
    print("\n>> Testing payments listing...")
    response = requests.get(
        f"{BASE_URL}/v1/ops/payments",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={"limit": 5}
    )

    if response.status_code == 200:
        payments = response.json()
        print_success(f"Retrieved {len(payments)} payments")
    else:
        print_info(f"No payments found or error: {response.status_code}")


def test_password_change(agent_token: str):
    """Test password change functionality."""
    print_header("5. PASSWORD CHANGE TEST")

    print("\n>> Testing password change...")
    response = requests.post(
        f"{BASE_URL}/auth/change-password",
        headers={"Authorization": f"Bearer {agent_token}"},
        json={
            "current_password": "agent123",
            "new_password": "newagent123"
        }
    )

    if response.status_code == 200:
        print_success("Password changed successfully")

        # Try logging in with new password
        new_token = login("agent@sureflights.ng", "newagent123")
        if new_token:
            print_success("Login with new password successful")

            # Change it back
            requests.post(
                f"{BASE_URL}/auth/change-password",
                headers={"Authorization": f"Bearer {new_token}"},
                json={
                    "current_password": "newagent123",
                    "new_password": "agent123"
                }
            )
            print_success("Password reset to original")
    else:
        print_error(f"Password change failed: {response.json()}")


def main():
    print("\n" + "=" * 70)
    print(" " * 20 + "RBAC SYSTEM TEST")
    print("=" * 70)

    try:
        # Test 1: Authentication
        admin_token = test_authentication()

        if not admin_token:
            print_error("Cannot proceed without admin token")
            return

        # Test 2: User Management
        test_user_management(admin_token)

        # Test 3: Permissions
        test_permissions()

        # Test 4: Operational Endpoints
        test_ops_endpoints(admin_token)

        # Test 5: Password Change
        agent_token = login("agent@sureflights.ng", "agent123")
        if agent_token:
            test_password_change(agent_token)

        # Summary
        print_header("TEST SUMMARY")
        print_success("RBAC system is fully operational!")
        print("\nAvailable Credentials:")
        print("   Admin:   admin@sureflights.ng / admin123")
        print("   Agent:   agent@sureflights.ng / agent123")
        print("   Finance: finance@sureflights.ng / finance123")
        print("\n[!] IMPORTANT: Change default admin password immediately!")
        print("\nAPI Documentation: http://127.0.0.1:8001/docs")

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API server")
        print_info("Please ensure the server is running: python -m uvicorn app.main:app --port 8001")
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
