"""Manage handler — edit and delete transactions (production-ready)."""

import logging

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.transaction_service import (
    get_last_transaction,
    update_transaction,
    delete_transaction,
)
from app.services.analytics_service import get_summary

logger = logging.getLogger(__name__)

router = Router()


def format_amount(amount: float) -> str:
    """Format amount with thousands separators."""
    if amount == 0:
        return "0"
    return f"{amount:,.0f}"


async def handle_edit_delete(
    message: Message,
    session: AsyncSession,
    command: dict,
) -> None:
    """Handle edit or delete commands for the last transaction."""
    try:
        user_id = message.from_user.id
        command_type = command.get("command_type")

        # Get last transaction
        last_tx = await get_last_transaction(session, user_id)

        if not last_tx:
            await message.answer(
                "❌ <b>Hech qanday tranzaksiya topilmadi.</b>\n\n"
                "Avval tranzaksiya qo'shing:\n"
                "<code>50k ovqatga sarfladim</code>",
                parse_mode="HTML",
            )
            return

        if command_type == "delete":
            tx_info = (
                f"💰 {format_amount(float(last_tx.amount))} so'm\n"
                f"🏷 {last_tx.category}\n"
                f"📅 {last_tx.date.strftime('%d.%m.%Y')}"
            )

            success = await delete_transaction(session, last_tx.id, user_id)

            if success:
                # Show updated stats
                summary = await get_summary(session, user_id, "today")
                await message.answer(
                    f"🗑 <b>Tranzaksiya o'chirildi!</b>\n"
                    f"{'━' * 28}\n"
                    f"{tx_info}\n"
                    f"{'━' * 28}\n\n"
                    f"📊 <b>Yangilangan bugungi hisobot:</b>\n"
                    f"📈 Daromad: {format_amount(summary['total_income'])} so'm\n"
                    f"📉 Xarajat: {format_amount(summary['total_expense'])} so'm\n"
                    f"💰 Balans: {format_amount(summary['balance'])} so'm",
                    parse_mode="HTML",
                )
            else:
                await message.answer(
                    "❌ Tranzaksiyani o'chirishda xatolik yuz berdi.",
                    parse_mode="HTML",
                )

        elif command_type == "edit":
            new_amount = command.get("new_amount")

            if not new_amount or new_amount <= 0:
                await message.answer(
                    "❓ <b>Yangi summani aniqlab bo'lmadi.</b>\n"
                    "Iltimos, qayta yozing.\n\n"
                    "Masalan: <code>500k emas 400k edi</code>",
                    parse_mode="HTML",
                )
                return

            old_amount = float(last_tx.amount)
            updated_tx = await update_transaction(
                session, last_tx.id, user_id, amount=new_amount
            )

            if updated_tx:
                diff = new_amount - old_amount
                diff_emoji = "📈" if diff > 0 else "📉"
                diff_label = f"+{format_amount(abs(diff))}" if diff > 0 else f"-{format_amount(abs(diff))}"

                # Show updated stats
                summary = await get_summary(session, user_id, "today")
                await message.answer(
                    f"✏️ <b>Tranzaksiya tahrirlandi!</b>\n"
                    f"{'━' * 28}\n\n"
                    f"Eski summa: {format_amount(old_amount)} so'm\n"
                    f"Yangi summa: <b>{format_amount(new_amount)} so'm</b>\n"
                    f"{diff_emoji} Farq: {diff_label} so'm\n"
                    f"🏷 Kategoriya: {last_tx.category}\n"
                    f"{'━' * 28}\n\n"
                    f"📊 <b>Yangilangan bugungi hisobot:</b>\n"
                    f"📈 Daromad: {format_amount(summary['total_income'])} so'm\n"
                    f"📉 Xarajat: {format_amount(summary['total_expense'])} so'm\n"
                    f"💰 Balans: {format_amount(summary['balance'])} so'm",
                    parse_mode="HTML",
                )
            else:
                await message.answer(
                    "❌ Tranzaksiyani tahrirlashda xatolik yuz berdi.",
                    parse_mode="HTML",
                )

    except Exception as e:
        logger.error(f"Edit/delete handler error: {e}")
        await message.answer(
            "❌ Buyruqni bajarishda xatolik yuz berdi.\n"
            "Iltimos, qayta urinib ko'ring.",
            parse_mode="HTML",
        )
