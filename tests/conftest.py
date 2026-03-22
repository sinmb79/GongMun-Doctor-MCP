"""Shared pytest fixtures."""

import shutil
import tempfile
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TMP_ROOT = Path.home() / ".codex" / "memories" / "gongmun-doctor-tests"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def road_repair_hwpx(fixtures_dir: Path) -> Path:
    return fixtures_dir / "test_01_road_repair.hwpx"


@pytest.fixture
def completion_inspect_hwpx(fixtures_dir: Path) -> Path:
    return fixtures_dir / "test_02_completion_inspect.hwpx"


@pytest.fixture
def cooperation_request_hwpx(fixtures_dir: Path) -> Path:
    return fixtures_dir / "test_03_cooperation_request.hwpx"


@pytest.fixture
def workspace_tmpdir() -> Path:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    tmpdir = Path(tempfile.mkdtemp(dir=TMP_ROOT))
    probe = tmpdir / "write_probe.hwpx"
    try:
        try:
            probe.write_bytes(b"probe")
            probe.unlink(missing_ok=True)
        except PermissionError:
            pytest.skip("environment does not allow writing temporary .hwpx files")
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
