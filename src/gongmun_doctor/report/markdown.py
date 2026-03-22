"""Markdown correction report generator."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CorrectionItem:
    paragraph_index: int
    original_text: str
    corrected_text: str
    rule_id: str
    rule_desc: str
    rule_source: str
    layer: str


@dataclass
class CorrectionReport:
    input_path: str
    output_path: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_paragraphs: int = 0
    total_corrections: int = 0
    corrections: list[CorrectionItem] = field(default_factory=list)
    format_preserved: bool = True
    dry_run: bool = False


def generate_markdown(report: CorrectionReport) -> str:
    """Generate a Markdown correction report string."""
    mode_label = "미리 보기 (dry-run)" if report.dry_run else "교정 완료"

    lines = [
        "# 공문닥터 교정 보고서",
        "",
        f"- **모드**: {mode_label}",
        f"- **입력 파일**: `{report.input_path}`",
        f"- **출력 파일**: `{report.output_path}`",
        f"- **처리 시각**: {report.timestamp}",
        f"- **총 문단 수**: {report.total_paragraphs}",
        f"- **교정 건수**: {report.total_corrections}",
        f"- **서식 보존**: {'✅ 예' if report.format_preserved else '❌ 아니오'}",
        "",
        "---",
        "",
        "## 교정 내역",
        "",
    ]

    if not report.corrections:
        lines.append("교정 사항이 없습니다.")
    else:
        # Group by paragraph index
        by_para: dict[int, list[CorrectionItem]] = {}
        for c in report.corrections:
            by_para.setdefault(c.paragraph_index, []).append(c)

        for p_idx in sorted(by_para.keys()):
            lines.append(f"### 문단 {p_idx}")
            lines.append("")
            for c in by_para[p_idx]:
                lines += [
                    "| 항목 | 내용 |",
                    "|------|------|",
                    f"| **규칙** | `{c.rule_id}` — {c.rule_desc} |",
                    f"| **계층** | {c.layer} |",
                    f"| **원문** | {c.original_text} |",
                    f"| **교정** | {c.corrected_text} |",
                    f"| **근거** | {c.rule_source} |",
                    "",
                ]

    lines += [
        "---",
        "",
        f"*공문닥터 v1.0 — {datetime.now().strftime('%Y-%m-%d')}*",
    ]

    return "\n".join(lines)


def write_report(report: CorrectionReport, path: str) -> None:
    """Write the Markdown report to a file."""
    content = generate_markdown(report)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
