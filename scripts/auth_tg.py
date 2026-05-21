"""Interactive Telegram auth. Run once to create session file.

    .venv/bin/python scripts/auth_tg.py

Needs TG_API_ID and TG_API_HASH in .env (or environment).
After auth, session is saved to <tg_session_name>.session and the
collector can start non-interactively.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telethon import TelegramClient
from app.config import settings


async def main() -> None:
    if not settings.tg_api_id or not settings.tg_api_hash:
        print("ERROR: Set TG_API_ID and TG_API_HASH in .env first.")
        sys.exit(1)

    client = TelegramClient(settings.tg_session_name, settings.tg_api_id, settings.tg_api_hash)
    await client.start()
    me = await client.get_me()
    print(f"\nAuthorized as: {me.first_name} (@{me.username})")
    print(f"Session: {settings.tg_session_name}.session")
    print("Now add telegram channels via POST /sources with source_type='telegram'.")
    await client.disconnect()


asyncio.run(main())
