"""Correction engine — applies rules to HWPX document paragraphs."""

import re

from hwpx.document import HwpxDocument

from gongmun_doctor.rules.loader import CorrectionRule
from gongmun_doctor.report.markdown import CorrectionItem, CorrectionReport


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


def correct_document(
    doc: HwpxDocument,
    rules: list[CorrectionRule],
    dry_run: bool = False,
) -> CorrectionReport:
    """Apply all rules to all paragraphs in the document.

    When dry_run=True the document object is not modified; the report
    still reflects what *would* be corrected.

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
    # We record what changed so the report is accurate, then replay the
    # actual document edits in phase 2.
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

    return report
