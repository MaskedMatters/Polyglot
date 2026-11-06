import json
import os
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure parent directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self):
        """Initialize database tables and indexes."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    timezone TEXT DEFAULT 'America/New_York',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_languages (
                    user_id INTEGER,
                    language TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    last_logged_date TEXT,
                    total_minutes INTEGER DEFAULT 0,
                    total_logs INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, language)
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS study_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    language TEXT,
                    duration_minutes INTEGER,
                    description TEXT,
                    proof_url TEXT,
                    log_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    creator_id INTEGER,
                    title TEXT,
                    penalty_amount REAL,
                    currency_symbol TEXT DEFAULT '$',
                    start_date TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS challenge_participants (
                    challenge_id INTEGER,
                    user_id INTEGER,
                    languages TEXT,
                    total_penalty REAL DEFAULT 0.0,
                    missed_days INTEGER DEFAULT 0,
                    last_logged_date TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (challenge_id, user_id)
                );
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS challenge_daily_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    challenge_id INTEGER,
                    audit_date TEXT,
                    penalized_user_ids TEXT,
                    audited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(challenge_id, audit_date)
                );
            """)

            await db.commit()

    # User operations
    async def get_or_create_user(self, user_id: int, username: str, default_tz: str = "America/New_York") -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()
            if user:
                return dict(user)

            await db.execute(
                "INSERT INTO users (user_id, username, timezone) VALUES (?, ?, ?)",
                (user_id, username, default_tz)
            )
            await db.commit()
            return {"user_id": user_id, "username": username, "timezone": default_tz}

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()
            return dict(user) if user else None

    async def set_user_timezone(self, user_id: int, timezone: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET timezone = ? WHERE user_id = ?",
                (timezone, user_id)
            )
            await db.commit()

    # Language operations
    async def add_user_language(self, user_id: int, language: str) -> bool:
        """Enroll user in a language. Returns True if newly added, False if already enrolled."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT language FROM user_languages WHERE user_id = ? AND LOWER(language) = LOWER(?)",
                (user_id, language)
            )
            if await cursor.fetchone():
                return False

            await db.execute(
                "INSERT INTO user_languages (user_id, language) VALUES (?, ?)",
                (user_id, language.strip().title())
            )
            await db.commit()
            return True

    async def remove_user_language(self, user_id: int, language: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM user_languages WHERE user_id = ? AND LOWER(language) = LOWER(?)",
                (user_id, language)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_user_languages(self, user_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_languages WHERE user_id = ? ORDER BY started_at ASC",
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_user_language(self, user_id: int, language: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_languages WHERE user_id = ? AND LOWER(language) = LOWER(?)",
                (user_id, language)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    # Study log operations
    async def log_study_session(
        self,
        user_id: int,
        language: str,
        duration_minutes: int,
        description: Optional[str],
        proof_url: Optional[str],
        log_date: str,
        new_streak: int,
        longest_streak: int
    ) -> Dict[str, Any]:
        """Logs a session and updates the user's language streak & totals."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Insert study log
            cursor = await db.execute(
                """
                INSERT INTO study_logs (user_id, language, duration_minutes, description, proof_url, log_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, language, duration_minutes, description, proof_url, log_date)
            )
            log_id = cursor.lastrowid

            # Update language stats
            await db.execute(
                """
                UPDATE user_languages
                SET current_streak = ?,
                    longest_streak = ?,
                    last_logged_date = ?,
                    total_minutes = total_minutes + ?,
                    total_logs = total_logs + 1
                WHERE user_id = ? AND LOWER(language) = LOWER(?)
                """,
                (new_streak, longest_streak, log_date, duration_minutes, user_id, language)
            )

            # Update challenge last_logged_date if participating in active challenges with this language
            cursor = await db.execute(
                """
                SELECT c.id, cp.languages
                FROM challenge_participants cp
                JOIN challenges c ON c.id = cp.challenge_id
                WHERE cp.user_id = ? AND c.is_active = 1
                """,
                (user_id,)
            )
            active_challenges = await cursor.fetchall()
            for row in active_challenges:
                ch_id = row["id"]
                ch_langs = json.loads(row["languages"])
                if any(l.lower() == language.lower() for l in ch_langs):
                    await db.execute(
                        "UPDATE challenge_participants SET last_logged_date = ? WHERE challenge_id = ? AND user_id = ?",
                        (log_date, ch_id, user_id)
                    )

            await db.commit()
            return {"log_id": log_id, "new_streak": new_streak, "longest_streak": longest_streak}

    async def get_user_stats(self, user_id: int, language: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregate statistics for a user, optionally filtered by language."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if language:
                cursor = await db.execute(
                    """
                    SELECT COUNT(*) as total_logs,
                           COALESCE(SUM(duration_minutes), 0) as total_minutes,
                           COUNT(DISTINCT log_date) as active_days
                    FROM study_logs
                    WHERE user_id = ? AND LOWER(language) = LOWER(?)
                    """,
                    (user_id, language)
                )
                stats = dict(await cursor.fetchone())
                lang_cursor = await db.execute(
                    "SELECT * FROM user_languages WHERE user_id = ? AND LOWER(language) = LOWER(?)",
                    (user_id, language)
                )
                lang_data = await lang_cursor.fetchone()
                stats["language_info"] = dict(lang_data) if lang_data else None
                return stats
            else:
                cursor = await db.execute(
                    """
                    SELECT COUNT(*) as total_logs,
                           COALESCE(SUM(duration_minutes), 0) as total_minutes,
                           COUNT(DISTINCT log_date) as active_days
                    FROM study_logs
                    WHERE user_id = ?
                    """,
                    (user_id,)
                )
                stats = dict(await cursor.fetchone())
                langs_cursor = await db.execute(
                    "SELECT * FROM user_languages WHERE user_id = ? ORDER BY total_minutes DESC",
                    (user_id,)
                )
                stats["languages"] = [dict(r) for r in await langs_cursor.fetchall()]
                return stats

    async def get_recent_logs(self, user_id: int, language: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if language:
                cursor = await db.execute(
                    """
                    SELECT * FROM study_logs
                    WHERE user_id = ? AND LOWER(language) = LOWER(?)
                    ORDER BY id DESC LIMIT ?
                    """,
                    (user_id, language, limit)
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM study_logs
                    WHERE user_id = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (user_id, limit)
                )
            return [dict(r) for r in await cursor.fetchall()]

    # Challenge operations
    async def create_challenge(
        self,
        guild_id: int,
        channel_id: int,
        creator_id: int,
        title: str,
        penalty_amount: float,
        currency_symbol: str,
        start_date: str
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO challenges (guild_id, channel_id, creator_id, title, penalty_amount, currency_symbol, start_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (guild_id, channel_id, creator_id, title, penalty_amount, currency_symbol, start_date)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_challenge(self, challenge_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_active_challenges(self, guild_id: Optional[int] = None) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if guild_id:
                cursor = await db.execute(
                    "SELECT * FROM challenges WHERE is_active = 1 AND guild_id = ? ORDER BY id DESC",
                    (guild_id,)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM challenges WHERE is_active = 1 ORDER BY id DESC"
                )
            return [dict(r) for r in await cursor.fetchall()]

    async def join_challenge(self, challenge_id: int, user_id: int, languages: List[str]) -> bool:
        """Join or update languages for a challenge."""
        langs_json = json.dumps([l.strip().title() for l in languages])
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO challenge_participants (challenge_id, user_id, languages)
                VALUES (?, ?, ?)
                ON CONFLICT(challenge_id, user_id) DO UPDATE SET
                    languages = excluded.languages
                """,
                (challenge_id, user_id, langs_json)
            )
            await db.commit()
            return True

    async def leave_challenge(self, challenge_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM challenge_participants WHERE challenge_id = ? AND user_id = ?",
                (challenge_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_challenge_participants(self, challenge_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT cp.*, u.username
                FROM challenge_participants cp
                LEFT JOIN users u ON u.user_id = cp.user_id
                WHERE cp.challenge_id = ?
                ORDER BY cp.total_penalty DESC, cp.missed_days DESC
                """,
                (challenge_id,)
            )
            rows = await cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["languages"] = json.loads(d["languages"]) if d.get("languages") else []
                result.append(d)
            return result

    async def has_logged_challenge_for_date(self, user_id: int, languages: List[str], target_date: str) -> bool:
        """Checks if a user logged at least one of their challenge languages on target_date."""
        if not languages:
            return False
        async with aiosqlite.connect(self.db_path) as db:
            placeholders = ",".join(["?"] * len(languages))
            sql = f"""
                SELECT 1 FROM study_logs
                WHERE user_id = ? AND log_date = ? AND LOWER(language) IN ({placeholders})
                LIMIT 1
            """
            params = [user_id, target_date] + [l.lower() for l in languages]
            cursor = await db.execute(sql, params)
            return await cursor.fetchone() is not None

    async def has_daily_audit_run(self, challenge_id: int, audit_date: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM challenge_daily_audits WHERE challenge_id = ? AND audit_date = ?",
                (challenge_id, audit_date)
            )
            return await cursor.fetchone() is not None

    async def record_daily_audit(self, challenge_id: int, audit_date: str, penalized_user_ids: List[int], penalty_amount: float):
        """Record audit and apply penalty to participants who missed the day."""
        async with aiosqlite.connect(self.db_path) as db:
            # Update penalized participants
            for uid in penalized_user_ids:
                await db.execute(
                    """
                    UPDATE challenge_participants
                    SET total_penalty = total_penalty + ?,
                        missed_days = missed_days + 1
                    WHERE challenge_id = ? AND user_id = ?
                    """,
                    (penalty_amount, challenge_id, uid)
                )

            # Insert audit record
            await db.execute(
                """
                INSERT INTO challenge_daily_audits (challenge_id, audit_date, penalized_user_ids)
                VALUES (?, ?, ?)
                """,
                (challenge_id, audit_date, json.dumps(penalized_user_ids))
            )
            await db.commit()

    async def end_challenge(self, challenge_id: int) -> bool:
        """Mark a challenge as ended / inactive."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE challenges SET is_active = 0 WHERE id = ?",
                (challenge_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_challenge_summary(self, challenge_id: int) -> Dict[str, Any]:
        """Get challenge details along with total pot and participants stats."""
        ch = await self.get_challenge(challenge_id)
        if not ch:
            return {}
        participants = await self.get_challenge_participants(challenge_id)
        total_pot = sum(p.get("total_penalty", 0.0) for p in participants)
        return {
            "challenge": ch,
            "participants": participants,
            "total_pot": total_pot,
            "participant_count": len(participants)
        }

