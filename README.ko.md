<h1 align="center">ΠΑΙΔΕΙΑ · Paideia <sub>for Hermes</sub></h1>

<p align="center">
  <strong>내 강의. 내 패턴. 내 실수. 내 치트시트.</strong><br>
  <em>내 자료를 영구적이고 편집 가능한 코스별 학습 그래프로 바꾸는 <a href="https://github.com/NousResearch/hermes-agent">hermes-agent</a> 플러그인 — 모든 산출물이 일반 강의계획서가 아니라 당신에게서 빚어집니다.</em>
</p>

<p align="center">
  <a href="https://github.com/OPTIMETA/PAIDEIA-Alt"><img height="30" src="https://img.shields.io/badge/Exam_Radar-OPTIMETA_Alt_plugin-333333?style=for-the-badge&labelColor=000000&color=333333" alt="Exam Radar — OPTIMETA Alt plugin"></a>
</p>

<p align="center">
  <sub><em><a href="https://github.com/OPTIMETA/PAIDEIA-Alt"><strong>Exam Radar</strong></a>(OPTIMETA Alt 플러그인)로 강의를 캡처하고 Paideia로 공부하세요. <code>/paideia alt</code>로 로드맵을 바로 흘려보낼 수 있습니다.</em></sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-333333?style=flat-square&labelColor=000000&color=333333" alt="License: MIT">
  <img src="https://img.shields.io/badge/hermes--agent-000000?style=flat-square&logo=anthropic&logoColor=white&labelColor=000000&color=000000" alt="hermes-agent">
  <img src="https://img.shields.io/badge/Plugin-000000?style=flat-square&labelColor=000000&color=000000" alt="Plugin">
  <img src="https://img.shields.io/badge/Model--agnostic-000000?style=flat-square&labelColor=000000&color=000000" alt="Model-agnostic">
  <img src="https://img.shields.io/badge/Markdown-000000?style=flat-square&logo=markdown&logoColor=white&labelColor=000000&color=000000" alt="Markdown">
  <img src="https://img.shields.io/badge/Python-000000?style=flat-square&logo=python&logoColor=white&labelColor=000000&color=000000" alt="Python">
  <img src="https://img.shields.io/badge/Ollama-000000?style=flat-square&logo=ollama&logoColor=white&labelColor=000000&color=000000" alt="Ollama">
  <img src="https://img.shields.io/badge/Qwen3--VL-000000?style=flat-square&labelColor=000000&color=000000" alt="Qwen3-VL">
  <img src="https://img.shields.io/badge/Tesseract-000000?style=flat-square&labelColor=000000&color=000000" alt="Tesseract">
  <img src="https://img.shields.io/badge/LaTeX-000000?style=flat-square&logo=latex&logoColor=white&labelColor=000000&color=000000" alt="LaTeX">
  <img src="https://img.shields.io/badge/Obsidian-000000?style=flat-square&logo=obsidian&logoColor=white&labelColor=000000&color=000000" alt="Obsidian">
</p>

<p align="center">
  <a href="./README.md">English README</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/OPTIMETA/PAIDEIA"><strong>PAIDEIA</strong> — 원본 (Claude Code)</a>
  &nbsp;·&nbsp;
  <a href="https://taewoopark.com"><strong>taewoopark.com</strong> — 제작자 사이트</a>
</p>

> **재작성이 아니라 포팅입니다.** PAIDEIA-Hermes는 [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)(원래 Claude Code 플러그인)를 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)의 확장 표면 위에 다시 표현한 것입니다. 같은 형성 사이클, 같은 온디스크 레이아웃, 같은 MIT 라이선스. hermes는 **모델 비종속적**이므로 동일한 플러그인이 hermes가 가리키는 어떤 provider 위에서도 동작합니다 — `~/.hermes/config.yaml`이 `provider: openai-codex`라면 Paideia는 **Codex(gpt-5.5)**로 구동되며, `/model`로 바꿔도 Paideia 쪽은 아무것도 바뀌지 않습니다.

