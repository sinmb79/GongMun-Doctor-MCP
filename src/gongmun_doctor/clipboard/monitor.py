"""ClipboardMonitor — read/write clipboard and run the correction pipeline.

Gate 1~4 (PIIMasker) is applied before correction, matching the same security
policy used for cloud LLM calls.
"""

from __future__ import annotations

import pyperclip

from gongmun_doctor.engine import correct_text
from gongmun_doctor.llm.pii_masker import PIIMasker
from gongmun_doctor.rules.loader import load_rules
from gongmun_doctor.report.markdown import CorrectionItem


class ClipboardMonitor:
    """Clipboard read/write + Security Gate 1~4 + rule-based correction.

    Usage::

        monitor = ClipboardMonitor()
        original, corrected, count = monitor.process_and_replace()
        # corrected text is now in the clipboard; count = number of corrections
    """

    def __init__(self) -> None:
        self._rules = load_rules()   # loads L1/L2/L3 rules from bundled rules/
        self._masker = PIIMasker()

    # ── public API ───────────────────────────────────────────────────────

    def read(self) -> str:
        """Return the current clipboard text."""
        return pyperclip.paste()

    def write(self, text: str) -> None:
        """Overwrite the clipboard with *text*."""
        pyperclip.copy(text)

    def process_and_replace(self) -> tuple[str, str, int]:
        """
        Full pipeline:
          1. Read clipboard
          2. Gate 1~4: PII masking (PIIMasker)
          3. Rule-based correction (L1/L2/L3)
          4. Write corrected text back to clipboard

        Returns:
            (original, corrected, correction_count)
        """
        original = self.read()
        if not original or not original.strip():
            return original, original, 0

        # Security Gate 1~4: mask PII before any processing
        safe_text = self._masker.mask(original)

        # Rule-based correction (L1 + L2 + L3)
        items: list[CorrectionItem] = correct_text(safe_text, self._rules)

        if items:
            corrected = items[-1].corrected_text
        else:
            corrected = safe_text

        self.write(corrected)
        return original, corrected, len(items)
