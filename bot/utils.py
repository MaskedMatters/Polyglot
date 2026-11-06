import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Tuple, Optional, Dict, Any, List
import discord
from bot.config import ALLOWED_CHANNEL_NAME, ALLOWED_CHANNEL_ID, DEFAULT_TIMEZONE
from bot.languages import get_language_flag

def get_language_emoji(language: str) -> str:
    """Return flag emoji from the official Google Translate registry."""
    return get_language_flag(language)

POPULAR_TIMEZONES = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Toronto",
    "America/Vancouver",
    "America/Sao_Paulo",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Europe/Madrid",
    "Europe/Rome",
    "Europe/Warsaw",
    "Asia/Tokyo",
    "Asia/Seoul",
    "Asia/Shanghai",
    "Asia/Hong_Kong",
    "Asia/Singapore",
    "Asia/Kolkata",
    "Asia/Dubai",
    "Australia/Sydney",
    "Australia/Melbourne",
    "Pacific/Auckland",
]

def validate_timezone(tz_name: str) -> bool:
    try:
        ZoneInfo(tz_name)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False

def get_current_date(tz_name: Optional[str] = None) -> Tuple[datetime.date, str]:
    """Get today's date in the user's timezone as (date_obj, 'YYYY-MM-DD')."""
    tz_str = tz_name if (tz_name and validate_timezone(tz_name)) else DEFAULT_TIMEZONE
    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.datetime.now(tz)
    return now.date(), now.strftime("%Y-%m-%d")

def calculate_streak(today_date: datetime.date, last_logged_date_str: Optional[str], current_streak: int, longest_streak: int) -> Tuple[int, int, bool]:
    """
    Computes updated streak based on the current date and the last logged date.
    Returns: (new_streak, new_longest_streak, already_logged_today)
    """
    if not last_logged_date_str:
        new_streak = 1
        return new_streak, max(longest_streak, new_streak), False

    try:
        last_date = datetime.date.fromisoformat(last_logged_date_str)
    except ValueError:
        return 1, max(longest_streak, 1), False

    delta_days = (today_date - last_date).days

    if delta_days == 0:
        # Already logged today! Keep the current streak
        return current_streak, longest_streak, True
    elif delta_days == 1:
        # Consecutive day! Increment streak
        new_streak = current_streak + 1
        return new_streak, max(longest_streak, new_streak), False
    elif delta_days > 1:
        # Missed at least one day, streak resets to 1
        new_streak = 1
        return new_streak, max(longest_streak, new_streak), False
    else:
        # Future date log or clock discrepancy; keep streak as is
        return current_streak, longest_streak, False

def format_duration(minutes: int) -> str:
    """Format minutes into concise, clean string: e.g. 1h 30m or 45m."""
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    rem = minutes % 60
    if rem == 0:
        return f"{hours}h"
    return f"{hours}h {rem}m"

def is_channel_allowed(interaction: discord.Interaction) -> bool:
    """Verify if the interaction is executed inside the permitted channel."""
    if not interaction.guild:
        return True # DMs or non-guild allowed if desired, or handle appropriately
    if ALLOWED_CHANNEL_ID:
        return interaction.channel_id == ALLOWED_CHANNEL_ID
    if interaction.channel and hasattr(interaction.channel, "name"):
        return interaction.channel.name.lower() == ALLOWED_CHANNEL_NAME
    return False

# Minimalist Embed Builders
def build_log_success_embed(
    language: str,
    duration_minutes: int,
    total_minutes: int,
    streak: int,
    longest_streak: int,
    total_days: int,
    description: Optional[str] = None,
    proof_url: Optional[str] = None
) -> discord.Embed:
    emoji = get_language_emoji(language)
    embed = discord.Embed(
        title=f"{emoji} {language} Logged",
        color=discord.Color.from_rgb(88, 101, 242) # Discord Blurple / Sleek Indigo
    )

    streak_badge = f"🔥 **{streak} day{'s' if streak != 1 else ''}**"
    time_badge = f"⏱️ **+{format_duration(duration_minutes)}**"
    total_badge = f"📚 Total: **{format_duration(total_minutes)}**"
    days_badge = f"📅 Day **{total_days}**"

    embed.description = f"{time_badge} ({total_badge}) • {streak_badge} • {days_badge}"

    if description:
        embed.add_field(name="Notes", value=f"> *{description}*", inline=False)

    if proof_url:
        embed.set_image(url=proof_url)

    embed.set_footer(text=f"Best Streak: {longest_streak} days • Keep up the momentum!")
    return embed

