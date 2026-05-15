"""Metadane scenariusza z pliku importu."""

from __future__ import annotations

import re
from dataclasses import dataclass


def slug_scenario_id(raw: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", raw.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return (s[:48] or "IMPORTED").upper()


@dataclass
class ImportMeta:
    scenario_id: str | None = None
    title: str | None = None
    description: str | None = None

    def scenario_id_or(self, fallback: str) -> str:
        sid = (self.scenario_id or "").strip()
        return slug_scenario_id(sid) if sid else fallback

    def title_or(self, fallback: str) -> str:
        t = (self.title or "").strip()
        return t if t else fallback

    def description_or(self, fallback: str) -> str:
        d = (self.description or "").strip()
        return d if d else fallback
