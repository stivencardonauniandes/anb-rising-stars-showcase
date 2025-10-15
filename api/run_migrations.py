#!/usr/bin/env python3
"""
Script to run database migrations
Usage: python run_migrations.py
"""
import os
import sys
from alembic.config import Config
from alembic import command

def run_migrations():
    """Run all pending migrations"""
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to alembic.ini
    alembic_cfg_path = os.path.join(current_dir, "alembic.ini")
    
    # Create Alembic configuration
    alembic_cfg = Config(alembic_cfg_path)
    
    # Set the script location (this should match what's in alembic.ini)
    alembic_cfg.set_main_option("script_location", os.path.join(current_dir, "alembic"))
    
    try:
        print("🔄 Running database migrations...")
        # Run migrations to head (latest)
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
