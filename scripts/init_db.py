"""Initialize the database with tables."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db, init_db_sync


async def init_database_async():
    """Initialize database asynchronously."""
    print("Initializing database asynchronously...")
    await init_db()
    print("✅ Database initialized successfully!")


def init_database_sync():
    """Initialize database synchronously."""
    print("Initializing database synchronously...")
    init_db_sync()
    print("✅ Database initialized successfully!")


if __name__ == "__main__":
    # Use sync version for simplicity
    init_database_sync()
    
    # Or use async version:
    # asyncio.run(init_database_async())

