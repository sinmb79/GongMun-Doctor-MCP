"""Tests for ClipboardShortcut — global hotkey registration."""

from unittest.mock import patch, MagicMock
import pytest
from gongmun_doctor.clipboard.shortcut import ClipboardShortcut


def test_shortcut_registers_hotkey():
    """Ctrl+Shift+G 핫키 등록 확인."""
    with patch("keyboard.add_hotkey") as mock_hotkey:
        shortcut = ClipboardShortcut()
        shortcut.register()
    mock_hotkey.assert_called_once()
    hotkey_str = mock_hotkey.call_args[0][0]
    assert hotkey_str == "ctrl+shift+g"


def test_shortcut_custom_hotkey():
    with patch("keyboard.add_hotkey") as mock_hotkey:
        shortcut = ClipboardShortcut(hotkey="ctrl+shift+c")
        shortcut.register()
    assert mock_hotkey.call_args[0][0] == "ctrl+shift+c"


def test_shortcut_unregister():
    with patch("keyboard.add_hotkey"):
        shortcut = ClipboardShortcut()
        shortcut.register()
    with patch("keyboard.remove_hotkey") as mock_remove:
        shortcut.unregister()
    mock_remove.assert_called_once_with("ctrl+shift+g")


def test_callback_calls_monitor():
    """핫키 콜백 실행 시 ClipboardMonitor.process_and_replace() 호출."""
    shortcut = ClipboardShortcut.__new__(ClipboardShortcut)
    shortcut._hotkey = "ctrl+shift+g"
    mock_monitor = MagicMock()
    mock_monitor.process_and_replace.return_value = ("orig", "corr", 3)
    shortcut._monitor = mock_monitor

    with patch("gongmun_doctor.clipboard.shortcut._show_toast"):
        shortcut._run()

    mock_monitor.process_and_replace.assert_called_once()


def test_toast_shows_count():
    """토스트에 교정 건수 표시."""
    shortcut = ClipboardShortcut.__new__(ClipboardShortcut)
    shortcut._hotkey = "ctrl+shift+g"
    mock_monitor = MagicMock()
    mock_monitor.process_and_replace.return_value = ("orig", "corr", 5)
    shortcut._monitor = mock_monitor

    with patch("gongmun_doctor.clipboard.shortcut._show_toast") as mock_toast:
        shortcut._run()

    msg = mock_toast.call_args[0][0]
    assert "5" in msg


def test_toast_no_corrections():
    """교정 없을 때 별도 메시지."""
    shortcut = ClipboardShortcut.__new__(ClipboardShortcut)
    shortcut._hotkey = "ctrl+shift+g"
    mock_monitor = MagicMock()
    mock_monitor.process_and_replace.return_value = ("text", "text", 0)
    shortcut._monitor = mock_monitor

    with patch("gongmun_doctor.clipboard.shortcut._show_toast") as mock_toast:
        shortcut._run()

    msg = mock_toast.call_args[0][0]
    assert "없" in msg


def test_toast_on_exception():
    """예외 발생 시 오류 메시지."""
    shortcut = ClipboardShortcut.__new__(ClipboardShortcut)
    shortcut._hotkey = "ctrl+shift+g"
    mock_monitor = MagicMock()
    mock_monitor.process_and_replace.side_effect = RuntimeError("클립보드 오류")
    shortcut._monitor = mock_monitor

    with patch("gongmun_doctor.clipboard.shortcut._show_toast") as mock_toast:
        shortcut._run()

    msg = mock_toast.call_args[0][0]
    assert "오류" in msg
