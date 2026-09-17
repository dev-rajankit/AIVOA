import asyncio
from app.db.session import async_session_factory
from sqlalchemy import delete
from app.db.models import Complaint

async def drop():
    async with async_session_factory() as db:
        await db.execute(delete(Complaint))
        await db.commit()

asyncio.run(drop())