> **보안 공지.** PAIDEIA-Hermes는 hermes-agent 플러그인(`hermes plugins install …`)으로 설치되며, `.zip` 다운로드·`.exe` 실행·별도 인스톨러를 절대 요구하지 않습니다. 이 README에서 명시적으로 링크되지 않은, PAIDEIA 이름을 쓰는 다른 저장소는 이 프로젝트와 무관합니다.

<p align="center">
  <em>일반 학습 도구는 평균 강의계획서를 가르칩니다. Paideia는 <strong>당신의</strong> 강의계획서를 가르칩니다 —<br>
  교수님의 노트, 당신의 숙제 강조점, 당신의 손글씨, 당신의 실수로부터. 모든 산출물은 당신이 편집할 수 있는 markdown 파일입니다.</em>
</p>

---

## Paideia의 의미

고대 그리스에서 **Παιδεία**는 수동적 학생에게 사실을 적립하는 것이 결코 아니었습니다. 그것은 — 원전과의 구조화된 만남, 스승 아래의 안내된 연습, 피드백을 더 깊은 개정으로 접어 넣는 성찰적 대화를 통한 — 온전한 인간의 평생에 걸친 형성이었습니다.

이 플러그인은 그 사이클을 수학·물리·공학 과목의 **시험 대비**라는 한정된 문제에 구현합니다:

```
  ingest ──▶ analyze ──▶ drill ──▶ grade ──▶ weakmap ──▶ cheatsheet
     ▲                                                        │
     └────────────────── 피드백 루프 ──────────────────────────┘
```

모든 단계는 코스 폴더에 영원히 남는 markdown 산출물을 만듭니다. 휘발되는 것도, API 뒤에 숨는 것도 없습니다. hermes가 모델 비종속적이므로 모델을 바꿔도 깨지지 않습니다.

---

## 일반 학습 도구가 못 하는 것

대부분의 학습 도구는 *당신의* 과목·교수·실수에 개인화할 수 없습니다 — 파는 상품이 일반 커리큘럼이기 때문입니다.

- **Coursera, edX, Khan Academy** — 고정 커리큘럼; 교수님이 실제로 무엇을 강조하는지 모름.
- **Quizlet, Anki** — 모든 카드를 직접 큐레이션; 당신의 풀이집에서 패턴을 뽑지 않음.
- **Chegg, Course Hero** — 일반 풀이집; 당신 과목의 반복 어법으로 정리돼 있지 않음.
- **ChatGPT Study Mode, Gemini, NotebookLM** — 코스별 영속 상태 없음. 매 세션이 백지에서 시작.

어느 것도 눈앞의 자료를 중심으로 이해를 *형성*하지 않습니다. Paideia는 반대로 합니다: 모든 산출물이 *당신의* 폴더 — 강의노트, 교재, 숙제, 풀이, 손글씨 시도 — 에서 파생되어, 편집 가능한 markdown으로 영구히 쌓입니다.

| 축 | Paideia | 일반 edu-SaaS / LLM 챗 |
|-----|---------|------------------------------|
| 풀이 패턴 (`P1..Pk`) | *당신 과목의* 풀이에서 추출, 당신 파일을 인용 | 일반 교재 리스트 또는 없음 |
| 드릴 우선순위 | *교수님의* 숙제 강조(숙제 빈도=시험 등급)로 가중 | 고정 커리큘럼 또는 추측 |
| 치트시트 | *당신의* `errors/log.md`에서 — 실제로 틀린 것 | 강의계획서 보일러플레이트 |
| 세션 간 코스 상태 | 영구 markdown+YAML, 작업하며 성장 | 대화 리셋; 히스토리는 유료 |
| 동의 안 되는 산출물 편집 | `.md`를 열어 저장 | 읽기 전용 UI |
| 작업하는 모델 | **당신이 설정한 것** — Nous, OpenAI/Codex, Anthropic, OpenRouter, 로컬 | 벤더 종속 |

플러그인은 hermes(당신이 고른 유료/로컬 모델 구동)로 무거운 일을 하지만, 산출물은 모두 디스크에 plain markdown으로 남습니다. 구독을 멈추든, provider를 바꾸든, 완전 로컬로 가든 — course-index, patterns, error log, weakmaps, cheatsheets는 전부 당신이 열고 읽고 편집하고 diff할 수 있습니다. 비계는 플러그인이고, 학습 그래프는 당신 것입니다.

