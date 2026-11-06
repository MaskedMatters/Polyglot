"""
Comprehensive registry of all Google Translate supported languages with their
respective primary country flag emojis.
"""

from typing import Dict, List, Optional, Tuple

GOOGLE_TRANSLATE_LANGUAGES: Dict[str, str] = {
    "Afrikaans": "🇿🇦",
    "Albanian": "🇦🇱",
    "Amharic": "🇪🇹",
    "Arabic": "🇸🇦",
    "Armenian": "🇦🇲",
    "Assamese": "🇮🇳",
    "Aymara": "🇧🇴",
    "Azerbaijani": "🇦🇿",
    "Bambara": "🇲🇱",
    "Basque": "🇪🇸",
    "Belarusian": "🇧🇾",
    "Bengali": "🇧🇩",
    "Bhojpuri": "🇮🇳",
    "Bosnian": "🇧🇦",
    "Bulgarian": "🇧🇬",
    "Catalan": "🇦🇩",
    "Cebuano": "🇵🇭",
    "Chichewa": "🇲🇼",
    "Chinese (Simplified)": "🇨🇳",
    "Chinese (Traditional)": "🇹🇼",
    "Corsican": "🇫🇷",
    "Croatian": "🇭🇷",
    "Czech": "🇨🇿",
    "Danish": "🇩🇰",
    "Dhivehi": "🇲🇻",
    "Dogri": "🇮🇳",
    "Dutch": "🇳🇱",
    "English": "🇬🇧",
    "Esperanto": "🟢",
    "Estonian": "🇪🇪",
    "Ewe": "🇬🇭",
    "Filipino (Tagalog)": "🇵🇭",
    "Finnish": "🇫🇮",
    "French": "🇫🇷",
    "Frisian": "🇳🇱",
    "Galician": "🇪🇸",
    "Georgian": "🇬🇪",
    "German": "🇩🇪",
    "Greek": "🇬🇷",
    "Guarani": "🇵🇾",
    "Gujarati": "🇮🇳",
    "Haitian Creole": "🇭🇹",
    "Hausa": "🇳🇬",
    "Hawaiian": "🌺",
    "Hebrew": "🇮🇱",
    "Hindi": "🇮🇳",
    "Hmong": "🇱🇦",
    "Hungarian": "🇭🇺",
    "Icelandic": "🇮🇸",
    "Igbo": "🇳🇬",
    "Ilocano": "🇵🇭",
    "Indonesian": "🇮🇩",
    "Irish": "🇮🇪",
    "Italian": "🇮🇹",
    "Japanese": "🇯🇵",
    "Javanese": "🇮🇩",
    "Kannada": "🇮🇳",
    "Kazakh": "🇰🇿",
    "Khmer": "🇰🇭",
    "Kinyarwanda": "🇷🇼",
    "Konkani": "🇮🇳",
    "Korean": "🇰🇷",
    "Krio": "🇸🇱",
    "Kurdish (Kurmanji)": "🇹🇷",
    "Kurdish (Sorani)": "🇮🇶",
    "Kyrgyz": "🇰🇬",
    "Lao": "🇱🇦",
    "Latin": "🏛️",
    "Latvian": "🇱🇻",
    "Lingala": "🇨🇩",
    "Lithuanian": "🇱🇹",
    "Luganda": "🇺🇬",
    "Luxembourgish": "🇱🇺",
    "Macedonian": "🇲🇰",
    "Maithili": "🇮🇳",
    "Malagasy": "🇲🇬",
    "Malay": "🇲🇾",
    "Malayalam": "🇮🇳",
    "Maltese": "🇲🇹",
    "Maori": "🇳🇿",
    "Marathi": "🇮🇳",
    "Meiteilon (Manipuri)": "🇮🇳",
    "Mizo": "🇮🇳",
    "Mongolian": "🇲🇳",
    "Myanmar (Burmese)": "🇲🇲",
    "Nepali": "🇳🇵",
    "Northern Sotho": "🇿🇦",
    "Norwegian": "🇳🇴",
    "Odia (Oriya)": "🇮🇳",
    "Oromo": "🇪🇹",
    "Pashto": "🇦🇫",
    "Persian (Farsi)": "🇮🇷",
    "Polish": "🇵🇱",
    "Portuguese": "🇧🇷",
    "Portuguese (Portugal)": "🇵🇹",
    "Punjabi": "🇮🇳",
    "Quechua": "🇵🇪",
    "Romanian": "🇷🇴",
    "Russian": "🇷🇺",
    "Samoan": "🇼🇸",
    "Sanskrit": "🇮🇳",
    "Scots Gaelic": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Sepedi": "🇿🇦",
    "Serbian": "🇷🇸",
    "Sesotho": "🇱🇸",
    "Shona": "🇿🇼",
    "Sindhi": "🇵🇰",
    "Sinhala": "🇱🇰",
    "Slovak": "🇸🇰",
    "Slovenian": "🇸🇮",
    "Somali": "🇸🇴",
    "Spanish": "🇪🇸",
    "Sundanese": "🇮🇩",
    "Swahili": "🇹🇿",
    "Swedish": "🇸🇪",
    "Tajik": "🇹🇯",
    "Tamil": "🇮🇳",
    "Tatar": "🇷🇺",
    "Telugu": "🇮🇳",
    "Thai": "🇹🇭",
    "Tigrinya": "🇪🇷",
    "Tsonga": "🇿🇦",
    "Turkish": "🇹🇷",
    "Turkmen": "🇹🇲",
    "Twi": "🇬🇭",
    "Ukrainian": "🇺🇦",
    "Urdu": "🇵🇰",
    "Uyghur": "🇨🇳",
    "Uzbek": "🇺🇿",
    "Vietnamese": "🇻🇳",
    "Welsh": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Xhosa": "🇿🇦",
    "Yiddish": "🇮🇱",
    "Yoruba": "🇳🇬",
    "Zulu": "🇿🇦",
}

