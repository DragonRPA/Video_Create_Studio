"""
전사 시스템 개발 표준 헌장 준수
모듈명: app_gui.py
역할: MiniMax H3 영상 생성 스튜디오 통합 데스크톱 UI
표준 준수:
  - 카테고리 3.1: 무수식어 건조한 명사·동사 단일 표준화
  - 카테고리 3.2: 셀 및 레이블 줄바꿈 방지 (No-Wrap)
  - 카테고리 3.4: 레이블-입력 필드 상하 세로 스택 배치
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional, Dict, Any, List

from config import (
    GLOBAL_CONFIG,
    HARDWARE_PROFILES,
    ASPECT_RATIOS,
    CAMERA_PRESETS,
    LIGHTING_PRESETS,
    OUTPUTS_DIR,
    SAMPLES_DIR,
    SAMPLE_PROMPTS,
)
from task_queue_manager import TaskQueueManager
from prompt_refiner import PromptRefiner
from comfy_workflow_engine import ComfyWorkflowEngine
from backend_orchestrator import BackendOrchestrator


class StudioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MiniMax H3 영상 생성 스튜디오")
        self.geometry("1280x880")
        self.minsize(1100, 750)

        # 윈도우 아이콘 설정
        ico_p = Path(__file__).resolve().parent / "studio_icon.ico"
        if ico_p.exists():
            try:
                self.iconbitmap(str(ico_p))
            except Exception:
                pass

        self.queue_mgr = TaskQueueManager()
        self.prompt_refiner = PromptRefiner()
        self.comfy_engine = ComfyWorkflowEngine()

        self._configure_theme()
        self._build_ui()

        # 창 종료 이벤트 바인딩
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # 백그라운드 워커 시작 및 이벤트 바인딩
        self.queue_mgr.start_worker()
        self.queue_mgr.register_listener(self._on_task_updated)
        self._refresh_task_table()
        self._check_system_health()

        # 백엔드(ComfyUI) 자동 기동 점검
        self._auto_start_backend()

    def _auto_start_backend(self):
        """앱 시작 시 ComfyUI 백엔드 미실행 상태면 백그라운드 자동 기동"""
        def start_worker_thread():
            if not BackendOrchestrator.is_comfy_running():
                def log_cb(msg):
                    self.after(0, lambda: self.status_lbl.configure(text=f"백엔드: {msg}", fg="#facc15"))

                BackendOrchestrator.start_backend_async(log_cb)
                self.after(0, self._check_system_health)

        threading.Thread(target=start_worker_thread, daemon=True).start()

    def _on_close(self):
        """앱 종료 시 백엔드 및 워커 정리"""
        try:
            BackendOrchestrator.stop_backend()
            self.queue_mgr.stop_worker()
        except Exception:
            pass
        self.destroy()

    def _configure_theme(self):
        """다크 테마 및 전사 UI 표준 스타일 설정"""
        self.configure(bg="#18181b")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        bg_dark = "#18181b"
        bg_panel = "#27272a"
        fg_text = "#f4f4f5"
        accent_blue = "#2563eb"
        accent_hover = "#1d4ed8"

        self.style.configure(".", background=bg_dark, foreground=fg_text, font=("Pretendard", 10))
        self.style.configure("TLabel", background=bg_panel, foreground="#e4e4e7", font=("Pretendard", 9, "bold"))
        self.style.configure("Panel.TFrame", background=bg_panel)
        self.style.configure("TNotebook", background=bg_dark, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#3f3f46", foreground="#ffffff", padding=[14, 6], font=("Pretendard", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", accent_blue)])

        # Treeview 스타일
        self.style.configure(
            "Treeview",
            background="#09090b",
            foreground="#f4f4f5",
            fieldbackground="#09090b",
            rowheight=28,
            font=("Pretendard", 9),
        )
        self.style.configure("Treeview.Heading", background="#27272a", foreground="#ffffff", font=("Pretendard", 9, "bold"))
        self.style.map("Treeview", background=[("selected", "#3b82f6")])

    def _build_ui(self):
        """카테고리 III 전사 표준에 맞춘 화면 구축"""
        main_container = tk.Frame(self, bg="#18181b", padx=14, pady=14)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 1. 상단 상태 헤더 바
        self._build_top_bar(main_container)

        # 2. 메인 좌우 분할 패널
        body_pane = tk.PanedWindow(main_container, orient=tk.HORIZONTAL, bg="#18181b", bd=0, sashwidth=6)
        body_pane.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 좌측 패널 (모드별 입력 & 파라미터 제어)
        left_panel = tk.Frame(body_pane, bg="#27272a", padx=14, pady=14)
        body_pane.add(left_panel, minsize=520, width=580)
        self._build_left_control_panel(left_panel)

        # 우측 패널 (작업 대장 & 프리뷰/비교 뷰어)
        right_panel = tk.Frame(body_pane, bg="#27272a", padx=14, pady=14)
        body_pane.add(right_panel, minsize=520)
        self._build_right_monitor_panel(right_panel)

    def _build_top_bar(self, parent: tk.Frame):
        top_bar = tk.Frame(parent, bg="#27272a", padx=12, pady=10)
        top_bar.pack(fill=tk.X)

        title_lbl = tk.Label(top_bar, text="MiniMax H3 영상 생성 스튜디오", font=("Pretendard", 13, "bold"), fg="#ffffff", bg="#27272a")
        title_lbl.pack(side=tk.LEFT)

        self.status_lbl = tk.Label(top_bar, text="상태 검사 중", font=("Pretendard", 9), fg="#a1a1aa", bg="#27272a")
        self.status_lbl.pack(side=tk.RIGHT)

    def _build_left_control_panel(self, parent: tk.Frame):
        """좌측 모드 탭 및 입력 파이프라인"""
        # 생성 모드 탭
        self.mode_notebook = ttk.Notebook(parent)
        self.mode_notebook.pack(fill=tk.X, pady=(0, 10))

        # 탭 1: T2V
        t2v_tab = tk.Frame(self.mode_notebook, bg="#27272a", padx=4, pady=8)
        self.mode_notebook.add(t2v_tab, text="텍스트 생성 (T2V)")

        # 탭 2: I2V
        i2v_tab = tk.Frame(self.mode_notebook, bg="#27272a", padx=4, pady=8)
        self.mode_notebook.add(i2v_tab, text="이미지 생성 (I2V)")
        self._build_i2v_inputs(i2v_tab)

        # 탭 3: R2V
        r2v_tab = tk.Frame(self.mode_notebook, bg="#27272a", padx=4, pady=8)
        self.mode_notebook.add(r2v_tab, text="레퍼런스 교체 (R2V)")
        self._build_r2v_inputs(r2v_tab)

        # 탭 4: Storyboard
        story_tab = tk.Frame(self.mode_notebook, bg="#27272a", padx=4, pady=8)
        self.mode_notebook.add(story_tab, text="다중 씬 (Storyboard)")
        self._build_storyboard_inputs(story_tab)

        # 공통 프롬프트 영역
        self._build_prompt_section(parent)

        # 엔진 파라미터 설정 패널
        self._build_engine_parameters(parent)

        # 작업 등록 버튼
        submit_btn = tk.Button(
            parent,
            text="작업 대기열 등록 및 실행",
            bg="#10b981",
            fg="#ffffff",
            bd=0,
            pady=8,
            font=("Pretendard", 11, "bold"),
            command=self._on_submit_task,
        )
        submit_btn.pack(fill=tk.X, pady=(10, 0))

    def _build_prompt_section(self, parent: tk.Frame):
        """프롬프트 입력 및 프리셋 빌더 (카테고리 3.4 상하 세로 스택)"""
        # 1. 샘플 프롬프트 및 파일 로더 툴바
        sample_bar = tk.Frame(parent, bg="#27272a")
        sample_bar.pack(fill=tk.X, pady=(0, 6))

        sample_col = tk.Frame(sample_bar, bg="#27272a")
        sample_col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self._create_stack_label(sample_col, "샘플 프롬프트 프리셋 불러오기")
        self.sample_var = tk.StringVar(value=list(SAMPLE_PROMPTS.keys())[0])
        sample_combo = ttk.Combobox(sample_col, textvariable=self.sample_var, values=list(SAMPLE_PROMPTS.keys()), state="readonly")
        sample_combo.pack(fill=tk.X)
        sample_combo.bind("<<ComboboxSelected>>", self._on_select_sample_preset)

        btn_group = tk.Frame(sample_bar, bg="#27272a")
        btn_group.pack(side=tk.RIGHT, pady=(16, 0))

        self.open_file_btn = tk.Button(btn_group, text="파일 열기", bg="#4f46e5", fg="#ffffff", bd=0, padx=8, pady=3, font=("Pretendard", 9, "bold"), command=self._on_open_prompt_file)
        self.open_file_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.run_sample_btn = tk.Button(btn_group, text="샘플 즉시 실행", bg="#10b981", fg="#ffffff", bd=0, padx=8, pady=3, font=("Pretendard", 9, "bold"), command=self._on_run_sample_immediately)
        self.run_sample_btn.pack(side=tk.LEFT)

        # 2. 프리셋 선택기 (가로 2열 배치)
        preset_frame = tk.Frame(parent, bg="#27272a")
        preset_frame.pack(fill=tk.X, pady=(0, 6))

        col1 = tk.Frame(preset_frame, bg="#27272a")
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self._create_stack_label(col1, "카메라 무빙 서식")
        self.camera_var = tk.StringVar(value=CAMERA_PRESETS[0])
        camera_combo = ttk.Combobox(col1, textvariable=self.camera_var, values=CAMERA_PRESETS, state="readonly")
        camera_combo.pack(fill=tk.X)

        col2 = tk.Frame(preset_frame, bg="#27272a")
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        self._create_stack_label(col2, "조명 및 무드 서식")
        self.lighting_var = tk.StringVar(value=LIGHTING_PRESETS[0])
        lighting_combo = ttk.Combobox(col2, textvariable=self.lighting_var, values=LIGHTING_PRESETS, state="readonly")
        lighting_combo.pack(fill=tk.X)

        # 3. 지시문 입력창
        self._create_stack_label(parent, "사용자 지시문")
        self.prompt_text = tk.Text(parent, height=3, bg="#09090b", fg="#ffffff", insertbackground="#ffffff", bd=1, relief=tk.FLAT, font=("Pretendard", 9))
        self.prompt_text.pack(fill=tk.X, pady=(0, 4))

        # 변환 버튼
        btn_bar = tk.Frame(parent, bg="#27272a")
        btn_bar.pack(fill=tk.X, pady=(0, 6))
        self.refine_btn = tk.Button(btn_bar, text="마크다운 프롬프트 자동 변환", bg="#3b82f6", fg="#ffffff", bd=0, padx=8, pady=4, font=("Pretendard", 9, "bold"), command=self._on_click_refine)
        self.refine_btn.pack(side=tk.RIGHT)

        # 4. 정제된 마크다운 결과창
        self._create_stack_label(parent, "MiniMax H3 규격 마크다운 (수정 및 직접 입력 가능)")
        self.refined_text = tk.Text(parent, height=6, bg="#09090b", fg="#93c5fd", insertbackground="#ffffff", bd=1, relief=tk.FLAT, font=("Consolas", 9))
        self.refined_text.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

    def _build_i2v_inputs(self, parent: tk.Frame):
        """I2V 모드 이미지 선택기"""
        self.i2v_first_frame = tk.StringVar()
        self.i2v_last_frame = tk.StringVar()

        self._create_file_selector(parent, "시작 프레임 이미지", self.i2v_first_frame, "이미지 파일 (*.png;*.jpg;*.webp)")
        self._create_file_selector(parent, "종료 프레임 이미지", self.i2v_last_frame, "이미지 파일 (*.png;*.jpg;*.webp)")

    def _build_r2v_inputs(self, parent: tk.Frame):
        """R2V Omni 모드 미디어 선택기"""
        self.r2v_ref_image = tk.StringVar()
        self.r2v_driver_video = tk.StringVar()

        self._create_file_selector(parent, "인물 레퍼런스 이미지", self.r2v_ref_image, "이미지 파일 (*.png;*.jpg;*.webp)")
        self._create_file_selector(parent, "모션 소스 비디오", self.r2v_driver_video, "비디오 파일 (*.mp4;*.mov;*.webm)")

    def _build_storyboard_inputs(self, parent: tk.Frame):
        """Storyboard 다중 씬 텍스트 안내"""
        lbl = tk.Label(parent, text="씬 분할 모드: 씬별 프롬프트를 줄바꿈(---)으로 구분하여 입력하십시오.", font=("Pretendard", 9), fg="#a1a1aa", bg="#27272a")
        lbl.pack(anchor=tk.W)

    def _build_engine_parameters(self, parent: tk.Frame):
        """엔진 하이퍼파라미터 및 하드웨어 프로파일"""
        param_frame = tk.Frame(parent, bg="#27272a")
        param_frame.pack(fill=tk.X, pady=(0, 4))

        # 1행: 화면비 및 하드웨어 프로파일
        row1 = tk.Frame(param_frame, bg="#27272a")
        row1.pack(fill=tk.X, pady=(0, 4))

        col_aspect = tk.Frame(row1, bg="#27272a")
        col_aspect.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self._create_stack_label(col_aspect, "화면비 및 해상도")
        self.aspect_var = tk.StringVar(value=list(ASPECT_RATIOS.keys())[0])
        aspect_combo = ttk.Combobox(col_aspect, textvariable=self.aspect_var, values=list(ASPECT_RATIOS.keys()), state="readonly")
        aspect_combo.pack(fill=tk.X)

        col_profile = tk.Frame(row1, bg="#27272a")
        col_profile.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        self._create_stack_label(col_profile, "하드웨어 프로파일")
        self.profile_var = tk.StringVar(value=GLOBAL_CONFIG.active_profile)
        profile_combo = ttk.Combobox(col_profile, textvariable=self.profile_var, values=list(HARDWARE_PROFILES.keys()), state="readonly")
        profile_combo.pack(fill=tk.X)

        # 2행: 스텝 / CFG / Flow Shift
        row2 = tk.Frame(param_frame, bg="#27272a")
        row2.pack(fill=tk.X)

        col_steps = tk.Frame(row2, bg="#27272a")
        col_steps.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self._create_stack_label(col_steps, "스텝 수 (Steps)")
        self.steps_var = tk.IntVar(value=25)
        steps_spin = tk.Spinbox(col_steps, from_=10, to=50, textvariable=self.steps_var, bg="#09090b", fg="#ffffff", bd=1, relief=tk.FLAT)
        steps_spin.pack(fill=tk.X)

        col_cfg = tk.Frame(row2, bg="#27272a")
        col_cfg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))
        self._create_stack_label(col_cfg, "CFG 스케일")
        self.cfg_var = tk.DoubleVar(value=6.0)
        cfg_spin = tk.Spinbox(col_cfg, from_=1.0, to=15.0, increment=0.5, textvariable=self.cfg_var, bg="#09090b", fg="#ffffff", bd=1, relief=tk.FLAT)
        cfg_spin.pack(fill=tk.X)

        col_shift = tk.Frame(row2, bg="#27272a")
        col_shift.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        self._create_stack_label(col_shift, "Flow Shift")
        self.shift_var = tk.DoubleVar(value=5.0)
        shift_spin = tk.Spinbox(col_shift, from_=1.0, to=10.0, increment=0.5, textvariable=self.shift_var, bg="#09090b", fg="#ffffff", bd=1, relief=tk.FLAT)
        shift_spin.pack(fill=tk.X)

    def _build_right_monitor_panel(self, parent: tk.Frame):
        """우측 작업 대장 및 결과 모니터링 패널"""
        header_lbl = tk.Label(parent, text="작업 대장", font=("Pretendard", 11, "bold"), fg="#ffffff", bg="#27272a")
        header_lbl.pack(anchor=tk.W, pady=(0, 6))

        # 작업 대장 테이블 (No-Wrap 준수)
        columns = ("id", "mode", "title", "status", "progress", "created_at")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="식별자")
        self.tree.heading("mode", text="모드")
        self.tree.heading("title", text="작업명")
        self.tree.heading("status", text="상태")
        self.tree.heading("progress", text="진행률")
        self.tree.heading("created_at", text="등록일시")

        self.tree.column("id", width=65, anchor=tk.CENTER)
        self.tree.column("mode", width=60, anchor=tk.CENTER)
        self.tree.column("title", width=140, anchor=tk.W)
        self.tree.column("status", width=95, anchor=tk.CENTER)
        self.tree.column("progress", width=65, anchor=tk.CENTER)
        self.tree.column("created_at", width=130, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.tree.bind("<<TreeviewSelect>>", self._on_select_row)
        self.tree.bind("<Double-1>", self._on_double_click_row)

        # 액션 제어 버튼 바
        action_bar = tk.Frame(parent, bg="#27272a")
        action_bar.pack(fill=tk.X, pady=(0, 10))

        self.play_btn = tk.Button(action_bar, text="결과 영상 열기", bg="#3b82f6", fg="#ffffff", bd=0, padx=12, pady=6, font=("Pretendard", 9, "bold"), command=self._on_open_video)
        self.play_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.retry_btn = tk.Button(action_bar, text="작업 재시도", bg="#d97706", fg="#ffffff", bd=0, padx=12, pady=6, font=("Pretendard", 9, "bold"), command=self._on_retry_task)
        self.retry_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.folder_btn = tk.Button(action_bar, text="저장 폴더 열기", bg="#52525b", fg="#ffffff", bd=0, padx=12, pady=6, font=("Pretendard", 9), command=self._on_open_folder)
        self.folder_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.refresh_btn = tk.Button(action_bar, text="대장 갱신", bg="#3f3f46", fg="#ffffff", bd=0, padx=10, pady=6, font=("Pretendard", 9), command=self._refresh_task_table)
        self.refresh_btn.pack(side=tk.LEFT)

        # 하단 상세 정보 모니터 (실시간 상태 / 실패 사유 정밀 표시)
        self._create_stack_label(parent, "실시간 작업 상세 모니터 (선택 작업의 상세 상태 및 실패 사유)")
        self.detail_text = tk.Text(parent, height=8, bg="#09090b", fg="#e4e4e7", insertbackground="#ffffff", bd=1, relief=tk.FLAT, font=("Consolas", 9))
        self.detail_text.pack(fill=tk.X)
        self.detail_text.tag_config("error", foreground="#f87171", font=("Consolas", 9, "bold"))
        self.detail_text.tag_config("success", foreground="#4ade80", font=("Consolas", 9, "bold"))
        self.detail_text.tag_config("info", foreground="#93c5fd")

    def _create_stack_label(self, parent: tk.Frame, text: str):
        lbl = tk.Label(parent, text=text, font=("Pretendard", 9, "bold"), fg="#cbd5e1", bg="#27272a")
        lbl.pack(anchor=tk.W, pady=(0, 3))

    def _create_file_selector(self, parent: tk.Frame, label_text: str, var: tk.StringVar, filetypes: str):
        self._create_stack_label(parent, label_text)
        box = tk.Frame(parent, bg="#27272a")
        box.pack(fill=tk.X, pady=(0, 6))

        entry = tk.Entry(box, textvariable=var, bg="#09090b", fg="#ffffff", insertbackground="#ffffff", bd=1, relief=tk.FLAT, font=("Pretendard", 9))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3, padx=(0, 4))

        def browse():
            f = filedialog.askopenfilename(filetypes=[("지원 파일", "*.*")])
            if f:
                var.set(f)

        btn = tk.Button(box, text="찾아보기", bg="#52525b", fg="#ffffff", bd=0, padx=8, pady=2, font=("Pretendard", 9), command=browse)
        btn.pack(side=tk.RIGHT)

    def _check_system_health(self):
        """백그라운드 시스템 상태 점검"""
        def check():
            h = self.comfy_engine.check_health()
            if h.get("online"):
                txt = f"ComfyUI 연결됨 | GPU: {h.get('gpu_name')} | VRAM 가용: {h.get('vram_free_gb')}GB / {h.get('vram_total_gb')}GB"
                color = "#4ade80"
            else:
                txt = f"ComfyUI 대기 중 (포트 {GLOBAL_CONFIG.comfy_port}) | 로컬 SLM: {GLOBAL_CONFIG.ollama_model}"
                color = "#facc15"
            self.after(0, lambda: self.status_lbl.configure(text=txt, fg=color))

        threading.Thread(target=check, daemon=True).start()

    def _on_select_sample_preset(self, event=None):
        """샘플 프리셋 선택 시 해당 마크다운 파일 자동 로드"""
        import re
        choice = self.sample_var.get()
        filename = SAMPLE_PROMPTS.get(choice)
        if not filename:
            return

        sample_file = SAMPLES_DIR / filename
        if sample_file.exists():
            try:
                with open(sample_file, "r", encoding="utf-8") as f:
                    content = f.read()

                self.refined_text.delete("1.0", tk.END)
                self.refined_text.insert("1.0", content)

                # Core Idea 추출하여 사용자 지시문 창에 요약 노출
                core_match = re.search(r"### \[Block 2: Core Idea\]\s*([\s\S]*?)(?=###|\Z)", content)
                summary = core_match.group(1).strip() if core_match else choice
                self.prompt_text.delete("1.0", tk.END)
                self.prompt_text.insert("1.0", summary)

                # 모드 탭 자동 전환
                if "Storyboard" in choice:
                    self.mode_notebook.select(3)
                else:
                    self.mode_notebook.select(0)
            except Exception as e:
                messagebox.showerror("파일 오류", f"샘플 파일을 읽을 수 없습니다:\n{e}")

    def _on_open_prompt_file(self):
        """사용자가 직접 파일 탐색기로 프롬프트 마크다운 파일 선택"""
        fpath = filedialog.askopenfilename(
            initialdir=str(SAMPLES_DIR),
            title="프롬프트 마크다운 파일 선택",
            filetypes=[("마크다운 파일", "*.md"), ("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
        )
        if not fpath:
            return

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            self.refined_text.delete("1.0", tk.END)
            self.refined_text.insert("1.0", content)
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", f"파일에서 로드됨: {Path(fpath).name}")
        except Exception as e:
            messagebox.showerror("파일 오류", f"파일을 열 수 없습니다:\n{e}")

    def _on_run_sample_immediately(self):
        """현재 로드된 샘플 또는 기본 샘플을 즉시 대기열에 등록하고 실행"""
        refined = self.refined_text.get("1.0", tk.END).strip()
        if not refined:
            # 아직 로드되지 않았으면 첫 번째 샘플 로드
            first_key = list(SAMPLE_PROMPTS.keys())[1]
            self.sample_var.set(first_key)
            self._on_select_sample_preset()
            refined = self.refined_text.get("1.0", tk.END).strip()

        preset_name = self.sample_var.get()
        title = f"SAMPLE_{preset_name.split('.')[1].strip() if '.' in preset_name else 'T2V_Sample'}"

        current_tab = self.mode_notebook.index(self.mode_notebook.select())
        mode_map = {0: "t2v", 1: "i2v", 2: "r2v", 3: "storyboard"}
        mode = mode_map.get(current_tab, "t2v")

        task_id = self.queue_mgr.add_task(
            title=title,
            raw_prompt=refined,
            mode=mode,
        )
        self.queue_mgr.update_task_status(task_id, "PENDING", 0, refined_prompt=refined)
        self._refresh_task_table()
        messagebox.showinfo("샘플 실행 등록", f"샘플 작업 '{title}' (ID: {task_id})이(가) 대기열에 즉시 등록되었습니다!")

    def _on_click_refine(self):
        raw_text = self.prompt_text.get("1.0", tk.END).strip()
        cam = self.camera_var.get()
        light = self.lighting_var.get()

        combined_input = raw_text
        if cam and not cam.startswith("기본"):
            combined_input += f", Camera Movement: {cam}"
        if light and not light.startswith("기본"):
            combined_input += f", Lighting/Atmosphere: {light}"

        if not combined_input:
            messagebox.showwarning("입력 필요", "사용자 지시문을 먼저 입력하십시오.")
            return

        self.refine_btn.configure(text="변환 중...", state=tk.DISABLED)

        def run_refine():
            current_tab = self.mode_notebook.index(self.mode_notebook.select())
            mode_map = {0: "t2v", 1: "i2v", 2: "r2v", 3: "storyboard"}
            mode = mode_map.get(current_tab, "t2v")

            res = self.prompt_refiner.refine(combined_input, mode=mode)
            pos = res.get("positive_prompt", "")
            self.after(0, lambda: self._update_refined_text(pos))

        threading.Thread(target=run_refine, daemon=True).start()

    def _update_refined_text(self, text: str):
        self.refined_text.delete("1.0", tk.END)
        self.refined_text.insert("1.0", text)
        self.refine_btn.configure(text="마크다운 프롬프트 자동 변환", state=tk.NORMAL)

    def _on_submit_task(self):
        raw_prompt = self.prompt_text.get("1.0", tk.END).strip()
        refined_prompt = self.refined_text.get("1.0", tk.END).strip()
        current_tab = self.mode_notebook.index(self.mode_notebook.select())
        mode_map = {0: "t2v", 1: "i2v", 2: "r2v", 3: "storyboard"}
        mode = mode_map.get(current_tab, "t2v")

        if not raw_prompt and not refined_prompt:
            messagebox.showwarning("입력 필요", "프롬프트를 입력하십시오.")
            return

        ref_media = None
        if mode == "i2v":
            ref_media = self.i2v_first_frame.get().strip()
        elif mode == "r2v":
            ref_media = self.r2v_driver_video.get().strip()

        title = f"{mode.upper()}_{raw_prompt[:15] if raw_prompt else '신규 작업'}"

        task_id = self.queue_mgr.add_task(
            title=title,
            raw_prompt=raw_prompt or refined_prompt,
            mode=mode,
            reference_media_path=ref_media,
        )

        if refined_prompt:
            self.queue_mgr.update_task_status(task_id, "PENDING", 0, refined_prompt=refined_prompt)

        self._refresh_task_table()
        self.prompt_text.delete("1.0", tk.END)
        self.refined_text.delete("1.0", tk.END)

    def _refresh_task_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        tasks = self.queue_mgr.list_tasks(100)
        for t in tasks:
            self.tree.insert(
                "",
                tk.END,
                iid=t["id"],
                values=(
                    t["id"],
                    t["mode"].upper(),
                    t["title"],
                    t["status"],
                    f"{t['progress']}%",
                    t["created_at"],
                ),
            )

    def _on_task_updated(self, task_data: Dict[str, Any]):
        def update_ui():
            self._refresh_task_table()
            # 갱신된 태스크가 현재 선택되어 있거나 실패한 경우 상세창 자동 갱신
            selected = self.tree.selection()
            if selected and selected[0] == task_data.get("id"):
                self._display_task_detail(task_data)
            elif task_data.get("status") == "FAILED":
                # 실패 건 자동 포커스 및 실패 사유 노출
                if not selected:
                    try:
                        self.tree.selection_set(task_data["id"])
                    except Exception:
                        pass
                self._display_task_detail(task_data)

        self.after(0, update_ui)

    def _on_select_row(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = selected[0]
        task = self.queue_mgr.get_task(task_id)
        if task:
            self._display_task_detail(task)
            if task.get("refined_prompt"):
                self.refined_text.delete("1.0", tk.END)
                self.refined_text.insert("1.0", task["refined_prompt"])

    def _display_task_detail(self, task: Dict[str, Any]):
        """상세 모니터에 상태 및 실패 사유 정밀 서식 출력"""
        status = task.get("status", "UNKNOWN")
        task_id = task.get("id", "")
        mode = task.get("mode", "").upper()
        title = task.get("title", "")
        progress = task.get("progress", 0)
        p_msg = task.get("progress_msg", "")
        err = task.get("error_message")
        out_v = task.get("output_video_path")

        self.detail_text.delete("1.0", tk.END)

        header_str = f"■ [작업 식별자] {task_id} | [모드] {mode} | [상태] {status} ({progress}%)\n"
        header_str += f"■ [작업 명칭] {title}\n"
        header_str += f"■ [진행 상태] {p_msg}\n"
        self.detail_text.insert(tk.END, header_str)

        if status == "FAILED" or err:
            err_box = "=" * 75 + "\n"
            err_box += f"❌ [실패 사유]: {err or '알 수 없는 오류'}\n"
            err_box += "-" * 75 + "\n"
            err_box += "💡 [조치 가이드]:\n"
            err_box += "   1. ComfyUI 서버가 켜져 있는지 확인하십시오 (http://127.0.0.1:8188)\n"
            err_box += "   2. 가중치 모델(models/)이 정상 다운로드되어 있는지 확인하십시오.\n"
            err_box += "   3. 조치 후 위의 [작업 재시도] 버튼을 누르면 즉시 재실행됩니다.\n"
            err_box += "=" * 75 + "\n"
            self.detail_text.insert(tk.END, err_box, "error")
        elif status == "COMPLETED" and out_v:
            succ_str = f"✅ [생성 완료 영상]: {out_v}\n"
            self.detail_text.insert(tk.END, succ_str, "success")

    def _on_double_click_row(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        task_id = selected[0]
        task = self.queue_mgr.get_task(task_id)
        if not task:
            return

        if task.get("status") == "FAILED":
            err = task.get("error_message", "알 수 없는 오류")
            retry = messagebox.askyesno(
                "작업 실패 사유",
                f"작업 식별자: {task_id}\n\n[실패 원인]\n{err}\n\n이 작업을 지금 재시도하시겠습니까?",
                icon="error",
            )
            if retry:
                self.queue_mgr.retry_task(task_id)
                self._refresh_task_table()
        elif task.get("status") == "COMPLETED":
            self._on_open_video()

    def _on_retry_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("선택 필요", "작업 대장에서 재시도할 작업을 먼저 선택하십시오.")
            return
        task_id = selected[0]
        task = self.queue_mgr.get_task(task_id)
        if not task:
            return

        self.queue_mgr.retry_task(task_id)
        self._refresh_task_table()
        messagebox.showinfo("재시도 등록", f"작업 '{task_id}'이(가) 대기열에 다시 등록되었습니다.")

    def _on_open_video(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("선택 필요", "작업 대장에서 항목을 먼저 선택하십시오.")
            return
        task_id = selected[0]
        task = self.queue_mgr.get_task(task_id)
        if not task or not task.get("output_video_path"):
            messagebox.showinfo("영상 없음", "생성 완료된 영상 파일이 존재하지 않습니다.")
            return

        video_p = Path(task["output_video_path"])
        if video_p.exists():
            os.startfile(str(video_p))
        else:
            messagebox.showerror("파일 없음", f"파일을 찾을 수 없습니다:\n{video_p}")

    def _on_open_folder(self):
        os.startfile(str(OUTPUTS_DIR))


if __name__ == "__main__":
    app = StudioApp()
    app.mainloop()