기본 OCR은 에이전트 자체의 네이티브 비전(당신 hermes provider가 노출하는 멀티모달 모델)을 씁니다. 손글씨 PDF가 기기를 떠나지 않길 원하면, `ollama pull qwen3-vl:8b` 한 번(~6 GB)으로 이후 모든 OCR이 로컬 Qwen3-VL 추론으로 바뀝니다.

---

## 핵심 원리: 숙제 빈도 = 시험 확률

대부분의 "스마트하게 공부하기" 조언은 약점을 사냥하라고 합니다. 그건 **거꾸로**입니다. 교수님은 숙제를 내줌으로써 시험 포인트가 어디인지 *이미 알려줬습니다*. 숙제가 많은 섹션은 🔥🔥 Exam-primary. 숙제가 0인 섹션은 ⚪ Low-risk — "숨은 함정"이 아닙니다. 교수의 생략은 그 주제가 시험에서 빠진다는 가장 강력한 신호입니다.

| 등급 | 섹션 숙제 수 | 처리 | 모의고사 배점 비중 |
|------|---------------------|-----------|---------------------------|
| 🔥🔥 Exam-primary | 3+ | 가장 강하게 드릴 | ≥70% |
| 🔥 Exam-likely | 2 | 다음으로 드릴 | ~25% |
| 🟡 Exam-possible | 1 | 가볍게 복습 | ≤5% |
| ⚪ Low-risk | 0 | 참조만 | 0 |

`/paideia quiz all`, `/paideia mock`, `/paideia hwmap hot`이 모두 이 등급으로 출력을 가중합니다. ⚪ 섹션을 굳이 드릴하면 한 번은 따르되 시험 확률이 낮다고 경고합니다.

---

## 형성 사이클, 단계별로

| 단계 | 하는 일 | 명령어 | 산출물 |
|-------|-------------|----------|----------|
| **만남(Encounter)** | 교수의 신호를 읽음 | `/paideia ingest` | `converted/**/*.md` — 모든 강의·교재·숙제·풀이를 깔끔한 LaTeX markdown으로 |
| **구조(Structure)** | 과목의 문법을 추출 | `/paideia analyze` | `course-index/{summary,patterns,coverage}.md` — 토픽 트리, 반복 패턴(P1..Pk), 숙제 빈도 시험 등급 |
| **연습(Practice)** | 교수가 실제로 내는 것에 가중된 능동 회상 | `/paideia quiz`·`twin`·`blind`·`chain`·`mock` | `quizzes/`·`twins/`·`chain/`·`mock/` — 종이에 푸는 문제 |
| **성찰(Reflection)** | 손글씨가 채점이 됨 | `/paideia grade` | `answers/converted/<name>.md` + `errors/log.md` — 에이전트 비전(기본)/Ollama/Tesseract OCR 후 전략 채점 |
| **진단(Diagnosis)** | 오류를 우선순위 약점 리포트로 압축 | `/paideia weakmap` | `weakmap/weakmap_<ts>.md` — 추가 전용 히스토리 |
| **증류(Distillation)** | 한 페이지, 오류 기반, 인쇄 가능 | `/paideia cheatsheet`·`derive`·`pattern` | `cheatsheet/final.md`, `derivations/<slug>.md` |

보조: `/paideia hwmap`(숙제 빈도 시험 확률), `/paideia status`(사이클 위치), `/paideia init`(코스 폴더 부트스트랩).

---

## 설치

### 사전 요구사항

**필수**

