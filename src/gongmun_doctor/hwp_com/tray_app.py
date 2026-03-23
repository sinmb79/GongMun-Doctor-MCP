"""
System tray application for 공문닥터 한글 plugin mode.

Sits in the Windows system tray. Responds to Ctrl+Shift+G to correct
the currently open 한글 document. Requires pywin32, pystray, Pillow, keyboard.

Usage::

    from gongmun_doctor.hwp_com.tray_app import TrayApp
    app = TrayApp(hotkey="ctrl+shift+g", mode="track_changes")
    app.run()  # blocks until user clicks 종료
"""

from __future__ import annotations

import threading


def _create_icon_image():
    """Create a simple 64x64 green square as the tray icon."""
    try:
        from PIL import Image, ImageDraw
    except ImportError as e:
        raise ImportError(
            "Pillow가 설치되어 있지 않습니다.\n설치 명령: pip install Pillow"
        ) from e
    img = Image.new("RGB", (64, 64), color="#38a169")
    draw = ImageDraw.Draw(img)
    draw.text((18, 20), "공문", fill="white")
    return img


class TrayApp:
    """System tray application for 공문닥터 한글 plugin mode.

    Args:
        hotkey: Global hotkey string (e.g. "ctrl+shift+g").
        mode:   Correction mode — "track_changes" | "direct".
        rules:  Pre-loaded list of CorrectionRule. If None, loads all rules.
    """

    def __init__(
        self,
        hotkey: str = "ctrl+shift+g",
        mode: str = "track_changes",
        rules=None,
    ) -> None:
        self._hotkey = hotkey
        self._mode = mode
        self._rules = rules
        self._icon = None
        self._status = "연결 안 됨"

    # ── public API ────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start the tray app. Blocks until user clicks 종료."""
        try:
            import pystray
        except ImportError as e:
            raise ImportError(
                "pystray가 설치되어 있지 않습니다.\n설치 명령: pip install pystray"
            ) from e
        try:
            import keyboard as kb
        except ImportError as e:
            raise ImportError(
                "keyboard가 설치되어 있지 않습니다.\n설치 명령: pip install keyboard"
            ) from e

        if self._rules is None:
            from gongmun_doctor.rules.loader import load_rules_by_layer
            self._rules = load_rules_by_layer()

        kb.add_hotkey(self._hotkey, self._on_hotkey)

        # Clipboard mode: separate hotkey Ctrl+Shift+C
        try:
            from gongmun_doctor.clipboard.shortcut import ClipboardShortcut
            self._clipboard_shortcut = ClipboardShortcut(hotkey="ctrl+shift+c")
            self._clipboard_shortcut.register()
        except ImportError:
            self._clipboard_shortcut = None

        menu = pystray.Menu(
            pystray.MenuItem("교정 실행 (변경추적)", lambda: self._trigger("track_changes")),
            pystray.MenuItem("교정 실행 (직접 적용)", lambda: self._trigger("direct")),
            pystray.MenuItem("클립보드 교정 (Ctrl+Shift+C)", self._trigger_clipboard),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda text: f"한글 상태: {self._status}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", self._quit),
        )

        self._icon = pystray.Icon(
            name="gongmun-doctor",
            icon=_create_icon_image(),
            title="공문닥터",
            menu=menu,
        )
        self._icon.run()

    # ── internal ─────────────────────────────────────────────────────────

    def _on_hotkey(self) -> None:
        """Called from keyboard listener thread on hotkey press."""
        threading.Thread(target=self._trigger, args=(self._mode,), daemon=True).start()

    def _trigger(self, mode: str) -> None:
        """Run correction in a worker thread (COM STA safe)."""
        _coinit = False
        try:
            import pythoncom
            pythoncom.CoInitialize()
            _coinit = True
        except ImportError:
            pass  # pywin32 not installed — error will surface in controller

        try:
            from gongmun_doctor.hwp_com.controller import HwpController
            from gongmun_doctor.hwp_com.bridge import HwpCorrectionBridge

            ctrl = HwpController()
            ctrl.connect()
            self._status = "연결됨"
            self._update_icon_tooltip()

            bridge = HwpCorrectionBridge(ctrl, self._rules)
            items = bridge.run_correction(mode=mode)

            self._notify(f"교정 완료: {len(items)}건")

        except RuntimeError as e:
            self._notify(f"오류: {e}")
            self._status = "연결 실패"
            self._update_icon_tooltip()
        except Exception as e:
            self._notify(f"알 수 없는 오류: {e}")
        finally:
            if _coinit:
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _notify(self, message: str) -> None:
        """Show a system tray notification."""
        if self._icon:
            self._icon.notify(message, "공문닥터")

    def _update_icon_tooltip(self) -> None:
        if self._icon:
            self._icon.title = f"공문닥터 — {self._status}"

    def _trigger_clipboard(self) -> None:
        """Run clipboard correction from tray menu."""
        if self._clipboard_shortcut is not None:
            threading.Thread(target=self._clipboard_shortcut._run, daemon=True).start()

    def _quit(self) -> None:
        if self._clipboard_shortcut is not None:
            try:
                self._clipboard_shortcut.unregister()
            except Exception:
                pass
        if self._icon:
            self._icon.stop()
