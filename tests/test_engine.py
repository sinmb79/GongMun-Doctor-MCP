"""Tests for the correction engine."""

import pytest
from unittest.mock import MagicMock

from gongmun_doctor.engine import _apply_rule_to_text, correct_document
from gongmun_doctor.rules.loader import CorrectionRule, load_rules


def _make_rule(id: str, rule_type: str, search: str, replace: str) -> CorrectionRule:
    return CorrectionRule(
        id=id,
        rule_type=rule_type,
        search=search,
        replace=replace,
        desc="test rule",
        source="test",
        layer="L1_spelling",
    )


class TestApplyRuleToText:
    def test_exact_replace_found(self):
        rule = _make_rule("T-001", "exact_replace", "오류", "올바름")
        result, count = _apply_rule_to_text("이것은 오류입니다", rule)
        assert result == "이것은 올바름입니다"
        assert count == 1

    def test_exact_replace_not_found(self):
        rule = _make_rule("T-002", "exact_replace", "없는단어", "교정")
        result, count = _apply_rule_to_text("이 텍스트에는 없습니다", rule)
        assert result == "이 텍스트에는 없습니다"
        assert count == 0

    def test_exact_replace_multiple(self):
        rule = _make_rule("T-003", "exact_replace", "오류", "수정")
        result, count = _apply_rule_to_text("오류가 오류입니다", rule)
        assert count == 2
        assert result == "수정가 수정입니다"

    def test_regex_replace_found(self):
        rule = _make_rule("T-004", "regex_replace", r"(\d+)원정", r"\1원")
        result, count = _apply_rule_to_text("1000원정을 납부", rule)
        assert count == 1
        assert "1000원" in result
        assert "원정" not in result

    def test_regex_replace_not_found(self):
        rule = _make_rule("T-005", "regex_replace", r"없는패턴\d+", r"교정")
        result, count = _apply_rule_to_text("이 텍스트에는 없습니다", rule)
        assert count == 0

    def test_unknown_rule_type_returns_original(self):
        rule = _make_rule("T-006", "unknown_type", "검색", "교정")
        result, count = _apply_rule_to_text("검색 텍스트", rule)
        assert result == "검색 텍스트"
        assert count == 0


class TestCorrectDocumentDryRun:
    def _make_mock_doc(self, paragraphs: list[str]):
        """Build a minimal mock HwpxDocument."""
        doc = MagicMock()
        mock_paras = []
        for text in paragraphs:
            para = MagicMock()
            para.text = text
            para.runs = []
            mock_paras.append(para)
        doc.paragraphs = mock_paras
        return doc

    def test_dry_run_does_not_call_replace_text_in_runs(self):
        doc = self._make_mock_doc(["도로 시행알림 공고"])
        rules = [_make_rule("SP-001", "exact_replace", "시행알림", "시행 알림")]

        report = correct_document(doc, rules, dry_run=True)

        doc.replace_text_in_runs.assert_not_called()
        assert report.dry_run is True

    def test_dry_run_still_reports_corrections(self):
        doc = self._make_mock_doc(["도로 시행알림 공고", "부탁드립니다"])
        rules = [
            _make_rule("SP-001", "exact_replace", "시행알림", "시행 알림"),
            _make_rule("OS-007", "exact_replace", "부탁드립니다", "바랍니다"),
        ]

        report = correct_document(doc, rules, dry_run=True)

        assert report.total_corrections == 2
        assert len(report.corrections) == 2

    def test_no_corrections_on_clean_text(self):
        doc = self._make_mock_doc(["올바른 문장입니다."])
        rules = [_make_rule("SP-001", "exact_replace", "시행알림", "시행 알림")]

        report = correct_document(doc, rules, dry_run=True)

        assert report.total_corrections == 0
        assert report.corrections == []

    def test_paragraph_count_recorded(self):
        doc = self._make_mock_doc(["문단 1", "문단 2", "문단 3"])
        rules = []

        report = correct_document(doc, rules, dry_run=True)

        assert report.total_paragraphs == 3

    def test_empty_paragraphs_skipped(self):
        doc = self._make_mock_doc(["", "   ", "실제 내용"])
        rules = [_make_rule("SP-001", "exact_replace", "시행알림", "시행 알림")]

        report = correct_document(doc, rules, dry_run=True)

        assert report.total_corrections == 0

    def test_correction_item_fields_populated(self):
        doc = self._make_mock_doc(["시행알림 공고"])
        rule = _make_rule("SP-001", "exact_replace", "시행알림", "시행 알림")
        rule.desc = "테스트 규칙"
        rule.source = "테스트 출처"
        rule.layer = "L1_spelling"

        report = correct_document(doc, [rule], dry_run=True)

        assert len(report.corrections) == 1
        c = report.corrections[0]
        assert c.rule_id == "SP-001"
        assert c.original_text == "시행알림 공고"
        assert c.corrected_text == "시행 알림 공고"
        assert c.paragraph_index == 0
        assert c.layer == "L1_spelling"
