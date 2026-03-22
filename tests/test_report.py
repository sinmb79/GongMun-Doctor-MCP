"""Tests for Markdown report generation."""

import pytest
from gongmun_doctor.report.markdown import (
    CorrectionItem,
    CorrectionReport,
    generate_markdown,
    write_report,
)
import tempfile
from pathlib import Path


def _make_report(**kwargs) -> CorrectionReport:
    defaults = dict(
        input_path="test.hwpx",
        output_path="test_corrected.hwpx",
        total_paragraphs=5,
        total_corrections=0,
    )
    defaults.update(kwargs)
    return CorrectionReport(**defaults)


def _make_item(paragraph_index: int = 0, rule_id: str = "SP-001") -> CorrectionItem:
    return CorrectionItem(
        paragraph_index=paragraph_index,
        original_text="원문",
        corrected_text="교정문",
        rule_id=rule_id,
        rule_desc="테스트 규칙",
        rule_source="한글 맞춤법",
        layer="L1_spelling",
    )


class TestGenerateMarkdown:
    def test_header_present(self):
        report = _make_report()
        md = generate_markdown(report)
        assert "공문닥터 교정 보고서" in md

    def test_input_path_shown(self):
        report = _make_report(input_path="/path/to/document.hwpx")
        md = generate_markdown(report)
        assert "document.hwpx" in md

    def test_no_corrections_message(self):
        report = _make_report()
        md = generate_markdown(report)
        assert "교정 사항이 없습니다" in md

    def test_correction_items_shown(self):
        item = _make_item(paragraph_index=2, rule_id="SP-006")
        report = _make_report(total_corrections=1)
        report.corrections = [item]
        md = generate_markdown(report)
        assert "SP-006" in md
        assert "원문" in md
        assert "교정문" in md
        assert "문단 2" in md

    def test_dry_run_label(self):
        report = _make_report(dry_run=True)
        md = generate_markdown(report)
        assert "dry-run" in md or "미리 보기" in md

    def test_multiple_paragraphs_grouped(self):
        items = [
            _make_item(paragraph_index=0, rule_id="SP-001"),
            _make_item(paragraph_index=3, rule_id="OS-007"),
        ]
        report = _make_report(total_corrections=2)
        report.corrections = items
        md = generate_markdown(report)
        assert "문단 0" in md
        assert "문단 3" in md


class TestWriteReport:
    def test_write_creates_file(self):
        report = _make_report()
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name
        write_report(report, path)
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "공문닥터" in content
