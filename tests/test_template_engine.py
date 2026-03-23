"""Tests for TemplateEngine."""

from pathlib import Path
import pytest
from gongmun_doctor.agents.administrative.template_engine import TemplateEngine

TEMPLATE_DIR = (
    Path(__file__).parent.parent
    / "src" / "gongmun_doctor" / "agents" / "administrative" / "templates"
)


@pytest.fixture
def engine():
    return TemplateEngine(TEMPLATE_DIR)


def test_load_templates(engine):
    assert len(engine.templates) >= 10


def test_load_all_50(engine):
    assert len(engine.templates) >= 50


def test_match_by_trigger_협조(engine):
    results = engine.match("협조 요청 공문 써줘")
    assert len(results) >= 1
    names = [r["name"] for r in results]
    assert any("협조" in n for n in names)


def test_match_by_trigger_착공(engine):
    results = engine.match("착공 알림 공문")
    assert len(results) >= 1


def test_match_returns_empty_for_unknown(engine):
    results = engine.match("xyzqrnothing")
    assert results == []


def test_get_variables_returns_list(engine):
    # pick first template
    tmpl_id = next(iter(engine.templates))
    variables = engine.get_variables(tmpl_id)
    assert isinstance(variables, list)
    for v in variables:
        assert "key" in v
        assert "label" in v


def test_render_substitutes_variables(engine):
    results = engine.match("협조 요청")
    assert results, "협조 요청 트리거 템플릿 없음"
    tmpl = results[0]
    rendered = engine.render(tmpl["id"], {"수신기관": "테스트기관장"})
    assert "테스트기관장" in rendered


def test_render_leaves_missing_vars(engine):
    tmpl_id = next(iter(engine.templates))
    rendered = engine.render(tmpl_id, {})
    # body should still contain {{...}} placeholders if variables exist
    tmpl = engine.templates[tmpl_id]
    if tmpl.get("variables"):
        assert "{{" in rendered


def test_list_templates_all(engine):
    all_tmpls = engine.list_templates()
    assert len(all_tmpls) >= 50


def test_list_templates_by_category(engine):
    result = engine.list_templates(category="일반행정")
    assert len(result) >= 15
