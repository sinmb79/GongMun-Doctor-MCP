"""Tkinter GUI for gongmun-doctor."""

import os
import queue
import shutil
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext
import tkinter as tk
import tkinter.ttk as ttk

from gongmun_doctor import __version__
from gongmun_doctor.engine import correct_document
from gongmun_doctor.parser.hwpx_handler import close_document, open_document, save_document
from gongmun_doctor.parser.hwp_converter import (
    LibreOfficeNotFoundError,
    convert_hwp_to_hwpx,
    is_libreoffice_available,
)
from gongmun_doctor.report.markdown import write_report
from gongmun_doctor.rules.loader import load_rules_by_layer


# ── helpers (pure functions reused from cli.py) ───────────────────────────────

def _backup(input_path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = input_path.with_suffix(f".{ts}.bak.hwpx")
    shutil.copy2(input_path, backup_path)
    return backup_path


# ── main app ──────────────────────────────────────────────────────────────────

class GongmunDoctorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"공문닥터 v{__version__}")
        self.resizable(True, True)
        self.minsize(700, 450)

        self._queue: queue.Queue = queue.Queue()
        self._input_path = tk.StringVar()
        self._llm_path = tk.StringVar()
        self._llm_mode = tk.StringVar(value="none")   # "none" | "local" | "cloud"
        self._cloud_provider = tk.StringVar(value="claude")
        self._cloud_model = tk.StringVar()
        self._opt_report = tk.BooleanVar(value=True)
        self._opt_dryrun = tk.BooleanVar(value=False)
        self._opt_strict = tk.BooleanVar(value=False)

        # track output paths for "open file" buttons
        self._output_path: Path | None = None
        self._report_path: Path | None = None
        self._summary_frame: tk.LabelFrame | None = None  # tracked for cleanup

        self._build_ui()
        self._set_idle()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, minsize=220)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._left = tk.Frame(self, width=220, padx=12, pady=12)
        self._left.grid(row=0, column=0, sticky="nsew")
        self._left.grid_propagate(False)

        sep = ttk.Separator(self, orient="vertical")
        sep.grid(row=0, column=0, sticky="nse", padx=(220, 0))

        self._right = tk.Frame(self, padx=12, pady=12, bg="#1a202c")
        self._right.grid(row=0, column=1, sticky="nsew")
        self._right.columnconfigure(0, weight=1)
        self._right.rowconfigure(1, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        lf = self._left
        lf.columnconfigure(0, weight=1)

        # ── 입력 파일 ──
        tk.Label(lf, text="입력 파일", font=("", 9, "bold"), anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 2)
        )
        path_entry = tk.Entry(lf, textvariable=self._input_path, state="readonly", width=18)
        path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 4))
        tk.Button(lf, text="찾기", width=5, command=self._pick_input).grid(row=1, column=1)

        ttk.Separator(lf, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=10
        )

        # ── 옵션 ──
        tk.Label(lf, text="옵션", font=("", 9, "bold"), anchor="w").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        tk.Checkbutton(lf, text="교정 보고서 생성 (.md)", variable=self._opt_report).grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        tk.Checkbutton(lf, text="dry-run (저장 안 함)", variable=self._opt_dryrun).grid(
            row=5, column=0, columnspan=2, sticky="w"
        )
        tk.Checkbutton(
            lf, text="엄격 모드 (LLM 제외)", variable=self._opt_strict
        ).grid(row=6, column=0, columnspan=2, sticky="w")

        ttk.Separator(lf, orient="horizontal").grid(
            row=7, column=0, columnspan=2, sticky="ew", pady=10
        )

        # ── LLM 분석 (선택) ──
        tk.Label(lf, text="L4 LLM 분석 (선택)", font=("", 9, "bold"), anchor="w").grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(0, 2)
        )
        tk.Radiobutton(lf, text="없음", variable=self._llm_mode, value="none",
                       command=self._on_llm_mode_change).grid(
            row=9, column=0, columnspan=2, sticky="w"
        )
        tk.Radiobutton(lf, text="로컬 GGUF", variable=self._llm_mode, value="local",
                       command=self._on_llm_mode_change).grid(
            row=10, column=0, columnspan=2, sticky="w"
        )
        tk.Radiobutton(lf, text="클라우드 API", variable=self._llm_mode, value="cloud",
                       command=self._on_llm_mode_change).grid(
            row=11, column=0, columnspan=2, sticky="w"
        )

        # Local GGUF row (shown when mode == "local")
        self._llm_local_frame = tk.Frame(lf)
        self._llm_local_frame.columnconfigure(0, weight=1)
        tk.Entry(self._llm_local_frame, textvariable=self._llm_path,
                 state="readonly", width=14).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        tk.Button(self._llm_local_frame, text="찾기", width=5,
                  command=self._pick_llm).grid(row=0, column=1)
        self._llm_local_frame.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self._llm_local_frame.grid_remove()

        # Cloud API row (shown when mode == "cloud")
        self._llm_cloud_frame = tk.Frame(lf)
        self._llm_cloud_frame.columnconfigure(0, weight=1)
        providers = ["claude", "openai", "gemini"]
        ttk.Combobox(
            self._llm_cloud_frame,
            textvariable=self._cloud_provider,
            values=providers,
            state="readonly",
            width=12,
        ).grid(row=0, column=0, sticky="ew")
        tk.Entry(
            self._llm_cloud_frame,
            textvariable=self._cloud_model,
            width=14,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 0))
        tk.Label(self._llm_cloud_frame, text="(환경변수 API 키)", font=("", 8), fg="#718096").grid(
            row=2, column=0, sticky="w", pady=(1, 0)
        )
        self._llm_cloud_frame.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        self._llm_cloud_frame.grid_remove()

        # ── 실행 버튼 영역 (bottom) ──
        self._btn_frame = tk.Frame(lf)
        self._btn_frame.grid(row=20, column=0, columnspan=2, sticky="sew", pady=(16, 0))
        lf.rowconfigure(20, weight=1)

        self._run_btn = tk.Button(
            self._btn_frame,
            text="교정 실행",
            font=("", 11, "bold"),
            bg="#38a169", fg="white",
            activebackground="#2f855a", activeforeground="white",
            relief="flat", pady=8,
            command=self._run_correction,
        )
        self._run_btn.pack(fill="x")

    def _build_right_panel(self):
        rf = self._right
        tk.Label(rf, text="실행 로그 / 교정 결과", font=("", 9, "bold"),
                 bg="#1a202c", fg="#a0aec0", anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )
        self._log = tk.Text(
            rf,
            bg="#1a202c", fg="#a0aec0",
            font=("Consolas", 10),
            state="disabled",
            wrap="word",
            relief="flat",
            padx=8, pady=8,
        )
        self._log.grid(row=1, column=0, sticky="nsew")

        sb = ttk.Scrollbar(rf, command=self._log.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self._log.configure(yscrollcommand=sb.set)

    # ── state transitions ─────────────────────────────────────────────────────

    def _set_idle(self):
        """State 1: waiting for file selection."""
        self._run_btn.configure(text="교정 실행", state="disabled",
                                bg="#718096", activebackground="#4a5568")
        # Remove action buttons if present
        for w in self._btn_frame.winfo_children():
            if w is not self._run_btn:
                w.destroy()
        # Remove summary frame if present
        if self._summary_frame is not None:
            self._summary_frame.destroy()
            self._summary_frame = None
        self._log_clear()
        self._append_log("파일을 선택하고 교정 실행을 누르세요.\n")

    def _set_running(self):
        """State 2: correction in progress."""
        self._run_btn.configure(text="실행 중...", state="disabled",
                                bg="#718096", activebackground="#4a5568")
        self._log_clear()

    def _set_complete(self, report, output_path: Path | None, report_path: Path | None):
        """State 3: correction complete."""
        # Summary box
        summary = tk.LabelFrame(self._left, text="교정 완료", fg="#2b6cb0",
                                padx=8, pady=6, font=("", 9, "bold"))
        self._summary_frame = summary
        summary.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        tk.Label(summary, text=f"총 문단: {report.total_paragraphs}개", anchor="w").pack(fill="x")
        tk.Label(summary, text=f"교정 건수: {report.total_corrections}건", anchor="w").pack(fill="x")
        if report.harmony_suggestions:
            tk.Label(summary, text=f"L4 제안: {len(report.harmony_suggestions)}건", anchor="w").pack(fill="x")
        if report.warnings:
            tk.Label(summary, text=f"경고: {len(report.warnings)}건", anchor="w").pack(fill="x")

        # Replace run button with action buttons
        self._run_btn.pack_forget()

        dry_run = self._opt_dryrun.get()
        has_report = self._opt_report.get() and report_path is not None

        tk.Button(
            self._btn_frame, text="교정 파일 열기",
            bg="#38a169", fg="white", activebackground="#2f855a", activeforeground="white",
            relief="flat", pady=6,
            state="disabled" if dry_run else "normal",
            command=lambda: os.startfile(str(output_path)) if output_path else None,
        ).pack(fill="x", pady=(0, 3))

        tk.Button(
            self._btn_frame, text="보고서 열기",
            bg="#3182ce", fg="white", activebackground="#2b6cb0", activeforeground="white",
            relief="flat", pady=6,
            state="normal" if has_report else "disabled",
            command=lambda: os.startfile(str(report_path)) if report_path else None,
        ).pack(fill="x", pady=(0, 3))

        tk.Button(
            self._btn_frame, text="새 파일 교정",
            bg="#4a5568", fg="white", activebackground="#2d3748", activeforeground="white",
            relief="flat", pady=6,
            command=self._reset,
        ).pack(fill="x")

        # Print correction list to log
        self._append_log(f"\n{'─'*40}\n")
        self._append_log(f"교정 완료: {report.total_corrections}건\n")
        for c in report.corrections:
            orig = c.original_text[:30]
            corr = c.corrected_text[:30]
            self._append_log(f"[{c.rule_id}] 문단{c.paragraph_index}: '{orig}' → '{corr}'\n")
        for s in report.harmony_suggestions:
            self._append_log(f"[L4/{s.issue_type}] 문단{s.paragraph_index}: {s.original} → {s.suggestion}\n")
        for warning in report.warnings:
            self._append_log(f"[Cloud LLM] 경고: {warning}\n")
        if report.total_corrections == 0 and not report.harmony_suggestions:
            self._append_log("교정 사항이 없습니다.\n")

    def _set_error(self, msg: str):
        """State 4: error."""
        self._append_log(f"\n오류: {msg}\n")
        self._run_btn.configure(text="교정 실행", state="normal",
                                bg="#38a169", activebackground="#2f855a")
        messagebox.showerror("오류", msg)

    def _reset(self):
        self._input_path.set("")
        self._output_path = None
        self._report_path = None
        self._run_btn.pack(fill="x")
        self._set_idle()

    # ── file pickers ──────────────────────────────────────────────────────────

    def _pick_input(self):
        path = filedialog.askopenfilename(
            title="입력 파일 선택",
            filetypes=[("HWP/HWPX 문서", "*.hwpx *.hwp"), ("모든 파일", "*.*")],
        )
        if path:
            self._input_path.set(path)
            self._run_btn.configure(
                state="normal", bg="#38a169", activebackground="#2f855a"
            )

    def _pick_llm(self):
        path = filedialog.askopenfilename(
            title="LLM 모델 파일 선택 (GGUF)",
            filetypes=[("GGUF 모델", "*.gguf"), ("모든 파일", "*.*")],
        )
        if path:
            self._llm_path.set(path)

    def _on_llm_mode_change(self):
        mode = self._llm_mode.get()
        if mode == "local":
            self._llm_local_frame.grid()
            self._llm_cloud_frame.grid_remove()
        elif mode == "cloud":
            self._llm_local_frame.grid_remove()
            self._llm_cloud_frame.grid()
        else:
            self._llm_local_frame.grid_remove()
            self._llm_cloud_frame.grid_remove()

    # ── log helpers ───────────────────────────────────────────────────────────

    def _log_clear(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _append_log(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", msg)
        self._log.see("end")
        self._log.configure(state="disabled")

    # ── correction pipeline ───────────────────────────────────────────────────

    def _run_correction(self):
        input_path = self._input_path.get().strip()
        if not input_path:
            messagebox.showwarning("경고", "파일을 선택해 주세요.")
            return

        self._set_running()

        # collect options
        dry_run = self._opt_dryrun.get()
        make_report = self._opt_report.get()
        strict = self._opt_strict.get()
        llm_mode = self._llm_mode.get()
        llm_model = self._llm_path.get().strip() if llm_mode == "local" else None
        cloud_provider = self._cloud_provider.get() if llm_mode == "cloud" else None
        cloud_model = self._cloud_model.get().strip() if llm_mode == "cloud" else None

        t = threading.Thread(
            target=self._correction_worker,
            args=(input_path, dry_run, make_report, strict, llm_model, cloud_provider, cloud_model),
            daemon=True,
        )
        t.start()
        self.after(100, self._drain_queue)

    def _correction_worker(
        self,
        input_path_str,
        dry_run,
        make_report,
        strict,
        llm_model,
        cloud_provider=None,
        cloud_model=None,
    ):
        q = self._queue

        def log(msg):
            q.put(("log", msg + "\n"))

        try:
            input_path = Path(input_path_str)
            if not input_path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_path}")

            # 1. Resolve HWP → HWPX
            suffix = input_path.suffix.lower()
            if suffix == ".hwp":
                if not is_libreoffice_available():
                    raise RuntimeError(
                        "HWP 파일 변환에 LibreOffice가 필요합니다.\n"
                        "LibreOffice를 설치하거나 HWPX 파일을 사용해 주세요."
                    )
                log(f"[HWP->HWPX] LibreOffice로 변환 중: {input_path.name}")
                try:
                    hwpx_path = convert_hwp_to_hwpx(input_path)
                except (LibreOfficeNotFoundError, RuntimeError) as e:
                    raise RuntimeError(f"HWP 변환 오류: {e}") from e
                log(f"[HWP->HWPX] 변환 완료: {hwpx_path.name}")
            elif suffix == ".hwpx":
                hwpx_path = input_path
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {suffix}")

            # 2. Load rules
            layers = ["L1_spelling", "L2_grammar", "L3_official_style"] if strict else None
            rules = load_rules_by_layer(layers=layers)
            log(f"[1/4] 규칙 로드 완료: {len(rules)}개")

            # 3. Backup
            if not dry_run:
                backup = _backup(hwpx_path)
                log(f"[2/4] 원본 백업: {backup.name}")
            else:
                log("[2/4] dry-run 모드: 파일을 수정하지 않습니다.")

            # 4. Open document
            doc = open_document(hwpx_path)
            para_count = len(doc.paragraphs)
            log(f"[3/4] 문서 열기 완료: {hwpx_path.name} ({para_count}개 문단)")

            # 5. LLM (optional)
            harmony_checker = None
            if llm_model and not strict:
                try:
                    from gongmun_doctor.llm.runtime import LLMRuntime
                    from gongmun_doctor.llm.harmony import HarmonyChecker
                    log(f"[LLM] 모델 로드 중: {Path(llm_model).name}")
                    harmony_checker = HarmonyChecker(LLMRuntime(llm_model))
                    log("[LLM] 모델 로드 완료")
                except (ImportError, RuntimeError) as e:
                    log(f"[LLM] 경고: {e} - LLM 없이 계속합니다.")
            elif cloud_provider and not strict:
                try:
                    from gongmun_doctor.llm.cloud_runtime import CloudLLMRuntime
                    from gongmun_doctor.llm.harmony import HarmonyChecker
                    log(f"[Cloud LLM] {cloud_provider} 연결 중...")
                    harmony_checker = HarmonyChecker(
                        CloudLLMRuntime(cloud_provider, model=cloud_model or None)
                    )
                    log(f"[Cloud LLM] {cloud_provider} 연결 완료")
                except (EnvironmentError, ImportError) as e:
                    log(f"[Cloud LLM] 경고: {e} - LLM 없이 계속합니다.")

            # 6. Correct
            output_path = hwpx_path.parent / f"{hwpx_path.stem}_corrected.hwpx"
            report = correct_document(doc, rules, dry_run=dry_run, harmony_checker=harmony_checker)
            report.input_path = str(hwpx_path)
            report.output_path = str(output_path) if not dry_run else "(dry-run)"

            # 7. Save
            if not dry_run:
                save_document(doc, output_path)
                log(f"[4/4] 교정 파일 저장: {output_path.name}")
            else:
                log("[4/4] dry-run 완료 (저장 건너뜀)")
            close_document(doc)

            # 8. Report
            report_path = None
            if make_report and not dry_run:
                report_path = output_path.with_suffix(".md")
                write_report(report, str(report_path))
                log(f"[보고서] {report_path.name}")

            q.put(("done", report, output_path if not dry_run else None, report_path))

        except Exception as e:
            q.put(("error", str(e)))

    def _drain_queue(self):
        try:
            while True:
                item = self._queue.get_nowait()
                if item is None:
                    return  # unexpected sentinel — stop polling safely
                kind, *data = item
                if kind == "log":
                    self._append_log(data[0])
                elif kind == "done":
                    report, output_path, report_path = data
                    self._output_path = output_path
                    self._report_path = report_path
                    self._set_complete(report, output_path, report_path)
                    return
                elif kind == "error":
                    self._set_error(data[0])
                    return
        except queue.Empty:
            self.after(100, self._drain_queue)


def main():
    app = GongmunDoctorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
