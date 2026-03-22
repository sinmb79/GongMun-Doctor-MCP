"""Mock-based tests for HwpCorrectionBridge — runs on all platforms."""

import pytest
from gongmun_doctor.hwp_com.bridge import HwpCorrectionBridge
from gongmun_doctor.rules.loader import CorrectionRule


def _make_rule(id: str, rule_type: str, search: str, replace: str) -> CorrectionRule:
    return CorrectionRule(
        id=id,
        rule_type=rule_type,
        search=search,
        replace=replace,
        desc="test",
        source="test",
        layer="L1_spelling",
    )


class MockHwpController:
    """Mock controller for testing without a live 한글 instance."""

    def __init__(self, text: str = ""):
        self._text = text
        self.replacements: list[tuple[str, str]] = []
        self.track_changes_enabled = False

    def get_text_all(self) -> str:
        return self._text

    def find_and_replace(self, find: str, replace: str) -> None:
        self.replacements.append((find, replace))

    def enable_track_changes(self) -> None:
        self.track_changes_enabled = True


class TestHwpCorrectionBridge:
    def _bridge(self, text: str, rules: list[CorrectionRule]) -> tuple[HwpCorrectionBridge, MockHwpController]:
        ctrl = MockHwpController(text)
        bridge = HwpCorrectionBridge(ctrl, rules)
        return bridge, ctrl

    def test_report_only_returns_corrections_without_replacing(self):
        rules = [_make_rule("SP-001", "exact_replace", "시행알림", "시행 알림")]
        bridge, ctrl = self._bridge("도로 시행알림 공고", rules)

        items = bridge.run_correction(mode="report_only")

        assert len(items) == 1
        assert items[0].rule_id == "SP-001"
        assert ctrl.replacements == []  # nothing replaced in report_only mode

    def test_track_changes_mode_enables_tracking_and_replaces(self):
        rules = [_make_rule("SP-001", "exact_replace", "시행알림", "시행 알림")]
        bridge, ctrl = self._bridge("도로 시행알림 공고", rules)

        bridge.run_correction(mode="track_changes")

        assert ctrl.track_changes_enabled is True
        assert ("시행알림", "시행 알림") in ctrl.replacements

    def test_direct_mode_replaces_without_tracking(self):
        rules = [_make_rule("SP-001", "exact_replace", "시행알림", "시행 알림")]
        bridge, ctrl = self._bridge("도로 시행알림 공고", rules)

        bridge.run_correction(mode="direct")

        assert ctrl.track_changes_enabled is False
        assert ("시행알림", "시행 알림") in ctrl.replacements

    def test_regex_rules_skipped_in_com_mode(self):
        rules = [_make_rule("GR-001", "regex_replace", r"(\d+)원정", r"\1원")]
        bridge, ctrl = self._bridge("1000원정 납부", rules)

        items = bridge.run_correction(mode="direct")

        # correct_text detects the match and returns an item for reporting,
        # but the bridge must NOT call find_and_replace for regex rules
        assert len(items) == 1           # regex match IS reported
        assert ctrl.replacements == []   # but NOT written to HWP document

    def test_no_matching_rules_returns_empty(self):
        rules = [_make_rule("SP-001", "exact_replace", "없는단어", "교정")]
        bridge, ctrl = self._bridge("깨끗한 문장", rules)

        items = bridge.run_correction(mode="report_only")

        assert items == []

    def test_multiple_matching_rules_all_applied(self):
        rules = [
            _make_rule("SP-001", "exact_replace", "시행알림", "시행 알림"),
            _make_rule("OS-001", "exact_replace", "했습니다", "하였습니다"),
        ]
        bridge, ctrl = self._bridge("시행알림 공고입니다. 잘 했습니다.", rules)

        bridge.run_correction(mode="direct")

        assert ("시행알림", "시행 알림") in ctrl.replacements
        assert ("했습니다", "하였습니다") in ctrl.replacements

    def test_clean_text_returns_empty_and_no_replacements(self):
        rules = [_make_rule("SP-001", "exact_replace", "시행알림", "시행 알림")]
        bridge, ctrl = self._bridge("깨끗한 공문서입니다.", rules)

        items = bridge.run_correction(mode="track_changes")

        assert items == []
        assert ctrl.replacements == []
