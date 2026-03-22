"""CLI entry point for gongmun-doctor."""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from gongmun_doctor import __version__
from gongmun_doctor.engine import correct_document
from gongmun_doctor.parser.hwpx_handler import (
    close_document,
    open_document,
    save_document,
)
from gongmun_doctor.parser.hwp_converter import (
    LibreOfficeNotFoundError,
    convert_hwp_to_hwpx,
    is_libreoffice_available,
)
from gongmun_doctor.report.markdown import CorrectionReport, write_report
from gongmun_doctor.rules.loader import load_rules, load_rules_by_layer


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_input(input_path: Path) -> Path:
    """Return an HWPX path, converting from HWP if needed."""
    suffix = input_path.suffix.lower()

    if suffix == ".hwpx":
        return input_path

    if suffix == ".hwp":
        if not is_libreoffice_available():
            print(
                "⚠️  HWP 파일 감지: LibreOffice가 설치되어 있지 않아 변환을 건너뜁니다.",
                file=sys.stderr,
            )
            print(
                "   HWP → HWPX 변환이 필요하면 LibreOffice를 설치하세요.",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"[HWP→HWPX] LibreOffice로 변환 중: {input_path}")
        try:
            converted = convert_hwp_to_hwpx(input_path)
            print(f"[HWP→HWPX] 변환 완료: {converted}")
            return converted
        except LibreOfficeNotFoundError as e:
            print(f"오류: {e}", file=sys.stderr)
            sys.exit(1)
        except RuntimeError as e:
            print(f"변환 오류: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"오류: 지원하지 않는 파일 형식입니다: {suffix}", file=sys.stderr)
    sys.exit(1)


def _backup(input_path: Path) -> Path:
    """Create a timestamped backup of the original file."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = input_path.with_suffix(f".{ts}.bak.hwpx")
    shutil.copy2(input_path, backup_path)
    return backup_path


# ─────────────────────────────────────────────────────────────────────────────
# Sub-command: correct
# ─────────────────────────────────────────────────────────────────────────────

def cmd_correct(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"오류: 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        return 1

    # Resolve to HWPX (converting from HWP if needed)
    hwpx_path = _resolve_input(input_path)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = hwpx_path.parent / f"{hwpx_path.stem}_corrected.hwpx"

    report_path = output_path.with_suffix(".md") if args.report else None

    # Layer filtering for --strict mode
    layers = None
    if args.strict:
        layers = ["L1_spelling", "L2_grammar", "L3_official_style"]

    # Load rules
    rules = load_rules_by_layer(layers=layers)
    if not rules:
        print("오류: 교정 규칙을 불러올 수 없습니다.", file=sys.stderr)
        return 1
    print(f"[1/4] 규칙 로드 완료: {len(rules)}개")

    # Backup original (skip in dry-run mode)
    if not args.dry_run:
        backup = _backup(hwpx_path)
        print(f"[2/4] 원본 백업: {backup}")
    else:
        print("[2/4] dry-run 모드: 파일을 수정하지 않습니다.")

    # Open document
    try:
        doc = open_document(hwpx_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1

    para_count = len(doc.paragraphs)
    print(f"[3/4] 문서 열기 완료: {hwpx_path.name} ({para_count}개 문단)")

    # Apply corrections
    report = correct_document(doc, rules, dry_run=args.dry_run)
    report.input_path = str(hwpx_path)
    report.output_path = str(output_path) if not args.dry_run else "(dry-run)"

    # Save corrected document
    if not args.dry_run:
        save_document(doc, output_path)
        print(f"[4/4] 교정 파일 저장: {output_path}")
    else:
        print(f"[4/4] dry-run 완료 (저장 건너뜀)")

    close_document(doc)

    # Write report
    if report_path:
        write_report(report, str(report_path))
        print(f"\n[보고서] {report_path}")

    # Summary
    print(f"\n{'─'*50}")
    print(f"  총 문단: {report.total_paragraphs}개")
    print(f"  교정 건수: {report.total_corrections}건")
    if not args.dry_run:
        print(f"  교정 파일: {output_path}")
    print(f"{'─'*50}")

    if report.total_corrections == 0:
        print("[완료] 교정 사항이 없습니다.")
    else:
        # Print corrections to stdout for quick review
        print(f"\n교정 내역 ({report.total_corrections}건):")
        for c in report.corrections:
            print(f"  [{c.rule_id}] 문단 {c.paragraph_index}: "
                  f"'{c.original_text[:40]}...' → '{c.corrected_text[:40]}...'")

    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Sub-command: list-rules
# ─────────────────────────────────────────────────────────────────────────────

def cmd_list_rules(args: argparse.Namespace) -> int:
    rules = load_rules()
    layer_filter = args.layer

    by_layer: dict[str, list] = {}
    for r in rules:
        if layer_filter and r.layer != layer_filter:
            continue
        by_layer.setdefault(r.layer, []).append(r)

    for layer, layer_rules in sorted(by_layer.items()):
        print(f"\n▶ {layer} ({len(layer_rules)}개 규칙)")
        for r in layer_rules:
            print(f"  {r.id:12s}  {r.desc}")

    print(f"\n총 {sum(len(v) for v in by_layer.values())}개 규칙")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gongmun-doctor",
        description=(
            "공문닥터 — HWPX/HWP 공문서 자동 교정 도구\n"
            "\n"
            "글자가 깨져 보일 경우: 명령 프롬프트에서 'chcp 65001' 입력 후 재실행하세요.\n"
            "\n"
            "빠른 시작:\n"
            "  gongmun-doctor correct 문서.hwpx           # 교정 실행\n"
            "  gongmun-doctor correct 문서.hwpx --dry-run # 수정 없이 미리 보기\n"
            "  gongmun-doctor correct 문서.hwpx --report  # 교정 보고서 함께 생성\n"
            "  gongmun-doctor list-rules                  # 규칙 목록 확인\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # correct
    p_correct = subparsers.add_parser("correct", help="공문서 교정")
    p_correct.add_argument("input", help="입력 파일 (.hwpx 또는 .hwp)")
    p_correct.add_argument("-o", "--output", help="출력 파일 경로 (기본: <입력>_corrected.hwpx)")
    p_correct.add_argument("--report", action="store_true", help="교정 보고서 생성 (.md)")
    p_correct.add_argument(
        "--dry-run",
        action="store_true",
        help="교정 내용만 표시하고 파일은 수정하지 않음",
    )
    p_correct.add_argument(
        "--strict",
        action="store_true",
        help="모든 규칙 계층 적용 (기본: L1+L2+L3)",
    )

    # list-rules
    p_rules = subparsers.add_parser("list-rules", help="교정 규칙 목록 표시")
    p_rules.add_argument("--layer", help="특정 계층만 표시 (예: L1_spelling)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "correct":
        sys.exit(cmd_correct(args))
    elif args.command == "list-rules":
        sys.exit(cmd_list_rules(args))
    else:
        parser.print_help()
        sys.exit(1)
