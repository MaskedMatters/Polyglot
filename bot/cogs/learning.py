import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
from bot.database import Database
from bot.languages import (
    search_languages,
    normalize_language_name,
    get_language_flag,
    GOOGLE_TRANSLATE_LANGUAGES
)
from bot.utils import (
    get_current_date,
    calculate_streak,
    get_language_emoji,
    validate_timezone,
    POPULAR_TIMEZONES,
    is_channel_allowed,
    build_log_success_embed,
    build_stats_embed,
    format_duration
)
from bot.config import ALLOWED_CHANNEL_NAME, ALLOWED_CHANNEL_ID

def channel_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not is_channel_allowed(interaction):
            chan_mention = f"<#{ALLOWED_CHANNEL_ID}>" if ALLOWED_CHANNEL_ID else f"`#{ALLOWED_CHANNEL_NAME}`"
            await interaction.response.send_message(
                f"⚠️ Polyglot commands are restricted to {chan_mention}. Please head over there!",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

class LearningCog(commands.Cog, name="Learning"):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db

    async def google_translate_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for all Google Translate supported languages with flags."""
        results = search_languages(current, limit=25)
        return [
            app_commands.Choice(name=f"{flag} {name}", value=name)
            for name, flag in results
        ]

    async def enrolled_languages_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for languages the user is currently learning."""
        user_langs = await self.db.get_user_languages(interaction.user.id)
        choices = []
        for l in user_langs:
            lang_name = l["language"]
            flag = get_language_flag(lang_name)
            if current.lower() in lang_name.lower():
                choices.append(app_commands.Choice(name=f"{flag} {lang_name}", value=lang_name))
        return choices[:25]

    async def timezone_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for popular timezones."""
        matches = [
            app_commands.Choice(name=tz, value=tz)
            for tz in POPULAR_TIMEZONES
            if current.lower() in tz.lower()
        ]
        return matches[:25]

    @app_commands.command(name="learn", description="Start learning a language from Google Translate's official list!")
    @app_commands.describe(language="Select a language from the official Google Translate list")
    @app_commands.autocomplete(language=google_translate_autocomplete)
    @channel_check()
    async def learn(self, interaction: discord.Interaction, language: str):
        canonical_lang = normalize_language_name(language)

        if not canonical_lang:
            await interaction.response.send_message(
                f"❌ **\"{language}\"** is not in the official Google Translate languages list.\n"
                f"Please choose a language from the dropdown menu when typing `/learn`.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        username = interaction.user.display_name

        await self.db.get_or_create_user(user_id, username)
        added = await self.db.add_user_language(user_id, canonical_lang)
        flag = get_language_flag(canonical_lang)

        if added:
            embed = discord.Embed(
                title=f"{flag} Started Learning {canonical_lang}!",
                description=(
                    f"Welcome to your **{canonical_lang}** journey, {interaction.user.mention}!\n\n"
                    f"• Log daily with `/log language:{canonical_lang} duration:<minutes>`\n"
                    f"• Set your timezone with `/timezone` to guarantee accurate streaks\n"
                    f"• Challenge friends with `/challenge create`!"
                ),
                color=discord.Color.from_rgb(88, 101, 242)
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                f"You are already learning **{flag} {canonical_lang}**! Log your study with `/log language:{canonical_lang}`.",
                ephemeral=True
            )

    @app_commands.command(name="giveup", description="Give up on or drop a language you are tracking")
    @app_commands.describe(language="The language you wish to stop learning")
    @app_commands.autocomplete(language=enrolled_languages_autocomplete)
    @channel_check()
    async def giveup(self, interaction: discord.Interaction, language: str):
        clean_lang = language.strip().title()
        user_id = interaction.user.id

        # Get existing stats for this language before removing
        lang_data = await self.db.get_user_language(user_id, clean_lang)
        if not lang_data:
            await interaction.response.send_message(
                f"You are not actively learning **{clean_lang}**.",
                ephemeral=True
            )
            return

        flag = get_language_flag(clean_lang)
        total_time = format_duration(lang_data.get("total_minutes", 0))
        longest = lang_data.get("longest_streak", 0)
        total_logs = lang_data.get("total_logs", 0)

        await self.db.remove_user_language(user_id, clean_lang)

        embed = discord.Embed(
            title=f"🏳️ Given Up: {flag} {clean_lang}",
            description=(
                f"{interaction.user.mention} has stopped learning **{clean_lang}**.\n\n"
                f"📊 **Final Record:**\n"
                f"• ⏱️ **Total Time:** {total_time}\n"
                f"• 🏆 **Best Streak:** {longest} days\n"
                f"• 📝 **Total Logs:** {total_logs}\n\n"
                f"*Your historical study sessions remain archived in the database if you ever return.*"
            ),
            color=discord.Color.from_rgb(235, 69, 158)
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unlearn", description="Stop tracking a language (alias for /giveup)")
    @app_commands.describe(language="The language you want to remove")
    @app_commands.autocomplete(language=enrolled_languages_autocomplete)
    @channel_check()
    async def unlearn(self, interaction: discord.Interaction, language: str):
        await self.giveup.callback(self, interaction, language)

    @app_commands.command(name="log", description="Log your daily language study session with streak tracking!")
    @app_commands.describe(
        language="Language studied",
        duration="Time spent studying in minutes (e.g. 30, 45, 60)",
        description="Optional brief notes on what you studied (e.g. Anki deck, chapter 4)",
        proof="Optional image proof of study (screenshot of app, book, notes)"
    )
    @app_commands.autocomplete(language=enrolled_languages_autocomplete)
    @channel_check()
    async def log(
        self,
        interaction: discord.Interaction,
        language: str,
        duration: int,
        description: Optional[str] = None,
        proof: Optional[discord.Attachment] = None
    ):
        if duration <= 0:
            await interaction.response.send_message("❌ Study duration must be at least 1 minute.", ephemeral=True)
            return
        if duration > 1440:
            await interaction.response.send_message("❌ Maximum duration for a single log is 1440 minutes (24 hours).", ephemeral=True)
            return

        canonical_lang = normalize_language_name(language)
        if not canonical_lang:
            await interaction.response.send_message(
                f"❌ **\"{language}\"** is not a recognized Google Translate language.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        username = interaction.user.display_name

        user = await self.db.get_or_create_user(user_id, username)
        user_tz = user.get("timezone") or "America/New_York"

        # Check if enrolled
        lang_data = await self.db.get_user_language(user_id, canonical_lang)
        if not lang_data:
            # Auto-enroll them if they haven't run /learn yet
            await self.db.add_user_language(user_id, canonical_lang)
            lang_data = await self.db.get_user_language(user_id, canonical_lang)

        today_date, today_str = get_current_date(user_tz)

        current_streak = lang_data.get("current_streak", 0)
        longest_streak = lang_data.get("longest_streak", 0)
        last_logged_date = lang_data.get("last_logged_date")

        new_streak, new_longest, already_logged_today = calculate_streak(
            today_date=today_date,
            last_logged_date_str=last_logged_date,
            current_streak=current_streak,
            longest_streak=longest_streak
        )

        proof_url = proof.url if proof and proof.content_type and proof.content_type.startswith("image") else None

        await self.db.log_study_session(
            user_id=user_id,
            language=canonical_lang,
            duration_minutes=duration,
            description=description,
            proof_url=proof_url,
            log_date=today_str,
            new_streak=new_streak,
            longest_streak=new_longest
        )

        # Retrieve updated stats
        stats = await self.db.get_user_stats(user_id, canonical_lang)
        total_minutes = stats.get("total_minutes", duration)
        active_days = stats.get("active_days", 1)

        embed = build_log_success_embed(
            language=canonical_lang,
            duration_minutes=duration,
            total_minutes=total_minutes,
            streak=new_streak,
            longest_streak=new_longest,
            total_days=active_days,
            description=description,
            proof_url=proof_url
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="View study statistics and streaks")
    @app_commands.describe(
        language="Optional: Filter stats for a specific language",
        user="Optional: View another member's statistics"
    )
    @app_commands.autocomplete(language=enrolled_languages_autocomplete)
    @channel_check()
    async def stats(
        self,
        interaction: discord.Interaction,
        language: Optional[str] = None,
        user: Optional[discord.User] = None
    ):
        target_user = user or interaction.user
        canonical_lang = normalize_language_name(language) if language else None

        stats_data = await self.db.get_user_stats(target_user.id, canonical_lang)
        embed = build_stats_embed(target_user, stats_data, canonical_lang)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="languages", description="List all languages you or another user are learning")
    @app_commands.describe(user="Optional: View another member's languages")
    @channel_check()
    async def languages(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        target_user = user or interaction.user
        langs = await self.db.get_user_languages(target_user.id)

        if not langs:
            msg = f"{target_user.display_name} has not enrolled in any languages yet."
            if target_user == interaction.user:
                msg += " Use `/learn` to choose a language from the list!"
            await interaction.response.send_message(msg, ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🌐 Languages: {target_user.display_name}",
            color=discord.Color.from_rgb(88, 101, 242)
        )
        lines = []
        for l in langs:
            flag = get_language_flag(l["language"])
            streak = l["current_streak"]
            longest = l["longest_streak"]
            total_time = format_duration(l["total_minutes"])
            lines.append(
                f"{flag} **{l['language']}**\n"
                f"└ 🔥 Current: **{streak}d** • 🏆 Best: **{longest}d** • ⏱️ **{total_time}** total"
            )

        embed.description = "\n\n".join(lines)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="timezone", description="Set your personal timezone for accurate daily cutoffs")
    @app_commands.describe(tz="Your timezone (e.g. America/New_York, Europe/London, Asia/Tokyo)")
    @app_commands.autocomplete(tz=timezone_autocomplete)
    @channel_check()
    async def set_timezone(self, interaction: discord.Interaction, tz: str):
        if not validate_timezone(tz):
            await interaction.response.send_message(
                f"❌ Invalid timezone name `{tz}`. Please select from the autocomplete list (e.g., `America/New_York`, `UTC`, `Asia/Tokyo`).",
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        await self.db.get_or_create_user(user_id, interaction.user.display_name, default_tz=tz)
        await self.db.set_user_timezone(user_id, tz)

        today_date, today_str = get_current_date(tz)
        await interaction.response.send_message(
            f"✅ Timezone set to **`{tz}`**! Your local date is currently **{today_str}**.\n"
            f"Daily cutoffs for your challenges and streaks will align with your local midnight (11:59 PM).",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    db: Database = bot.db
    await bot.add_cog(LearningCog(bot, db))
