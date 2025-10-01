#!/usr/bin/env python3
"""
Create seed data for MultiCardz™ development and testing.

This script creates realistic test data including:
- Sample users with proper authentication
- Sample workspaces
- Sample cards with realistic tags
- User-workspace-card relationships
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.shared.services.database_storage import (
    create_database_connection,
    initialize_database_schema,
    save_user,
    save_card_summary,
    save_user_session,
    add_card_to_user_workspace,
    save_user_preferences,
    DatabaseConfig,
)
from apps.shared.models.card import CardSummary
from apps.shared.models.user_preferences import UserPreferences


def hash_password(password: str) -> str:
    """Simple password hashing for development (use proper hashing in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_sample_users() -> list[dict]:
    """Create sample users for testing."""
    now = datetime.utcnow()

    users = [
        {
            'id': 'user-DEMO001',
            'username': 'demo_user',
            'email': 'demo@multicardz.com',
            'password_hash': hash_password('demo123'),
            'full_name': 'Demo User',
            'is_active': True,
            'is_verified': True,
            'created_at': now.isoformat(),
            'default_workspace_id': 'ws-MAIN001',
        },
        {
            'id': 'user-ADMIN01',
            'username': 'admin',
            'email': 'admin@multicardz.com',
            'password_hash': hash_password('admin123'),
            'full_name': 'System Administrator',
            'is_active': True,
            'is_verified': True,
            'created_at': now.isoformat(),
            'default_workspace_id': 'ws-ADMIN01',
        },
        {
            'id': 'user-ALICE01',
            'username': 'alice',
            'email': 'alice@example.com',
            'password_hash': hash_password('alice123'),
            'full_name': 'Alice Johnson',
            'is_active': True,
            'is_verified': True,
            'created_at': now.isoformat(),
            'default_workspace_id': 'ws-ALICE01',
        },
    ]

    return users


def create_sample_cards() -> list[CardSummary]:
    """Create sample cards with realistic content and tags."""
    now = datetime.utcnow()

    cards = [
        CardSummary(
            id='CARD001',
            title='Machine Learning Fundamentals',
            tags=frozenset(['machine-learning', 'ai', 'python', 'algorithms', 'education']),
            created_at=now - timedelta(days=5),
            modified_at=now - timedelta(days=2),
            has_attachments=False,
        ),
        CardSummary(
            id='CARD002',
            title='Database Design Best Practices',
            tags=frozenset(['database', 'sql', 'design', 'normalization', 'performance']),
            created_at=now - timedelta(days=10),
            modified_at=now - timedelta(days=1),
            has_attachments=True,
        ),
        CardSummary(
            id='CARD003',
            title='React Component Architecture',
            tags=frozenset(['react', 'javascript', 'frontend', 'components', 'web-development']),
            created_at=now - timedelta(days=3),
            modified_at=now - timedelta(hours=6),
            has_attachments=False,
        ),
        CardSummary(
            id='CARD004',
            title='Python FastAPI Tutorial',
            tags=frozenset(['python', 'fastapi', 'api', 'backend', 'tutorial']),
            created_at=now - timedelta(days=7),
            modified_at=now - timedelta(days=1),
            has_attachments=True,
        ),
        CardSummary(
            id='CARD005',
            title='Git Workflow Strategies',
            tags=frozenset(['git', 'version-control', 'workflow', 'development', 'collaboration']),
            created_at=now - timedelta(days=12),
            modified_at=now - timedelta(days=4),
            has_attachments=False,
        ),
        CardSummary(
            id='CARD006',
            title='Docker Container Best Practices',
            tags=frozenset(['docker', 'containers', 'devops', 'deployment', 'infrastructure']),
            created_at=now - timedelta(days=8),
            modified_at=now - timedelta(days=2),
            has_attachments=True,
        ),
        CardSummary(
            id='CARD007',
            title='SQL Query Optimization',
            tags=frozenset(['sql', 'database', 'optimization', 'performance', 'indexing']),
            created_at=now - timedelta(days=6),
            modified_at=now - timedelta(hours=12),
            has_attachments=False,
        ),
        CardSummary(
            id='CARD008',
            title='JavaScript ES6+ Features',
            tags=frozenset(['javascript', 'es6', 'features', 'modern', 'web-development']),
            created_at=now - timedelta(days=4),
            modified_at=now - timedelta(hours=8),
            has_attachments=False,
        ),
        CardSummary(
            id='CARD009',
            title='Linux System Administration',
            tags=frozenset(['linux', 'system-admin', 'server', 'bash', 'infrastructure']),
            created_at=now - timedelta(days=15),
            modified_at=now - timedelta(days=3),
            has_attachments=True,
        ),
        CardSummary(
            id='CARD010',
            title='API Security Guidelines',
            tags=frozenset(['api', 'security', 'authentication', 'authorization', 'best-practices']),
            created_at=now - timedelta(days=9),
            modified_at=now - timedelta(days=1),
            has_attachments=False,
        ),
    ]

    return cards


def create_workspace_assignments() -> list[tuple[str, str, str]]:
    """Create user-workspace-card assignments."""
    assignments = [
        # Demo user gets most cards
        ('user-DEMO001', 'ws-MAIN001', 'CARD001'),
        ('user-DEMO001', 'ws-MAIN001', 'CARD002'),
        ('user-DEMO001', 'ws-MAIN001', 'CARD003'),
        ('user-DEMO001', 'ws-MAIN001', 'CARD004'),
        ('user-DEMO001', 'ws-MAIN001', 'CARD005'),
        ('user-DEMO001', 'ws-MAIN001', 'CARD006'),

        # Admin gets system-related cards
        ('user-ADMIN01', 'ws-ADMIN01', 'CARD002'),
        ('user-ADMIN01', 'ws-ADMIN01', 'CARD006'),
        ('user-ADMIN01', 'ws-ADMIN01', 'CARD009'),
        ('user-ADMIN01', 'ws-ADMIN01', 'CARD010'),

        # Alice gets development-focused cards
        ('user-ALICE01', 'ws-ALICE01', 'CARD001'),
        ('user-ALICE01', 'ws-ALICE01', 'CARD003'),
        ('user-ALICE01', 'ws-ALICE01', 'CARD004'),
        ('user-ALICE01', 'ws-ALICE01', 'CARD007'),
        ('user-ALICE01', 'ws-ALICE01', 'CARD008'),
    ]

    return assignments


def create_sample_sessions() -> list[dict]:
    """Create sample active sessions."""
    now = datetime.utcnow()
    expires = now + timedelta(hours=24)

    sessions = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'user-DEMO001',
            'created_at': now.isoformat(),
            'expires_at': expires.isoformat(),
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla/5.0 (Demo Browser)',
        },
    ]

    return sessions


