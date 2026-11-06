import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, List
from bot.database import Database
from bot.languages import (
    normalize_language_name,
    get_language_flag,
    search_languages
)
from bot.utils import (
    get_current_date,
    is_channel_allowed,
    build_challenge_summary_embed,
    get_language_emoji
)
from bot.config import ALLOWED_CHANNEL_NAME, ALLOWED_CHANNEL_ID

def channel_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not is_channel_allowed(interaction):
            chan_mention = f"<#{ALLOWED_CHANNEL_ID}>" if ALLOWED_CHANNEL_ID else f"`#{ALLOWED_CHANNEL_NAME}`"
            await interaction.response.send_message(
                f"⚠️ Polyglot commands are restricted to {chan_mention}.",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

class JoinChallengeModal(discord.ui.Modal):
    def __init__(self, db: Database, challenge_id: int, challenge_title: str):
        super().__init__(title=f"Join: {challenge_title[:35]}")
        self.db = db
        self.challenge_id = challenge_id

        self.languages_input = discord.ui.TextInput(
            label="Languages to Pledge (Google Translate list)",
            placeholder="e.g. Japanese, Spanish, French",
            required=True,
            max_length=150
        )
        self.add_item(self.languages_input)

    async def on_submit(self, interaction: discord.Interaction):
        raw_langs = self.languages_input.value.split(",")
        valid_langs = []
        invalid_langs = []

        for l in raw_langs:
            clean = l.strip()
            if not clean:
                continue
            normalized = normalize_language_name(clean)
            if normalized:
                valid_langs.append(normalized)
            else:
                invalid_langs.append(clean)

        if not valid_langs:
            await interaction.response.send_message(
                f"❌ None of the provided languages matched Google Translate: `{', '.join(invalid_langs)}`.\n"
                f"Please check `/learn` for the exact language names.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        await self.db.get_or_create_user(user_id, interaction.user.display_name)

        # Auto-enroll in any languages not already enrolled
        for lang in valid_langs:
            await self.db.add_user_language(user_id, lang)

        await self.db.join_challenge(self.challenge_id, user_id, valid_langs)

        joined_str = ", ".join([f"{get_language_flag(l)} {l}" for l in valid_langs])
        warning_msg = f"\n*(Ignored invalid languages: {', '.join(invalid_langs)})*" if invalid_langs else ""

        await interaction.response.send_message(
            f"🎉 {interaction.user.mention} joined Challenge **#{self.challenge_id}** pledging: **{joined_str}**!{warning_msg}\n"
            f"Log at least one of these daily by 11:59 PM to keep the pot safe!",
            ephemeral=False
        )

class ChallengeJoinView(discord.ui.View):
    def __init__(self, db: Database, challenge_id: int, challenge_title: str):
        super().__init__(timeout=None) # Persistent view
        self.db = db
        self.challenge_id = challenge_id
        self.challenge_title = challenge_title

    @discord.ui.button(label="⚔️ Join Challenge", style=discord.ButtonStyle.primary, custom_id="challenge_join_btn")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self.db.get_challenge(self.challenge_id)
        if not ch or not ch.get("is_active"):
            await interaction.response.send_message("❌ This challenge is no longer active.", ephemeral=True)
            return

        modal = JoinChallengeModal(self.db, self.challenge_id, ch["title"])
        await interaction.response.send_modal(modal)

class ChallengesCog(commands.GroupCog, name="challenge"):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db
        super().__init__()

    async def active_challenges_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> List[app_commands.Choice[int]]:
        challenges = await self.db.get_active_challenges(interaction.guild_id)
        choices = []
        for ch in challenges:
            label = f"#{ch['id']} - {ch['title']} ({ch['currency_symbol']}{ch['penalty_amount']}/day)"
            if current.lower() in label.lower():
                choices.append(app_commands.Choice(name=label[:100], value=ch["id"]))
        return choices[:25]

    @app_commands.command(name="create", description="Create a daily study challenge with a monetary/point penalty pot!")
    @app_commands.describe(
        title="Title of the challenge (e.g. 30-Day Fluency Sprint)",
        penalty="Amount added to the pot per missed day (e.g. 5 for $5.00)",
        languages="Comma-separated Google Translate language(s) you will track (e.g. Japanese, French)",
        currency="Currency symbol or unit (default is $)"
    )
    @channel_check()
    async def create(
        self,
        interaction: discord.Interaction,
        title: str,
        penalty: float,
        languages: str,
        currency: str = "$"
    ):
        if penalty <= 0:
            await interaction.response.send_message("❌ Penalty amount must be greater than 0.", ephemeral=True)
            return

        raw_langs = languages.split(",")
        valid_langs = []
        invalid_langs = []

        for l in raw_langs:
            clean = l.strip()
            if not clean:
                continue
            normalized = normalize_language_name(clean)
            if normalized:
                valid_langs.append(normalized)
            else:
                invalid_langs.append(clean)

        if not valid_langs:
            await interaction.response.send_message(
                f"❌ Please provide at least one valid Google Translate language.\n"
                f"Unrecognized: `{', '.join(invalid_langs)}`",
                ephemeral=True
            )
            return

        guild_id = interaction.guild_id or 0
        channel_id = interaction.channel_id or 0
        creator_id = interaction.user.id
        username = interaction.user.display_name

        user = await self.db.get_or_create_user(creator_id, username)
        _, today_str = get_current_date(user.get("timezone"))

        challenge_id = await self.db.create_challenge(
            guild_id=guild_id,
            channel_id=channel_id,
            creator_id=creator_id,
            title=title,
            penalty_amount=penalty,
            currency_symbol=currency,
            start_date=today_str
        )

        for lang in valid_langs:
            await self.db.add_user_language(creator_id, lang)

        await self.db.join_challenge(challenge_id, creator_id, valid_langs)

        creator_langs_str = ", ".join([f"{get_language_flag(l)} {l}" for l in valid_langs])

        embed = discord.Embed(
            title=f"⚔️ New Challenge Created: {title}",
            description=(
                f"**Challenge #{challenge_id}** is now live!\n\n"
                f"💰 **Penalty Pot Rule:** Anyone who fails to log at least one study session by **11:59 PM** will have **{currency}{penalty:,.2f}** added to their tab in the pot!\n\n"
                f"👑 **Creator:** {interaction.user.mention} ({creator_langs_str})\n"
                f"Click the button below to join!"
            ),
            color=discord.Color.from_rgb(254, 231, 92)
        )
        embed.set_footer(text=f"Challenge ID: {challenge_id} • /challenge stats challenge_id:{challenge_id}")

        view = ChallengeJoinView(self.db, challenge_id, title)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="join", description="Join an active challenge with your selected language(s)")
    @app_commands.describe(
        challenge_id="The ID of the challenge to join",
        languages="Comma-separated Google Translate language(s) to pledge (e.g. Japanese, German)"
    )
    @app_commands.autocomplete(challenge_id=active_challenges_autocomplete)
    @channel_check()
    async def join(self, interaction: discord.Interaction, challenge_id: int, languages: str):
        ch = await self.db.get_challenge(challenge_id)
        if not ch or not ch.get("is_active"):
            await interaction.response.send_message("❌ Challenge not found or already ended.", ephemeral=True)
            return

        raw_langs = languages.split(",")
        valid_langs = []
        invalid_langs = []

        for l in raw_langs:
            clean = l.strip()
            if not clean:
                continue
            normalized = normalize_language_name(clean)
            if normalized:
                valid_langs.append(normalized)
            else:
                invalid_langs.append(clean)

        if not valid_langs:
            await interaction.response.send_message(
                f"❌ Please provide at least one valid Google Translate language.\n"
                f"Unrecognized: `{', '.join(invalid_langs)}`",
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        await self.db.get_or_create_user(user_id, interaction.user.display_name)

        for l in valid_langs:
            await self.db.add_user_language(user_id, l)

        await self.db.join_challenge(challenge_id, user_id, valid_langs)

        joined_str = ", ".join([f"{get_language_flag(l)} {l}" for l in valid_langs])
        await interaction.response.send_message(
            f"⚔️ {interaction.user.mention} joined **{ch['title']}** (ID: `#{challenge_id}`) tracking **{joined_str}**!\n"
            f"Daily penalty: **{ch['currency_symbol']}{ch['penalty_amount']:,.2f}** if you miss a day."
        )

    @app_commands.command(name="leave", description="Leave an active challenge")
    @app_commands.describe(challenge_id="The ID of the challenge to leave")
    @app_commands.autocomplete(challenge_id=active_challenges_autocomplete)
    @channel_check()
    async def leave(self, interaction: discord.Interaction, challenge_id: int):
        success = await self.db.leave_challenge(challenge_id, interaction.user.id)
        if success:
            await interaction.response.send_message(
                f"🚪 You have left challenge `#{challenge_id}`. You will no longer be audited for daily penalties.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ You are not participating in that challenge.", ephemeral=True)

    @app_commands.command(name="end", description="End a challenge and display the final pot & champions (Creator/Admin)")
    @app_commands.describe(challenge_id="The ID of the challenge to end")
    @app_commands.autocomplete(challenge_id=active_challenges_autocomplete)
    @channel_check()
    async def end_challenge(self, interaction: discord.Interaction, challenge_id: int):
        ch = await self.db.get_challenge(challenge_id)
        if not ch:
            await interaction.response.send_message("❌ Challenge not found.", ephemeral=True)
            return

        if not ch.get("is_active"):
            await interaction.response.send_message("❌ This challenge has already ended.", ephemeral=True)
            return

        # Check permission: Creator or Server Administrator
        is_creator = (interaction.user.id == ch.get("creator_id"))
        is_admin = interaction.user.guild_permissions.administrator if interaction.guild else False

        if not (is_creator or is_admin):
            await interaction.response.send_message(
                "❌ Only the challenge creator or a server administrator can end this challenge.",
                ephemeral=True
            )
            return

        # End challenge
        await self.db.end_challenge(challenge_id)
        summary = await self.db.get_challenge_summary(challenge_id)

        participants = summary.get("participants", [])
        total_pot = summary.get("total_pot", 0.0)
        sym = ch.get("currency_symbol", "$")

        embed = discord.Embed(
            title=f"🏁 Challenge Concluded: {ch['title']}",
            description=(
                f"Challenge `#{challenge_id}` has officially ended!\n\n"
                f"💰 **Final Pot Total:** **{sym}{total_pot:,.2f}**\n"
                f"Daily penalty rate was {sym}{ch['penalty_amount']:,.2f}/day."
            ),
            color=discord.Color.from_rgb(255, 170, 0)
        )

        champions = [p for p in participants if p.get("missed_days", 0) == 0]
        if champions:
            champ_mentions = ", ".join([f"<@{p['user_id']}>" for p in champions])
            embed.add_field(
                name="🏆 Flawless Champions (0 Missed Days)",
                value=champ_mentions,
                inline=False
            )

        if participants:
            lines = []
            for p in sorted(participants, key=lambda x: x.get("total_penalty", 0), reverse=True):
                uname = p.get("username") or f"<@{p['user_id']}>"
                penalty = p.get("total_penalty", 0.0)
                missed = p.get("missed_days", 0)
                lines.append(f"• **{uname}**: {sym}{penalty:,.2f} ({missed} missed days)")
            embed.add_field(name="Final Pot Standings", value="\n".join(lines), inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="List all active challenges in the server")
    @channel_check()
    async def list_challenges(self, interaction: discord.Interaction):
        challenges = await self.db.get_active_challenges(interaction.guild_id)
        if not challenges:
            await interaction.response.send_message(
                "No active challenges right now. Create one using `/challenge create`!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚔️ Active Server Challenges",
            color=discord.Color.from_rgb(254, 231, 92)
        )

        lines = []
        for ch in challenges:
            summary = await self.db.get_challenge_summary(ch["id"])
            pot = summary.get("total_pot", 0.0)
            count = summary.get("participant_count", 0)
            sym = ch.get("currency_symbol", "$")
            lines.append(
                f"**#{ch['id']} - {ch['title']}**\n"
                f"└ Pot: **{sym}{pot:,.2f}** • Penalty: **{sym}{ch['penalty_amount']:,.2f}/day** • {count} participant{'s' if count != 1 else ''}\n"
                f"  *View details: `/challenge stats challenge_id:{ch['id']}`*"
            )

        embed.description = "\n\n".join(lines)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stats", description="View current pot and participant statistics for a challenge")
    @app_commands.describe(challenge_id="The ID of the challenge")
    @app_commands.autocomplete(challenge_id=active_challenges_autocomplete)
    @channel_check()
    async def stats(self, interaction: discord.Interaction, challenge_id: int):
        summary = await self.db.get_challenge_summary(challenge_id)
        if not summary or not summary.get("challenge"):
            await interaction.response.send_message("❌ Challenge not found.", ephemeral=True)
            return

        user = await self.db.get_user(interaction.user.id)
        user_tz = user.get("timezone") if user else "America/New_York"
        _, today_str = get_current_date(user_tz)

        embed = build_challenge_summary_embed(summary, today_str)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    db: Database = bot.db
    await bot.add_cog(ChallengesCog(bot, db))
