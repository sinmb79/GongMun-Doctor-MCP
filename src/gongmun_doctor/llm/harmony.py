"""L4 Sentence Harmony Checker — uses LLM to detect redundancy, complexity, passive overuse."""

import re

from gongmun_doctor.llm.runtime import LLMRuntime
from gongmun_doctor.report.markdown import HarmonySuggestion

_SYSTEM_PROMPT = """당신은 한국 공문서 교정 전문가입니다. 주어진 문단에서 아래 네 가지 문제만 찾아 보고하세요.

문제 유형:
- [redundancy] 중복 표현 (예: "미리 사전에", "서로 함께", "약 ~정도")
- [complexity] 지나치게 긴 문장 또는 복문 과다 (한 문장에 접속사 3개 이상)
- [passive] 불필요한 피동형 (예: "~되어지다", "~시켜지다")
- [inconsistency] 문단 내 표현 불일치 (같은 대상에 다른 호칭 사용)

응답 형식 (문제가 있을 때만, 한 줄에 하나):
[유형태그] 원문 표현 → 수정 제안 | 이유

문제가 없으면 반드시 "없음" 한 단어만 출력하세요.
다른 설명은 절대 추가하지 마세요."""

_LINE_PATTERN = re.compile(
    r"\[(redundancy|complexity|passive|inconsistency)\]\s*(.+?)\s*→\s*(.+?)\s*\|\s*(.+)"
)


class HarmonyChecker:
    """Applies L4 harmony analysis to individual paragraphs using a local LLM."""

    def __init__(self, runtime: LLMRuntime) -> None:
        self._runtime = runtime
        self._warnings: list[str] = []

    def check_paragraph(self, text: str, para_idx: int) -> list[HarmonySuggestion]:
        """Analyse one paragraph and return a list of harmony suggestions.

        Returns an empty list if the text is blank, the LLM finds no issues,
        or the LLM fails (graceful fallback).
        """
        if not text or not text.strip():
            return []

        prompt = f"{_SYSTEM_PROMPT}\n\n문단:\n{text}\n\n응답:"
        response = self._runtime.generate(prompt, max_tokens=256, temperature=0.1)
        runtime_warning = getattr(self._runtime, "last_error", None)
        if runtime_warning and runtime_warning not in self._warnings:
            self._warnings.append(runtime_warning)
        return self._parse_response(response, para_idx)

    def consume_warnings(self) -> list[str]:
        warnings = list(self._warnings)
        self._warnings.clear()
        return warnings

    def _parse_response(self, response: str, para_idx: int) -> list[HarmonySuggestion]:
        """Parse LLM response lines into HarmonySuggestion objects."""
        stripped = response.strip()
        if not stripped or stripped.startswith("없음"):
            return []

        suggestions: list[HarmonySuggestion] = []
        for line in stripped.splitlines():
            line = line.strip()
            if not line:
                continue
            m = _LINE_PATTERN.match(line)
            if m:
                issue_type, original, suggestion, reason = m.groups()
                suggestions.append(
                    HarmonySuggestion(
                        paragraph_index=para_idx,
                        issue_type=issue_type,
                        original=original.strip(),
                        suggestion=suggestion.strip(),
                        reason=reason.strip(),
                    )
                )
        return suggestions
