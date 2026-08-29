# 릴리즈 노트 (Release Notes)

## [v1.0.0.Build.1] - 2026-08-29 14:10

### 1. 신규 구축 및 핵심 아키텍처 (Initial Release)
- **MiniMax H3 비디오 생성 엔진 로컬 전자동화**:
  - MiniMax H3 DiT (`MiniMax_H3_fv8_scaled.safetensors`), T5 Text Encoder (`mvfp4`), VAE 파이프라인 연동.
  - **SageAttention v2 커널 가속**: 35~40% 추론 시간 단축 패치 노드 통합.
- **로컬 SLM 기반 마크다운 프롬프트 자동 변환기 (`prompt_refiner.py`)**:
  - Ollama / Qwen 2.5 7B 연동을 통한 MiniMax H3 5단 계층 마크다운 프롬프트 자동 생성.
  - 3중 방어 원칙(LLM 파싱, 재시도, 고품질 휴리스틱 템플릿 폴백) 적용.
- **Headless ComfyUI 워크플로우 엔진 (`comfy_workflow_engine.py`)**:
  - T2V (Text-to-Video), I2V (First & Last Frame 모핑), R2V (Omni Reference 캐릭터/모션 교체 - Ref2VA) 지원.
  - Flow Shift (1.0~10.0) 및 실시간 WebSocket/REST 진행률 모니터링.
- **FFmpeg 비디오/오디오 후처리 파이프라인 (`post_processor.py`)**:
  - 레퍼런스 비디오 오디오 추출 및 최종 영상 1:1 싱크 합성.
  - 다중 씬(Storyboard) 자동 결합(`concatenate_scenes`), 24fps 프레임 정규화, 썸네일 생성.
- **SQLite 기반 비동기 태스크 큐 및 오케스트레이터 (`task_queue_manager.py`)**:
  - 비동기 백그라운드 렌더링 워커, 상태머신(PENDING, REFINING, QUEUED, RENDERING, POST_PROCESSING, COMPLETED, FAILED) 관리.
- **전사 표준 준수 데스크톱 GUI (`app_gui.py`)**:
  - 카테고리 3.1 무수식어 건조한 명사·동사 표준 UI.
  - 카테고리 3.2 줄바꿈 방지 (`white-space: nowrap`) 테이블 및 레이블.
  - 카테고리 3.4 레이블-입력창 상하 세로 스택 레이아웃 100% 적용.
- **CLI/GUI 통합 런처 (`main.py`)**:
  - `--refine`, `--t2v`, `--list`, `--worker`, `--gui` 지원.
