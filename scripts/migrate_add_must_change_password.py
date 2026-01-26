#!/usr/bin/env python3
"""Migration script to add must_change_password column to users table.

This script safely adds the must_change_password column to existing databases.
"""
import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from reverse_proxy_mcp.core.config import settings


def migrate():
    """Add must_change_password column to users table."""
    db_path = settings.database_url.replace("sqlite:///", "")
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "must_change_password" in columns:
            print("✓ Column 'must_change_password' already exists. No migration needed.")
            conn.close()
            return
        
        # Add the column with default value False
        print("Adding must_change_password column...")
        cursor.execute(
            "ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT 0 NOT NULL"
        )
        
        # Set must_change_password=True for admin user with default password
        print("Checking admin user password...")
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            # Check if admin has default password hash (we can't verify directly, so set flag)
            print(f"Found admin user (ID: {admin_user[0]}). Setting must_change_password=True.")
            cursor.execute(
                "UPDATE users SET must_change_password = 1 WHERE username = 'admin'"
            )
        
        conn.commit()
        print("✓ Migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    migrate()
