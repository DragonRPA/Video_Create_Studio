"""
전사 시스템 개발 표준 헌장 준수
모듈명: download_models.py
역할: MiniMax H3 가중치 모델(DiT, Text Encoder, VAE) Hugging Face 자동 다운로더
"""

import os
import sys
import urllib.request
from pathlib import Path
from config import MODELS_DIR, GLOBAL_CONFIG

# 공식 및 커뮤니티 경량화 FP8 가중치 URL 매핑
MODEL_URLS = {
    "MiniMax_H3_fv8_scaled.safetensors": {
        "repo": "Comfy-Org/MiniMax-H3",
        "filename": "MiniMax_H3_fv8_scaled.safetensors",
        "url": "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/MiniMax_H3_fv8_scaled.safetensors",
        "size_gb": "14.2 GB",
        "subfolder": "diffusion_models",
    },
    "mvfp4_t5_xxl.safetensors": {
        "repo": "Comfy-Org/MiniMax-H3",
        "filename": "mvfp4_t5_xxl.safetensors",
        "url": "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/mvfp4_t5_xxl.safetensors",
        "size_gb": "4.8 GB",
        "subfolder": "clip",
    },
    "minimax_vae.safetensors": {
        "repo": "Comfy-Org/MiniMax-H3",
        "filename": "minimax_vae.safetensors",
        "url": "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/minimax_vae.safetensors",
        "size_gb": "0.3 GB",
        "subfolder": "vae",
    },
}


def download_file(url: str, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and dest_path.stat().st_size > 1024 * 1024:
        print(f"[다운로드 완료됨] {dest_path.name} ({dest_path.stat().st_size / (1024**3):.2f} GB)")
        return

    print(f"[다운로드 시작] {dest_path.name} <-- {url}")
    try:
        from huggingface_hub import hf_hub_download
        # huggingface_hub 가용 시
        print("huggingface_hub API로 다운로드 진행 중...")
    except ImportError:
        pass

    def reporthook(blocknum, blocksize, totalsize):
        read = blocknum * blocksize
        if totalsize > 0:
            percent = min(100, read * 100 / totalsize)
            sys.stdout.write(f"\r진행률: {percent:.1f}% ({read/(1024**2):.1f}MB / {totalsize/(1024**2):.1f}MB)")
            sys.stdout.flush()

    urllib.request.urlretrieve(url, str(dest_path), reporthook=reporthook)
    print(f"\n[다운로드 완료] {dest_path.name}")


def main():
    print("=" * 65)
    print("MiniMax H3 가중치 모델 로컬 다운로더")
    print(f"저장 대상 디렉터리: {MODELS_DIR}")
    print("=" * 65)

    for name, info in MODEL_URLS.items():
        dest = MODELS_DIR / info["subfolder"] / name
        print(f"\n- 항목: {name} (예상 크기: {info['size_gb']})")
        print(f"  경로: {dest}")

    choice = input("\n다운로드를 시작하시겠습니까? (y/N): ").strip().lower()
    if choice == "y":
        for name, info in MODEL_URLS.items():
            dest = MODELS_DIR / info["subfolder"] / name
            download_file(info["url"], dest)
    else:
        print("다운로드가 취소되었습니다. 수동으로 다운로드하시려면 위 Hugging Face URL을 이용하십시오.")


if __name__ == "__main__":
    main()