def create_sample_preferences() -> list[UserPreferences]:
    """Create sample user preferences."""
    preferences = [
        UserPreferences(
            user_id='user-DEMO001',
        ),
        UserPreferences(
            user_id='user-ADMIN01',
        ),
        UserPreferences(
            user_id='user-ALICE01',
        ),
    ]

    return preferences


def main():
    """Create seed data for MultiCardz development."""
    print("Creating MultiCardz seed data...")

    # Database configuration for development
    db_path = Path("/var/data/multicardz_dev.db")
    db_path.parent.mkdir(exist_ok=True)

    config: DatabaseConfig = (
        db_path,
        True,  # enable_foreign_keys
        30.0,  # timeout
        False,  # check_same_thread
        100,   # max_attachment_size_mb
    )

    # Create database connection and initialize schema
    conn = create_database_connection(config)

    try:
        print("Initializing database schema...")
        initialize_database_schema(conn)

        # Create sample users
        print("Creating sample users...")
        users = create_sample_users()
        for user in users:
            save_user(conn, user)
        print(f"Created {len(users)} users")

        # Create sample cards
        print("Creating sample cards...")
        cards = create_sample_cards()
        for card in cards:
            save_card_summary(conn, card)
        print(f"Created {len(cards)} cards")

        # Create workspace assignments
        print("Creating workspace assignments...")
        assignments = create_workspace_assignments()
        for user_id, workspace_id, card_id in assignments:
            add_card_to_user_workspace(conn, user_id, workspace_id, card_id)
        print(f"Created {len(assignments)} workspace assignments")

        # Create sample sessions
        print("Creating sample sessions...")
        sessions = create_sample_sessions()
        for session in sessions:
            save_user_session(conn, session)
        print(f"Created {len(sessions)} active sessions")

        # Create sample preferences
        print("Creating sample preferences...")
        preferences = create_sample_preferences()
        for pref in preferences:
            save_user_preferences(conn, pref)
        print(f"Created {len(preferences)} user preferences")

        print("\n✅ Seed data creation completed successfully!")
        print(f"Database created at: {db_path}")
        print("\nSample login credentials:")
        print("- Username: demo_user, Password: demo123")
        print("- Username: admin, Password: admin123")
        print("- Username: alice, Password: alice123")

    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        return 1

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    exit(main())