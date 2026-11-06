import asyncio
import os
import shutil
import tempfile
import unittest
import datetime

from bot.database import Database
from bot.languages import (
    search_languages,
    normalize_language_name,
    get_language_flag,
    GOOGLE_TRANSLATE_LANGUAGES
)
from bot.utils import calculate_streak, format_duration, get_language_emoji

class TestBotCore(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.db = Database(self.db_path)
        await self.db.init_db()

    async def asyncTearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_google_translate_languages_registry(self):
        # Check size and coverage
        self.assertGreater(len(GOOGLE_TRANSLATE_LANGUAGES), 100)

        # Flag tests
        self.assertEqual(get_language_flag("Japanese"), "🇯🇵")
        self.assertEqual(get_language_flag("spanish"), "🇪🇸")
        self.assertEqual(get_language_flag("French"), "🇫🇷")
        self.assertEqual(get_language_flag("German"), "🇩🇪")
        self.assertEqual(get_language_flag("Korean"), "🇰🇷")

        # Normalization
        self.assertEqual(normalize_language_name("japanese"), "Japanese")
        self.assertEqual(normalize_language_name("chinese"), "Chinese (Simplified)")
        self.assertEqual(normalize_language_name("farsi"), "Persian (Farsi)")
        self.assertIsNone(normalize_language_name("klingon"))

        # Autocomplete search
        search_res = search_languages("jap")
        self.assertTrue(any(lang == "Japanese" for lang, flag in search_res))

        search_empty = search_languages("")
        self.assertGreater(len(search_empty), 0)

    def test_format_duration(self):
        self.assertEqual(format_duration(15), "15m")
        self.assertEqual(format_duration(60), "1h")
        self.assertEqual(format_duration(90), "1h 30m")
        self.assertEqual(format_duration(125), "2h 5m")

    def test_streak_calculation(self):
        d0 = datetime.date(2026, 11, 1)
        d1 = datetime.date(2026, 11, 2)
        d2 = datetime.date(2026, 11, 3)
        d5 = datetime.date(2026, 11, 6)

        # First log ever
        streak, longest, already = calculate_streak(d0, None, 0, 0)
        self.assertEqual(streak, 1)
        self.assertEqual(longest, 1)
        self.assertFalse(already)

        # Logging again on same day
        streak, longest, already = calculate_streak(d0, "2026-11-01", 1, 1)
        self.assertEqual(streak, 1)
        self.assertEqual(longest, 1)
        self.assertTrue(already)

        # Consecutive day log
        streak, longest, already = calculate_streak(d1, "2026-11-01", 1, 1)
        self.assertEqual(streak, 2)
        self.assertEqual(longest, 2)
        self.assertFalse(already)

        # Day 3 consecutive
        streak, longest, already = calculate_streak(d2, "2026-11-02", 2, 2)
        self.assertEqual(streak, 3)
        self.assertEqual(longest, 3)
        self.assertFalse(already)

        # Gap of several days (streak reset)
        streak, longest, already = calculate_streak(d5, "2026-11-03", 3, 3)
        self.assertEqual(streak, 1)
        self.assertEqual(longest, 3) # Longest is preserved!
        self.assertFalse(already)

    async def test_user_and_language_operations(self):
        user_id = 12345
        user = await self.db.get_or_create_user(user_id, "Alice")
        self.assertEqual(user["username"], "Alice")

        # Add language
        added = await self.db.add_user_language(user_id, "Japanese")
        self.assertTrue(added)

        # Duplicate language add should return False
        added_again = await self.db.add_user_language(user_id, "japanese")
        self.assertFalse(added_again)

        # Add second language
        await self.db.add_user_language(user_id, "Spanish")

        langs = await self.db.get_user_languages(user_id)
        self.assertEqual(len(langs), 2)
        lang_names = [l["language"] for l in langs]
        self.assertIn("Japanese", lang_names)
        self.assertIn("Spanish", lang_names)

        # Give up / remove language
        removed = await self.db.remove_user_language(user_id, "Spanish")
        self.assertTrue(removed)
        langs_after = await self.db.get_user_languages(user_id)
        self.assertEqual(len(langs_after), 1)
        self.assertEqual(langs_after[0]["language"], "Japanese")

    async def test_study_logging_and_stats(self):
        user_id = 999
        await self.db.get_or_create_user(user_id, "Bob")
        await self.db.add_user_language(user_id, "Japanese")

        # Log study session
        res = await self.db.log_study_session(
            user_id=user_id,
            language="Japanese",
            duration_minutes=45,
            description="Kanji practice",
            proof_url=None,
            log_date="2026-11-04",
            new_streak=1,
            longest_streak=1
        )
        self.assertIsNotNone(res["log_id"])

        # Check stats
        stats = await self.db.get_user_stats(user_id, "Japanese")
        self.assertEqual(stats["total_logs"], 1)
        self.assertEqual(stats["total_minutes"], 45)
        self.assertEqual(stats["active_days"], 1)
        self.assertEqual(stats["language_info"]["current_streak"], 1)

    async def test_challenge_workflow_penalty_pot_and_ending(self):
        creator_id = 101
        participant_id = 102

        await self.db.get_or_create_user(creator_id, "Alice")
        await self.db.get_or_create_user(participant_id, "Bob")

        # Create challenge
        ch_id = await self.db.create_challenge(
            guild_id=1,
            channel_id=1,
            creator_id=creator_id,
            title="Japanese Mastery Sprint",
            penalty_amount=5.0,
            currency_symbol="$",
            start_date="2026-11-01"
        )
        self.assertEqual(ch_id, 1)

        # Join challenge with pledged languages
        await self.db.join_challenge(ch_id, creator_id, ["Japanese"])
        await self.db.join_challenge(ch_id, participant_id, ["Japanese", "Spanish"])

        # Creator logs on 2026-11-01
        await self.db.log_study_session(
            user_id=creator_id,
            language="Japanese",
            duration_minutes=30,
            description="Logged",
            proof_url=None,
            log_date="2026-11-01",
            new_streak=1,
            longest_streak=1
        )

        # Check who logged on 2026-11-01
        alice_logged = await self.db.has_logged_challenge_for_date(creator_id, ["Japanese"], "2026-11-01")
        bob_logged = await self.db.has_logged_challenge_for_date(participant_id, ["Japanese", "Spanish"], "2026-11-01")

        self.assertTrue(alice_logged)
        self.assertFalse(bob_logged)

        # Audit day 2026-11-01: Bob missed, Alice didn't!
        penalized = [participant_id]
        await self.db.record_daily_audit(
            challenge_id=ch_id,
            audit_date="2026-11-01",
            penalized_user_ids=penalized,
            penalty_amount=5.0
        )

        # Summary check
        summary = await self.db.get_challenge_summary(ch_id)
        self.assertEqual(summary["total_pot"], 5.0)

        # End challenge
        ended = await self.db.end_challenge(ch_id)
        self.assertTrue(ended)

        ch = await self.db.get_challenge(ch_id)
        self.assertEqual(ch["is_active"], 0)

        active = await self.db.get_active_challenges()
        self.assertEqual(len(active), 0)

if __name__ == "__main__":
    unittest.main()
