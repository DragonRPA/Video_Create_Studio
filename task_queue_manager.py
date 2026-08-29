"""
전사 시스템 개발 표준 헌장 준수
모듈명: task_queue_manager.py
역할: SQLite 기반 태스크 큐, 오케스트레이션 상태머신, 배치 렌더링 스케줄러
"""

import sqlite3
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from config import GLOBAL_CONFIG, DB_PATH, OUTPUTS_DIR
from prompt_refiner import PromptRefiner
from comfy_workflow_engine import ComfyWorkflowEngine
from post_processor import FFmpegPostProcessor


class TaskQueueManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_db()
        self.prompt_refiner = PromptRefiner()
        self.workflow_engine = ComfyWorkflowEngine()
        self.post_processor = FFmpegPostProcessor()
        self._is_running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._status_listeners: List[Callable[[Dict[str, Any]], None]] = []

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """데이터베이스 및 태스크 테이블 초기화"""
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    raw_prompt TEXT NOT NULL,
                    refined_prompt TEXT,
                    negative_prompt TEXT,
                    reference_media_path TEXT,
                    reference_audio_path TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    progress INTEGER NOT NULL DEFAULT 0,
                    progress_msg TEXT DEFAULT '',
                    output_video_path TEXT,
                    output_thumb_path TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add_task(
        self,
        title: str,
        raw_prompt: str,
        mode: str = "t2v",
        reference_media_path: Optional[str] = None,
        reference_audio_path: Optional[str] = None,
    ) -> str:
        """신규 렌더링 태스크 등록"""
        task_id = str(uuid.uuid4())[:8]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clean_title = title.strip() or f"Task_{task_id}"

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, title, mode, raw_prompt, reference_media_path,
                    reference_audio_path, status, progress, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', 0, ?, ?)
                """,
                (
                    task_id,
                    clean_title,
                    mode,
                    raw_prompt,
                    reference_media_path,
                    reference_audio_path,
                    now,
                    now,
                ),
            )
            conn.commit()

        self._notify_listeners(self.get_task(task_id))
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """단일 태스크 상세 조회"""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """전체 태스크 목록 조회 (최신순)"""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cur.fetchall()]

    def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: int,
        msg: str = "",
        output_video: Optional[str] = None,
        output_thumb: Optional[str] = None,
        error_msg: Optional[str] = None,
        refined_prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
    ):
        """태스크 상태 및 진행률 업데이트"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, progress = ?, progress_msg = ?,
                    output_video_path = COALESCE(?, output_video_path),
                    output_thumb_path = COALESCE(?, output_thumb_path),
                    error_message = ?,
                    refined_prompt = COALESCE(?, refined_prompt),
                    negative_prompt = COALESCE(?, negative_prompt),
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    progress,
                    msg,
                    output_video,
                    output_thumb,
                    error_msg,
                    refined_prompt,
                    negative_prompt,
                    now,
                    task_id,
                ),
            )
            conn.commit()

        updated = self.get_task(task_id)
        if updated:
            self._notify_listeners(updated)

    def register_listener(self, cb: Callable[[Dict[str, Any]], None]):
        """상태 변경 콜백 리스너 등록"""
        self._status_listeners.append(cb)

    def _notify_listeners(self, task_data: Optional[Dict[str, Any]]):
        if not task_data:
            return
        for cb in self._status_listeners:
            try:
                cb(task_data)
            except Exception:
                pass

    def start_worker(self):
        """백그라운드 큐 처리 워커 시작"""
        if self._is_running:
            return
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def stop_worker(self):
        """워커 정지"""
        self._is_running = False

    def _worker_loop(self):
        """대기열 순차 처리 메인 루프"""
        while self._is_running:
            task = self._fetch_next_pending()
            if not task:
                time.sleep(1.0)
                continue

            self._process_single_task(task)

    def _fetch_next_pending(self) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.execute(
                "SELECT * FROM tasks WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT 1"
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def _process_single_task(self, task: Dict[str, Any]):
        task_id = task["id"]
        try:
            # 1. 프롬프트 정제 (Refining)
            self.update_task_status(task_id, "REFINING", 10, "MiniMax 마크다운 프롬프트 자동 변환 중")
            refine_res = self.prompt_refiner.refine(task["raw_prompt"], mode=task["mode"])
            pos_prompt = refine_res["positive_prompt"]
            neg_prompt = refine_res["negative_prompt"]

            self.update_task_status(
                task_id,
                "QUEUED",
                25,
                "ComfyUI 워크플로우 큐 등록 중",
                refined_prompt=pos_prompt,
                negative_prompt=neg_prompt,
            )

            # 2. ComfyUI 워크플로우 구성 및 큐 전송
            workflow = self.workflow_engine.build_t2v_workflow(
                positive_prompt=pos_prompt,
                negative_prompt=neg_prompt,
                profile=GLOBAL_CONFIG.profile,
            )
            prompt_id = self.workflow_engine.queue_workflow(workflow)

            # 3. 추론 렌더링 폴링
            self.update_task_status(task_id, "RENDERING", 30, f"추론 렌더링 시작 (Prompt ID: {prompt_id})")

            def on_progress(p: int, msg: str):
                calc_progress = 30 + int(p * 0.5)  # 30% -> 80%
                self.update_task_status(task_id, "RENDERING", calc_progress, msg)

            poll_result = self.workflow_engine.poll_execution(
                prompt_id=prompt_id, progress_cb=on_progress
            )

            # 4. 출력물 파일 다운로드
            self.update_task_status(task_id, "POST_PROCESSING", 85, "산출물 다운로드 및 후처리")
            raw_video_path = OUTPUTS_DIR / f"{task_id}_raw.mp4"
            final_video_path = OUTPUTS_DIR / f"{task_id}_final.mp4"
            thumb_path = OUTPUTS_DIR / f"{task_id}_thumb.jpg"

            outputs = poll_result.get("outputs", [])
            if outputs:
                first_out = outputs[0]
                self.workflow_engine.download_output_file(
                    filename=first_out.get("filename"),
                    subfolder=first_out.get("subfolder", ""),
                    folder_type=first_out.get("type", "output"),
                    dest_path=str(raw_video_path),
                )
            else:
                raise RuntimeError("ComfyUI 산출물 파일 없음")

            # 5. FFmpeg 후처리: 오디오 믹싱 & 최적화
            extracted_audio = None
            if task.get("reference_media_path"):
                ref_media = task["reference_media_path"]
                audio_tmp = OUTPUTS_DIR / f"{task_id}_ref_audio.aac"
                if self.post_processor.extract_audio(ref_media, str(audio_tmp)):
                    extracted_audio = str(audio_tmp)

            target_audio = task.get("reference_audio_path") or extracted_audio

            if target_audio and Path(target_audio).exists():
                self.post_processor.merge_video_audio(
                    str(raw_video_path), target_audio, str(final_video_path)
                )
            else:
                self.post_processor.optimize_video(str(raw_video_path), str(final_video_path))

            # 6. 썸네일 생성
            self.post_processor.generate_thumbnail(str(final_video_path), str(thumb_path))

            # 7. 완료 마감
            self.update_task_status(
                task_id,
                "COMPLETED",
                100,
                "영상 생성 완료",
                output_video=str(final_video_path),
                output_thumb=str(thumb_path),
            )

        except Exception as e:
            raw_err = f"{type(e).__name__}: {str(e)}"
            # 사용자 친화적 진단 메시지 생성
            if "Connection" in raw_err or "refused" in raw_err.lower() or "8188" in raw_err:
                diagnostic = f"ComfyUI 서버(http://127.0.0.1:{GLOBAL_CONFIG.comfy_port})에 연결할 수 없습니다. ComfyUI를 먼저 실행한 후 [작업 재시도]를 클릭하십시오."
            elif "out of memory" in raw_err.lower() or "cuda" in raw_err.lower() and "memory" in raw_err.lower():
                diagnostic = "GPU VRAM 부족(OOM) 오류입니다. 해상도를 848x480으로 낮추거나 하드웨어 프로파일을 VRAM_12GB_ECO로 변경하십시오."
            elif "timeout" in raw_err.lower():
                diagnostic = "추론 렌더링 시간이 초과되었습니다 (30분 초과). 백엔드 상태를 점검하십시오."
            else:
                diagnostic = raw_err

            print(f"[TaskQueueManager] 태스크({task_id}) 실패: {diagnostic}")
            self.update_task_status(
                task_id, "FAILED", 0, "작업 실패", error_msg=diagnostic
            )

    def retry_task(self, task_id: str) -> bool:
        """실패한 작업을 PENDING 상태로 재등록하여 재실행"""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET status = 'PENDING', progress = 0, progress_msg = '재시도 대기 중', error_message = NULL, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (task_id,),
            )
            conn.commit()
        updated = self.get_task(task_id)
        if updated:
            self._notify_listeners(updated)
        return True


if __name__ == "__main__":
    mgr = TaskQueueManager()
    tasks = mgr.list_tasks(5)
    print(f"[TaskQueueManager] DB 초기화 완료. 현재 등록된 태스크 수: {len(tasks)}")
