# 🤖 Finance Bot — Smart Telegram Accounting with Gemini AI

A production-ready Telegram bot designed for high-performance financial tracking. Powered by **Gemini 2.5 Flash**, it understands natural language (text & voice) in Uzbek, Russian, and English.

## 🌟 Key Features

- **🗣 Voice-to-Data**: Send a voice message like *"Today I spent 50k on a taxi and bought apples for 20k"* — the bot transcribes, parses, and saves both transactions instantly.
- **🧠 Advanced NL Parsing**: High-accuracy extraction from messy, mixed-language, or dialect-heavy input (Uzbek dialects, Russian slang, English).
- **🛤 Multi-Transaction Support**: Automatically splits multiple entries from a single message (e.g., *"10k meal, 25k fuel, 5k coffee"*).
- **📊 Professional Analytics**:
  - **Summary**: Today, Yesterday, This Week, This Month reports.
  - **Pagination**: Browse history with `/tranzaksiyalar` via interactive inline buttons.
  - **Insights**: AI-driven breakdown of spending habits and category totals.
- **✏️ Natural Language Management**:
  - *"O'chir"* (Delete) — removes the last entry.
  - *"500 emas 400 edi"* (Edit) — fixes the last entry's amount.
- **🐳 Dockerized**: Fully containerized with PostgreSQL 16 (Alpine).

## 🛠 Tech Stack

- **Core**: Python 3.11+ & [aiogram 3](https://docs.aiogram.dev/)
- **AI**: [Google Gemini 2.5 Flash](https://aistudio.google.com/) (Multimodal)
- **Database**: [PostgreSQL 16](https://www.postgresql.org/) (Async via `asyncpg`)
- **ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)

---

## 🚀 Quick Start (Docker)

The fastest way to get started is using Docker Compose.

1. **Clone and Configure**:
   ```bash
   git clone <repo_url>
   cd "Finance Bot"
   cp .env.example .env
   ```
2. **Edit `.env`**:
   - `BOT_TOKEN`: Get from [@BotFather](https://t.me/BotFather)
   - `GEMINI_API_KEY`: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - `DATABASE_URL`: `postgresql+asyncpg://user:password@postgres:5432/finance_db`
3. **Launch**:
   ```bash
   docker-compose up -d --build
   ```

---

## 💬 Usage Guide

### 📤 Adding Transactions (Text or Voice)
The bot is flexible. Try these formats:
- *"50k ovqatga"* (50,000 expense, category food)
- *"3 mln oylik oldim"* (3,000,000 income, category salary)
- *"Spent 100k on groceries and 20k for taxi"* (2 transactions split)
- *"10000 som Husanboyga qarz berdim"* (Note: Husanboyga qarz)

### 📊 Checking Statistics
- `/stats` — Today's summary.
- `/week` — This week's summary.
- `/month` — Detailed monthly report with categories.
- `/tranzaksiyalar` — Interactive history list with pagination.

### ⚙️ Managing Records
- **Delete**: Just say *"o'chir"*, *"delete last"*, or *"bekor qil"*.
- **Edit**: Say *"50k emas 60k edi"* or *"tuzat 50000"*.

---

## 📁 Project Architecture

```text
app/
├── main.py              # Entry point & startup logic
├── config.py            # Environment-based configuration
├── ai/
│   └── parser.py        # Gemini AI (Async, Unified Intent Analysis)
├── bot/
│   ├── bot.py           # Bot configuration & command routers
│   ├── handlers/        # Business logic (Text, Voice, History, Manage)
│   └── middlewares/     # Database session management
├── db/
│   ├── engine.py        # Async SQL engine setup
│   └── init_db.py       # Table initialization
├── models/              # SQLAlchemy schemas (Transaction, Category)
└── services/            # Core business services (Analytics, CRUD)
```

---

## 🛡 Production Features
- **Auto-rollback**: `DbSessionMiddleware` ensures no partial saves on errors.
- **Polling Resiliency**: Graceful startup with connection retries.
- **Secure Sessions**: Proper async session handling for high concurrency.

## 📝 License
Built with ❤️ by [@devit_uz](https://t.me/devit_uz) | [delgo.uz](https://delgo.uz/)
License: MIT
