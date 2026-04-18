"""Category ORM model."""

import uuid

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Category(Base):
    """User-specific transaction category."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="Telegram user ID",
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="income or expense",
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, type={self.type})>"
