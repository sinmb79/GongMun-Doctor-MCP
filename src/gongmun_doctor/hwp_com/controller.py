"""
HWP OLE/COM Controller — interfaces with running 한글 program via COM automation.

Requirements:
    pip install pywin32

Platform: Windows only. On other platforms, importing this module is safe,
but instantiating HwpController raises ImportError.

COM threading note: All methods must be called from the same STA thread.
Call pythoncom.CoInitialize() before creating an instance in a new thread.
"""

from __future__ import annotations


class HwpController:
    """Controls a running instance of 한컴오피스 한글 via COM automation.

    Usage::

        ctrl = HwpController()
        ctrl.connect()          # connect to running 한글 or launch new
        text = ctrl.get_text_all()
        ctrl.find_and_replace("오류", "수정")
        ctrl.save()
    """

    def __init__(self) -> None:
        try:
            import win32com.client  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "pywin32가 설치되어 있지 않습니다.\n"
                "설치 명령: pip install pywin32"
            ) from e
        self._hwp = None

    # ── connection ────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Connect to a running 한글 instance, or launch a new one.

        Returns True if connection succeeded.
        Raises RuntimeError if 한글 is not installed.
        """
        import win32com.client as win32

        try:
            self._hwp = win32.GetActiveObject("HWPFrame.HwpObject")
        except Exception:
            try:
                self._hwp = win32.Dispatch("HWPFrame.HwpObject")
            except Exception as e:
                raise RuntimeError(
                    "한글 프로그램에 연결할 수 없습니다.\n"
                    "한컴오피스 한글이 설치되어 있는지 확인해 주세요."
                ) from e

        try:
            # Suppress file-path security dialogs (optional DLL, ignored if absent)
            self._hwp.RegisterModule(
                "FilePathCheckDLL", "FilePathCheckerModuleExample"
            )
        except Exception:
            pass  # DLL not present — tool still works, user may see dialogs

        return True

    def is_connected(self) -> bool:
        """Return True if the COM object is live."""
        if self._hwp is None:
            return False
        try:
            _ = self._hwp.Path
            return True
        except Exception:
            return False

    # ── document info ─────────────────────────────────────────────────────

    def get_document_path(self) -> str:
        """Return the file path of the currently open document."""
        self._require_connection()
        return self._hwp.Path

    # ── text extraction ───────────────────────────────────────────────────

    def get_text_all(self) -> str:
        """Extract all text from the current document as a single string.

        Paragraphs are separated by newlines.
        """
        self._require_connection()
        self._hwp.InitScan()
        parts: list[str] = []
        try:
            while True:
                state, text = self._hwp.GetText()
                if text:
                    parts.append(text)
                if state == 0:  # end of document
                    break
        finally:
            self._hwp.ReleaseScan()
        return "\n".join(parts)

    # ── editing ───────────────────────────────────────────────────────────

    def find_and_replace(self, find_text: str, replace_text: str) -> None:
        """Find and replace text throughout the document.

        Uses HWP's built-in AllReplace action. No-op if find_text is not found.
        Does NOT support regex — plain text only.
        """
        self._require_connection()
        pset = self._hwp.HParameterSet.HFindReplace
        self._hwp.HAction.GetDefault("AllReplace", pset.HSet)
        pset.FindString = find_text
        pset.ReplaceString = replace_text
        pset.IgnoreCase = 0
        pset.WholeWordOnly = 0
        pset.Direction = 0    # forward search
        pset.ReplaceMode = 1  # replace all
        self._hwp.HAction.Execute("AllReplace", pset.HSet)

    def enable_track_changes(self) -> None:
        """Enable track changes (변경 내용 추적).

        Checks current state first to avoid toggling it off accidentally.
        """
        self._require_connection()
        try:
            state = self._hwp.GetTrackChange()
            if not state:
                self._hwp.HAction.Run("TrackChange")
        except Exception:
            # Fallback: just run the toggle command
            self._hwp.HAction.Run("TrackChange")

    def save(self) -> None:
        """Save the current document."""
        self._require_connection()
        self._hwp.HAction.Run("FileSave")

    # ── internal ─────────────────────────────────────────────────────────

    def _require_connection(self) -> None:
        if not self.is_connected():
            raise RuntimeError(
                "한글에 연결되어 있지 않습니다. connect()를 먼저 호출하세요."
            )
