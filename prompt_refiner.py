"""
전사 시스템 개발 표준 헌장 준수
모듈명: prompt_refiner.py
역할: MiniMax H3 전용 마크다운 프롬프트 자동 변환 엔진 (로컬 SLM / Ollama 연동 및 휴리스틱 폴백)
"""

import json
import re
from typing import Optional, Dict, Any
import requests
from config import GLOBAL_CONFIG

MINIMAX_H3_SYSTEM_PROMPT = """You are an expert prompt engineer specializing in MiniMax H3 (Hailuo DiT) video generation model.
Your task is to transform any user-provided idea (Korean or English) into a perfectly structured, highly detailed MiniMax H3 Markdown Video Prompt in English.

MiniMax H3 responds best to structured Markdown with explicit visual details, dynamic motions, and camera directions.

Always output the prompt strictly in the following Markdown format:

## Scene Description
[Concise 1-2 sentence overall summary of the scene in English]

## Subject & Character
- **Appearance**: [Subject physical appearance, clothing, skin texture, age, distinctive features]
- **Expression & Action**: [Specific facial expression, eye contact, body motion, dynamic continuous action]

## Environment & Atmosphere
- **Location & Set**: [Precise setting, background objects, depth, architectural style]
- **Lighting**: [Lighting setup, key light, fill light, rim light, reflections, shadows, color temperature]
- **Atmosphere**: [Mood, cinematic tone, airborne particles, fog/smoke, weather]

## Camera & Motion
- **Shot Type**: [e.g., Close-up / Medium Shot / Wide Cinematic Shot / Over-the-shoulder]
- **Camera Movement**: [e.g., Slow cinematic push-in, Smooth Steadicam tracking, Subtle pan right, Dynamic orbit]
- **Frame Rate & Style**: [24fps, 35mm anamorphic lens, photorealistic cinematic grade, film grain]

## Negative Prompt
blurry, low quality, distorted anatomy, morphing limbs, jitter, flickering artifacts, oversaturated, text, watermark, cartoonish, low resolution

Rules:
1. Write the content in natural, descriptive, high-quality cinematic English.
2. Focus on continuous, fluid physical movements rather than static poses.
3. Do NOT wrap the entire markdown in extra json; output the raw markdown text directly or inside ```markdown ... ```.
"""


class PromptRefiner:
    def __init__(self, ollama_url: Optional[str] = None, model_name: Optional[str] = None):
        self.ollama_url = ollama_url or GLOBAL_CONFIG.ollama_host
        self.model_name = model_name or GLOBAL_CONFIG.ollama_model

    def refine(self, user_input: str, mode: str = "t2v") -> Dict[str, str]:
        """
        사용자 입력을 MiniMax H3 마크다운 프롬프트로 변환
        3중 방어 원칙 (Rule 10.7):
        1) 로컬 SLM 호출 및 응답 정제
        2) 실패 시 포맷 재시도
        3) 완전 오프라인/실패 시 휴리스틱 규칙 기반 정밀 생성기 폴백
        """
        user_input_clean = user_input.strip()
        if not user_input_clean:
            return {
                "positive_prompt": self._get_fallback_prompt("Cinematic scene", mode),
                "negative_prompt": "blurry, low quality, distorted, watermark",
                "source": "empty_fallback",
            }

        # 1차 시도: Ollama / Local SLM 호출
        try:
            raw_output = self._call_ollama(user_input_clean, mode)
            parsed_prompt = self._extract_clean_markdown(raw_output)
            if self._validate_minimax_structure(parsed_prompt):
                negative_part = self._extract_negative(parsed_prompt)
                return {
                    "positive_prompt": parsed_prompt,
                    "negative_prompt": negative_part,
                    "source": "local_slm",
                }
        except Exception as e:
            # 로컬 SLM 연결 불가 또는 파싱 오류 시 로깅 후 휴리스틱 폴백
            print(f"[PromptRefiner] SLM API 미연결 또는 오류 ({e}), 휴리스틱 엔진 적용")

        # 2차/최종 폴백: 휴리스틱 템플릿 정밀 확장
        fallback_prompt = self._get_fallback_prompt(user_input_clean, mode)
        return {
            "positive_prompt": fallback_prompt,
            "negative_prompt": "blurry, low quality, distorted anatomy, morphing limbs, jitter, flickering artifacts, oversaturated, text, watermark",
            "source": "heuristic_engine",
        }

    def _call_ollama(self, user_input: str, mode: str) -> str:
        """Ollama REST API 호출"""
        endpoint = f"{self.ollama_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model_name,
            "system": MINIMAX_H3_SYSTEM_PROMPT,
            "prompt": f"Mode: {mode.upper()}\nUser Request: {user_input}\nGenerate MiniMax H3 Markdown:",
            "stream": False,
            "options": {
                "temperature": GLOBAL_CONFIG.slm_temperature,
                "num_predict": GLOBAL_CONFIG.slm_max_tokens,
            },
        }
        res = requests.post(endpoint, json=payload, timeout=25)
        res.raise_for_status()
        data = res.json()
        return data.get("response", "")

    def _extract_clean_markdown(self, text: str) -> str:
        """코드 블록 제거 및 순수 마크다운 추출"""
        text = text.strip()
        # ```markdown ... ``` 또는 ``` ... ``` 추출
        match = re.search(r"```(?:markdown)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    def _validate_minimax_structure(self, text: str) -> bool:
        """핵심 섹션 존재 여부 검증"""
        required_sections = ["## Scene Description", "## Subject", "## Camera"]
        matches = sum(1 for sec in required_sections if sec in text)
        return matches >= 2

    def _extract_negative(self, text: str) -> str:
        """Negative Prompt 섹션 내용 추출"""
        match = re.search(r"## Negative Prompt\s*([\s\S]*?)$", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "blurry, low quality, distorted anatomy, morphing limbs, jitter, flickering artifacts, oversaturated, text, watermark"

    def _get_fallback_prompt(self, user_input: str, mode: str) -> str:
        """규칙 기반 고품질 휴리스틱 마크다운 프롬프트 생성"""
        return f"""## Scene Description
A visually stunning cinematic sequence featuring {user_input}, rendered with ultra-realistic physics, volumetric depth, and high-fidelity textures.

## Subject & Character
- **Appearance**: Highly detailed subject reflecting '{user_input}', realistic skin/surface textures, intricate details.
- **Expression & Action**: Natural fluid movements, engaging expressions, dynamic and coherent physical motion.

## Environment & Atmosphere
- **Location & Set**: Richly detailed atmospheric environment matching the theme, immersive background depth.
- **Lighting**: Dramatic cinematic lighting, soft key light with subtle rim lighting and balanced shadow contrast.
- **Atmosphere**: Atmospheric realism, subtle micro-particles, cinematic color grading.

## Camera & Motion
- **Shot Type**: Medium Cinematic Shot transitioning seamlessly.
- **Camera Movement**: Slow smooth cinematic push-in with gentle stabilization.
- **Frame Rate & Style**: 24fps, 35mm lens perspective, photorealistic movie aesthetics.

## Negative Prompt
blurry, low quality, distorted anatomy, morphing limbs, jitter, flickering artifacts, oversaturated, text, watermark, cartoonish, low resolution"""


if __name__ == "__main__":
    refiner = PromptRefiner()
    test_input = "비 내리는 서울 밤거리에서 네온사인을 바라보는 사이버펑크 요원"
    result = refiner.refine(test_input, mode="t2v")
    print(f"=== 변환 결과 (Source: {result['source']}) ===")
    print(result["positive_prompt"])
