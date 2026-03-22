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
