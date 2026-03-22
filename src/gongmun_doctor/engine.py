"""Correction engine — applies rules to HWPX document paragraphs."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from hwpx.document import HwpxDocument

from gongmun_doctor.rules.loader import CorrectionRule
from gongmun_doctor.report.markdown import CorrectionItem, CorrectionReport

if TYPE_CHECKING:
    from gongmun_doctor.llm.harmony import HarmonyChecker


def _apply_rule_to_text(text: str, rule: CorrectionRule) -> tuple[str, int]:
    """Apply a single rule to a text string.

    Returns:
        (new_text, match_count)
    """
    if rule.rule_type == "exact_replace":
        count = text.count(rule.search)
        if count > 0:
            return text.replace(rule.search, rule.replace), count
        return text, 0

    if rule.rule_type == "regex_replace":
        new_text, count = re.subn(rule.search, rule.replace, text)
        return new_text, count

    return text, 0


def correct_text(
    text: str,
    rules: list[CorrectionRule],
    paragraph_index: int = 0,
) -> list[CorrectionItem]:
    """Apply rules to a plain text string and return correction items.

    Used by HwpCorrectionBridge (COM mode) to analyse text extracted from
    a running 한글 instance. Returns an empty list for blank text.

    Args:
        text: The text to correct.
        rules: List of CorrectionRule objects to apply.
        paragraph_index: Paragraph index to store in each returned CorrectionItem.

    Returns:
        List of CorrectionItem, one per rule that produced a match.
    """
    if not text or not text.strip():
        return []

    items: list[CorrectionItem] = []
    current = text
    for rule in rules:
        new_text, count = _apply_rule_to_text(current, rule)
        if count > 0:
            items.append(
                CorrectionItem(
                    paragraph_index=paragraph_index,
                    original_text=current,
                    corrected_text=new_text,
                    rule_id=rule.id,
                    rule_desc=rule.desc,
                    rule_source=rule.source,
                    layer=rule.layer,
                )
            )
            current = new_text
    return items


def correct_document(
    doc: HwpxDocument,
    rules: list[CorrectionRule],
    dry_run: bool = False,
    harmony_checker: HarmonyChecker | None = None,
) -> CorrectionReport:
    """Apply all rules to all paragraphs in the document.

    When dry_run=True the document object is not modified; the report
    still reflects what *would* be corrected.

    harmony_checker is optional — if provided, an L4 AI pass is run after
    the rule-based passes and suggestions are added to the report.

    Returns:
        CorrectionReport with all corrections found (and applied unless dry_run).
    """
    report = CorrectionReport(
        input_path="",
        output_path="",
        dry_run=dry_run,
    )

    paragraphs = doc.paragraphs
    report.total_paragraphs = len(paragraphs)

    # ── Phase 1: collect corrections by scanning paragraph text ──────────
    for p_idx, para in enumerate(paragraphs):
        original = para.text
        if not original or not original.strip():
            continue

        current = original
        for rule in rules:
            new_text, count = _apply_rule_to_text(current, rule)
            if count > 0:
                report.corrections.append(
                    CorrectionItem(
                        paragraph_index=p_idx,
                        original_text=current,
                        corrected_text=new_text,
                        rule_id=rule.id,
                        rule_desc=rule.desc,
                        rule_source=rule.source,
                        layer=rule.layer,
                    )
                )
                report.total_corrections += count
                current = new_text

    # ── Phase 2: apply changes to the actual document (skip if dry-run) ──
    if not dry_run:
        for rule in rules:
            if rule.rule_type == "exact_replace":
                doc.replace_text_in_runs(rule.search, rule.replace)
            elif rule.rule_type == "regex_replace":
                for para in doc.paragraphs:
                    for run in para.runs:
                        if run.text and re.search(rule.search, run.text):
                            new_text = re.sub(rule.search, rule.replace, run.text)
                            run.replace_text(run.text, new_text)

    # ── Phase 3: L4 harmony analysis via LLM (optional) ─────────────────
    # paragraphs is already defined above (doc.paragraphs, Line 57)
    if harmony_checker is not None:
        for p_idx, para in enumerate(paragraphs):
            text = para.text
            if not text or not text.strip():
                continue
            suggestions = harmony_checker.check_paragraph(text, para_idx=p_idx)
            report.harmony_suggestions.extend(suggestions)
            consume_warnings = getattr(harmony_checker, "consume_warnings", None)
            if callable(consume_warnings):
                warnings = consume_warnings()
                if isinstance(warnings, list):
                    report.warnings.extend(warnings)

    return report
