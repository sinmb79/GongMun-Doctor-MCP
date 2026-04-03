"""Tests for MCP service wrappers."""

from pathlib import Path
from types import SimpleNamespace

from gongmun_doctor.mcp.services import GongmunDoctorMcpService
from gongmun_doctor.report.markdown import CorrectionItem, CorrectionReport
from gongmun_doctor.rules.loader import load_rules


def test_server_info_defaults_to_stdio():
    service = GongmunDoctorMcpService()

    info = service.get_server_info()

    assert info.recommended_transport == "stdio"
    assert "text correction preview" in info.ready_domains
    assert "no network calls in default tools" in info.security_posture


def test_preview_text_corrections_returns_final_text():
    service = GongmunDoctorMcpService()
    rule = next(rule for rule in load_rules() if rule.rule_type == "exact_replace" and rule.search)
    source_text = f"prefix {rule.search} suffix"

    preview = service.preview_text_corrections(source_text)

    assert preview.total_corrections >= 1
    assert preview.corrected_text != preview.original_text
    assert rule.replace in preview.corrected_text


def test_list_templates_returns_bundled_templates():
    service = GongmunDoctorMcpService()

    templates = service.list_templates()

    assert len(templates) >= 50


def test_match_templates_scores_results():
    service = GongmunDoctorMcpService()
    template = service.list_templates()[0]
    trigger = template.triggers[0]

    matches = service.match_templates(f"{trigger} 문서를 찾고 싶다")

    assert matches
    assert matches[0].score >= 1
    assert matches[0].matched_triggers


def test_render_template_reports_missing_variables():
    service = GongmunDoctorMcpService()

    template = next(template for template in service.list_templates() if template.triggers)
    rendered = service.render_template(template.id, {})

    assert rendered.template_id == template.id
    variables = service.get_template_variables(template.id)
    if variables:
        assert rendered.missing_variables


def test_correct_document_dry_run_returns_structured_result(monkeypatch, tmp_path: Path):
    service = GongmunDoctorMcpService()
    input_file = tmp_path / "sample.hwpx"
    input_file.write_text("dummy", encoding="utf-8")

    fake_doc = SimpleNamespace(paragraphs=["p1", "p2"])
    fake_report = CorrectionReport(
        input_path="",
        output_path="",
        total_paragraphs=2,
        total_corrections=1,
        corrections=[
            CorrectionItem(
                paragraph_index=0,
                original_text="before",
                corrected_text="after",
                rule_id="SP-001",
                rule_desc="desc",
                rule_source="source",
                layer="L1_spelling",
            )
        ],
    )

    monkeypatch.setattr(
        "gongmun_doctor.mcp.services._load_document_runtime",
        lambda: (
            lambda path: fake_doc,
            lambda doc, path: None,
            lambda doc: None,
        ),
    )
    monkeypatch.setattr(
        "gongmun_doctor.mcp.services.apply_document_corrections",
        lambda document, rules, dry_run: fake_report,
    )

    result = service.correct_document(str(input_file), dry_run=True, report=False)

    assert result.dry_run is True
    assert result.output_written is False
    assert result.backup_path is None
    assert result.total_corrections == 1
    assert result.corrections[0].corrected_text == "after"


def test_correct_document_report_can_be_read_back(monkeypatch, tmp_path: Path):
    service = GongmunDoctorMcpService()
    input_file = tmp_path / "sample.hwpx"
    input_file.write_text("dummy", encoding="utf-8")

    fake_doc = SimpleNamespace(paragraphs=["p1"])
    fake_report = CorrectionReport(
        input_path="",
        output_path="",
        total_paragraphs=1,
        total_corrections=0,
    )

    monkeypatch.setattr(
        "gongmun_doctor.mcp.services._load_document_runtime",
        lambda: (
            lambda path: fake_doc,
            lambda doc, path: None,
            lambda doc: None,
        ),
    )
    monkeypatch.setattr(
        "gongmun_doctor.mcp.services.apply_document_corrections",
        lambda document, rules, dry_run: fake_report,
    )

    result = service.correct_document(str(input_file), dry_run=True, report=True)
    stored = service.get_correction_report(str(input_file))

    assert result.report_written is True
    assert result.report_path is not None
    assert stored.exists is True
    assert stored.markdown is not None


def test_get_correction_report_returns_missing_state(tmp_path: Path):
    service = GongmunDoctorMcpService()
    input_file = tmp_path / "missing.hwpx"

    stored = service.get_correction_report(str(input_file))

    assert stored.exists is False
    assert stored.markdown is None


def test_correct_documents_in_folder_aggregates_results(monkeypatch, tmp_path: Path):
    service = GongmunDoctorMcpService()
    (tmp_path / "a.hwpx").write_text("a", encoding="utf-8")
    (tmp_path / "b.hwp").write_text("b", encoding="utf-8")
    (tmp_path / "note.txt").write_text("ignore", encoding="utf-8")

    def fake_correct_document(file_path: str, dry_run: bool, report: bool):
        return type(
            "Result",
            (),
            {
                "total_corrections": 2,
                "output_path": file_path + ".out",
                "report_path": file_path + ".md" if report else None,
            },
        )()

    monkeypatch.setattr(service, "correct_document", fake_correct_document)

    batch = service.correct_documents_in_folder(
        str(tmp_path),
        dry_run=True,
        report=True,
        recursive=False,
    )

    assert batch.discovered_files == 2
    assert batch.succeeded_files == 2
    assert batch.failed_files == 0
    assert batch.total_corrections == 4


def test_correct_documents_in_folder_records_failures(monkeypatch, tmp_path: Path):
    service = GongmunDoctorMcpService()
    (tmp_path / "a.hwpx").write_text("a", encoding="utf-8")

    def fake_correct_document(file_path: str, dry_run: bool, report: bool):
        raise RuntimeError("blocked")

    monkeypatch.setattr(service, "correct_document", fake_correct_document)

    batch = service.correct_documents_in_folder(str(tmp_path))

    assert batch.discovered_files == 1
    assert batch.succeeded_files == 0
    assert batch.failed_files == 1
    assert batch.items[0].error == "blocked"
