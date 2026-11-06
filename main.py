import asyncio
import base64
import logging
import sys
import discord
from discord.ext import commands

from bot.config import (
    DISCORD_TOKEN,
    DATABASE_PATH,
    GUILD_ID,
    BOT_NAME
)
from bot.database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Polyglot")

class PolyglotBot(commands.Bot):
    def __init__(self, db: Database):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        app_id = None
        if DISCORD_TOKEN and "." in DISCORD_TOKEN:
            try:
                raw_id = DISCORD_TOKEN.split(".")[0]
                padded = raw_id + "=" * (-len(raw_id) % 4)
                app_id = int(base64.b64decode(padded).decode("utf-8"))
            except Exception:
                pass

        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=app_id,
            help_command=None
        )
        self.db = db
        self.synced = False

    async def setup_hook(self):
        # Initialize database tables
        logger.info("Initializing database...")
        await self.db.init_db()

        # Load extension cogs
        cogs = [
            "bot.cogs.learning",
            "bot.cogs.challenges",
            "bot.cogs.scheduler",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded extension: {cog}")
            except Exception as e:
                logger.error(f"Failed to load extension {cog}: {e}", exc_info=True)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        # Sync slash commands if not already synced
        if not self.synced:
            try:
                # If a specific GUILD_ID is set, clear guild-specific copies to remove duplicates
                if GUILD_ID:
                    guild = discord.Object(id=GUILD_ID)
                    self.tree.clear_commands(guild=guild)
                    await self.tree.sync(guild=guild)
                    logger.info(f"Cleared guild-specific duplicates for guild ID {GUILD_ID}")

                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands globally (single unified set)")
                self.synced = True
            except Exception as e:
                logger.error(f"Failed to sync slash commands: {e}", exc_info=True)

        logger.info(f"{BOT_NAME} is active and listening for commands!")
        activity = discord.Activity(type=discord.ActivityType.listening, name="/log in #languages")
        await self.change_presence(status=discord.Status.online, activity=activity)

async def main():
    if not DISCORD_TOKEN:
        logger.error(
            "DISCORD_TOKEN is missing! Please edit your .env file and set DISCORD_TOKEN=your_token."
        )
        sys.exit(1)

    db = Database(DATABASE_PATH)
    bot = PolyglotBot(db)

    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutting down gracefully.")

