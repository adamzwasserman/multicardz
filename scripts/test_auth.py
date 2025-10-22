#!/usr/bin/env python3
"""
Test authentication service functionality.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.shared.services.auth_service import (
    InvalidCredentialsError,
    SessionExpiredError,
    authenticate_user,
    create_user_session,
    logout_user,
    validate_session,
)
from apps.shared.services.database_storage import (
    DatabaseConfig,
    create_database_connection,
)


def test_authentication():
    """Test the authentication system."""
    print("Testing multicardz authentication system...")

    # Database configuration
    db_path = Path("/var/data/multicardz_dev.db")
    config: DatabaseConfig = (db_path, True, 30.0, False, 100)
    conn = create_database_connection(config)

    try:
        # Test 1: Valid login
        print("\n1. Testing valid login...")
        try:
            user = authenticate_user(conn, "demo_user", "demo123")
            print(f"✅ Login successful: {user['username']} ({user['full_name']})")
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False

        # Test 2: Invalid password
        print("\n2. Testing invalid password...")
        try:
            authenticate_user(conn, "demo_user", "wrong_password")
            print("❌ Should have failed with wrong password")
            return False
        except InvalidCredentialsError:
            print("✅ Correctly rejected invalid password")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

        # Test 3: Email login
        print("\n3. Testing email login...")
        try:
            user = authenticate_user(conn, "demo@multicardz.com", "demo123")
            print(f"✅ Email login successful: {user['email']}")
        except Exception as e:
            print(f"❌ Email login failed: {e}")
            return False

        # Test 4: Session creation
        print("\n4. Testing session creation...")
        try:
            session_id = create_user_session(
                conn, user['id'], "127.0.0.1", "Test Browser"
            )
            print(f"✅ Session created: {session_id[:8]}...")
        except Exception as e:
            print(f"❌ Session creation failed: {e}")
            return False

        # Test 5: Session validation
        print("\n5. Testing session validation...")
        try:
            validated_user = validate_session(conn, session_id)
            print(f"✅ Session valid: {validated_user['username']}")
        except Exception as e:
            print(f"❌ Session validation failed: {e}")
            return False

        # Test 6: Logout
        print("\n6. Testing logout...")
        try:
            logout_result = logout_user(conn, session_id)
            print(f"✅ Logout successful: {logout_result}")
        except Exception as e:
            print(f"❌ Logout failed: {e}")
            return False

        # Test 7: Validate expired session
        print("\n7. Testing expired session...")
        try:
            validate_session(conn, session_id)
            print("❌ Should have failed with expired session")
            return False
        except SessionExpiredError:
            print("✅ Correctly rejected expired session")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

        print("\n✅ All authentication tests passed!")
        return True

    finally:
        conn.close()


if __name__ == "__main__":
    success = test_authentication()
    exit(0 if success else 1)
