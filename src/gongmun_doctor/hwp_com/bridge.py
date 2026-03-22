"""
Bridge between HWP COM controller and the 공문닥터 correction engine.

Orchestrates: read text from 한글 → correct_text() → write back via find_and_replace.

Note on regex rules: HWP's AllReplace does not support regex. Only exact_replace
rules are applied back to the document. Regex rules still appear in the returned
CorrectionItem list (for reporting) but are not written to the document.
"""

from __future__ import annotations

from gongmun_doctor.engine import correct_text
from gongmun_doctor.report.markdown import CorrectionItem
from gongmun_doctor.rules.loader import CorrectionRule


class HwpCorrectionBridge:
    """Wires HwpController to correct_text() for COM-mode correction.

    Args:
        controller: A connected HwpController instance (or any object that
                    implements get_text_all(), find_and_replace(), and
                    enable_track_changes() — duck-typed for testability).
        rules: Pre-loaded list of CorrectionRule objects.
    """

    def __init__(self, controller, rules: list[CorrectionRule]) -> None:
        self._controller = controller
        self._rules = rules

    def run_correction(self, mode: str = "track_changes") -> list[CorrectionItem]:
        """Run correction on the currently open 한글 document.

        Args:
            mode: One of:
                - "track_changes" — enable 변경추적 then apply (user reviews)
                - "direct"        — apply directly without tracking
                - "report_only"   — return corrections without modifying document

        Returns:
            List of CorrectionItem describing what was (or would be) corrected.
            Regex-matched rules are included in the list but not written to the
            document (HWP find_and_replace is plain-text only).
        """
        text = self._controller.get_text_all()
        items = correct_text(text, self._rules, paragraph_index=0)

        if mode == "report_only":
            return items

        if not items:
            return []

        if mode == "track_changes":
            self._controller.enable_track_changes()

        # Apply only exact_replace rules — HWP find_and_replace is plain-text only
        fired_ids = {item.rule_id for item in items}
        for rule in self._rules:
            if rule.id not in fired_ids:
                continue
            if rule.rule_type == "exact_replace":
                self._controller.find_and_replace(rule.search, rule.replace)
            # regex_replace: skip (not supported by HWP find_and_replace)

        return items
