"""Mock-based tests for CloudLLMRuntime — runs without real API keys."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch


def test_unknown_provider_raises():
    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime
    with pytest.raises(ValueError, match="지원하지 않는"):
        CloudLLMRuntime(provider="unknown")


def test_missing_api_key_raises(monkeypatch):
    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        CloudLLMRuntime(provider="claude")


def test_claude_generate_calls_sdk(monkeypatch):
    """CloudLLMRuntime.generate() calls anthropic SDK and returns text."""
    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime

    mock_anthropic = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="[redundancy] 미리 사전에 → 미리 | 중복")]
    mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_msg

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", mock_anthropic)

    runtime = CloudLLMRuntime(provider="claude")
    result = runtime.generate("테스트 프롬프트")

    assert result == "[redundancy] 미리 사전에 → 미리 | 중복"
    mock_anthropic.Anthropic.return_value.messages.create.assert_called_once()


def test_openai_generate_calls_sdk(monkeypatch):
    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime

    mock_openai = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "없음"
    mock_openai.OpenAI.return_value.chat.completions.create.return_value.choices = [mock_choice]

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", mock_openai)

    runtime = CloudLLMRuntime(provider="openai")
    result = runtime.generate("테스트")

    assert result == "없음"


def test_gemini_generate_calls_sdk(monkeypatch):
    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime

    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value.generate_content.return_value.text = "없음"

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    # google.generativeai is accessed as 'google.generativeai'
    mock_google = MagicMock()
    mock_google.generativeai = mock_genai
    monkeypatch.setitem(sys.modules, "google", mock_google)
    monkeypatch.setitem(sys.modules, "google.generativeai", mock_genai)

    runtime = CloudLLMRuntime(provider="gemini")
    result = runtime.generate("테스트")

    assert result == "없음"


def test_generate_returns_empty_on_exception(monkeypatch):
    """generate() must return '' (not raise) on any API error — graceful fallback."""
    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime

    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic.return_value.messages.create.side_effect = Exception("API error")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", mock_anthropic)

    runtime = CloudLLMRuntime(provider="claude")
    result = runtime.generate("테스트")

    assert result == ""


def test_pii_is_masked_before_api_call(monkeypatch):
    """Verify PIIMasker is applied: phone number in prompt must not reach the API."""
    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime

    captured_prompts = []

    mock_anthropic = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="없음")]

    def capture_create(**kwargs):
        captured_prompts.append(kwargs["messages"][0]["content"])
        return mock_msg

    mock_anthropic.Anthropic.return_value.messages.create.side_effect = capture_create

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", mock_anthropic)

    runtime = CloudLLMRuntime(provider="claude")
    runtime.generate("담당자 연락처: 010-1234-5678 확인 바랍니다.")

    assert len(captured_prompts) == 1
    assert "010-1234-5678" not in captured_prompts[0]
    assert "[전화번호]" in captured_prompts[0]


def test_custom_model_override(monkeypatch):
    """Custom model parameter is passed to API."""
    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime

    mock_anthropic = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="없음")]
    mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_msg

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", mock_anthropic)

    runtime = CloudLLMRuntime(provider="claude", model="claude-opus-4-6")
    runtime.generate("테스트")

    call_kwargs = mock_anthropic.Anthropic.return_value.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-opus-4-6"
