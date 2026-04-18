"""Transaction service — CRUD operations and business logic."""

import logging
import uuid
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select, delete, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


async def create_transaction(
    session: AsyncSession,
    user_id: int,
    amount: float,
    type_: str,
    category: str,
    tx_date: date,
    note: Optional[str] = None,
) -> Transaction:
    """Create and save a new transaction."""
    tx = Transaction(
        user_id=user_id,
        amount=amount,
        type=type_,
        category=category,
        date=tx_date,
        note=note,
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)
    logger.info(f"Created transaction {tx.id} for user {user_id}")
    return tx


async def get_transactions(
    session: AsyncSession,
    user_id: int,
    type_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 50,
) -> list[Transaction]:
    """Fetch transactions for a user with optional filters."""
    query = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.created_at))
    )

    if type_filter:
        query = query.where(Transaction.type == type_filter)
    if category_filter:
        query = query.where(Transaction.category == category_filter)
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)

    query = query.limit(limit)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_last_transaction(
    session: AsyncSession,
    user_id: int,
) -> Optional[Transaction]:
    """Get the most recent transaction for a user."""
    query = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.created_at))
        .limit(1)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def update_transaction(
    session: AsyncSession,
    tx_id: uuid.UUID,
    user_id: int,
    **kwargs,
) -> Optional[Transaction]:
    """Update a transaction's fields. Only updates provided kwargs."""
    # Filter out None values
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    if not update_data:
        return None

    await session.execute(
        update(Transaction)
        .where(Transaction.id == tx_id, Transaction.user_id == user_id)
        .values(**update_data)
    )
    await session.commit()

    # Fetch updated record
    result = await session.execute(
        select(Transaction).where(Transaction.id == tx_id)
    )
    return result.scalar_one_or_none()


async def delete_transaction(
    session: AsyncSession,
    tx_id: uuid.UUID,
    user_id: int,
) -> bool:
    """Delete a transaction. Returns True if deleted."""
    result = await session.execute(
        delete(Transaction)
        .where(Transaction.id == tx_id, Transaction.user_id == user_id)
    )
    await session.commit()
    deleted = result.rowcount > 0
    if deleted:
        logger.info(f"Deleted transaction {tx_id} for user {user_id}")
    return deleted


async def get_transactions_by_period(
    session: AsyncSession,
    user_id: int,
    period: str,
    type_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
) -> list[Transaction]:
    """Get transactions by period shorthand: today, yesterday, week, month."""
    today = date.today()

    if period == "today":
        date_from = today
        date_to = today
    elif period == "yesterday":
        date_from = today - timedelta(days=1)
        date_to = today - timedelta(days=1)
    elif period == "week":
        date_from = today - timedelta(days=today.weekday())  # Monday
        date_to = today
    elif period == "month":
        date_from = today.replace(day=1)
        date_to = today
    else:
        date_from = today
        date_to = today

    return await get_transactions(
        session=session,
        user_id=user_id,
        type_filter=type_filter,
        category_filter=category_filter,
        date_from=date_from,
        date_to=date_to,
        limit=200,
    )
