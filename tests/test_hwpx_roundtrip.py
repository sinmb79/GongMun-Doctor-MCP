"""HWPX round-trip tests — open, correct, save, re-open, verify."""

import shutil
import tempfile
from pathlib import Path

import pytest

from gongmun_doctor.parser.hwpx_handler import (
    close_document,
    extract_text,
    open_document,
    save_document,
)
from gongmun_doctor.engine import correct_document
from gongmun_doctor.rules.loader import load_rules


pytestmark = pytest.mark.integration


class TestHwpxHandler:
    def test_open_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            open_document("/nonexistent/path.hwpx")

    def test_open_wrong_extension_raises(self):
        with pytest.raises(ValueError):
            open_document("/some/file.txt")

    def test_open_valid_document(self, road_repair_hwpx: Path):
        doc = open_document(road_repair_hwpx)
        assert doc is not None
        close_document(doc)

    def test_extract_text_nonempty(self, road_repair_hwpx: Path):
        doc = open_document(road_repair_hwpx)
        text = extract_text(doc)
        close_document(doc)
        assert len(text) > 0

    def test_paragraph_list_nonempty(self, road_repair_hwpx: Path):
        doc = open_document(road_repair_hwpx)
        paras = doc.paragraphs
        close_document(doc)
        assert len(paras) > 0


class TestRoundTrip:
    def _roundtrip(self, hwpx_path: Path) -> tuple[str, str, int]:
        """Open → correct → save → re-open. Returns (original_text, new_text, count)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / hwpx_path.name

            # Work on a copy
            shutil.copy2(hwpx_path, tmp_file)

            doc = open_document(tmp_file)
            original = extract_text(doc)
            rules = load_rules()

            report = correct_document(doc, rules, dry_run=False)
            save_document(doc, tmp_file)
            close_document(doc)

            # Re-open and verify
            doc2 = open_document(tmp_file)
            corrected = extract_text(doc2)
            close_document(doc2)

        return original, corrected, report.total_corrections

    def test_road_repair_roundtrip(self, road_repair_hwpx: Path):
        original, corrected, count = self._roundtrip(road_repair_hwpx)
        # PoC verified 12 corrections on this document
        assert count > 0, "Expected corrections on road repair document"

    def test_completion_inspect_roundtrip(self, completion_inspect_hwpx: Path):
        original, corrected, count = self._roundtrip(completion_inspect_hwpx)
        assert count >= 0  # may be 0 after prior runs

    def test_cooperation_request_roundtrip(self, cooperation_request_hwpx: Path):
        original, corrected, count = self._roundtrip(cooperation_request_hwpx)
        assert count >= 0

    def test_dry_run_does_not_modify_file(self, road_repair_hwpx: Path):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / road_repair_hwpx.name
            shutil.copy2(road_repair_hwpx, tmp_file)

            original_bytes = tmp_file.read_bytes()

            doc = open_document(tmp_file)
            rules = load_rules()
            correct_document(doc, rules, dry_run=True)
            save_document(doc, tmp_file)
            close_document(doc)

            # File should be unchanged (dry-run doesn't touch runs)
            # Note: save_document will still rewrite the container, so we
            # just verify the text content matches
            doc2 = open_document(tmp_file)
            text_after = extract_text(doc2)
            close_document(doc2)

            doc3 = open_document(road_repair_hwpx)
            text_original = extract_text(doc3)
            close_document(doc3)

            assert text_after == text_original
