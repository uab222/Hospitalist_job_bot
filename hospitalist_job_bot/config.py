"""Loads config.yaml (preferences) and secrets from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config.yaml"
DEFAULT_RESUME_PATH = REPO_ROOT / "resume.yaml"
DEFAULT_DB_PATH = REPO_ROOT / "data" / "jobs.db"
DEFAULT_REVIEW_PATH = REPO_ROOT / "data" / "review.md"


@dataclass
class Secrets:
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    @classmethod
    def from_env(cls) -> "Secrets":
        return cls(
            adzuna_app_id=os.environ.get("ADZUNA_APP_ID", ""),
            adzuna_app_key=os.environ.get("ADZUNA_APP_KEY", ""),
            smtp_host=os.environ.get("SMTP_HOST", ""),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            smtp_user=os.environ.get("SMTP_USER", ""),
            smtp_password=os.environ.get("SMTP_PASSWORD", ""),
        )


@dataclass
class Config:
    titles: list = field(default_factory=list)
    locations: list = field(default_factory=list)
    employment_types: list = field(default_factory=list)
    schedule_preferences: list = field(default_factory=list)
    min_score: int = 40
    exclude_employers: list = field(default_factory=list)
    sources: dict = field(default_factory=dict)
    secrets: Secrets = field(default_factory=Secrets.from_env)

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG_PATH) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        return cls(
            titles=raw.get("titles", []),
            locations=raw.get("locations", []),
            employment_types=raw.get("employment_types", []),
            schedule_preferences=raw.get("schedule_preferences", []),
            min_score=int(raw.get("min_score", 40)),
            exclude_employers=raw.get("exclude_employers", []),
            sources=raw.get("sources", {}),
            secrets=Secrets.from_env(),
        )


def load_resume(path: Path = DEFAULT_RESUME_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