- [hermes-agent](https://github.com/NousResearch/hermes-agent), 임의의 provider(Nous Portal, OpenAI/Codex, Anthropic, OpenRouter, 로컬, …).
- Python 3 + Unix 셸(`bash`/`zsh`; Windows는 WSL2).
- `poppler`(`pdftoppm`) — 모든 OCR 티어 필수.
  - **macOS**: `brew install poppler tesseract tesseract-lang`
  - **Linux**: `apt-get install poppler-utils tesseract-ocr tesseract-ocr-kor`
- Python 라이브러리(지연 — ingest/grade/cheatsheet 시): `pip install pypdf pdfplumber pdf2image pillow reportlab pytesseract`

**선택 — `--ocr=ollama`용(모든 페이지 이미지가 기기에 남음)**

- `ollama` + `qwen3-vl:8b`(~6 GB). `ollama pull qwen3-vl:8b`.

언제든 `/paideia doctor`로 위 항목을 점검하세요(`/paideia doctor --fix`로 안전 항목 자동 수정). 에이전트의 `terminal`이 쓰는 바로 그 `python3`를 검사하므로 실제로 돌릴 수 있는지를 정확히 보고합니다.

### 플러그인 설치

```bash
hermes plugins install OPTIMETA/PAIDEIA-Hermes
hermes plugins enable paideia
```

hermes 재시작 후 모든 세션에서 `/paideia`가 뜹니다. 대안:

```bash
# B) 유저 플러그인 디렉터리에 직접 clone
git clone https://github.com/OPTIMETA/PAIDEIA-Hermes ~/.hermes/plugins/paideia
hermes plugins enable paideia

# C) 개발/로컬 (심링크 — 수정이 다음 세션에 바로 반영)
git clone https://github.com/OPTIMETA/PAIDEIA-Hermes && ./PAIDEIA-Hermes/install.sh
```

`~/.hermes/config.yaml`은 손댈 필요 없습니다 — `~/.hermes/plugins/paideia/`에서 자동 발견됩니다.

### 코스별 부트스트랩

코스 폴더에서 hermes를 열고 마법사를 돌리거나:

```
/paideia init
```

…한 줄로 비대화식 스캐폴딩:

```
/paideia init name="복소해석 MATH 405" exam=2026-12-15 type=final lang=ko ocr=claude weak="등각적분"
```

의존성을 점검하고, 인터페이스 언어 `en|ko`, `COURSE_NAME`, `EXAM_DATE`, `EXAM_TYPE`, `USER_WEAK_ZONES`, OCR 엔진을 (인자로 또는 대화로) 받은 뒤 디렉터리 스켈레톤·`.course-meta`·`PAIDEIA.md`를 만들고 `errors/log.md`를 시드합니다. 단일 채점만 엔진 덮어쓰기: `/paideia grade --ocr=claude path/to/answer.pdf`.

---

## 코스 폴더 레이아웃

```
my-course/
├── .course-meta                     # 코스명, 시험일, 인터페이스 언어(en|ko), OCR 엔진
├── PAIDEIA.md                       # 에이전트가 읽는 코스별 워크플로 컨텍스트
├── .gitignore                       # 원본 스캔·OCR 스크래치 숨김; 학습 그래프 본체는 커밋 유지
│
├── materials/                       # 원본 파일을 여기 둠 (PDF/MD)
│   ├── lectures/  textbook/  homework/  solutions/
├── converted/                       # 자동 생성 markdown — 편집 금지 (/paideia ingest 출력)
│   ├── lectures/  textbook/  homework/  solutions/
├── course-index/                    # 지식 베이스 — /paideia analyze 생성
│   ├── summary.md  patterns.md  coverage.md  radar.md
├── answers/                         # 손글씨 스캔 PDF를 여기 둠
│   └── converted/                   # /paideia grade 가 OCR markdown을 씀
├── errors/log.md                    # 추가 전용 YAML 오류 로그 (/weakmap·/cheatsheet 씨앗)
├── quizzes/  mock/  twins/  chain/  derivations/  cheatsheet/  weakmap/
```

**손으로 편집하는 디렉터리는 둘뿐**: `materials/`(원본 PDF/MD), `answers/`(손글씨 스캔). 나머지는 `/paideia` 명령이 생성하며 재생성 가능합니다. 온디스크 레이아웃은 **상위 [PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)와 바이트 호환**이라 코스 폴더가 Claude Code 플러그인과 이 hermes 포트 사이를 그대로 오갑니다.

---

## 읽기 팁: Obsidian

Paideia는 모든 것을 LaTeX 수식(`$...$`, `$$...$$`) 포함 plain markdown으로 씁니다. **[Obsidian](https://obsidian.md)**이 자연스러운 선택입니다: MathJax 수식 렌더링(설정 0), 백링크로 `quizzes/`에서 인용된 `converted/lectures/`로 클릭 이동, 코스 폴더 전체를 검색 가능한 그래프 vault로. 터미널은 수식에 약하니 맞서지 마세요.

## 그리고 강의 끝단: Alt

Obsidian이 읽기 끝단의 동반자라면, **[Alt](https://www.altalt.io/ko/)**는 강의가 들어오는 다른 끝단의 동반자입니다. Alt가 강의를 녹음·전사하고, OPTIMETA의 **Exam Radar** 플러그인이 교수의 구두 강조 강도로 토픽을 랭크합니다. 그걸 `/paideia alt`로 Paideia에 넣으면 루프가 닫힙니다: **강의 듣기 → 캡처 → 시험 신호 추출 → 중요한 것 공부.**

---

## 전체 워크플로 — 예시

**Phase 0 — 코스당 1회(15분).** `materials/{lectures,textbook,homework,solutions}/`에 PDF를 넣고:

```
/paideia ingest                     # 모든 PDF → 비전 파이프라인 (PDF당 서브에이전트, LaTeX 충실)
/paideia analyze <약점 힌트>        # patterns + coverage + summary 구축
/paideia hwmap hot                  # 🔥🔥 시험 핵심존 표시
```

**Phase 1 — 진단(40분).** `/paideia quiz all 20` → 종이에 풀고 `answers/diagnostic.pdf`로 스캔 → `/paideia grade`.

**Phase 2 — 집중 드릴(대부분의 시간).** `/paideia weakmap` → `/paideia blind hw3-p2` · `/paideia twin hw3-p2` · `/paideia chain 3` · `/paideia quiz weakmap 5`.

**Phase 3 — 통합(~90분).** `/paideia mock 90` → 종이 풀이·스캔 → `/paideia grade`.

**Phase 4 — 압축(전날 밤).** `/paideia cheatsheet --pdf` · `/paideia weakmap`.

**Phase 5 — 쿨다운(시험 10분 전).** `/paideia weakmap` — 상위 3개만. 새로운 건 배우지 말 것.

---

## 명령어 (총 16개)

`/paideia <서브커맨드> [인자]` — `/paideia help`로 목록 확인.

| 명령어 | 목적 |
|---------|---------|
| `/paideia init [name=… exam=… …]` | 코스 폴더 부트스트랩(마법사 또는 인자 한 줄) |
| `/paideia doctor [--fix]` | 설치+워크스페이스 진단; `--fix`는 권한 불필요 항목 수리 |
| `/paideia status` | 한 줄 `코스 · D-N · 단계 · 최다 실수 패턴` |
| `/paideia ingest [--force]` | `materials/**` PDF → `converted/**` markdown(PDF당 서브에이전트) |
| `/paideia analyze [힌트]` | `course-index/{summary,patterns,coverage}.md` 구축 |
| `/paideia hwmap hot\|<§>` | 숙제 빈도순 🔥🔥 시험 핵심 섹션 |
| `/paideia pattern <§\|Pk\|키워드>` | course-index 패턴 카드 |
| `/paideia derive <대상>` | `derivations/<slug>.md`에 깔끔한 참조 유도 |
| `/paideia quiz <주제\|§\|weakmap> [N]` | 연습문제 N개, 정답은 `_answers.md`에 숨김 |
| `/paideia blind <problem-id>` | 알려진 문제의 전략 점검 드릴 |
| `/paideia twin <problem-id>` | 같은 패턴·새 표면 변형 |
| `/paideia chain <N>` | N개 패턴 통합 문제 |
| `/paideia mock <분>` | 숙제 가중 모의고사 |
| `/paideia grade [--ocr=<엔진>] [경로]` | 답안 PDF OCR + 전략 채점 + `errors/log.md` 기록 |
| `/paideia weakmap [개념]` | 우선순위 약점 리포트 → `weakmap/weakmap_<ts>.md` |
| `/paideia cheatsheet [--pdf]` | 오류 기반 한 페이지 |
| `/paideia alt [붙여넣기]` | OPTIMETA Exam Radar(Alt) export 가져오기 → `radar.md` + `coverage.md` 강의강조 열 |

---

## Slack 및 기타 메시징 게이트웨이

PAIDEIA-Hermes는 CLI뿐 아니라 hermes 메시징 게이트웨이(Slack, Discord, Telegram, …)에서도 동작합니다. 플랫폼의 타입드-커맨드 접두사를 쓰세요(Slack/Matrix는 `!`, 그 외 대부분 `/`):

- **결정적 커맨드** — `!paideia status`·`doctor`·`init …`·`help` — 텍스트로 바로 응답.
- **에이전트 구동 커맨드** — `!paideia ingest|analyze|quiz|grade|weakmap|mock|twin|…` — `pre_gateway_dispatch` 훅이 일반 에이전트 턴으로 재작성(게이트웨이엔 인세션 `inject_message`가 없음). 접두사 없는 문구도 동작: `paideia quiz §1.2 3`.

게이트웨이는 설정된 작업 디렉터리(`terminal.cwd`)에서 돌므로 그 경로를 코스 폴더로 두세요. 각 커맨드가 `.course-meta`의 `INTERFACE_LANG`을 직접 읽어 Slack에서도 한/영 산문이 유지됩니다.

---

## 내부 동작

### Ingest 파이프라인: 모든 PDF에 비전

`/paideia ingest`는 `materials/**`의 모든 PDF를 하나의 비전 파이프라인으로 보냅니다. `pdfplumber`는 수식·그림·다단 레이아웃이 섞이면 산문 페이지조차 깨져 신뢰 불가였기에 전부 비전으로 통일했습니다. `materials/**/*.md`는 출처 헤더와 함께 그대로 복사됩니다.

모든 페이지를 `dpi=160` PNG로 렌더링하고 **에이전트가 읽기 전에** 긴 변 ≤1800px로 리사이즈(초과 이미지는 멀티모달이 거부)한 뒤, hermes가 **PDF당 서브에이전트 하나를 위임**하여 각자 페이지를 *순차로* 읽어 LaTeX markdown으로 전사합니다 — `ℏ ∂ p2 …` 대신 `$$\hat H = -\frac{\hbar^2}{2m}\partial_x^2 + V(x)$$`. 자세히는 `skills/paideia-pdf/VISION.md`.

### 손글씨 OCR: 세 엔진, 당신이 선택

채팅에 수식을 타이핑하지 않습니다 — 종이에 풀고 스캔해 `answers/`에 넣고 `/paideia grade`. 엔진은 코스별(`.course-meta`의 `OCR_ENGINE`)이며 호출별로 `--ocr=`로 덮어씁니다:

| 엔진 | 기본? | 동작 | 선택 기준 |
|---|---|---|---|
| `claude` | **예** | `pdftoppm`로 페이지 렌더 → 에이전트가 자체 네이티브 비전으로 각 PNG를 읽어 markdown 합성. 추가 설치 없음. | 기본 경로. |
| `ollama` | 옵트인 | `pd_vision_ocr.py --engine=ollama` → 로컬 Qwen3-VL 8B + tesseract 자동 폴백. | 페이지 이미지가 기기를 떠나면 안 될 때. |
| `tesseract` | 옵트인 | `pd_vision_ocr.py --engine=tesseract` → pytesseract(`eng`/`eng+kor`). | 가장 가벼움; 타이핑 스캔에 적당. |

> 기본 엔진 이름이 `claude`인 것은 상위 PAIDEIA와의 온디스크 호환 때문이며, hermes에서는 **"에이전트 자체의 네이티브 비전"**(provider가 노출하는 멀티모달 모델, 예: `openai-codex`의 gpt-5.5)을 뜻합니다. Anthropic에 묶이지 않습니다.

### 줄 단위가 아닌 전략 채점

OCR 노이즈로 엄밀한 대수 채점은 무용하고, 실제 시험 병목은 **패턴 인식**입니다. 채점기는 문제당 (1) **패턴**(올바른 `Pk`?), (2) **변수**(올바른 치환/기저/등고선?), (3) **최종 형태**(올바른 모양?)를 봅니다. 오류는 타입 분류(`pattern-missed | wrong-variable | wrong-end-form | algebraic | sign | definition`)와 함께 `errors/log.md`에 YAML로 기록됩니다. 이 로그가 `/paideia weakmap`의 씨앗이자 `/paideia cheatsheet`의 유일한 입력입니다.

### *당신의* 풀이에서 추출한 패턴

`/paideia analyze`는 당신 과목의 실제 풀이집을 읽어 반복 동작을 P1, P2, …로 라벨링하고 당신의 `converted/solutions/` 파일을 인용합니다. 복소해석의 P3는 "닫힌 등고선 + Jordan 보조정리 + 유수"일 수 있고, 선형시스템의 P3는 "부분분수 + 복소극 역라플라스"일 수 있습니다.

### 상태 & 세션 배너

hermes엔 프롬프트별 플러그인 statusline 슬롯이 없어, 같은 신호를 두 방식으로 표면화합니다:

- **`/paideia status`** — 요청 시 `paideia · <코스> · D-N · <단계> · P<최다실수> ↑`.
- **`on_session_start` 훅** — 코스 폴더에서 세션을 열면 배너 출력.

`<단계>`는 **디스크 활동**에서 파생되어 산출물을 실제로 쓸 때 전진합니다: `setup`(patterns.md 없음) → `diag`(패턴 있음, 채점 없음) → `drill`(퀴즈 + 채점된 로그 항목) → `mock`(모의 출처 항목 등장) → `cram`(`cheatsheet/final.*`) → `cool`(`D-0`). `<최다실수>`는 최신 weakmap의 최빈 `pattern:` 태그(없으면 `errors/log.md`). 코스 폴더 밖에선 둘 다 침묵.

---

## 무엇이 포함되나

```
PAIDEIA-Hermes/                     # == ~/.hermes/plugins/paideia/
├── plugin.yaml  __init__.py        # 매니페스트 + register(ctx)
├── pd_meta/workspace/errlog/weakmap.py    # 결정적 엔진
├── pd_status/banner/doctor.py             # 상태 / 배너 / 진단
├── pd_render/vision_ocr.py                # PDF→PNG + 오프라인 OCR (독립 실행)
├── pd_prompts/commands.py                 # inject 프롬프트 + /paideia 디스패처
├── commands/                       # 15개 에이전트용 커맨드 스펙(.md)
├── skills/paideia-{pdf,vision-ocr,course-builder,exam-drill,answer-processing,alt-import}/
└── install.sh  LICENSE  README.md  README.ko.md
```

매핑:

| PAIDEIA (Claude Code) | PAIDEIA-Hermes (hermes-agent) |
|---|---|
| `/paideia:*` 네임스페이스 16개 | 단일 `/paideia` + 서브커맨드 디스패치(`ctx.register_command`) |
| 자동 로드 skills | `skills/paideia-*/SKILL.md`, inject 시 절대경로로 로드 |
| 커맨드 `.md` 직접 실행 | 핸들러 `inject_message()`(CLI) / `pre_gateway_dispatch` 재작성(Slack 등) |
| `SessionStart` 훅 | `on_session_start` 훅 |
| `statusLine` 훅 | `/paideia status` + 세션 배너 |
| 병렬 ingest 에이전트 | hermes 서브에이전트 위임 |
| 코스별 `CLAUDE.md` | 코스별 `PAIDEIA.md` |

---

## 설계 신념

1. **터미널은 수식에 약하다.** 에이전트가 markdown을 만들고 당신이 읽는다(Obsidian 권장).
2. **풀이 타이핑은 느리고 오류가 많다.** 종이에 풀고 스캔, 로컬 OCR.
3. **OCR 노이즈는 불가피하다** — 그래서 전략 채점(패턴/변수/최종형태). 실제 채점기가 보는 것이 그것이다.
4. **패턴은 *당신* 과목의 풀이에서 추출**되어야 한다 — 일반 리스트가 아니라.
5. **당신의 실수가 가장 값진 신호다.** 치트시트는 강의계획서가 아니라 `errors/log.md`에서.
6. **숙제 빈도가 시험을 말한다.** 유한한 시간을 점수가 있는 곳에.
7. **모든 것이 편집 가능**하다 — 당신의 git 히스토리 속 plain markdown/YAML.
8. **태생적으로 모델 비종속.** 같은 플러그인이 Codex·Nous·Anthropic·OpenRouter·로컬에서 동작 — 학습 그래프는 한 벤더에 종속되지 않는다.

---

## FAQ

**비수학 과목도 되나요?** 문제-패턴 추출 중심이라 정량 분야(수학·물리·EE·CS이론·통계)에서 빛납니다. 역사·문학은 ingest·요약은 되지만 드릴 명령은 풀이 패턴을 가정합니다.

**한/영 혼합 자료?** 네. OCR은 `eng+kor`, 산문은 원어 유지, 플러그인 서술 언어는 `INTERFACE_LANG`(`en|ko`).

**어떤 모델이 돌리나요 — Codex가 꼭 필요?** hermes provider에 따릅니다. `provider: openai-codex`면 Codex(gpt-5.5), `/model`로 바꿔도 Paideia는 그대로. 기본 OCR 엔진 `claude`는 "에이전트 자체 비전"을 뜻하며 Anthropic 전용이 아닙니다.

**Slack에서 되나요?** 네 — [Slack 및 기타 게이트웨이](#slack-및-기타-메시징-게이트웨이) 참고. 결정적 커맨드는 텍스트로, 에이전트 구동 커맨드는 `pre_gateway_dispatch` 훅이 턴으로 재작성.

**Ollama/Qwen3-VL 필요?** 아니요. 기본은 에이전트 비전. Ollama는 이미지를 완전 로컬로 두려는 옵트인.

**패턴/치트시트/weakmap 편집 가능?** 네 — plain markdown의 요점. `course-index/patterns.md`의 `P3`를 고치면 다음 드릴이 반영합니다.

**여러 코스 재사용?** 네 — 각 코스가 자체 `.course-meta`·`course-index/`·`errors/log.md`·`weakmap/`를 가진 독립 폴더. 공유·오염 없음.

**내 데이터는 사적인가요?** PDF·markdown·오류·weakmap은 로컬 코스 폴더에 있습니다. 네트워크는 OCR 엔진에 따라: `claude`는 평소 hermes provider 경로로 이미지 전송, `ollama`/`tesseract`는 기기 밖으로 나가지 않음.

---

## 연락

<p align="center">
  <a href="https://github.com/TaewoooPark"><img src="https://img.shields.io/badge/-GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"></a>
  <a href="https://x.com/theoverstrcture"><img src="https://img.shields.io/badge/-X-000000?style=for-the-badge&logo=x&logoColor=white" alt="X"></a>
  <a href="https://www.linkedin.com/in/taewoo-park-427a05352"><img src="https://img.shields.io/badge/-LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
  <a href="https://taewoopark.com"><img src="https://img.shields.io/badge/-taewoopark.com-000000?style=for-the-badge&logo=safari&logoColor=white" alt="Personal site"></a>
  <a href="mailto:ptw151125@kaist.ac.kr"><img src="https://img.shields.io/badge/-Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"></a>
</p>

---

## 라이선스

**MIT.** PAIDEIA-Hermes는 [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)의 hermes-agent 포트로, 같은 라이선스와 저작권(© 2026 Taewoo Park)을 따릅니다 — [`LICENSE`](./LICENSE) 참고. 자유롭게 쓰고, 당신의 과목에 맞게 포크·수정하세요. 핵심은, 이 플러그인이 만드는 학습 그래프가 당신이 빚어 가는 것이지 감수해야 할 고정 제품이 아니라는 점입니다.

크레딧: 원본 [PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)(Claude Code), 호스트 플랫폼 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)(MIT).

---

<p align="center">
  <em>일반 커리큘럼은 평균 학생을 가르친다. Παιδεία — 한 번에 한 학생씩, 형성.</em>
</p>
