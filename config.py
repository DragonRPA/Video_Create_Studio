"""
전사 시스템 개발 표준 헌장 준수
모듈명: config.py
역할: MiniMax H3 로컬 영상 생성 스튜디오 전역 설정, 화면비 및 프리셋 관리
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR
INPUTS_DIR = WORKSPACE_DIR / "inputs"
OUTPUTS_DIR = WORKSPACE_DIR / "outputs"
WORKFLOWS_DIR = WORKSPACE_DIR / "workflows"
MODELS_DIR = WORKSPACE_DIR / "models"
DB_PATH = WORKSPACE_DIR / "video_studio.db"

# 기본 디렉터리 자동 생성
for d in [INPUTS_DIR, OUTPUTS_DIR, WORKFLOWS_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# 화면비 프리셋
ASPECT_RATIOS = {
    "16:9 (가로 표준 720p)": (1280, 720),
    "16:9 (가로 HD 1080p)": (1920, 1080),
    "9:16 (세로 쇼츠 720p)": (720, 1280),
    "1:1 (정사각형 768p)": (768, 768),
    "21:9 (시네마스코프)": (1344, 576),
}

# 카메라 무빙 프리셋
CAMERA_PRESETS = [
    "기본 (프롬프트 자동 결정)",
    "Slow Push-in (전진 확대)",
    "Pull-out (후진 축소)",
    "Pan Left-to-Right (좌에서 우로 패닝)",
    "Pan Right-to-Left (우에서 좌로 패닝)",
    "Orbit 360 (피사체 중심 회전)",
    "Crane Down (상하 수직 하강)",
    "Crane Up (상하 수직 상승)",
    "FPV Drone Tracking (역동적 드론 추적)",
    "Static Camera (카메라 고정 / 피사체 모션)",
]

# 조명 및 무드 프리셋
LIGHTING_PRESETS = [
    "기본 (자연스러운 영화 톤)",
    "Cinematic Film 35mm (아나모픽 렌즈 필름 질감)",
    "Moody Noir (고대비 흑백/어두운 명암)",
    "Cyberpunk Neon (화려한 네온 빛 반사)",
    "Golden Hour (따뜻한 일몰 자연광)",
    "Studio Softbox (부드러운 스튜디오 조명)",
    "Volumetric Fog Rays (안개 속 빛줄기 연출)",
]


@dataclass
class HardwareProfile:
    name: str
    vram_gb: int
    resolution_w: int
    resolution_h: int
    fps: int
    steps: int
    flow_shift: float
    enable_sage_attn: bool
    enable_cpu_offload: bool
    quant_precision: str  # fp8_e4m3fn, fp8_e5m2, gguf_q4, bf16


# 하드웨어별 프로파일 프리셋
HARDWARE_PROFILES: Dict[str, HardwareProfile] = {
    "VRAM_12GB_ECO": HardwareProfile(
        name="12GB 저용량 (RTX 3060/4060)",
        vram_gb=12,
        resolution_w=848,
        resolution_h=480,
        fps=24,
        steps=20,
        flow_shift=5.0,
        enable_sage_attn=True,
        enable_cpu_offload=True,
        quant_precision="fp8_e4m3fn",
    ),
    "VRAM_16GB_BALANCED": HardwareProfile(
        name="16GB 표준 (RTX 4070Ti Super/4080)",
        vram_gb=16,
        resolution_w=1280,
        resolution_h=720,
        fps=24,
        steps=25,
        flow_shift=5.0,
        enable_sage_attn=True,
        enable_cpu_offload=False,
        quant_precision="fp8_e4m3fn",
    ),
    "VRAM_24GB_HIGH": HardwareProfile(
        name="24GB 고성능 (RTX 3090/4090)",
        vram_gb=24,
        resolution_w=1280,
        resolution_h=720,
        fps=24,
        steps=30,
        flow_shift=5.0,
        enable_sage_attn=True,
        enable_cpu_offload=False,
        quant_precision="bf16",
    ),
}


@dataclass
class StudioConfig:
    # ComfyUI Headless 연동 설정
    comfy_host: str = "127.0.0.1"
    comfy_port: int = 8188
    comfy_ws_url: str = "ws://127.0.0.1:8188/ws"
    comfy_http_url: str = "http://127.0.0.1:8188"

    # 로컬 SLM (Ollama / Local API) 설정
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    slm_temperature: float = 0.4
    slm_max_tokens: int = 1024

    # 공식 검증 가중치 모델 파일명 (Comfy-Org/MiniMax-H3 기준)
    minimax_dit_model: str = "minimax_h3_fl2va_pruned_fp8_scaled.safetensors"
    minimax_r2v_model: str = "minimax_h3_ref2va_pruned_fp8_scaled.safetensors"
    text_encoder_model: str = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
    video_vae_model: str = "minimax_h3_video_vae_fp16.safetensors"
    audio_vae_model: str = "minimax_h3_audio_vae_fp32.safetensors"

    # FFmpeg 설정
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"
    video_codec: str = "libx264"
    crf: int = 19
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"

    # 기본 하드웨어 프로파일
    active_profile: str = "VRAM_16GB_BALANCED"

    @property
    def vae_model(self) -> str:
        return self.video_vae_model

    @property
    def profile(self) -> HardwareProfile:
        return HARDWARE_PROFILES.get(
            self.active_profile, HARDWARE_PROFILES["VRAM_16GB_BALANCED"]
        )


GLOBAL_CONFIG = StudioConfig()
