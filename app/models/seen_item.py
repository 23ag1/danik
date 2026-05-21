from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SeenItem(Base):
    __tablename__ = "seen_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
