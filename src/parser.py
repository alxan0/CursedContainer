import logging
import os
import re
from urllib.parse import urlparse

class ParserError(Exception):
    pass

class InvalidModEntryError(ParserError):
    pass

class UnsupportedModUrlError(InvalidModEntryError):
    pass

class ModListParser:
    SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$", re.IGNORECASE)
    ALLOWED_HOSTS = {"curseforge.com", "www.curseforge.com"}

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._lines: list[tuple[int, str]] = []
        self._index = 0
        self._load_file()

    def _load_file(self) -> None:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Missing mod list at {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as fin:
            for line_no, line in enumerate(fin, start=1):
                value = line.strip()
                if value and not value.startswith("#"):
                    self._lines.append((line_no, value))

    def __iter__(self):
        return self
    
    def __next__(self) -> str:
        while self._index < len(self._lines):
            line_no, raw_target = self._lines[self._index]
            self._index += 1

            try:
                return self._clean_entry(raw_target)
            except InvalidModEntryError as exc:
                logging.warning(f"Skipping invalid mod entry at line {line_no}: {exc}")
                continue
        raise StopIteration
    
    def _clean_entry(self, entry: str) -> str:
        candidate = entry.strip()
        if not candidate:
            raise InvalidModEntryError("Empty entry.")

        if "://" in candidate:
            slug = self._extract_slug_from_url(candidate)
        else:
            slug = candidate

        if not self.SLUG_PATTERN.fullmatch(slug):
            raise InvalidModEntryError(
                f"Invalid slug '{slug}'. Allowed: letters, numbers, '_' and '-'."
            )

        return slug.lower()

    def _extract_slug_from_url(self, url: str) -> str:
        parsed = urlparse(url)

        if parsed.scheme.lower() not in {"http", "https"}:
            raise UnsupportedModUrlError(f"Unsupported URL scheme: {parsed.scheme}")

        host = (parsed.hostname or "").lower()
        if host not in self.ALLOWED_HOSTS:
            raise UnsupportedModUrlError(f"Unsupported host: {host}")

        # Expected path: /hytale/mods/<slug>
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 3 or parts[0].lower() != "hytale" or parts[1].lower() != "mods":
            raise UnsupportedModUrlError(
                "Expected URL path format '/hytale/mods/<slug>'."
            )

        slug = parts[2].strip()
        if not slug:
            raise InvalidModEntryError("Missing slug segment in URL.")

        return slug


