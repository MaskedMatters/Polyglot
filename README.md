# 🌐 Polyglot — Discord Language Tracking & Challenge Bot

> **Polyglot** is a sleek, minimalist Discord bot designed to keep language learners motivated and accountable in your server's `#languages` channel.

---

## 🌟 Name Ideas For Your Bot

Here are some suggested names for your Discord bot application:
1. **Polyglot** *(Default — classic, sleek, prestigious)*
2. **LingoForge** *(Modern, gamified, community-driven)*
3. **BabelBot** *(Playful reference to the Tower of Babel)*
4. **LinguaVault** *(Aesthetic, focused on logged hours and streaks)*
5. **StreakLingo** *(Direct, competitive, habit-forming)*

You can set your bot's name in `.env` under `BOT_NAME`.

---

## ✨ Features

- **Channel-Restricted**: Works exclusively in `#languages` (customizable via `.env`). Commands run in other channels get an ephemeral notification pointing users to `#languages`.
- **Multi-Language Support**: Users can track multiple languages simultaneously (e.g., Japanese, Spanish, French).
- **Daily Study Logging (`/log`)**:
  - Log study minutes (e.g., 30m, 45m).
  - Optional description notes (e.g., *Anki vocabulary deck, Genki Chapter 3*).
  - Optional proof image attachment (screenshot of Duolingo, textbook, or notes).
  - Automatic streak calculation and longest-streak memory.
  - Minimalist response embed with study time, active days, and streak badges.
- **Personalized Timezones (`/timezone`)**: Each user can set their timezone (e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`) so midnight deadlines align with their real-world day.
- **Language Profiles & Statistics (`/stats`, `/languages`)**:
  - Track current streak, best streak, total study hours, active study days, and daily session averages.
- **Accountability Challenges (`/challenge`)**:
  - Anyone can create a challenge with a specified daily penalty amount (e.g. `$5.00` per missed day).
  - Others can join via interactive **"⚔️ Join Challenge"** button or `/challenge join`, pledging one or multiple languages.
  - **11:59 PM Cutoff**: If a participant does not log at least one study session in their pledged languages by 11:59 PM, the penalty amount is automatically added to their tab in the challenge pot.
  - **Morning Briefing (8:00 AM)**: The bot automatically posts a daily morning briefing embed in `#languages` announcing total pot standings, streak champions, and who contributed to the pot overnight.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- A Discord Bot Application from the [Discord Developer Portal](https://discord.com/developers/applications)

### 2. Configure Discord Bot Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications) and click **"New Application"** (name it **Polyglot** or your chosen name).
2. Go to the **Bot** tab:
   - Click **"Reset Token"** and copy your token.
   - Upload the custom avatar icon located at `assets/icon.png`.
   - Under **Privileged Gateway Intents**, enable:
     - **Server Members Intent**
     - **Message Content Intent**
3. Go to **OAuth2 > URL Generator**:
   - Under **Scopes**: select `bot` and `applications.commands`.
   - Under **Bot Permissions**: select `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`, `Use Slash Commands`.
   - Copy the generated URL and open it in your browser to invite the bot to your server.
4. Ensure your server has a channel named `#languages`.

### 3. Installation

Clone or navigate to the repository folder:

```bash
cd LangBot
```

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Open `.env` and fill in your Discord Bot Token:

```ini
# Discord Bot Token
DISCORD_TOKEN=your_token_here

# Channel name where commands are allowed (default: languages)
ALLOWED_CHANNEL_NAME=languages

# Optional: Specific Channel ID if you prefer strict ID matching
ALLOWED_CHANNEL_ID=

# Optional: Server Guild ID for instant slash command sync during setup
GUILD_ID=

# Server Default Timezone
DEFAULT_TIMEZONE=America/New_York

# Morning report time (8:00 AM)
MORNING_REPORT_HOUR=8
MORNING_REPORT_MINUTE=0
```

### 5. Running the Bot

#### Option A: Running with Docker (Recommended)
You can run the bot inside a lightweight Docker container with persistent SQLite storage:

```bash
# Start in the background using Docker Compose
docker compose up -d --build

# View real-time logs
docker compose logs -f

# Stop the bot
docker compose down
```

Or using standard `docker build` & `docker run`:
```bash
# Build the image
docker build -t polyglot-bot .

# Run with .env and persistent data mount
docker run -d --name polyglot-bot --env-file .env -v $(pwd)/data:/app/data --restart unless-stopped polyglot-bot
```

#### Option B: Running Locally with Python
```bash
source .venv/bin/activate
python3 main.py
```

Slash commands will register automatically on startup!

---

## 📖 Command Reference

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `/learn` | `language: <name>` | Enroll in a language from the official Google Translate list (with flag emojis). |
| `/giveup` | `language: <name>` | Drop/give up on a language, displaying your final stats and streak. |
| `/unlearn` | `language: <name>` | Alias for `/giveup`. |
| `/log` | `language: <name>`, `duration: <min>`, `[description]`, `[proof]` | Log study minutes, streak, notes, and optional proof image. |
| `/stats` | `[language]`, `[user]` | View detailed study statistics and streak data. |
| `/languages` | `[user]` | View all languages and current streaks for a user. |
| `/timezone` | `tz: <timezone>` | Set your personal timezone for accurate daily cutoffs. |
| `/challenge create` | `title: <text>`, `penalty: <amount>`, `languages: <langs>`, `[currency]` | Create an accountability challenge with a daily penalty pot. |
| `/challenge join` | `challenge_id: <id>`, `languages: <langs>` | Join an active challenge pledging Google Translate language(s). |
| `/challenge stats` | `challenge_id: <id>` | View the pot total, leaderboard, and participant tabs. |
| `/challenge list` | *None* | List all active challenges in the server. |
| `/challenge leave` | `challenge_id: <id>` | Leave an active challenge (removes you from future penalty audits). |
| `/challenge end` | `challenge_id: <id>` | (Creator/Admin) Finalize a challenge, post final pot & crown champions. |
| `/audit_now` | *(Admin only)* | Trigger an immediate manual audit for yesterday's study logs. |

---

## 🧪 Running Tests

The test suite validates database integrity, streak arithmetic, and challenge penalty calculations:

```bash
source .venv/bin/activate
python3 -m unittest discover tests
```

---

## 📁 Project Structure

```
LangBot/
├── bot/
│   ├── __init__.py
│   ├── config.py         # Environment configuration
│   ├── database.py       # Asynchronous SQLite storage & audit logic
│   ├── languages.py      # Google Translate registry & flag emojis
│   ├── utils.py          # Streak calculation, timezone helpers, embeds
│   └── cogs/
│       ├── learning.py   # /learn, /giveup, /log, /stats, /languages, /timezone
│       ├── challenges.py # /challenge create, join, leave, end, list, stats
│       └── scheduler.py  # 11:59 PM audit task & 8:00 AM morning report
├── tests/
│   └── test_bot.py       # Unit test suite
├── assets/
│   ├── icon.png          # Bot avatar icon (flat light theme)
│   ├── icon_option1.png
│   ├── icon_option2.png
│   └── icon_option3.png
├── Dockerfile            # Container definition
├── docker-compose.yml    # Docker Compose configuration
├── .dockerignore         # Docker ignore rules
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── main.py               # Bot entry point
└── README.md             # Documentation
```

