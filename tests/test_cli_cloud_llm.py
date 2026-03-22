"""Tests for --cloud-llm CLI flag (no real API calls)."""

import pytest


def test_cloud_llm_flag_parsed_correctly():
    from gongmun_doctor.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["correct", "doc.hwpx", "--cloud-llm", "claude"])
    assert args.cloud_llm == "claude"


def test_cloud_llm_default_is_none():
    from gongmun_doctor.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["correct", "doc.hwpx"])
    assert args.cloud_llm is None


def test_cloud_llm_all_providers_accepted():
    from gongmun_doctor.cli import build_parser
    parser = build_parser()
    for provider in ["claude", "openai", "gemini"]:
        args = parser.parse_args(["correct", "doc.hwpx", "--cloud-llm", provider])
        assert args.cloud_llm == provider


def test_cloud_llm_invalid_provider_rejected():
    from gongmun_doctor.cli import build_parser
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["correct", "doc.hwpx", "--cloud-llm", "invalid"])


def test_plugin_cloud_llm_flag_accepted():
    from gongmun_doctor.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["plugin", "--cloud-llm", "openai"])
    assert args.cloud_llm == "openai"
