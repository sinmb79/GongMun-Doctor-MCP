"""Shared pytest fixtures."""

import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
