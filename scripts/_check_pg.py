"""Quick check that PostgreSQL is reachable and the current alembic head is what we expect."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
from sqlalchemy import text
from app.database import engine


async def main() -> None:
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT current_database(), current_user, version()"))
        db, user, ver = r.one()
        print(f"DB:      {db}")
        print(f"User:    {user}")
        print(f"Version: {ver[:60]}")

    # Check alembic head
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    print(f"Alembic head: {script.get_current_head()}")


if __name__ == "__main__":
    asyncio.run(main())
