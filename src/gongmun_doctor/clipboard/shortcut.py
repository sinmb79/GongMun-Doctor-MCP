"""ClipboardShortcut — global hotkey that triggers clipboard correction.

Registers Ctrl+Shift+G (configurable).  When fired:
  1. Reads clipboard
  2. Runs Gate 1~4 + correction via ClipboardMonitor
  3. Writes result back to clipboard
  4. Shows a toast notification

Windows-only (keyboard library requires admin or INPUT access on Windows).
"""

from __future__ import annotations

import threading


def _show_toast(message: str) -> None:
    """Show a Windows toast notification, falling back to print."""
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast("공문닥터", message, duration=3, threaded=True)
    except ImportError:
        print(f"[공문닥터] {message}")


class ClipboardShortcut:
    """Global hotkey (default: Ctrl+Shift+G) for clipboard correction.

    Args:
        hotkey: Hotkey string accepted by the ``keyboard`` library.
    """

    DEFAULT_HOTKEY = "ctrl+shift+g"

    def __init__(self, hotkey: str = DEFAULT_HOTKEY) -> None:
        self._hotkey = hotkey
        from gongmun_doctor.clipboard.monitor import ClipboardMonitor
        self._monitor = ClipboardMonitor()

    # ── public API ───────────────────────────────────────────────────────

    def register(self) -> None:
        """Register the global hotkey with the keyboard library."""
        import keyboard
        keyboard.add_hotkey(self._hotkey, self._callback)

    def unregister(self) -> None:
        """Remove the registered hotkey."""
        import keyboard
        keyboard.remove_hotkey(self._hotkey)

    # ── internal ─────────────────────────────────────────────────────────

    def _callback(self) -> None:
        """Hotkey callback — run correction in a daemon thread."""
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        try:
            _original, _corrected, count = self._monitor.process_and_replace()
            if count > 0:
                _show_toast(f"{count}건 교정 완료. Ctrl+V로 붙여넣으세요.")
            else:
                _show_toast("교정할 항목이 없습니다.")
        except Exception as exc:  # noqa: BLE001
            _show_toast(f"교정 오류: {exc}")
