"""Tests for rule loading and rule content validation."""

import pytest
from gongmun_doctor.rules.loader import load_rules, load_rules_by_layer, CorrectionRule


class TestRuleLoading:
    def test_load_rules_returns_list(self):
        rules = load_rules()
        assert isinstance(rules, list)

    def test_load_rules_nonempty(self):
        rules = load_rules()
        assert len(rules) > 0

    def test_total_rule_count_meets_minimum(self):
        """Phase 1 DoD: 30+ L1, 10+ L2, 20+ L3."""
        rules = load_rules()
        l1 = [r for r in rules if r.layer == "L1_spelling"]
        l2 = [r for r in rules if r.layer == "L2_grammar"]
        l3 = [r for r in rules if r.layer == "L3_official_style"]
        assert len(l1) >= 30, f"L1 has only {len(l1)} rules"
        assert len(l2) >= 10, f"L2 has only {len(l2)} rules"
        assert len(l3) >= 20, f"L3 has only {len(l3)} rules"

    def test_each_rule_has_required_fields(self):
        rules = load_rules()
        for r in rules:
            assert r.id, f"Rule missing id: {r}"
            assert r.rule_type in ("exact_replace", "regex_replace"), \
                f"Unknown rule_type: {r.rule_type} in {r.id}"
            assert r.search, f"Rule missing search pattern: {r.id}"
            assert r.replace is not None, f"Rule missing replace: {r.id}"
            assert r.desc, f"Rule missing desc: {r.id}"
            assert r.source, f"Rule missing source: {r.id}"
            assert r.layer, f"Rule missing layer: {r.id}"

    def test_rule_ids_are_unique(self):
        rules = load_rules()
        ids = [r.id for r in rules]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs found"

    def test_load_rules_by_layer_filters(self):
        l1_only = load_rules_by_layer(layers=["L1_spelling"])
        assert all(r.layer == "L1_spelling" for r in l1_only)
        assert len(l1_only) > 0

    def test_load_rules_by_layer_multiple(self):
        rules = load_rules_by_layer(layers=["L1_spelling", "L2_grammar"])
        layers = {r.layer for r in rules}
        assert "L1_spelling" in layers
        assert "L2_grammar" in layers
        assert "L3_official_style" not in layers

    def test_load_rules_by_layer_none_returns_all(self):
        all_rules = load_rules()
        none_filtered = load_rules_by_layer(layers=None)
        assert len(all_rules) == len(none_filtered)


class TestL1SpellingRules:
    def test_sp001_시행알림(self):
        from gongmun_doctor.engine import _apply_rule_to_text
        rule = next(r for r in load_rules() if r.id == "SP-001")
        result, count = _apply_rule_to_text("도로 시행알림 공고", rule)
        assert result == "도로 시행 알림 공고"
        assert count == 1

    def test_sp006_할려고(self):
        from gongmun_doctor.engine import _apply_rule_to_text
        rule = next(r for r in load_rules() if r.id == "SP-006")
        result, count = _apply_rule_to_text("시행할려고 합니다", rule)
        assert result == "시행하려고 합니다"
        assert count == 1

    def test_sp012_됬(self):
        from gongmun_doctor.engine import _apply_rule_to_text
        rule = next(r for r in load_rules() if r.id == "SP-012")
        result, count = _apply_rule_to_text("완료됬습니다", rule)
        assert result == "완료됐습니다"
        assert count == 1


class TestL3OfficialStyleRules:
    def test_os005_되시기바랍니다(self):
        from gongmun_doctor.engine import _apply_rule_to_text
        rule = next(r for r in load_rules() if r.id == "OS-005")
        result, count = _apply_rule_to_text("참고되시기 바랍니다", rule)
        assert count == 1
        assert "됩니다" in result

    def test_os007_부탁드립니다(self):
        from gongmun_doctor.engine import _apply_rule_to_text
        rule = next(r for r in load_rules() if r.id == "OS-007")
        result, count = _apply_rule_to_text("협조 부탁드립니다", rule)
        assert count == 1
        assert "바랍니다" in result

    def test_os017_하기와같이(self):
        from gongmun_doctor.engine import _apply_rule_to_text
        rule = next(r for r in load_rules() if r.id == "OS-017")
        result, count = _apply_rule_to_text("하기와 같이 처리하겠습니다", rule)
        assert count == 1
        assert "다음과 같이" in result


class TestL2GrammarRules:
    def test_gr006_이중피동(self):
        from gongmun_doctor.engine import _apply_rule_to_text
        rule = next(r for r in load_rules() if r.id == "GR-006")
        result, count = _apply_rule_to_text("처리되어지고 있습니다", rule)
        assert count == 1
        assert "되어지" not in result

    def test_gr009_해야됩니다(self):
        from gongmun_doctor.engine import _apply_rule_to_text
        rule = next(r for r in load_rules() if r.id == "GR-009")
        result, count = _apply_rule_to_text("제출해야됩니다", rule)
        assert count == 1
        assert "하여야 합니다" in result
