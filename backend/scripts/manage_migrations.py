"""
Migration management script for Alembic.

This script provides utilities for managing database migrations,
including creating, applying, and rolling back migrations.
"""

import os
import sys
import argparse
from pathlib import Path
from subprocess import run, CalledProcessError
import logging

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic."""

    def __init__(self):
        """Initialize the migration manager."""
        self.backend_dir = Path(__file__).parent.parent
        self.alembic_cmd = "alembic"
        self.env = os.environ.copy()

        # Ensure DATABASE_URL is set for Alembic
        if not self.env.get("DATABASE_URL"):
            self.env["DATABASE_URL"] = settings.database_url_sync

    def run_alembic_command(self, *args) -> bool:
        """
        Run an Alembic command.

        Args:
            *args: Command arguments

        Returns:
            bool: True if command succeeded
        """
        try:
            cmd = [self.alembic_cmd] + list(args)
            logger.info(f"Running command: {' '.join(cmd)}")

            result = run(
                cmd,
                cwd=self.backend_dir,
                env=self.env,
                check=True,
                capture_output=True,
                text=True
            )

            if result.stdout:
                logger.info(f"Alembic output: {result.stdout}")

            return True

        except CalledProcessError as e:
            logger.error(f"Alembic command failed: {e}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error running Alembic command: {e}")
            return False

    def create_migration(self, message: str, autogenerate: bool = True) -> bool:
        """
        Create a new migration.

        Args:
            message: Migration message
            autogenerate: Whether to autogenerate migration

        Returns:
            bool: True if migration created successfully
        """
        logger.info(f"Creating migration: {message}")

        args = ["revision", "--autogenerate"] if autogenerate else ["revision"]
        args.extend(["-m", message])

        return self.run_alembic_command(*args)

    def upgrade_database(self, revision: str = "head") -> bool:
        """
        Upgrade database to specified revision.

        Args:
            revision: Target revision (default: head)

        Returns:
            bool: True if upgrade succeeded
        """
        logger.info(f"Upgrading database to revision: {revision}")
        return self.run_alembic_command("upgrade", revision)

    def downgrade_database(self, revision: str = "-1") -> bool:
        """
        Downgrade database to specified revision.

        Args:
            revision: Target revision (default: previous)

        Returns:
            bool: True if downgrade succeeded
        """
        logger.info(f"Downgrading database to revision: {revision}")
        return self.run_alembic_command("downgrade", revision)

    def get_current_revision(self) -> str:
        """
        Get current database revision.

        Returns:
            str: Current revision
        """
        try:
            result = run(
                [self.alembic_cmd, "current"],
                cwd=self.backend_dir,
                env=self.env,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except CalledProcessError as e:
            logger.error(f"Failed to get current revision: {e}")
            return ""

    def get_migration_history(self) -> str:
        """
        Get migration history.

        Returns:
            str: Migration history
        """
        try:
            result = run(
                [self.alembic_cmd, "history", "--verbose"],
                cwd=self.backend_dir,
                env=self.env,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except CalledProcessError as e:
            logger.error(f"Failed to get migration history: {e}")
            return ""

    def check_migration_status(self) -> dict:
        """
        Check migration status.

        Returns:
            dict: Migration status information
        """
        current = self.get_current_revision()
        history = self.get_migration_history()

        return {
            "current_revision": current,
            "has_migrations": bool(history.strip()),
            "needs_upgrade": current != "head",
            "database_url": self.env.get("DATABASE_URL", ""),
        }

    def reset_database(self) -> bool:
        """
        Reset database (drop and recreate all tables).

        Returns:
            bool: True if reset succeeded
        """
        logger.warning("Resetting database - this will delete all data!")

        # First, downgrade to base
        if not self.downgrade_database("base"):
            logger.error("Failed to downgrade database to base")
            return False

        # Then upgrade to head
        if not self.upgrade_database("head"):
            logger.error("Failed to upgrade database to head")
            return False

        logger.info("Database reset successfully")
        return True


def main():
    """Main function for CLI interface."""
    parser = argparse.ArgumentParser(description="Migration management tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message")
    create_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Don't autogenerate migration"
    )

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Target revision (default: head)"
    )

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="-1",
        help="Target revision (default: previous)"
    )

    # Status command
    subparsers.add_parser("status", help="Show migration status")

    # History command
    subparsers.add_parser("history", help="Show migration history")

    # Reset command
    subparsers.add_parser("reset", help="Reset database (destructive)")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create migration manager
    manager = MigrationManager()

    # Execute command
    if args.command == "create":
        success = manager.create_migration(
            args.message,
            autogenerate=not args.no_autogenerate
        )
        if success:
            logger.info("Migration created successfully")
        else:
            logger.error("Failed to create migration")
            sys.exit(1)

    elif args.command == "upgrade":
        success = manager.upgrade_database(args.revision)
        if success:
            logger.info("Database upgraded successfully")
        else:
            logger.error("Failed to upgrade database")
            sys.exit(1)

    elif args.command == "downgrade":
        success = manager.downgrade_database(args.revision)
        if success:
            logger.info("Database downgraded successfully")
        else:
            logger.error("Failed to downgrade database")
            sys.exit(1)

    elif args.command == "status":
        status = manager.check_migration_status()
        print("Migration Status:")
        print(f"  Current Revision: {status['current_revision']}")
        print(f"  Has Migrations: {status['has_migrations']}")
        print(f"  Needs Upgrade: {status['needs_upgrade']}")
        print(f"  Database URL: {status['database_url']}")

    elif args.command == "history":
        history = manager.get_migration_history()
        if history:
            print("Migration History:")
            print(history)
        else:
            print("No migrations found")

    elif args.command == "reset":
        confirm = input("Are you sure you want to reset the database? This will delete all data. (y/N): ")
        if confirm.lower() in ['y', 'yes']:
            success = manager.reset_database()
            if success:
                logger.info("Database reset successfully")
            else:
                logger.error("Failed to reset database")
                sys.exit(1)
        else:
            logger.info("Database reset cancelled")


if __name__ == "__main__":
    main()