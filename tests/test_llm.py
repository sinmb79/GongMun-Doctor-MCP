"""Tests for LLM runtime — all tests use mocks, no real model required."""

import sys
import importlib
import pytest
from unittest.mock import MagicMock, patch


class TestLLMRuntime:
    def _clean_module_cache(self):
        """Remove cached llm modules to avoid cross-test pollution."""
        for key in list(sys.modules):
            if "gongmun_doctor.llm" in key:
                sys.modules.pop(key, None)

    def test_import(self):
        from gongmun_doctor.llm.runtime import LLMRuntime
        assert LLMRuntime is not None

    def test_llama_cpp_not_installed_raises_helpful_error(self):
        self._clean_module_cache()
        with patch.dict("sys.modules", {"llama_cpp": None}):
            mod = importlib.import_module("gongmun_doctor.llm.runtime")
            with pytest.raises(ImportError, match="llama-cpp-python"):
                mod.LLMRuntime("/nonexistent/model.gguf")
        self._clean_module_cache()

    def test_model_file_not_found_raises(self):
        fake_llama = MagicMock()
        fake_llama.Llama.side_effect = Exception("model not found")
        self._clean_module_cache()
        with patch.dict("sys.modules", {"llama_cpp": fake_llama}):
            mod = importlib.import_module("gongmun_doctor.llm.runtime")
            with pytest.raises(RuntimeError, match="모델 파일"):
                mod.LLMRuntime("/nonexistent/model.gguf")
        self._clean_module_cache()

    def test_generate_returns_string(self):
        from gongmun_doctor.llm.runtime import LLMRuntime
        rt = LLMRuntime.__new__(LLMRuntime)
        rt._model = MagicMock(return_value={"choices": [{"text": "응답 텍스트"}]})
        result = rt.generate("테스트 프롬프트")
        assert isinstance(result, str)
        assert result == "응답 텍스트"

    def test_generate_on_exception_returns_empty(self):
        from gongmun_doctor.llm.runtime import LLMRuntime
        rt = LLMRuntime.__new__(LLMRuntime)
        rt._model = MagicMock(side_effect=RuntimeError("추론 실패"))
        result = rt.generate("프롬프트")
        assert result == ""


class TestHarmonyChecker:
    def _make_runtime(self, response: str):
        from gongmun_doctor.llm.runtime import LLMRuntime
        rt = LLMRuntime.__new__(LLMRuntime)
        rt._model = MagicMock(return_value={"choices": [{"text": response}]})
        return rt

    def test_import(self):
        from gongmun_doctor.llm.harmony import HarmonyChecker
        assert HarmonyChecker is not None

    def test_check_returns_list(self):
        from gongmun_doctor.llm.harmony import HarmonyChecker
        rt = self._make_runtime("[redundancy] 미리 사전에 → 사전에 | 중복 표현")
        checker = HarmonyChecker(rt)
        results = checker.check_paragraph("미리 사전에 검토하였습니다.", para_idx=0)
        assert isinstance(results, list)

    def test_empty_response_returns_empty_list(self):
        from gongmun_doctor.llm.harmony import HarmonyChecker
        rt = self._make_runtime("")
        checker = HarmonyChecker(rt)
        results = checker.check_paragraph("올바른 문장입니다.", para_idx=0)
        assert results == []

    def test_없음_response_returns_empty_list(self):
        from gongmun_doctor.llm.harmony import HarmonyChecker
        rt = self._make_runtime("없음")
        checker = HarmonyChecker(rt)
        results = checker.check_paragraph("올바른 문장입니다.", para_idx=1)
        assert results == []

    def test_parsed_suggestion_fields(self):
        from gongmun_doctor.llm.harmony import HarmonyChecker
        from gongmun_doctor.report.markdown import HarmonySuggestion
        response = "[redundancy] 미리 사전에 → 사전에 | 중복 표현입니다"
        rt = self._make_runtime(response)
        checker = HarmonyChecker(rt)
        results = checker.check_paragraph("미리 사전에 검토", para_idx=3)
        assert len(results) == 1
        s = results[0]
        assert isinstance(s, HarmonySuggestion)
        assert s.paragraph_index == 3
        assert s.issue_type == "redundancy"
        assert s.original == "미리 사전에"
        assert s.suggestion == "사전에"

    def test_empty_paragraph_returns_empty_list(self):
        from gongmun_doctor.llm.harmony import HarmonyChecker
        rt = self._make_runtime("should not be called")
        checker = HarmonyChecker(rt)
        assert checker.check_paragraph("", para_idx=0) == []
        assert checker.check_paragraph("   ", para_idx=0) == []
