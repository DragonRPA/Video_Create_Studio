# MiniMax H3 로컬 독립실행 영상 생성 스튜디오

## 1. 개요
본 시스템은 **MiniMax H3 (Hailuo DiT)** 오픈소스 영상 생성 멀티모달 모델을 로컬 환경에서 전자동으로 구동하기 위한 독립실행(Standalone) 어플리케이션입니다.

- **핵심 엔진**: MiniMax H3 DiT + T5 Text Encoder (`mvfp4`) + MiniMax VAE
- **가속 최적화**: SageAttention v2 커널 노드 주입 (생성 시간 35~40% 단축)
- **프롬프트 자동화**: Ollama / 로컬 SLM(Qwen 2.5 7B 등) 기반 MiniMax 규격 마크다운 자동 생성
- **후처리**: FFmpeg 기반 오디오 추출/재합성 및 24fps MP4 H.264/AV1 최적화

---

## 2. 파일 구성
```
d:/01.AntiGravity/Video_Create_Studio/
├── config.py                 # 전역 설정 및 VRAM 하드웨어 프로파일
├── prompt_refiner.py         # MiniMax H3 마크다운 프롬프트 자동 변환 엔진
├── comfy_workflow_engine.py  # ComfyUI Headless API 및 SageAttention 노드 주입
├── post_processor.py         # FFmpeg 비디오/오디오 후처리 및 싱크 합성
├── task_queue_manager.py     # SQLite 태스크 큐 및 오케스트레이션 상태머신
├── app_gui.py                # 데스크톱 GUI (전사 카테고리 III UI 표준 준수)
├── main.py                   # 통합 실행 진입점 (CLI/GUI/워커)
├── requirements.txt          # 패키지 의존성 목록
└── video_studio.db           # 로컬 SQLite 데이터베이스
```

---

## 3. 실행 방법

### 3.1 데스크톱 GUI 실행
```bash
python main.py
```

### 3.2 프롬프트 자동 변환 CLI 테스트
```bash
python main.py --refine "비 내리는 서울 밤거리에서 네온사인을 바라보는 사이버펑크 요원"
```

### 3.3 작업 대장 목록 확인
```bash
python main.py --list
```

### 3.4 백그라운드 렌더링 워커 데몬 실행
```bash
python main.py --worker
```

---

## 4. 하드웨어 요구사항 및 프로파일

| 프로파일 명칭 | 권장 사양 | 해상도 | 단계(Steps) | 양자화 | SageAttention |
|---|---|---|---|---|---|
| `VRAM_12GB_ECO` | RTX 3060/4060 (12GB) | 848x480 | 20 | FP8 Scaled | 활성화 |
| `VRAM_16GB_BALANCED` | RTX 4070Ti/4080 (16GB) | 1280x720 | 25 | FP8 Scaled | 활성화 |
| `VRAM_24GB_HIGH` | RTX 3090/4090 (24GB) | 1280x720 | 30 | BF16 | 활성화 |
