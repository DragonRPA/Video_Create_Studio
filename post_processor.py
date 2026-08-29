"""
전사 시스템 개발 표준 헌장 준수
모듈명: post_processor.py
역할: FFmpeg 기반 비디오/오디오 후처리, 레퍼런스 사운드 추출/합성, 다중 씬 결합, 코덱 최적화
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from config import GLOBAL_CONFIG, WORKSPACE_DIR


class FFmpegPostProcessor:
    def __init__(self, ffmpeg_bin: Optional[str] = None, ffprobe_bin: Optional[str] = None):
        self.ffmpeg_bin = ffmpeg_bin or self._detect_binary(GLOBAL_CONFIG.ffmpeg_binary)
        self.ffprobe_bin = ffprobe_bin or self._detect_binary(GLOBAL_CONFIG.ffprobe_binary)

    def _detect_binary(self, name: str) -> str:
        """시스템 PATH 또는 로컬 디렉터리에서 바이너리 탐색"""
        found = shutil.which(name)
        if found:
            return found
        local_candidate = Path(WORKSPACE_DIR) / "tools" / f"{name}.exe"
        if local_candidate.exists():
            return str(local_candidate)
        return name

    def is_available(self) -> bool:
        """FFmpeg 사용 가능 여부 검사"""
        try:
            res = subprocess.run(
                [self.ffmpeg_bin, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False

    def extract_audio(self, video_path: str, output_audio_path: str) -> bool:
        """비디오 파일에서 원본 오디오 스트림 추출"""
        video_p = Path(video_path)
        out_p = Path(output_audio_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i", str(video_p),
            "-vn",
            "-acodec", "copy",
            str(out_p),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if res.returncode != 0:
                cmd_fallback = [
                    self.ffmpeg_bin,
                    "-y",
                    "-i", str(video_p),
                    "-vn",
                    "-acodec", "aac",
                    "-b:a", "192k",
                    str(out_p),
                ]
                res_fb = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                return res_fb.returncode == 0
            return True
        except Exception as e:
            print(f"[FFmpeg] 오디오 추출 실패: {e}")
            return False

    def merge_video_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        match_shortest: bool = True,
    ) -> bool:
        """생성된 비디오와 오디오 트랙을 1:1 싱크 합성"""
        video_p = Path(video_path)
        audio_p = Path(audio_path)
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i", str(video_p),
            "-i", str(audio_p),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", GLOBAL_CONFIG.audio_bitrate,
            "-map", "0:v:0",
            "-map", "1:a:0",
        ]
        if match_shortest:
            cmd.append("-shortest")
        cmd.append(str(out_p))

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            return res.returncode == 0
        except Exception as e:
            print(f"[FFmpeg] 비디오-오디오 병합 실패: {e}")
            return False

    def optimize_video(
        self,
        input_path: str,
        output_path: str,
        target_fps: int = 24,
        crf: int = 19,
        codec: Optional[str] = None,
    ) -> bool:
        """비디오 최적화 및 24fps 표준 프레임 정규화"""
        inp = Path(input_path)
        outp = Path(output_path)
        outp.parent.mkdir(parents=True, exist_ok=True)
        use_codec = codec or GLOBAL_CONFIG.video_codec

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i", str(inp),
            "-r", str(target_fps),
            "-c:v", use_codec,
            "-crf", str(crf),
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(outp),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            return res.returncode == 0
        except Exception as e:
            print(f"[FFmpeg] 비디오 최적화 실패: {e}")
            return False

    def concatenate_scenes(
        self,
        video_paths: List[str],
        output_path: str,
    ) -> bool:
        """다중 씬(스토리보드) 비디오 순차 결합"""
        outp = Path(output_path)
        outp.parent.mkdir(parents=True, exist_ok=True)

        # concat 파일 생성
        concat_list_file = outp.parent / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in video_paths:
                f.write(f"file '{Path(p).resolve().as_posix()}'\n")

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(outp),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if concat_list_file.exists():
                concat_list_file.unlink()
            return res.returncode == 0
        except Exception as e:
            print(f"[FFmpeg] 씬 결합 실패: {e}")
            return False

    def generate_thumbnail(self, video_path: str, output_thumb_path: str, sec: float = 0.5) -> bool:
        """비디오 썸네일 이미지 추출"""
        inp = Path(video_path)
        outp = Path(output_thumb_path)
        outp.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-ss", str(sec),
            "-i", str(inp),
            "-vframes", "1",
            "-q:v", "2",
            str(outp),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            return res.returncode == 0
        except Exception as e:
            print(f"[FFmpeg] 썸네일 추출 실패: {e}")
            return False


if __name__ == "__main__":
    processor = FFmpegPostProcessor()
    avail = processor.is_available()
    print(f"[FFmpegPostProcessor] FFmpeg 가용 상태: {'정상' if avail else '미설치/PATH미등록'}")
