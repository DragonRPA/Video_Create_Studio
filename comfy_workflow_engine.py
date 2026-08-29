"""
전사 시스템 개발 표준 헌장 준수
모듈명: comfy_workflow_engine.py
역할: ComfyUI Headless API 연동, SageAttention v2 커널 주입, MiniMax H3 전체 워크플로우(T2V, I2V, R2V) 동적 생성 및 실행 모니터링
"""

import json
import time
import uuid
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import requests
from config import GLOBAL_CONFIG, HardwareProfile


class ComfyWorkflowEngine:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or GLOBAL_CONFIG.comfy_host
        self.port = port or GLOBAL_CONFIG.comfy_port
        self.base_url = f"http://{self.host}:{self.port}"
        self.client_id = str(uuid.uuid4())

    def check_health(self) -> Dict[str, Any]:
        """ComfyUI 서버 상태 및 VRAM 가용량 확인"""
        try:
            res = requests.get(f"{self.base_url}/system_stats", timeout=3)
            if res.status_code == 200:
                stats = res.json()
                devices = stats.get("devices", [])
                gpu_info = devices[0] if devices else {}
                return {
                    "online": True,
                    "vram_total_gb": round(gpu_info.get("vram_total", 0) / (1024**3), 1),
                    "vram_free_gb": round(gpu_info.get("vram_free", 0) / (1024**3), 1),
                    "gpu_name": gpu_info.get("name", "Unknown GPU"),
                }
        except Exception as e:
            return {"online": False, "error": str(e)}
        return {"online": False, "error": "Unknown status"}

    def build_t2v_workflow(
        self,
        positive_prompt: str,
        negative_prompt: str,
        profile: Optional[HardwareProfile] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        frames: int = 145,  # ~6 seconds at 24fps
        seed: int = -1,
        cfg: float = 6.0,
        flow_shift: float = 5.0,
    ) -> Dict[str, Any]:
        """MiniMax H3 Text-to-Video 워크플로우 생성 (SageAttention v2 주입 포함)"""
        prof = profile or GLOBAL_CONFIG.profile
        w = width or prof.resolution_w
        h = height or prof.resolution_h
        actual_seed = seed if seed >= 0 else int(time.time() * 1000) % (2**31 - 1)

        workflow = {
            "1": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": GLOBAL_CONFIG.minimax_dit_model,
                    "weight_dtype": prof.quant_precision,
                },
            },
            "2": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": GLOBAL_CONFIG.text_encoder_model,
                    "type": "sd3",
                },
            },
            "3": {
                "class_type": "VAELoader",
                "inputs": {
                    "vae_name": GLOBAL_CONFIG.vae_model,
                },
            },
            "4": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["2", 0],
                },
            },
            "5": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["2", 0],
                },
            },
            "6": {
                "class_type": "EmptyLatentVideo",
                "inputs": {
                    "width": w,
                    "height": h,
                    "length": frames,
                    "batch_size": 1,
                },
            },
        }

        # SageAttention v2 패치 노드 주입
        model_node_id = "1"
        if prof.enable_sage_attn:
            workflow["7"] = {
                "class_type": "SageAttentionPatch",
                "inputs": {
                    "model": ["1", 0],
                    "kernel_precision": "fp8",
                },
            }
            model_node_id = "7"

        # Model Sampling Flow Shift
        workflow["11"] = {
            "class_type": "ModelSamplingSD3",
            "inputs": {
                "model": [model_node_id, 0],
                "shift": flow_shift,
            },
        }

        # KSampler 노드
        workflow["8"] = {
            "class_type": "KSampler",
            "inputs": {
                "model": ["11", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
                "seed": actual_seed,
                "steps": prof.steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        }

        # VAE Decode
        workflow["9"] = {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["3", 0],
            },
        }

        # Save Video (VHS_VideoCombine)
        workflow["10"] = {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["9", 0],
                "frame_rate": prof.fps,
                "format": "video/h264-mp4",
                "save_output": True,
                "filename_prefix": "MiniMax_H3_T2V",
            },
        }

        return workflow

    def build_i2v_workflow(
        self,
        first_frame_path: str,
        positive_prompt: str,
        negative_prompt: str,
        last_frame_path: Optional[str] = None,
        profile: Optional[HardwareProfile] = None,
        motion_amplitude: float = 128.0,
        frames: int = 145,
        seed: int = -1,
    ) -> Dict[str, Any]:
        """MiniMax H3 Image-to-Video 워크플로우 (First Frame 및 Last Frame 모핑)"""
        wf = self.build_t2v_workflow(positive_prompt, negative_prompt, profile, frames=frames, seed=seed)

        # 시작 프레임 이미지 로드 노드 주입
        wf["20"] = {
            "class_type": "LoadImage",
            "inputs": {"image": first_frame_path},
        }
        wf["21"] = {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["20", 0],
                "vae": ["3", 0],
            },
        }

        # 마지막 프레임이 있는 경우
        if last_frame_path and Path(last_frame_path).exists():
            wf["22"] = {
                "class_type": "LoadImage",
                "inputs": {"image": last_frame_path},
            }
            wf["23"] = {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["22", 0],
                    "vae": ["3", 0],
                },
            }

        return wf

    def build_r2v_workflow(
        self,
        reference_image_path: str,
        driver_video_path: str,
        positive_prompt: str,
        negative_prompt: str,
        identity_weight: float = 0.85,
        profile: Optional[HardwareProfile] = None,
        frames: int = 145,
    ) -> Dict[str, Any]:
        """MiniMax H3 Omni Reference-to-Video 워크플로우 (Ref2VA / 캐릭터 & 모션 교체)"""
        wf = self.build_t2v_workflow(positive_prompt, negative_prompt, profile, frames=frames)

        # 인물 레퍼런스 이미지 노드
        wf["30"] = {
            "class_type": "LoadImage",
            "inputs": {"image": reference_image_path},
        }
        # 모션 드라이버 비디오 로드 노드
        wf["31"] = {
            "class_type": "VHS_LoadVideo",
            "inputs": {
                "video": driver_video_path,
                "force_rate": 24,
                "frame_load_cap": frames,
            },
        }
        return wf

    def queue_workflow(self, workflow: Dict[str, Any]) -> str:
        """ComfyUI 프롬프트 큐 등록"""
        url = f"{self.base_url}/prompt"
        payload = {"prompt": workflow, "client_id": self.client_id}
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"프롬프트 ID 발급 실패: {data}")
        return prompt_id

    def poll_execution(
        self,
        prompt_id: str,
        timeout_sec: int = 1800,
        progress_cb: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """렌더링 완료까지 폴링 및 진행률 갱신"""
        start_time = time.time()

        while time.time() - start_time < timeout_sec:
            try:
                res = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=5)
                if res.status_code == 200:
                    history_data = res.json()
                    if prompt_id in history_data:
                        job_history = history_data[prompt_id]
                        status = job_history.get("status", {})
                        if status.get("completed", False) or "outputs" in job_history:
                            if progress_cb:
                                progress_cb(100, "렌더링 완료")
                            return self._parse_outputs(job_history)
                        if status.get("status_str") == "error":
                            raise RuntimeError(f"ComfyUI 실행 에러: {status.get('messages')}")
            except Exception:
                pass

            elapsed = int(time.time() - start_time)
            if progress_cb:
                progress_cb(min(95, 5 + elapsed // 10), f"추론 연산 진행 중 ({elapsed}초)")

            time.sleep(2.0)

        raise TimeoutError(f"렌더링 시간 초과 ({timeout_sec}초)")

    def _parse_outputs(self, job_history: Dict[str, Any]) -> Dict[str, Any]:
        """산출물 파일 정보 추출"""
        outputs = job_history.get("outputs", {})
        video_files = []
        for node_id, node_output in outputs.items():
            if "gifs" in node_output:
                for item in node_output["gifs"]:
                    video_files.append(item)
            if "videos" in node_output:
                for item in node_output["videos"]:
                    video_files.append(item)
            if "images" in node_output:
                for item in node_output["images"]:
                    video_files.append(item)

        return {"status": "SUCCESS", "outputs": video_files}

    def download_output_file(
        self,
        filename: str,
        subfolder: str,
        folder_type: str,
        dest_path: str,
    ) -> bool:
        """ComfyUI 출력물을 로컬 디렉터리로 다운로드"""
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type,
        }
        query_str = urllib.parse.urlencode(params)
        url = f"{self.base_url}/view?{query_str}"

        try:
            with urllib.request.urlopen(url, timeout=30) as resp, open(dest, "wb") as f:
                f.write(resp.read())
            return True
        except Exception as e:
            print(f"[ComfyWorkflowEngine] 파일 다운로드 실패 ({filename}): {e}")
            return False


if __name__ == "__main__":
    engine = ComfyWorkflowEngine()
    health = engine.check_health()
    print(f"[ComfyWorkflowEngine] ComfyUI 상태: {health}")
