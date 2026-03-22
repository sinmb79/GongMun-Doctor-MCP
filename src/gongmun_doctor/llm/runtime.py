"""llama-cpp-python wrapper — CPU GGUF model inference."""

from pathlib import Path


class LLMRuntime:
    """Thin wrapper around llama_cpp.Llama for GGUF model inference."""

    def __init__(
        self,
        model_path: str | Path,
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_gpu_layers: int = 0,
    ) -> None:
        try:
            import llama_cpp  # noqa: F401
        except (ImportError, ModuleNotFoundError):
            raise ImportError(
                "llama-cpp-python이 설치되지 않았습니다.\n"
                "설치 명령: pip install llama-cpp-python --prefer-binary"
            )

        model_path = Path(model_path)
        try:
            from llama_cpp import Llama
            self._model = Llama(
                model_path=str(model_path),
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
            )
        except Exception as e:
            raise RuntimeError(
                f"모델 파일을 불러올 수 없습니다: {model_path}\n"
                f"오류: {e}\n"
                "GGUF 형식의 모델 파일 경로가 맞는지 확인하세요."
            )

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.1) -> str:
        """Run inference. Returns empty string on any error (graceful fallback)."""
        try:
            result = self._model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["</s>", "[/INST]", "<|im_end|>"],
                echo=False,
            )
            return result["choices"][0]["text"].strip()
        except Exception:
            return ""
