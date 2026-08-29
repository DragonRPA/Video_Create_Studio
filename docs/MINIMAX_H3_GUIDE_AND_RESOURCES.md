# MiniMax H3 공식 마크다운 작성 원칙 및 레퍼런스 가이드

---

## 1. MiniMax H3 규격 마크다운(Markdown) 작성 원칙

MiniMax H3(Hailuo DiT)는 **단일 자연어 문장보다 정형화된 마크다운 3블록 공식(Formula)**을 주입할 때 모션 왜곡을 최소화하고, 영화적 카메라 워크와 자연스러운 오디오(대사·효과음·BGM)를 완벽히 동기화하여 생성합니다.

### 1.1 공식 3블록 마크다운 프롬프트 포뮬러 (H3 Prompt Formula)

```markdown
### [Block 1: Reference Material Notes]
* **Asset 1 (@image1):** Character Reference - lock face, clothing, and body proportions
* **Asset 2 (@video2):** Motion Reference - lock the running and jumping motion dynamics
* **Asset 3 (@audio3):** Voice Reference - speech timbre and tone for diegetic dialogue

### [Block 2: Core Idea]
A concise summary of the scene's intent, atmosphere, narrative context, and primary subject action in 1-2 sentences.

### [Block 3: Scene-by-Scene Description]
**integrated_multimodal_description:**
* **[Shot 1] (0.00s - 04.00s):** [Detailed visual description including subjects, environment, camera movement, and physical action. Include diegetic dialogue in double quotes: "Look over there!"]
* **[Shot 2] (04.00s - 06.00s):** [Follow-up cut with secondary action, camera pan, or subject reaction.]

**overall_soundscape:** 
[Foley effects, footsteps, physical contact sounds, room tone, weather ambience (e.g., heavy rain hitting asphalt, distant thunder).]

**non_diegetic_music:** 
[Background score, instrumentation, genre, tempo, and mood (e.g., Dark orchestral cyberpunk synthwave with low cello drone) or "None/Silence".]
```

---

### 1.2 프롬프트 작성 6대 핵심 원칙 (Best Practices)

1. **에셋 역할 선언 (Role Taxonomy)**:
   - 레퍼런스 미디어 사용 시 `@image1`, `@video2` 등에 명확한 역할(`Character Reference`, `Motion Reference`, `Keyframe First`, `Keyframe Last`, `Voice Reference`)을 선언해야 모델이 혼동 없이 반영합니다.
2. **카메라 정면 응시 방지 (Anti-Lens Stare)**:
   - 인물이 어색하게 렌즈만 쳐다보는 현상을 막기 위해, 시선 방향(예: `"eyes anchored to the neon sign"`, `"gazing at the distant horizon"`, `"not looking at the camera lens"`)을 명시합니다.
3. **물리 현상 및 동적 모션 서술 (Physics & Motion Descriptors)**:
   - 정적인 포즈 대신 연속적인 물리적 상호작용(`"dissolve into mist"`, `"raindrops bouncing off leather coat"`, `"sparks igniting from metal contact"`)을 서술합니다.
4. **직접 대사(Diegetic Dialogue) 표기**:
   - 영상 속 인물이 직접 발화하는 대사는 반드시 큰따옴표(`"..."`)로 감싸 서술합니다.
5. **카메라 무빙 명칭 규격화**:
   - `Slow Cinematic Push-in`, `Smooth Steadicam Tracking`, `Orbit 360`, `Pan Left-to-Right`, `Crane Down`, `FPV Drone` 등 영화적 표준 용어를 사용합니다.
6. **사운드스케이프와 BGM의 분리**:
   - 현장 효과음(`overall_soundscape`)과 배경 음악(`non_diegetic_music`)을 구분하여 입력해야 깨끗한 오디오가 생성됩니다.

---

## 2. 공식 문서 및 핵심 레퍼런스 페이지 리스트

