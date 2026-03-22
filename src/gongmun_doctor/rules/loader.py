"""Rule file loader — reads JSON rule files from the rules directory."""

import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CorrectionRule:
    id: str
    rule_type: str   # "exact_replace" or "regex_replace"
    search: str      # plain text or regex pattern
    replace: str     # replacement (may include backreferences for regex)
    desc: str        # human-readable description in Korean
    source: str      # citation
    layer: str = ""  # populated from file meta (e.g. "L1_spelling")


def load_rules(rules_dir: Path | str | None = None) -> list[CorrectionRule]:
    """Load all JSON rule files from the rules directory.

    If rules_dir is None, defaults to the bundled rules/ directory
    next to this file.
    """
    if rules_dir is None:
        rules_dir = Path(__file__).parent
    else:
        rules_dir = Path(rules_dir)

    rules: list[CorrectionRule] = []

    for json_file in sorted(rules_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        layer = data.get("meta", {}).get("layer", "unknown")

        for r in data.get("rules", []):
            search_key = r.get("search") or r.get("pattern") or ""
            rules.append(
                CorrectionRule(
                    id=r["id"],
                    rule_type=r.get("type", "exact_replace"),
                    search=search_key,
                    replace=r["replace"],
                    desc=r["desc"],
                    source=r["source"],
                    layer=layer,
                )
            )

    return rules


def load_rules_by_layer(
    rules_dir: Path | str | None = None,
    layers: list[str] | None = None,
) -> list[CorrectionRule]:
    """Load rules, optionally filtered to specific layers.

    layers: e.g. ["L1_spelling", "L3_official_style"]
    """
    all_rules = load_rules(rules_dir)
    if layers is None:
        return all_rules
    return [r for r in all_rules if r.layer in layers]
