import datetime
from zoneinfo import ZoneInfo
import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot.database import Database
from bot.utils import get_current_date, build_challenge_summary_embed
from bot.config import (
    DEFAULT_TIMEZONE,
    MORNING_REPORT_HOUR,
    MORNING_REPORT_MINUTE,
    ALLOWED_CHANNEL_NAME,
    ALLOWED_CHANNEL_ID
)

class SchedulerCog(commands.Cog, name="Scheduler"):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db

    async def cog_load(self):
        self.daily_audit_loop.start()
        self.morning_briefing_loop.start()

    def cog_unload(self):
        self.daily_audit_loop.cancel()
        self.morning_briefing_loop.cancel()

    async def run_audit_for_date(self, audit_date: str) -> dict:
        """
        Audits all active challenges for a given date.
        Participants who did not log any of their pledged languages on that date
        are penalized according to the challenge penalty amount.
        """
        challenges = await self.db.get_active_challenges()
        results = {}

        for ch in challenges:
            ch_id = ch["id"]
            # Skip if already audited for this date
            if await self.db.has_daily_audit_run(ch_id, audit_date):
                continue

            # Don't audit dates before the challenge started
            start_date = ch.get("start_date")
            if start_date and audit_date < start_date:
                continue

            participants = await self.db.get_challenge_participants(ch_id)
            penalized_users = []

            for p in participants:
                uid = p["user_id"]
                langs = p.get("languages", [])

                # Check if user logged any of their pledged languages on audit_date
                has_logged = await self.db.has_logged_challenge_for_date(uid, langs, audit_date)
                if not has_logged:
                    penalized_users.append(uid)

            # Record audit and update penalties
            penalty_amount = ch.get("penalty_amount", 0.0)
            await self.db.record_daily_audit(
                challenge_id=ch_id,
                audit_date=audit_date,
                penalized_user_ids=penalized_users,
                penalty_amount=penalty_amount
            )
            results[ch_id] = {
                "challenge": ch,
                "penalized_users": penalized_users,
                "penalty_amount": penalty_amount
            }

        return results

    @tasks.loop(minutes=15)
    async def daily_audit_loop(self):
        """
        Runs every 15 minutes to check if midnight has passed.
        Audits yesterday's study logs for all active challenges.
        """
        await self.bot.wait_until_ready()
        try:
            tz = ZoneInfo(DEFAULT_TIMEZONE)
        except Exception:
            tz = ZoneInfo("UTC")

        now = datetime.datetime.now(tz)
        yesterday = (now.date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        await self.run_audit_for_date(yesterday)

    @daily_audit_loop.before_loop
    async def before_daily_audit(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def morning_briefing_loop(self):
        """
        Checks once every minute whether it is time for the morning briefing.
        Sends a briefing message to the languages channel for all active challenges.
        """
        await self.bot.wait_until_ready()
        try:
            tz = ZoneInfo(DEFAULT_TIMEZONE)
        except Exception:
            tz = ZoneInfo("UTC")

        now = datetime.datetime.now(tz)
        if now.hour == MORNING_REPORT_HOUR and now.minute == MORNING_REPORT_MINUTE:
            today_str = now.strftime("%Y-%m-%d")
            yesterday_str = (now.date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

            # Make sure yesterday's audit has run
            await self.run_audit_for_date(yesterday_str)

            challenges = await self.db.get_active_challenges()
            if not challenges:
                return

            for ch in challenges:
                summary = await self.db.get_challenge_summary(ch["id"])
                if not summary:
                    continue

                # Locate channel to send to
                target_channel = None
                ch_channel_id = ch.get("channel_id")
                if ch_channel_id:
                    target_channel = self.bot.get_channel(ch_channel_id)

                if not target_channel and ALLOWED_CHANNEL_ID:
                    target_channel = self.bot.get_channel(ALLOWED_CHANNEL_ID)

                if not target_channel:
                    # Find by channel name in guild
                    guild = self.bot.get_guild(ch.get("guild_id"))
                    if guild:
                        target_channel = discord.utils.get(guild.text_channels, name=ALLOWED_CHANNEL_NAME)

                if not target_channel:
                    continue

                embed = build_challenge_summary_embed(summary, today_str)
                embed.title = f"🌅 Morning Briefing: {ch['title']}"

                # Calculate who missed yesterday
                sym = ch.get("currency_symbol", "$")
                penalties = ch.get("penalty_amount", 0.0)

                participants = summary.get("participants", [])
                missed_yesterday = []
                for p in participants:
                    has_logged = await self.db.has_logged_challenge_for_date(p["user_id"], p.get("languages", []), yesterday_str)
                    if not has_logged:
                        missed_yesterday.append(f"<@{p['user_id']}> (+{sym}{penalties:,.2f})")

                if missed_yesterday:
                    embed.add_field(
                        name="💸 Missed Yesterday (Pot Additions)",
                        value=", ".join(missed_yesterday),
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🔥 Flawless Day!",
                        value="Everyone logged their languages yesterday! No penalties added.",
                        inline=False
                    )

                embed.set_footer(text="Log your progress today before 11:59 PM to protect your streak!")
                try:
                    await target_channel.send(content="☀️ **Good morning language learners! Here is today's challenge update:**", embed=embed)
                except Exception as e:
                    print(f"Failed to post morning briefing to channel {target_channel.id}: {e}")

    @morning_briefing_loop.before_loop
    async def before_morning_briefing(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="audit_now", description="(Admin) Force an immediate audit of challenge penalties for yesterday")
    @app_commands.default_permissions(administrator=True)
    async def audit_now(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            tz = ZoneInfo(DEFAULT_TIMEZONE)
        except Exception:
            tz = ZoneInfo("UTC")
        yesterday_str = (datetime.datetime.now(tz).date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        results = await self.run_audit_for_date(yesterday_str)
        if not results:
            await interaction.followup.send(f"Audit for `{yesterday_str}` was already completed or no active challenges.", ephemeral=True)
        else:
            msg = [f"✅ Audit completed for `{yesterday_str}`:"]
            for cid, data in results.items():
                msg.append(f"• Challenge #{cid}: {len(data['penalized_users'])} participants penalized")
            await interaction.followup.send("\n".join(msg), ephemeral=True)

async def setup(bot: commands.Bot):
    db: Database = bot.db
    await bot.add_cog(SchedulerCog(bot, db))

