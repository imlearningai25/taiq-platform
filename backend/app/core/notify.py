from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Notification


async def notify(db: AsyncSession, user_id: int, type: str, title: str, message: str) -> None:
    db.add(Notification(user_id=user_id, type=type, title=title, message=message))
