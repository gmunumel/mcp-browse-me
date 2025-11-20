"""Project settings and environment loading helpers."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_PATH = DEFAULT_PROJECT_ROOT / ".env"


class Settings:
    """Settings container with basic .env loading."""

    def __init__(
        self, project_root: Path | None = None, env_path: Path | None = None
    ) -> None:
        self.project_root = project_root or DEFAULT_PROJECT_ROOT
        self.env_path = env_path or DEFAULT_ENV_PATH

    def load_env(self) -> None:
        """Populate os.environ with values from the project .env file if present."""
        if not self.env_path.exists():
            return

        for line in self.env_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


settings = Settings()
