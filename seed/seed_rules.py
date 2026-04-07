#!/usr/bin/env python3
"""
Seed rules into the Rule API database using UUID5 for deterministic device IDs.
Integrated with the rule-api microservice models and configuration.

Usage:
    python seed_rules.py
    python seed_rules.py --dry-run
    python seed_rules.py --clear  # Clear existing rules before seeding
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_DNS, uuid4, uuid5

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import from the rule-api application
from app.core.settings import settings
from app.db.db import Base
from app.models.models import Rule


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

SEED_DATA_FILE = Path(__file__).parent / "seed_rules_data.json"
DEVICE_UUID5_NAMESPACE = NAMESPACE_DNS


# ─────────────────────────────────────────────────────────────────────────────
# UUID Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_device_uuid(device_code: str) -> str:
    """
    Generate a deterministic UUID5 from a device serial number.
    Same input always produces the same UUID.

    Args:
        device_code: Device serial number (e.g., 'VIB-SN-001')

    Returns:
        Deterministic UUID5 string
    """
    return str(uuid5(DEVICE_UUID5_NAMESPACE, device_code))


# ─────────────────────────────────────────────────────────────────────────────
# Database Setup
# ─────────────────────────────────────────────────────────────────────────────

def get_session():
    """Create and return a database session."""
    engine = create_engine(
        settings.database_url,
        echo=settings.echo_sql,
        future=True,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


# ─────────────────────────────────────────────────────────────────────────────
# Seeding Logic
# ─────────────────────────────────────────────────────────────────────────────

def load_seed_data() -> dict:
    """Load rules data from JSON file."""
    if not SEED_DATA_FILE.exists():
        raise FileNotFoundError(f"Seed data file not found: {SEED_DATA_FILE}")

    with open(SEED_DATA_FILE) as f:
        return json.load(f)


def rule_exists(session, device_id: str, rule_name: str) -> bool:
    """Check if a rule already exists for the device."""
    return (
        session.query(Rule)
        .filter(Rule.device_id == device_id, Rule.name == rule_name)
        .first()
        is not None
    )


def seed_rules(session, rules_data: list, dry_run: bool = False) -> dict:
    """
    Insert rules into the database using UUID5 device IDs.

    Args:
        session: SQLAlchemy database session
        rules_data: List of rule dictionaries from seed data
        dry_run: If True, don't commit to database

    Returns:
        Dictionary with statistics (inserted, skipped, errors)
    """
    stats = {"inserted": 0, "skipped": 0, "errors": 0}
    now = datetime.now(timezone.utc)

    for rule_data in rules_data:
        try:
            device_serial = rule_data.get("device")
            rule_name = rule_data.get("name")

            if not device_serial:
                print(f"  ✗ Rule missing 'device' field: {rule_name}", file=sys.stderr)
                stats["errors"] += 1
                continue

            if not rule_name:
                print(f"  ✗ Rule missing 'name' field", file=sys.stderr)
                stats["errors"] += 1
                continue

            # Generate deterministic device UUID from serial number
            device_id = generate_device_uuid(device_serial)

            # Check if rule already exists (idempotent)
            if rule_exists(session, device_id, rule_name):
                stats["skipped"] += 1
                continue

            # Create the rule
            rule = Rule(
                id=str(uuid4()),  # Rule ID (random)
                device_id=device_id,  # ✅ Stable device UUID from serial number
                name=rule_name,
                description=rule_data.get("description"),
                condition=rule_data.get("condition"),
                action_config=rule_data.get("action_config"),
                is_enabled=rule_data.get("is_enabled", True),
                created_at=now,
                updated_at=now,
            )

            session.add(rule)
            stats["inserted"] += 1

        except Exception as e:
            print(f"  ✗ Error processing rule '{rule_name}': {e}", file=sys.stderr)
            stats["errors"] += 1
            continue

    # Commit or rollback based on dry_run flag
    if not dry_run:
        try:
            session.commit()
            print(
                f"[seed_rules] ✓ Committed {stats['inserted']} rules to database",
                file=sys.stderr,
            )
        except Exception as e:
            session.rollback()
            print(f"[seed_rules] ✗ Error committing to database: {e}", file=sys.stderr)
            stats["errors"] += 1
    else:
        session.rollback()
        print("[seed_rules] (dry-run mode: no changes committed)", file=sys.stderr)

    return stats


def clear_rules(session, dry_run: bool = False) -> int:
    """
    Delete all existing rules from the database.

    Args:
        session: SQLAlchemy database session
        dry_run: If True, don't commit deletion

    Returns:
        Number of rules deleted
    """
    try:
        count = session.query(Rule).count()

        if count > 0:
            session.query(Rule).delete()

            if not dry_run:
                session.commit()
                print(
                    f"[seed_rules] ✓ Deleted {count} existing rules",
                    file=sys.stderr,
                )
            else:
                session.rollback()
                print(
                    f"[seed_rules] (dry-run: would delete {count} rules)",
                    file=sys.stderr,
                )

        return count

    except Exception as e:
        print(f"[seed_rules] ✗ Error clearing rules: {e}", file=sys.stderr)
        session.rollback()
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed rules into the Rule API database using UUID5 device IDs"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing to database",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete all existing rules before seeding",
    )

    args = parser.parse_args()

    print("[seed_rules] Starting rule seeding...", file=sys.stderr)
    print(
        f"[seed_rules] Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else settings.database_url}",
        file=sys.stderr,
    )

    session = None
    try:
        # Load seed data
        try:
            data = load_seed_data()
            rules_data = data.get("rules", [])
            if not rules_data:
                print("[seed_rules] ✗ No rules found in seed data", file=sys.stderr)
                return 1
        except FileNotFoundError as e:
            print(f"[seed_rules] ✗ {e}", file=sys.stderr)
            return 1
        except json.JSONDecodeError as e:
            print(f"[seed_rules] ✗ Invalid JSON in seed data: {e}", file=sys.stderr)
            return 1

        # Connect to database
        session = get_session()

        # Clear existing rules if requested
        if args.clear:
            clear_rules(session, dry_run=args.dry_run)

        # Seed rules
        print(f"[seed_rules] Seeding {len(rules_data)} rules...", file=sys.stderr)
        stats = seed_rules(session, rules_data, dry_run=args.dry_run)

        # Print summary
        print(
            f"[seed_rules] Results: {stats['inserted']} inserted, {stats['skipped']} skipped, {stats['errors']} errors",
            file=sys.stderr,
        )

        if stats["errors"] > 0:
            return 1

        print("[seed_rules] ✓ Done.", file=sys.stderr)
        return 0

    except Exception as e:
        print(f"[seed_rules] ✗ Fatal error: {e}", file=sys.stderr)
        return 1

    finally:
        if session:
            session.close()


if __name__ == "__main__":
    sys.exit(main())
