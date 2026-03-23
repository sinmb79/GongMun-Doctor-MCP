"""End-to-end integration tests: clipboard → Gate 1~4 → correction pipeline."""

from unittest.mock import patch
from gongmun_doctor.clipboard.monitor import ClipboardMonitor


def test_full_pipeline_pii_then_correction():
    """주민번호(Gate1) + 맞춤법 오류 동시 처리."""
    monitor = ClipboardMonitor()
    input_text = "900101-1234567 담당자가 할려고 합니다"
    with patch("pyperclip.paste", return_value=input_text):
        with patch("pyperclip.copy") as mock_copy:
            _orig, corrected, count = monitor.process_and_replace()
    result = mock_copy.call_args[0][0]
    assert "900101-1234567" not in result   # Gate 1 통과
    assert count > 0                        # 교정 적용됨


def test_empty_clipboard_no_crash():
    monitor = ClipboardMonitor()
    with patch("pyperclip.paste", return_value=""):
        original, corrected, count = monitor.process_and_replace()
    assert count == 0
    assert original == corrected


def test_clean_text_passes_unchanged():
    """교정 필요 없는 깨끗한 공문 텍스트."""
    monitor = ClipboardMonitor()
    text = "위 사항을 알려드리오니 업무에 참고하시기 바랍니다."
    with patch("pyperclip.paste", return_value=text):
        with patch("pyperclip.copy") as mock_copy:
            _orig, corrected, count = monitor.process_and_replace()
    # 교정 0건이면 copy는 여전히 호출되지만 텍스트는 동일
    assert corrected == text


def test_multiple_pii_types():
    """여러 PII 유형 동시 마스킹."""
    monitor = ClipboardMonitor()
    text = "홍길동(900101-1234567, 010-1234-5678, hong@test.com) 담당자"
    with patch("pyperclip.paste", return_value=text):
        with patch("pyperclip.copy") as mock_copy:
            monitor.process_and_replace()
    result = mock_copy.call_args[0][0]
    assert "900101-1234567" not in result
    assert "010-1234-5678" not in result
    assert "hong@test.com" not in result
