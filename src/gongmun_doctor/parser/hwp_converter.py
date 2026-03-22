"""HWP → HWPX conversion via LibreOffice headless."""

import shutil
import subprocess
import tempfile
from pathlib import Path


class LibreOfficeNotFoundError(RuntimeError):
    pass


def _find_libreoffice() -> str | None:
    """Return path to LibreOffice executable, or None if not found."""
    candidates = [
        "libreoffice",
        "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    for candidate in candidates:
        found = shutil.which(candidate) or (Path(candidate).exists() and candidate)
        if found:
            return str(found)
    return None


def is_libreoffice_available() -> bool:
    """Check if LibreOffice headless conversion is available."""
    return _find_libreoffice() is not None


def convert_hwp_to_hwpx(hwp_path: str | Path, output_dir: str | Path | None = None) -> Path:
    """Convert a .hwp file to .hwpx using LibreOffice headless.

    Args:
        hwp_path: Path to the source .hwp file.
        output_dir: Directory to place the converted file.
                    Defaults to the same directory as hwp_path.

    Returns:
        Path to the resulting .hwpx file.

    Raises:
        LibreOfficeNotFoundError: If LibreOffice is not installed.
        FileNotFoundError: If the input file does not exist.
        RuntimeError: If conversion fails.
    """
    hwp_path = Path(hwp_path)
    if not hwp_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {hwp_path}")
    if hwp_path.suffix.lower() != ".hwp":
        raise ValueError(f"HWP 파일이 아닙니다: {hwp_path}")

    soffice = _find_libreoffice()
    if not soffice:
        raise LibreOfficeNotFoundError(
            "LibreOffice를 찾을 수 없습니다. "
            "HWP → HWPX 변환을 위해 LibreOffice를 설치하세요."
        )

    if output_dir is None:
        output_dir = hwp_path.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # LibreOffice writes the output to output_dir with the same stem
    cmd = [
        soffice,
        "--headless",
        "--convert-to", "hwpx",
        "--outdir", str(output_dir),
        str(hwp_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice 변환 실패 (returncode={result.returncode}):\n"
            f"{result.stderr}"
        )

    converted = output_dir / (hwp_path.stem + ".hwpx")
    if not converted.exists():
        raise RuntimeError(
            f"변환 결과 파일을 찾을 수 없습니다: {converted}\n"
            f"LibreOffice 출력:\n{result.stdout}\n{result.stderr}"
        )

    return converted