# Pre-indexed lowercase lookup
_LOWER_TO_CANONICAL: Dict[str, str] = {
    name.lower(): name for name in GOOGLE_TRANSLATE_LANGUAGES
}

# Add common aliases
_LOWER_TO_CANONICAL["chinese"] = "Chinese (Simplified)"
_LOWER_TO_CANONICAL["mandarin"] = "Chinese (Simplified)"
_LOWER_TO_CANONICAL["tagalog"] = "Filipino (Tagalog)"
_LOWER_TO_CANONICAL["persian"] = "Persian (Farsi)"
_LOWER_TO_CANONICAL["farsi"] = "Persian (Farsi)"
_LOWER_TO_CANONICAL["burmese"] = "Myanmar (Burmese)"

POPULAR_LANGUAGES: List[str] = [
    "Japanese",
    "Spanish",
    "French",
    "German",
    "Korean",
    "Chinese (Simplified)",
    "Italian",
    "Russian",
    "Portuguese",
    "Arabic",
    "Hindi",
    "Dutch",
    "Swedish",
    "Polish",
    "Turkish",
    "Vietnamese",
    "Greek",
    "English",
]

def get_language_flag(language: str) -> str:
    """Return flag emoji for a given language, or a default globe icon."""
    canonical = _LOWER_TO_CANONICAL.get(language.strip().lower())
    if canonical:
        return GOOGLE_TRANSLATE_LANGUAGES.get(canonical, "🌐")
    return "🌐"

def normalize_language_name(language: str) -> Optional[str]:
    """Return the official Google Translate canonical name if valid, else None."""
    return _LOWER_TO_CANONICAL.get(language.strip().lower())

def is_valid_google_translate_language(language: str) -> bool:
    """Verify if a language is in the official Google Translate list."""
    return language.strip().lower() in _LOWER_TO_CANONICAL

def search_languages(query: str, limit: int = 25) -> List[Tuple[str, str]]:
    """
    Search languages by substring match.
    Returns a list of (canonical_name, flag_emoji).
    If query is empty, returns popular languages.
    """
    clean_q = query.strip().lower()
    if not clean_q:
        return [(lang, GOOGLE_TRANSLATE_LANGUAGES[lang]) for lang in POPULAR_LANGUAGES[:limit]]

    matches: List[Tuple[str, str]] = []

    # Priority 1: Prefix match
    for name, flag in GOOGLE_TRANSLATE_LANGUAGES.items():
        if name.lower().startswith(clean_q):
            matches.append((name, flag))
            if len(matches) >= limit:
                return matches

    # Priority 2: Substring match
    for name, flag in GOOGLE_TRANSLATE_LANGUAGES.items():
        if clean_q in name.lower() and (name, flag) not in matches:
            matches.append((name, flag))
            if len(matches) >= limit:
                return matches

    return matches