def build_stats_embed(user: discord.User, stats: Dict[str, Any], language: Optional[str] = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"📊 Study Stats: {user.display_name}",
        color=discord.Color.from_rgb(87, 242, 135) # Minimalist Emerald
    )
    if user.avatar:
        embed.set_author(name=user.display_name, icon_url=user.avatar.url)

    total_logs = stats.get("total_logs", 0)
    total_min = stats.get("total_minutes", 0)
    active_days = stats.get("active_days", 0)

    avg_minutes = (total_min // active_days) if active_days > 0 else 0

    if language:
        emoji = get_language_emoji(language)
        lang_info = stats.get("language_info") or {}
        streak = lang_info.get("current_streak", 0)
        longest = lang_info.get("longest_streak", 0)
        embed.title = f"{emoji} {language} Stats: {user.display_name}"
        embed.description = (
            f"🔥 **Current Streak:** {streak} days\n"
            f"🏆 **Best Streak:** {longest} days\n"
            f"⏱️ **Total Time:** {format_duration(total_min)}\n"
            f"📅 **Active Days:** {active_days} days\n"
            f"📈 **Daily Average:** {format_duration(avg_minutes)}\n"
            f"📝 **Total Logs:** {total_logs}"
        )
    else:
        embed.description = (
            f"⏱️ **Total Time:** {format_duration(total_min)} across all languages\n"
            f"📅 **Active Study Days:** {active_days}\n"
            f"📈 **Average Session / Day:** {format_duration(avg_minutes)}\n"
            f"📝 **Total Logs Recorded:** {total_logs}"
        )
        langs = stats.get("languages", [])
        if langs:
            lang_lines = []
            for l in langs:
                emoji = get_language_emoji(l["language"])
                lang_lines.append(
                    f"{emoji} **{l['language']}**: {format_duration(l['total_minutes'])} • 🔥 {l['current_streak']}d streak (best: {l['longest_streak']}d)"
                )
            embed.add_field(name="Languages Tracked", value="\n".join(lang_lines), inline=False)
        else:
            embed.add_field(name="Languages", value="No languages tracked yet. Use `/learn <language>` to start!", inline=False)

    return embed

def build_challenge_summary_embed(summary: Dict[str, Any], date_str: str) -> discord.Embed:
    ch = summary["challenge"]
    participants = summary["participants"]
    total_pot = summary["total_pot"]
    sym = ch.get("currency_symbol", "$")

    embed = discord.Embed(
        title=f"⚔️ Challenge: {ch['title']}",
        description=f"💰 **Total Pot: {sym}{total_pot:,.2f}**\n⚠️ **Daily Penalty:** {sym}{ch['penalty_amount']:,.2f} per missed day",
        color=discord.Color.from_rgb(254, 231, 92) # Radiant Gold
    )

    if not participants:
        embed.add_field(name="Participants", value="No participants have joined yet. Use `/challenge join`!", inline=False)
        return embed

    lines = []
    for p in participants:
        uname = p.get("username") or f"<@{p['user_id']}>"
        langs = ", ".join(p.get("languages", []))
        penalty = p.get("total_penalty", 0.0)
        missed = p.get("missed_days", 0)
        logged_today = (p.get("last_logged_date") == date_str)
        status_icon = "✅" if logged_today else "⏳"

        lines.append(
            f"{status_icon} **{uname}** ({langs})\n"
            f"└ Pot Contribution: **{sym}{penalty:,.2f}** ({missed} missed days)"
        )

    embed.add_field(name=f"Participants ({len(participants)})", value="\n".join(lines), inline=False)
    embed.set_footer(text="Log progress daily before 11:59 PM to protect your streak and avoid the pot!")
    return embed

