"""Texts of the web page, one JSON file per language in data/messages/.

A new language is a new file. No text for people lives in Python code.
English is the reference: a text that is missing in another language falls back to English,
and the tests fail until every language has every key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MESSAGES_DIR = Path(__file__).resolve().parents[2] / "data" / "messages"
DEFAULT_LANGUAGE = "en"


@dataclass(frozen=True)
class Messages:
    language: str
    language_name: str
    text: dict[str, str]
    violations: dict[str, str]

    def t(self, key: str, **values: object) -> str:
        """The text for a key, with {placeholders} filled in."""
        return self.text[key].format(**values)

    def violation(self, code: str, fallback: str) -> str:
        """The text for a rule violation; the technical message when none is translated."""
        return self.violations.get(code, fallback)


def available_languages(directory: Path = MESSAGES_DIR) -> list[str]:
    """Language codes with a file, the default language first."""
    codes = sorted(path.stem for path in directory.glob("*.json"))
    return sorted(codes, key=lambda code: code != DEFAULT_LANGUAGE)


def _read(language: str, directory: Path) -> dict[str, Any]:
    with (directory / f"{language}.json").open(encoding="utf-8") as handle:
        raw: dict[str, Any] = json.load(handle)
    return raw


def load_messages(language: str | None = None, directory: Path = MESSAGES_DIR) -> Messages:
    """Loads one language on top of English. Unknown or missing codes give English."""
    reference = _read(DEFAULT_LANGUAGE, directory)
    if language is None or language not in available_languages(directory):
        language = DEFAULT_LANGUAGE
    chosen = _read(language, directory)
    return Messages(
        language=language,
        language_name=str(chosen.get("language_name", language)),
        text={**reference["text"], **chosen.get("text", {})},
        violations={**reference["violations"], **chosen.get("violations", {})},
    )
