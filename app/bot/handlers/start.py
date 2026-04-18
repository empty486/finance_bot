"""Start and help command handlers."""

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command — welcome message with usage guide."""
    name = message.from_user.first_name or "do'stim"

    welcome_text = (
        f"👋 <b>Salom, {name}! Finance Bot'ga xush kelibsiz!</b>\n\n"
        "Men sizning moliyaviy tranzaksiyalaringizni kuzatishga yordam beraman.\n"
        "🎤 <b>Ovozli va matnli xabarlar</b> orqali ishlaydi!\n\n"
        "📝 <b>Qanday foydalanish:</b>\n\n"
        "💰 <b>Tranzaksiya qo'shish:</b>\n"
        "Oddiy matn yoki ovozli xabar yuboring:\n"
        "• <code>50k ovqatga sarfladim</code>\n"
        "• <code>500 ming taxi uchun</code>\n"
        "• <code>2 mln oylik oldim</code>\n"
        "• <code>Spent 100k on groceries</code>\n"
        "• <code>Получил зарплату 3 mln</code>\n\n"
        "📊 <b>Statistika so'rash:</b>\n"
        "• <code>Bugun qancha?</code>\n"
        "• <code>Bu hafta xarajat qancha?</code>\n"
        "• <code>Kechagi hisobot</code>\n"
        "• <code>Bu oy nima saqlandi?</code>\n\n"
        "✏️ <b>Tahrirlash/O'chirish:</b>\n"
        "• <code>Oxirgisini o'chir</code>\n"
        "• <code>500k emas 400k edi</code>\n\n"
        "📋 <b>Buyruqlar:</b>\n"
        "/stats — Bugungi statistika\n"
        "/week — Haftalik hisobot\n"
        "/month — Oylik hisobot\n"
        "/tranzaksiyalar — Barcha tranzaksiyalar tarixi\n"
        "/help — Yordam"
    )
    await message.answer(welcome_text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command — detailed usage instructions."""
    help_text = (
        "🆘 <b>Yordam — Finance Bot</b>\n\n"
        "🔹 <b>Tranzaksiya qo'shish</b>\n"
        "Oddiy matn yoki 🎤 ovozli xabar yuboring — bot avtomatik ravishda "
        "summani, turini va kategoriyani aniqlaydi.\n\n"
        "🔹 <b>Qo'llab-quvvatlanadigan tillar:</b>\n"
        "🇺🇿 O'zbek (barcha shevalar) | 🇷🇺 Русский | 🇬🇧 English\n"
        "Aralash gapirish ham ishlaydi!\n\n"
        "🔹 <b>Summa formatlari:</b>\n"
        "• 500 ming = 500,000\n"
        "• 1 mln = 1,000,000\n"
        "• 50k = 50,000\n"
        "• ikki yarim million = 2,500,000\n\n"
        "🔹 <b>Statistika so'rovlari:</b>\n"
        "• Bugun / Kecha / Bu hafta / Bu oy\n"
        "• Qancha / Necha / Jami / Balans\n"
        "• Ovozli xabarda ham so'rash mumkin!\n\n"
        "🔹 <b>Boshqarish:</b>\n"
        "• O'chirish: <code>o'chir</code> / <code>удали</code> / <code>delete</code>\n"
        "• Tahrirlash: <code>500k emas 400k edi</code>"
    )
    await message.answer(help_text, parse_mode="HTML")
