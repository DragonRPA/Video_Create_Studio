"""
전사 시스템 개발 표준 헌장 준수
모듈명: download_models.py
역할: MiniMax H3 공식 가중치 모델(DiT, Text Encoder, VAE, Turbo LoRA) Hugging Face 자동 다운로더
"""

import os
import sys
import time
from pathlib import Path
import requests
from config import MODELS_DIR

# Hugging Face 공식 Comfy-Org/MiniMax-H3 저장소 경로
HF_BASE_URL = "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main"

PACKAGES = {
    "1": {
        "name": "기본 T2V/I2V 필수 패키지 (권장)",
        "desc": "텍스트 및 이미지 기반 비디오+오디오 생성 필수 모델 (약 39.5 GB)",
        "files": [
            {
                "rel_path": "diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors",
                "size_gb": 19.52,
                "dest_folder": "diffusion_models",
            },
            {
                "rel_path": "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
                "size_gb": 14.61,
                "dest_folder": "text_encoders",
            },
            {
                "rel_path": "vae/minimax_h3_video_vae_fp16.safetensors",
                "size_gb": 4.85,
                "dest_folder": "vae",
            },
            {
                "rel_path": "vae/minimax_h3_audio_vae_fp32.safetensors",
                "size_gb": 0.56,
                "dest_folder": "vae",
            },
        ],
    },
    "2": {
        "name": "Omni R2V 레퍼런스 확장 패키지",
        "desc": "인물 및 모션 소스 교체(Ref2VA) 전용 Diffusion 모델 (약 19.5 GB)",
        "files": [
            {
                "rel_path": "diffusion_models/minimax_h3_ref2va_pruned_fp8_scaled.safetensors",
                "size_gb": 19.52,
                "dest_folder": "diffusion_models",
            }
        ],
    },
    "3": {
        "name": "Turbo 4-Step / 8-Step 가속 LoRA",
        "desc": "초고속 4스텝 렌더링 지원 LoRA (약 3.6 GB)",
        "files": [
            {
                "rel_path": "loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors",
                "size_gb": 1.82,
                "dest_folder": "loras",
            },
            {
                "rel_path": "loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
                "size_gb": 1.82,
                "dest_folder": "loras",
            },
        ],
    },
}


def download_file_stream(url: str, dest_path: Path, expected_size_gb: float):
    """스트리밍 청크 다운로드 및 이어받기 지원"""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".part")

    downloaded = 0
    if temp_path.exists():
        downloaded = temp_path.stat().st_size

    # 이미 완료된 파일 검사
    if dest_path.exists():
        actual_size = dest_path.stat().st_size / (1024**3)
        if actual_size >= expected_size_gb * 0.95:
            print(f"[완료됨] {dest_path.name} ({actual_size:.2f} GB)")
            return

    headers = {}
    if downloaded > 0:
        headers["Range"] = f"bytes={downloaded}-"
        print(f"[이어받기] {dest_path.name} ({downloaded / (1024**2):.1f} MB 부터 재개)")
    else:
        print(f"[다운로드 시작] {dest_path.name} ({expected_size_gb:.2f} GB)")

    start_time = time.time()
    last_print = 0

    with requests.get(url, headers=headers, stream=True, timeout=30) as r:
        if r.status_code == 416:  # Range Not Satisfiable -> 이미 완료
            if temp_path.exists():
                temp_path.rename(dest_path)
            return
        r.raise_for_status()

        total_bytes = int(r.headers.get("content-length", 0)) + downloaded
        mode = "ab" if downloaded > 0 else "wb"

        with open(temp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB 청크
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    if now - last_print > 0.5:
                        last_print = now
                        elapsed = max(0.1, now - start_time)
                        speed_mb = (downloaded / (1024 * 1024)) / elapsed
                        pct = (downloaded / total_bytes * 100) if total_bytes > 0 else 0
                        sys.stdout.write(
                            f"\r진행률: {pct:5.1f}% | {downloaded / (1024**3):5.2f}GB / {total_bytes / (1024**3):5.2f}GB | 속도: {speed_mb:5.1f} MB/s"
                        )
                        sys.stdout.flush()

    sys.stdout.write("\n")
    if temp_path.exists():
        temp_path.rename(dest_path)
    print(f"[다운로드 완료] {dest_path.name}")


def main():
    print("=" * 70)
    print("MiniMax H3 공식 Hugging Face 가중치 다운로더")
    print(f"로컬 저장소: {MODELS_DIR}")
    print("=" * 70)

    print("\n[다운로드 패키지 목록]")
    for key, pkg in PACKAGES.items():
        print(f"  [{key}] {pkg['name']}")
        print(f"      - 설명: {pkg['desc']}")
        for f in pkg["files"]:
            print(f"      * {f['rel_path']} ({f['size_gb']} GB)")

    print("  [A] 전체 패키지 일괄 다운로드")
    print("  [Q] 종료")

    choice = input("\n다운로드할 번호를 입력하십시오 (기본값: 1): ").strip().upper() or "1"

    if choice == "Q":
        print("종료합니다.")
        return

    selected_files = []
    if choice == "A":
        for pkg in PACKAGES.values():
            selected_files.extend(pkg["files"])
    elif choice in PACKAGES:
        selected_files.extend(PACKAGES[choice]["files"])
    else:
        print("잘못된 입력입니다.")
        return

    total_req_gb = sum(f["size_gb"] for f in selected_files)
    print(f"\n총 다운로드 대상: {len(selected_files)}개 파일 (약 {total_req_gb:.2f} GB)")
    confirm = input("다운로드를 계속 진행하시겠습니까? (Y/n): ").strip().lower()
    if confirm in ["", "y", "yes"]:
        for f in selected_files:
            file_url = f"{HF_BASE_URL}/{f['rel_path']}"
            dest = MODELS_DIR / f["dest_folder"] / Path(f["rel_path"]).name
            try:
                download_file_stream(file_url, dest, f["size_gb"])
            except Exception as e:
                print(f"\n[오류 발생] {f['rel_path']} 다운로드 실패: {e}")
        print("\n모든 선택 항목의 다운로드 처리가 완료되었습니다.")
    else:
        print("다운로드가 취소되었습니다.")


if __name__ == "__main__":
    main()
