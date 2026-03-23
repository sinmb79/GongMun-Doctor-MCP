"""Template engine — loads, matches, and renders government document form templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "templates"


class TemplateEngine:
    """JSON 기반 공문 서식 로딩·트리거 매칭·변수 치환 엔진.

    Templates are stored as JSON files under *template_dir*.  Each file must
    contain at least ``id``, ``name``, ``triggers``, ``variables``, and
    ``body`` keys (see project docs for full schema).
    """

    def __init__(self, template_dir: Path | str | None = None) -> None:
        self._dir = Path(template_dir) if template_dir is not None else _DEFAULT_TEMPLATE_DIR
        self.templates: dict[str, dict[str, Any]] = {}
        self._load()

    # ── loading ──────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Load all *.json files from the template directory."""
        for path in sorted(self._dir.glob("*.json")):
            try:
                with path.open(encoding="utf-8") as f:
                    tmpl = json.load(f)
                tmpl_id = tmpl.get("id")
                if tmpl_id:
                    self.templates[tmpl_id] = tmpl
            except (json.JSONDecodeError, KeyError, OSError):
                pass  # skip malformed files

    def reload(self) -> None:
        """Reload all templates from disk (e.g. after user edits a JSON file)."""
        self.templates.clear()
        self._load()

    # ── querying ─────────────────────────────────────────────────────────

    def match(self, query: str) -> list[dict[str, Any]]:
        """Return templates whose trigger keywords appear in *query*.

        Results are ordered by number of matching triggers (descending).
        """
        scored: list[tuple[int, dict[str, Any]]] = []
        for tmpl in self.templates.values():
            hits = sum(1 for t in tmpl.get("triggers", []) if t in query)
            if hits:
                scored.append((hits, tmpl))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [tmpl for _, tmpl in scored]

    def get_variables(self, template_id: str) -> list[dict[str, str]]:
        """Return the variable definitions for a template.

        Each item has at least ``key`` and ``label`` keys and an optional
        ``example`` key.
        """
        tmpl = self.templates[template_id]
        return list(tmpl.get("variables", []))

    # ── rendering ────────────────────────────────────────────────────────

    def render(self, template_id: str, values: dict[str, str]) -> str:
        """Substitute *values* into the template body and return the result.

        Unreplaced ``{{variable}}`` placeholders are left as-is so callers
        can detect which variables were not supplied.
        """
        tmpl = self.templates[template_id]
        body: str = tmpl.get("body", "")
        for key, val in values.items():
            body = body.replace("{{" + key + "}}", val)
        return body

    def list_templates(self, category: str | None = None) -> list[dict[str, Any]]:
        """Return all (or category-filtered) templates as a list."""
        if category is None:
            return list(self.templates.values())
        return [t for t in self.templates.values() if t.get("category") == category]
