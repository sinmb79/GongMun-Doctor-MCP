"""JSON-safe service wrappers used by the MCP server."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
from typing import Any

from gongmun_doctor import __version__
from gongmun_doctor.agents.administrative.template_engine import TemplateEngine
from gongmun_doctor.engine import correct_document as apply_document_corrections
from gongmun_doctor.engine import correct_text
from gongmun_doctor.mcp.models import (
    CorrectionReportFile,
    CorrectionPreviewItem,
    DocumentCorrectionResult,
    RuleInfo,
    ServerInfo,
    TemplateInfo,
    TemplateMatch,
    TemplateRenderResult,
    TemplateVariableInfo,
    TextCorrectionPreview,
)
from gongmun_doctor.report.markdown import generate_markdown
from gongmun_doctor.rules.loader import load_rules_by_layer


def _load_document_runtime():
    try:
        from gongmun_doctor.parser.hwpx_handler import (
            close_document,
            open_document,
            save_document,
        )
    except ImportError as exc:
        raise RuntimeError(
            "HWPX 문서 교정 기능을 사용하려면 python-hwpx 런타임이 설치되어 있어야 합니다."
        ) from exc
    return open_document, save_document, close_document


def _load_hwp_conversion_runtime():
    from gongmun_doctor.parser.hwp_converter import (
        LibreOfficeNotFoundError,
        convert_hwp_to_hwpx,
        is_libreoffice_available,
    )
    return LibreOfficeNotFoundError, convert_hwp_to_hwpx, is_libreoffice_available


class GongmunDoctorMcpService:
    """Thin adapter that turns package internals into MCP-friendly outputs."""

    def __init__(self, template_engine: TemplateEngine | None = None) -> None:
        self._template_engine = template_engine or TemplateEngine()

    def get_server_info(self) -> ServerInfo:
        return ServerInfo(
            name="gongmun-doctor",
            version=__version__,
            recommended_transport="stdio",
            supported_transports=["stdio"],
            ready_domains=[
                "rule catalog",
                "local document correction",
                "stored report retrieval",
                "text correction preview",
                "template discovery",
                "template rendering",
            ],
            deferred_domains=[
                "HWP COM automation",
                "clipboard automation",
                "cloud LLM-backed harmony analysis",
            ],
            security_posture=[
                "local filesystem paths only",
                "no network calls in default tools",
                "no API keys required",
                "sidecar markdown reports only when explicitly requested",
            ],
        )

    def list_rules(self, layer: str | None = None) -> list[RuleInfo]:
        layers = [layer] if layer else None
        return [
            RuleInfo(
                id=rule.id,
                layer=rule.layer,
                rule_type=rule.rule_type,
                search=rule.search,
                replace=rule.replace,
                description=rule.desc,
                source=rule.source,
            )
            for rule in load_rules_by_layer(layers=layers)
        ]

    def preview_text_corrections(
        self,
        text: str,
        layers: list[str] | None = None,
    ) -> TextCorrectionPreview:
        rules = load_rules_by_layer(layers=layers)
        items = correct_text(text, rules)
        return TextCorrectionPreview(
            original_text=text,
            corrected_text=items[-1].corrected_text if items else text,
            total_corrections=len(items),
            corrections=[
                CorrectionPreviewItem(
                    rule_id=item.rule_id,
                    layer=item.layer,
                    paragraph_index=item.paragraph_index,
                    original_text=item.original_text,
                    corrected_text=item.corrected_text,
                    description=item.rule_desc,
                    source=item.rule_source,
                )
                for item in items
            ],
        )

    def correct_document(
        self,
        file_path: str,
        dry_run: bool = False,
        report: bool = False,
    ) -> DocumentCorrectionResult:
        requested_path = file_path
        resolved_input_path = self._resolve_document_input(file_path)
        output_path = self._default_output_path(resolved_input_path)
        report_path = self._default_report_path(output_path) if report else None

        open_document, save_document, close_document = _load_document_runtime()
        rules = load_rules_by_layer()
        if not rules:
            raise ValueError("no correction rules available")

        document = open_document(resolved_input_path)
        backup_path: str | None = None
        report_markdown: str | None = None

        try:
            if not dry_run:
                backup_path = str(self._backup_document(resolved_input_path))

            correction_report = apply_document_corrections(
                document,
                rules,
                dry_run=dry_run,
            )
            correction_report.input_path = str(resolved_input_path)
            correction_report.output_path = str(output_path) if not dry_run else "(dry-run)"

            if not dry_run:
                save_document(document, output_path)

            if report_path is not None:
                report_markdown = generate_markdown(correction_report)
                report_path.write_text(report_markdown, encoding="utf-8")
        finally:
            close_document(document)

        return DocumentCorrectionResult(
            requested_path=requested_path,
            resolved_input_path=str(resolved_input_path),
            output_path=str(output_path),
            output_written=not dry_run,
            backup_path=backup_path,
            report_path=str(report_path) if report_path is not None else None,
            report_written=report_path is not None,
            dry_run=dry_run,
            total_paragraphs=correction_report.total_paragraphs,
            total_corrections=correction_report.total_corrections,
            corrections=[
                CorrectionPreviewItem(
                    rule_id=item.rule_id,
                    layer=item.layer,
                    paragraph_index=item.paragraph_index,
                    original_text=item.original_text,
                    corrected_text=item.corrected_text,
                    description=item.rule_desc,
                    source=item.rule_source,
                )
                for item in correction_report.corrections
            ],
            warnings=list(correction_report.warnings),
            report_markdown=report_markdown,
        )

    def get_correction_report(self, file_path: str) -> CorrectionReportFile:
        report_path = self._resolve_report_path(file_path)
        if not report_path.exists():
            return CorrectionReportFile(
                requested_path=file_path,
                resolved_report_path=str(report_path),
                exists=False,
                markdown=None,
            )

        return CorrectionReportFile(
            requested_path=file_path,
            resolved_report_path=str(report_path),
            exists=True,
            markdown=report_path.read_text(encoding="utf-8"),
        )

    def list_templates(self, category: str | None = None) -> list[TemplateInfo]:
        return [
            self._to_template_info(template)
            for template in self._template_engine.list_templates(category=category)
        ]

    def match_templates(self, query: str) -> list[TemplateMatch]:
        matches: list[TemplateMatch] = []
        for template in self._template_engine.match(query):
            matched_triggers = [
                trigger for trigger in template.get("triggers", []) if trigger in query
            ]
            matches.append(
                TemplateMatch(
                    template=self._to_template_info(template),
                    score=len(matched_triggers),
                    matched_triggers=matched_triggers,
                )
            )
        return matches

    def get_template_variables(self, template_id: str) -> list[TemplateVariableInfo]:
        template = self._get_template(template_id)
        return [
            TemplateVariableInfo(
                key=variable["key"],
                label=variable["label"],
                example=variable.get("example"),
            )
            for variable in template.get("variables", [])
        ]

    def render_template(
        self,
        template_id: str,
        values: dict[str, str],
    ) -> TemplateRenderResult:
        template = self._get_template(template_id)
        rendered_text = self._template_engine.render(template_id, values)
        missing_variables = [
            variable["key"]
            for variable in template.get("variables", [])
            if "{{" + variable["key"] + "}}" in rendered_text
        ]
        return TemplateRenderResult(
            template_id=template_id,
            template_name=template.get("name", template_id),
            rendered_text=rendered_text,
            missing_variables=missing_variables,
        )

    def _get_template(self, template_id: str) -> dict[str, Any]:
        try:
            return self._template_engine.templates[template_id]
        except KeyError as exc:
            raise ValueError(f"unknown template_id: {template_id}") from exc

    def _resolve_document_input(self, file_path: str) -> Path:
        path = self._normalize_local_path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"document not found: {path}")
        if path.is_dir():
            raise IsADirectoryError(f"expected a file path, got directory: {path}")

        suffix = path.suffix.lower()
        if suffix == ".hwpx":
            return path
        if suffix == ".hwp":
            (
                libreoffice_error,
                convert_hwp_to_hwpx,
                is_libreoffice_available,
            ) = _load_hwp_conversion_runtime()
            if not is_libreoffice_available():
                raise RuntimeError(
                    "HWP 입력은 LibreOffice가 설치된 환경에서만 HWPX로 변환할 수 있습니다."
                )
            try:
                return convert_hwp_to_hwpx(path)
            except libreoffice_error as exc:
                raise RuntimeError(str(exc)) from exc
        raise ValueError("only .hwpx and .hwp files are supported")

    def _resolve_report_path(self, file_path: str) -> Path:
        path = self._normalize_local_path(file_path)
        if path.suffix.lower() == ".md":
            return path
        if path.name.endswith("_corrected.hwpx"):
            return path.with_suffix(".md")
        if path.suffix.lower() in {".hwpx", ".hwp"}:
            return path.parent / f"{path.stem}_corrected.md"
        return path.with_suffix(".md")

    @staticmethod
    def _normalize_local_path(file_path: str) -> Path:
        raw_path = file_path.strip()
        if not raw_path:
            raise ValueError("file_path must not be empty")
        if "://" in raw_path:
            raise ValueError("only local filesystem paths are supported")
        path = Path(raw_path).expanduser()
        return path.resolve()

    @staticmethod
    def _default_output_path(input_path: Path) -> Path:
        return input_path.parent / f"{input_path.stem}_corrected.hwpx"

    @staticmethod
    def _default_report_path(output_path: Path) -> Path:
        return output_path.with_suffix(".md")

    @staticmethod
    def _backup_document(input_path: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = input_path.with_suffix(f".{timestamp}.bak.hwpx")
        shutil.copy2(input_path, backup_path)
        return backup_path

    @staticmethod
    def _to_template_info(template: dict[str, Any]) -> TemplateInfo:
        return TemplateInfo(
            id=template.get("id", ""),
            name=template.get("name", ""),
            category=template.get("category", ""),
            triggers=list(template.get("triggers", [])),
        )
