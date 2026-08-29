"""
전사 시스템 개발 표준 헌장 준수
모듈명: backend_orchestrator.py
역할: ComfyUI 및 Ollama 백엔드 생명주기 완전 자동화 (원클릭 자동 설치, 백그라운드 기동 및 종료 제어)
"""

import os
import sys
import time
import shutil
import atexit
import subprocess
from pathlib import Path
from typing import Optional, Callable
import requests

from config import GLOBAL_CONFIG, WORKSPACE_DIR, MODELS_DIR

COMFY_DIR = Path(WORKSPACE_DIR) / "ComfyUI"
COMFY_MAIN = COMFY_DIR / "main.py"
EXTRA_MODELS_YAML = Path(WORKSPACE_DIR) / "extra_model_paths.yaml"

_comfy_process: Optional[subprocess.Popen] = None


class BackendOrchestrator:
    @staticmethod
    def is_comfy_running() -> bool:
        """ComfyUI 포트 8188 응답 여부 확인"""
        try:
            r = requests.get(f"{GLOBAL_CONFIG.comfy_http_url}/system_stats", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    @staticmethod
    def ensure_comfy_installed(progress_cb: Optional[Callable[[str], None]] = None) -> bool:
        """ComfyUI 및 필수 노드가 없으면 자동 설치"""
        if COMFY_MAIN.exists():
            return True

        if progress_cb:
            progress_cb("ComfyUI 백엔드가 발견되지 않아 자동 설치를 진행합니다...")

        # 1. ComfyUI 저장소 클론
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git", str(COMFY_DIR)],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception as e:
            if progress_cb:
                progress_cb(f"ComfyUI Git 복제 실패: {e}")
            return False

        # 2. VideoHelperSuite 노드 설치
        nodes_dir = COMFY_DIR / "custom_nodes"
        vhs_dir = nodes_dir / "ComfyUI-VideoHelperSuite"
        if not vhs_dir.exists():
            if progress_cb:
                progress_cb("비디오 확장 노드(VideoHelperSuite) 설치 중...")
            try:
                subprocess.run(
                    ["git", "clone", "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git", str(vhs_dir)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except Exception:
                pass

        # 3. extra_model_paths.yaml 복사
        dest_yaml = COMFY_DIR / "extra_model_paths.yaml"
        if EXTRA_MODELS_YAML.exists():
            shutil.copy(str(EXTRA_MODELS_YAML), str(dest_yaml))

        # 4. 패키지 설치
        if progress_cb:
            progress_cb("ComfyUI 의존성 패키지 점검 및 설치 중...")
        try:
            req_file = COMFY_DIR / "requirements.txt"
            if req_file.exists():
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], check=False)
        except Exception:
            pass

        return COMFY_MAIN.exists()

    @classmethod
    def start_backend_async(cls, progress_cb: Optional[Callable[[str], None]] = None) -> bool:
        """백그라운드에서 ComfyUI 서버 기동"""
        global _comfy_process

        if cls.is_comfy_running():
            if progress_cb:
                progress_cb("ComfyUI 백엔드 서버가 이미 활성화되어 있습니다.")
            return True

        # 설치 여부 점검
        if not COMFY_MAIN.exists():
            ok = cls.ensure_comfy_installed(progress_cb)
            if not ok:
                if progress_cb:
                    progress_cb("ComfyUI 설치에 실패했습니다.")
                return False

        # 모델 경로 파일 갱신 보장
        dest_yaml = COMFY_DIR / "extra_model_paths.yaml"
        if EXTRA_MODELS_YAML.exists():
            shutil.copy(str(EXTRA_MODELS_YAML), str(dest_yaml))

        if progress_cb:
            progress_cb("ComfyUI 백엔드 서버를 백그라운드로 자동 실행합니다...")

        cmd = [
            sys.executable,
            str(COMFY_MAIN),
            "--listen", "127.0.0.1",
            "--port", str(GLOBAL_CONFIG.comfy_port),
            "--windows-standalone-build",
        ]

        # Windows 백그라운드 플래그
        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.CREATE_NO_WINDOW

        try:
            _comfy_process = subprocess.Popen(
                cmd,
                cwd=str(COMFY_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        except Exception as e:
            if progress_cb:
                progress_cb(f"ComfyUI 실행 실패: {e}")
            return False

        # 포트 활성화 대기 (최대 25초)
        for i in range(25):
            time.sleep(1.0)
            if cls.is_comfy_running():
                if progress_cb:
                    progress_cb("ComfyUI 백엔드 서버가 준비되었습니다 (포트 8188 연결됨).")
                return True
            if progress_cb and i % 3 == 0:
                progress_cb(f"ComfyUI 기동 대기 중 ({i+1}/25초)...")

        return cls.is_comfy_running()

    @classmethod
    def stop_backend(cls):
        """앱 종료 시 백그라운드 프로세스 정리"""
        global _comfy_process
        if _comfy_process:
            try:
                _comfy_process.terminate()
                _comfy_process.wait(timeout=3)
            except Exception:
                try:
                    _comfy_process.kill()
                except Exception:
                    pass
            _comfy_process = None


# 파이썬 종료 시 자동 리소스 해제 등록
atexit.register(BackendOrchestrator.stop_backend)


if __name__ == "__main__":
    def log(msg):
        print(f"[Orchestrator] {msg}")

    print("ComfyUI 자동 기동 테스트...")
    success = BackendOrchestrator.start_backend_async(log)
    print(f"기동 결과: {'성공' if success else '실패'}")