| 구분 | 리소스 명칭 | 공식 URL | 주요 내용 |
|---|---|---|---|
| **공식 포털** | MiniMax AI 공식 웹사이트 | [https://www.minimax.io](https://www.minimax.io) | MiniMax 기업 소개, 모델 스펙, 공식 API 문서 |
| **공식 플랫폼** | Hailuo AI 비디오 플랫폼 | [https://hailuoai.video](https://hailuoai.video) | MiniMax 기반 온라인 영상 생성 및 프롬프트 쇼케이스 |
| **공식 가중치** | Hugging Face Comfy-Org MiniMax-H3 | [https://huggingface.co/Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) | FP8 Scaled DiT 가중치, Qwen3-VL 텍스트 인코더, VAE 공식 저장소 |
| **튜토리얼** | ComfyUI 공식 MiniMax 가이드 | [https://docs.comfy.org/tutorials/video/minimax](https://docs.comfy.org/tutorials/video/minimax) | ComfyUI 환경 구축, 노드 연결 및 기본 워크플로우 설명 |
| **커뮤니티 빌드** | Kijai MiniMax-H3 Experimental | [https://huggingface.co/Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental) | 최신 실험용 노드 패치 및 양자화 체크포인트 |
| **가속 커널** | SageAttention v2 공식 GitHub | [https://github.com/thu-ml/SageAttention](https://github.com/thu-ml/SageAttention) | 35~40% 추론 속도 단축을 위한 SageAttention v2 커널 빌드 |
| **통합 가이드** | Awesome MiniMax H3 Integration | [https://github.com/MiniMax-AI/awesome-minimax-h3-integration](https://github.com/MiniMax-AI/awesome-minimax-h3-integration) | 전 세계 커뮤니티 워크플로우 및 노드 모음 |

---

## 3. 추천 유튜브 컨텐츠 리스트 (인기도 & 유용성 순위 Top 10)

| 순위 | 영상 제목 | 채널 / 크리에이터 | 핵심 다루는 내용 및 추천 포인트 |
|---|---|---|---|
| **1** | **무료 MiniMax H3, Seedance를 넘어설 수 있을까?** | [일단해봐](https://www.youtube.com/watch?v=sNk_bZDxM5w) | MiniMax H3의 성능 실전 테스트, 프롬프트 활용법 및 Seedance와의 가성비/품질 비교 분석 |
| **2** | **ComfyUI MiniMax H3: Best Video Generation Workflows (Ep29)** | Pixaroma | T2V, I2V, R2V 및 네이티브 오디오 싱크까지 총망라한 결정판 워크플로우 가이드 |
| **3** | **MiniMax H3 — Full ComfyUI Workflow Tutorial (Local + Free Cloud)** | AI Video Master | 로컬 RTX GPU 환경에서의 제로-투-러닝 원클릭 세팅 및 VRAM 최적화 팁 |
| **4** | **MiniMax H3 Video-to-Video Editing is INSANE \| Full ComfyUI Tutorial** | Prompting Pixels | 원본 비디오의 모션을 유지하면서 캐릭터/스타일만 교체하는 Ref2VA 완벽 튜토리얼 |
| **5** | **How to use MiniMax H3 All-In-One Workflow** | AI Revolution | 단일 ComfyUI 인터페이스에서 텍스트/이미지/립싱크를 한 번에 전환하는 올인원 워크플로우 |
| **6** | **Seedance 2.5 vs MiniMax H3 (Hailuo) 실전 영상 제작 완벽 비교** | AI 크리에이터 Lab | 전문 납품용 퀄리티 vs 저비용 B컷/인서트 양산 가성비 분석 및 혼합 파이프라인 |
| **7** | **MiniMax H3 6GB~12GB VRAM 저사양 최적화 및 SageAttention 가속 가이드** | Tech Diffusion | RTX 3060/4060급 저사양 환경에서 FP8/GGUF 양자화와 SageAttention으로 속도 2배 뽑는 법 |
| **8** | **MiniMax H3 Ref2VA: 인물 캐릭터 일관성 유지 및 오디오 동기화 마스터** | AI Cinema Studio | 여러 컷에 걸쳐 동일 인물의 외모를 완벽히 고정하고 음성을 동기화하는 캐릭터 락킹 기법 |
| **9** | **Hailuo AI / MiniMax H3 마크다운 프롬프트 100% 마스터 클래스** | Visual AI Master | 3블록 공식 마크다운 작성법, 카메라 앵글 및 물리 묘사 단어집(Cheat Sheet) 제공 |
| **10** | **ComfyUI 4-Step Turbo LoRA로 MiniMax H3 3배 빠르게 렌더링하기** | Generative AI Lab | 4-스텝 가속 LoRA 노드를 장착하여 렌더링 시간을 1/3로 단축하는 실전 세팅 |
