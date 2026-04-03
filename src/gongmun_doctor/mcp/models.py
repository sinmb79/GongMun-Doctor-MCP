"""Structured models exposed by the MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ServerInfo:
    name: str
    version: str
    recommended_transport: str
    supported_transports: list[str]
    ready_domains: list[str]
    deferred_domains: list[str]
    security_posture: list[str] = field(default_factory=list)


@dataclass
class RuleInfo:
    id: str
    layer: str
    rule_type: str
    search: str
    replace: str
    description: str
    source: str


@dataclass
class CorrectionPreviewItem:
    rule_id: str
    layer: str
    paragraph_index: int
    original_text: str
    corrected_text: str
    description: str
    source: str


@dataclass
class TextCorrectionPreview:
    original_text: str
    corrected_text: str
    total_corrections: int
    corrections: list[CorrectionPreviewItem] = field(default_factory=list)


@dataclass
class DocumentCorrectionResult:
    requested_path: str
    resolved_input_path: str
    output_path: str
    output_written: bool
    backup_path: str | None
    report_path: str | None
    report_written: bool
    dry_run: bool
    total_paragraphs: int
    total_corrections: int
    corrections: list[CorrectionPreviewItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    report_markdown: str | None = None


@dataclass
class CorrectionReportFile:
    requested_path: str
    resolved_report_path: str
    exists: bool
    markdown: str | None = None


@dataclass
class TemplateVariableInfo:
    key: str
    label: str
    example: str | None = None


@dataclass
class TemplateInfo:
    id: str
    name: str
    category: str
    triggers: list[str] = field(default_factory=list)


@dataclass
class TemplateMatch:
    template: TemplateInfo
    score: int
    matched_triggers: list[str] = field(default_factory=list)


@dataclass
class TemplateRenderResult:
    template_id: str
    template_name: str
    rendered_text: str
    missing_variables: list[str] = field(default_factory=list)
