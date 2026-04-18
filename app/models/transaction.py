"""Transaction ORM model."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, Date, Numeric, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Transaction(Base):
    """Financial transaction record."""

    __tablename__ = "transactions"

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
    amount: Mapped[float] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="income or expense",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, user={self.user_id}, "
            f"amount={self.amount}, type={self.type}, "
            f"category={self.category})>"
        )
