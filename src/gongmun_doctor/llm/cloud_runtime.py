"""Cloud LLM API runtime — Claude / OpenAI / Gemini.

Implements the same generate() interface as LLMRuntime so HarmonyChecker
works without any changes.

API keys are read from environment variables:
  Claude  → ANTHROPIC_API_KEY
  OpenAI  → OPENAI_API_KEY
  Gemini  → GOOGLE_API_KEY

PII in prompts is automatically masked by PIIMasker before transmission.
"""

from __future__ import annotations

import os

_ENV_KEYS = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}

_DEFAULT_MODELS = {
    "claude": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-1.5-flash",
}

_SUPPORTED = frozenset(_ENV_KEYS)


class CloudLLMRuntime:
    """Cloud LLM backend with the same generate() interface as LLMRuntime.

    Args:
        provider: One of "claude", "openai", "gemini".
        model:    Override the default model for the provider.
    """

    def __init__(self, provider: str, model: str | None = None) -> None:
        provider = provider.lower()
        if provider not in _SUPPORTED:
            raise ValueError(
                f"지원하지 않는 제공자: '{provider}'. "
                f"사용 가능: {', '.join(sorted(_SUPPORTED))}"
            )

        env_key = _ENV_KEYS[provider]
        api_key = os.environ.get(env_key, "").strip()
        if not api_key:
            raise EnvironmentError(
                f"환경변수 {env_key}가 설정되지 않았습니다.\n"
                f"설정 방법: set {env_key}=<your-api-key>  (Windows)\n"
                f"           export {env_key}=<your-api-key>  (Linux/macOS)"
            )

        self._provider = provider
        self._api_key = api_key
        self._model = model or _DEFAULT_MODELS[provider]
        self._last_error: str | None = None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.1) -> str:
        """Call cloud API. Returns empty string on any error (graceful fallback).

        PII in the prompt is automatically masked before transmission.
        """
        from gongmun_doctor.llm.pii_masker import PIIMasker
        safe_prompt = PIIMasker().mask(prompt)
        self._last_error = None
        try:
            if self._provider == "claude":
                return self._generate_claude(safe_prompt, max_tokens, temperature)
            elif self._provider == "openai":
                return self._generate_openai(safe_prompt, max_tokens, temperature)
            elif self._provider == "gemini":
                return self._generate_gemini(safe_prompt, max_tokens, temperature)
        except Exception as exc:
            self._last_error = (
                f"{self._provider} model '{self._model}' request failed: {exc}"
            )
            return ""

    def _generate_claude(self, prompt: str, max_tokens: int, temperature: float) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic 패키지가 설치되지 않았습니다.\n"
                "설치: pip install gongmun-doctor[cloud]"
            )
        client = anthropic.Anthropic(api_key=self._api_key)
        msg = client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai 패키지가 설치되지 않았습니다.\n"
                "설치: pip install gongmun-doctor[cloud]"
            )
        client = openai.OpenAI(api_key=self._api_key)
        resp = client.chat.completions.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()

    def _generate_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai 패키지가 설치되지 않았습니다.\n"
                "설치: pip install gongmun-doctor[cloud]"
            )
        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(
            self._model,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        resp = model.generate_content(prompt)
        return resp.text.strip()
