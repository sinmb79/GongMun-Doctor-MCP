"""Tests for ClipboardMonitor — clipboard read/write + PII gate + correction."""

from unittest.mock import patch
import pytest
from gongmun_doctor.clipboard.monitor import ClipboardMonitor


@pytest.fixture
def monitor():
    return ClipboardMonitor()


def test_read_clipboard(monitor):
    with patch("pyperclip.paste", return_value="테스트 텍스트"):
        text = monitor.read()
    assert text == "테스트 텍스트"


def test_write_clipboard(monitor):
    with patch("pyperclip.copy") as mock_copy:
        monitor.write("교정된 텍스트")
    mock_copy.assert_called_once_with("교정된 텍스트")


def test_process_empty_clipboard(monitor):
    with patch("pyperclip.paste", return_value=""):
        original, corrected, count = monitor.process_and_replace()
    assert count == 0
    assert original == corrected


def test_process_whitespace_only(monitor):
    with patch("pyperclip.paste", return_value="   \n"):
        original, corrected, count = monitor.process_and_replace()
    assert count == 0


def test_process_masks_pii_gate1_주민번호(monitor):
    """Gate 1: 주민등록번호 마스킹."""
    text = "홍길동 900101-1234567 담당자입니다"
    with patch("pyperclip.paste", return_value=text):
        with patch("pyperclip.copy") as mock_copy:
            monitor.process_and_replace()
    result = mock_copy.call_args[0][0]
    assert "900101-1234567" not in result
    assert "[주민번호]" in result


def test_process_masks_pii_gate2_전화번호(monitor):
    """Gate 2: 전화번호 마스킹."""
    text = "연락처 010-1234-5678 로 연락 바랍니다"
    with patch("pyperclip.paste", return_value=text):
        with patch("pyperclip.copy") as mock_copy:
            monitor.process_and_replace()
    result = mock_copy.call_args[0][0]
    assert "010-1234-5678" not in result


def test_process_masks_pii_gate3_이메일(monitor):
    """Gate 3: 이메일 마스킹."""
    text = "문의: hong@example.com 으로 보내주세요"
    with patch("pyperclip.paste", return_value=text):
        with patch("pyperclip.copy") as mock_copy:
            monitor.process_and_replace()
    result = mock_copy.call_args[0][0]
    assert "hong@example.com" not in result


def test_process_applies_correction(monitor):
    """교정 규칙 적용 확인 (할려고 → 하려고)."""
    text = "업무를 할려고 합니다"
    with patch("pyperclip.paste", return_value=text):
        with patch("pyperclip.copy") as mock_copy:
            original, corrected, count = monitor.process_and_replace()
    assert mock_copy.called
    assert corrected != text  # 교정됨
    assert count > 0


def test_process_returns_tuple(monitor):
    with patch("pyperclip.paste", return_value="정상 텍스트"):
        with patch("pyperclip.copy"):
            result = monitor.process_and_replace()
    assert isinstance(result, tuple)
    assert len(result) == 3  # (original, corrected, count)
