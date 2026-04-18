"""Analytics service — summaries, breakdowns, and smart insights."""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


def _get_period_range(period: str) -> tuple[date, date]:
    """Convert period string to date range."""
    today = date.today()
    if period == "today":
        return today, today
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif period == "week":
        monday = today - timedelta(days=today.weekday())
        return monday, today
    elif period == "month":
        return today.replace(day=1), today
    else:
        return today, today


async def get_summary(
    session: AsyncSession,
    user_id: int,
    period: str = "today",
    category: Optional[str] = None,
) -> dict:
    """Get income/expense totals for a period.

    Returns:
        {
            "period": str,
            "total_income": float,
            "total_expense": float,
            "balance": float,
            "transaction_count": int
        }
    """
    date_from, date_to = _get_period_range(period)

    query = select(
        func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "income", Transaction.amount),
                    else_=0,
                )
            ),
            0,
        ).label("total_income"),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.type == "expense", Transaction.amount),
                    else_=0,
                )
            ),
            0,
        ).label("total_expense"),
        func.count(Transaction.id).label("count"),
    ).where(
        Transaction.user_id == user_id,
        Transaction.date >= date_from,
        Transaction.date <= date_to,
    )

    if category:
        query = query.where(Transaction.category == category)

    result = await session.execute(query)
    row = result.one()

    total_income = float(row.total_income or 0)
    total_expense = float(row.total_expense or 0)

    return {
        "period": period,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "transaction_count": row.count,
    }


async def get_category_breakdown(
    session: AsyncSession,
    user_id: int,
    period: str = "month",
    type_filter: Optional[str] = None,
) -> list[dict]:
    """Get spending/income breakdown by category.

    Returns:
        [{"category": str, "total": float, "count": int, "percentage": float}]
    """
    date_from, date_to = _get_period_range(period)

    query = select(
        Transaction.category,
        func.sum(Transaction.amount).label("total"),
        func.count(Transaction.id).label("count"),
    ).where(
        Transaction.user_id == user_id,
        Transaction.date >= date_from,
        Transaction.date <= date_to,
    ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc())

    if type_filter:
        query = query.where(Transaction.type == type_filter)

    result = await session.execute(query)
    rows = result.all()

    # Calculate percentages
    grand_total = sum(float(row.total) for row in rows) if rows else 1

    return [
        {
            "category": row.category,
            "total": float(row.total),
            "count": row.count,
            "percentage": round(float(row.total) / grand_total * 100, 1),
        }
        for row in rows
    ]


async def generate_insight(
    session: AsyncSession,
    user_id: int,
) -> Optional[str]:
    """Generate a smart spending insight by comparing this week to last week.

    Returns:
        Insight string like "You spent 30% more on food this week" or None
    """
    today = date.today()
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start - timedelta(days=1)

    # This week's expenses by category
    this_week_query = select(
        Transaction.category,
        func.sum(Transaction.amount).label("total"),
    ).where(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.date >= this_week_start,
        Transaction.date <= today,
    ).group_by(Transaction.category)

    # Last week's expenses by category
    last_week_query = select(
        Transaction.category,
        func.sum(Transaction.amount).label("total"),
    ).where(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.date >= last_week_start,
        Transaction.date <= last_week_end,
    ).group_by(Transaction.category)

    this_result = await session.execute(this_week_query)
    last_result = await session.execute(last_week_query)

    this_data = {row.category: float(row.total) for row in this_result.all()}
    last_data = {row.category: float(row.total) for row in last_result.all()}

    if not this_data or not last_data:
        return None

    # Find biggest increase
    biggest_change = None
    biggest_pct = 0

    for cat, this_total in this_data.items():
        last_total = last_data.get(cat, 0)
        if last_total > 0:
            change_pct = ((this_total - last_total) / last_total) * 100
            if abs(change_pct) > abs(biggest_pct):
                biggest_pct = change_pct
                biggest_change = cat

    if biggest_change and abs(biggest_pct) >= 10:
        direction = "more" if biggest_pct > 0 else "less"
        return (
            f"📊 You spent {abs(biggest_pct):.0f}% {direction} on "
            f"{biggest_change} this week compared to last week."
        )

    return None


async def get_monthly_report(
    session: AsyncSession,
    user_id: int,
) -> dict:
    """Generate a comprehensive monthly report.

    Returns:
        {
            "summary": dict,
            "categories": list[dict],
            "insight": str or None,
            "daily_avg_expense": float,
            "daily_avg_income": float,
        }
    """
    summary = await get_summary(session, user_id, "month")
    categories = await get_category_breakdown(session, user_id, "month", "expense")
    insight = await generate_insight(session, user_id)

    today = date.today()
    days_in_month = today.day  # Days elapsed so far

    return {
        "summary": summary,
        "expense_categories": categories,
        "income_categories": await get_category_breakdown(
            session, user_id, "month", "income"
        ),
        "insight": insight,
        "daily_avg_expense": round(
            summary["total_expense"] / max(days_in_month, 1), 2
        ),
        "daily_avg_income": round(
            summary["total_income"] / max(days_in_month, 1), 2
        ),
    }
