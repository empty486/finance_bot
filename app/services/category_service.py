"""Category service — normalization and management."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category

logger = logging.getLogger(__name__)

# Category normalization map (Uzbek/Russian → English)
CATEGORY_MAP = {
    # Food
    "ovqat": "food",
    "oziq-ovqat": "food",
    "taomnoma": "food",
    "еда": "food",
    "продукты": "food",
    "обед": "food",
    "ужин": "food",
    "завтрак": "food",
    "breakfast": "food",
    "lunch": "food",
    "dinner": "food",
    "restaurant": "food",
    "restoran": "food",
    "ресторан": "food",
    "cafe": "food",
    "kafe": "food",
    "grocery": "food",

    # Transport
    "taxi": "transport",
    "taksi": "transport",
    "такси": "transport",
    "transport": "transport",
    "yolovchi": "transport",
    "avtobus": "transport",
    "metro": "transport",
    "транспорт": "transport",
    "бензин": "transport",
    "benzin": "transport",
    "fuel": "transport",
    "uber": "transport",
    "yandex": "transport",

    # Housing/Rent
    "uy": "rent",
    "ijara": "rent",
    "kvartira": "rent",
    "аренда": "rent",
    "квартира": "rent",
    "rent": "rent",
    "housing": "rent",

    # Utilities
    "kommunal": "utilities",
    "gaz": "utilities",
    "suv": "utilities",
    "elektr": "utilities",
    "коммуналка": "utilities",
    "свет": "utilities",
    "вода": "utilities",
    "газ": "utilities",
    "internet": "utilities",
    "telefon": "utilities",
    "телефон": "utilities",
    "phone": "utilities",

    # Salary/Income
    "maosh": "salary",
    "oylik": "salary",
    "ish haqi": "salary",
    "зарплата": "salary",
    "salary": "salary",
    "daromad": "income",
    "kirim": "income",
    "доход": "income",
    "income": "income",

    # Shopping
    "kiyim": "shopping",
    "одежда": "shopping",
    "clothes": "shopping",
    "shopping": "shopping",
    "xarid": "shopping",
    "покупки": "shopping",

    # Entertainment
    "ko'ngilochar": "entertainment",
    "kino": "entertainment",
    "кино": "entertainment",
    "развлечения": "entertainment",
    "entertainment": "entertainment",
    "game": "entertainment",
    "o'yin": "entertainment",
    "игра": "entertainment",

    # Health
    "dorixona": "health",
    "tabletka": "health",
    "shifokor": "health",
    "аптека": "health",
    "врач": "health",
    "лекарство": "health",
    "hospital": "health",
    "kasalxona": "health",
    "health": "health",
    "medicine": "health",

    # Education
    "ta'lim": "education",
    "kurs": "education",
    "kitob": "education",
    "образование": "education",
    "курс": "education",
    "книга": "education",
    "education": "education",
    "school": "education",
    "maktab": "education",

    # Business
    "biznes": "business",
    "бизнес": "business",
    "business": "business",
    "investitsiya": "business",
    "инвестиция": "business",
    "investment": "business",
}


def normalize_category(raw: str) -> str:
    """Normalize a category name to a standard English form.

    Args:
        raw: Raw category string from AI or user input.

    Returns:
        Normalized category name in lowercase English.
    """
    cleaned = raw.strip().lower()
    return CATEGORY_MAP.get(cleaned, cleaned)


async def get_or_create_category(
    session: AsyncSession,
    user_id: int,
    name: str,
    type_: str,
) -> Category:
    """Get an existing category or create a new one."""
    normalized = normalize_category(name)

    query = select(Category).where(
        Category.user_id == user_id,
        Category.name == normalized,
        Category.type == type_,
    )
    result = await session.execute(query)
    category = result.scalar_one_or_none()

    if not category:
        category = Category(
            user_id=user_id,
            name=normalized,
            type=type_,
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        logger.info(f"Created category '{normalized}' for user {user_id}")

    return category


async def get_user_categories(
    session: AsyncSession,
    user_id: int,
    type_filter: Optional[str] = None,
) -> list[Category]:
    """Get all categories for a user."""
    query = select(Category).where(Category.user_id == user_id)
    if type_filter:
        query = query.where(Category.type == type_filter)

    result = await session.execute(query)
    return list(result.scalars().all())
