<h1 align="center">ΠΑΙΔΕΙΑ · Paideia <sub>for Hermes</sub></h1>

<p align="center">
  <strong>당신의 강의. 당신의 패턴. 당신의 실수. 당신의 치트시트.</strong><br>
  <em>당신의 자료를 영구적이고 편집 가능한 과목별 학습 그래프로 바꾸는 <a href="https://github.com/NousResearch/hermes-agent">hermes-agent</a> 플러그인입니다. 모든 산출물이 범용 실러버스가 아니라 당신에게서 빚어집니다.</em>
</p>

<p align="center">
  <a href="https://github.com/OPTIMETA/PAIDEIA-Alt"><img height="30" src="https://img.shields.io/badge/Exam_Radar-OPTIMETA_Alt_plugin-333333?style=for-the-badge&labelColor=000000&color=333333" alt="Exam Radar — OPTIMETA Alt plugin"></a>
</p>

<p align="center">
  <sub><em>강의는 <a href="https://github.com/OPTIMETA/PAIDEIA-Alt"><strong>Exam Radar</strong></a>(OPTIMETA Alt 플러그인)로 담고, 공부는 Paideia로 합니다. 로드맵은 <code>/paideia alt</code> 한 번으로 흘려보냅니다.</em></sub>
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

> **다시 쓴 게 아니라, 옮긴 것입니다.** PAIDEIA-Hermes는 원래 Claude Code 플러그인이던 [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)를 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)의 확장 표면 위에 다시 얹은 것입니다. 형성 사이클도, 디스크에 쌓이는 구조도, MIT 라이선스도 그대로입니다. hermes는 **모델에 묶이지 않으므로**, 똑같은 플러그인이 당신이 hermes에 연결해 둔 어떤 provider 위에서든 돕니다. `~/.hermes/config.yaml`에 `provider: openai-codex`라고 적혀 있다면 Paideia는 **Codex(gpt-5.5)**가 돌리고, `/model`로 갈아타도 Paideia 쪽은 한 줄도 달라지지 않습니다.

> **보안 안내.** PAIDEIA-Hermes는 hermes-agent 플러그인으로 설치됩니다(`hermes plugins install …`). `.zip`을 받게 하거나 `.exe`를 실행시키거나 별도 인스톨러를 쓰게 하는 일은 절대 없습니다. 이 README에 직접 링크되지 않았는데 PAIDEIA 이름을 단 저장소는 이 프로젝트와 무관합니다.

<p align="center">
  <em>일반 학습 도구는 평균적인 실러버스를 가르칩니다. Paideia는 <strong>당신의</strong> 실러버스를 가르칩니다 —<br>
  교수님의 노트, 당신이 받은 숙제의 무게, 당신의 손글씨, 당신의 실수에서요. 모든 산출물은 당신이 직접 고칠 수 있는 마크다운 한 장입니다.</em>
</p>

---

## Paideia라는 말

고대 그리스에서 **Παιδεία(파이데이아)**는 수동적인 학생에게 지식을 채워 넣는 일이 아니었습니다. 원전과 마주하고, 스승 곁에서 익히고, 피드백을 더 깊은 고쳐 씀으로 되돌리는 대화를 거쳐 — 한 사람을 평생에 걸쳐 빚어 가는 일이었지요.

이 플러그인은 그 순환을 **수학·물리·공학 과목의 시험 준비**라는 좁고 분명한 문제에 맞춰 옮겨 놓았습니다.

```
  ingest ──▶ analyze ──▶ drill ──▶ grade ──▶ weakmap ──▶ cheatsheet
     ▲                                                        │
     └────────────────── feedback loop ───────────────────────┘
```

단계마다 당신의 과목 폴더에 영원히 남는 마크다운 한 장이 나옵니다. 휘발되는 것도, API 뒤에 숨는 것도 없습니다. hermes가 모델을 가리지 않으니, 모델을 바꿔도 멈추는 것이 없고요.

---

## 일반 학습 도구가 하지 못하는 것

대부분의 학습 도구는 *당신의* 과목, *당신의* 교수님, *당신의* 실수에 맞추지 못합니다. 파는 물건 자체가 범용 커리큘럼이니까요.

- **Coursera, edX, Khan Academy** — 고정된 커리큘럼. 교수님이 실제로 어디를 강조하시는지 알 길이 없습니다.
- **Quizlet, Anki** — 카드 하나하나를 직접 만들어야 하고, 당신 과목의 풀이집에서 패턴을 뽑아 주지는 않습니다.
- **Chegg, Course Hero** — 범용 풀이집이라, 당신 과목이 반복하는 관용구를 중심으로 묶여 있지 않습니다.
- **ChatGPT Study Mode, Gemini, NotebookLM** — 과목별로 이어지는 상태가 없습니다. 세션을 새로 열 때마다 백지에서 출발하지요.

어느 쪽도 눈앞의 그 자료를 토대로 이해를 *빚지는* 못합니다. Paideia는 정반대로 갑니다. 모든 산출물이 *당신 폴더* — 강의노트, 교재, 숙제, 풀이, 손으로 푼 흔적 — 에서 나와, 당신이 직접 고칠 수 있는 평범한 마크다운으로 영원히 쌓입니다.

| 축 | Paideia | 흔한 교육 SaaS · LLM 챗 |
|-----|---------|------------------------------|
| 풀이 패턴 (`P1..Pk`) | *당신 과목의* 풀이에서 직접 뽑고, 당신 파일을 인용합니다 | 범용 교과서 목록, 또는 없음 |
| 드릴 우선순위 | *당신 교수님의* 숙제 강조도(숙제 밀도 = 출제 티어)로 가중합니다 | 고정 커리큘럼, 또는 당신의 감 |
| 치트시트 | *당신의* `errors/log.md`, 즉 실제로 틀린 것에서 만듭니다 | 실러버스 보일러플레이트 |
| 세션 사이의 과목 상태 | 마크다운+YAML로 영속, 공부할수록 자랍니다 | 대화는 초기화, 이력은 유료 |
| 마음에 안 드는 산출물 | `.md`를 열어 고치면 끝 | 읽기 전용 UI |
| 내 이해의 버전 기록 | 산출물마다 `git log` · `git diff` | 드러나지 않음 |
| 산출물이 있는 곳 | 텍스트 그대로, 당신 디스크에 | 원격 DB, 내보내기는 유료 |
| 작업하는 모델 | **당신이 정한 것** — Nous, OpenAI/Codex, Anthropic, OpenRouter, 로컬 | 한 벤더에 고정 |

플러그인은 hermes(당신이 고른 유료 모델이든 로컬 모델이든)로 무거운 일을 처리하지만, 결과물은 전부 디스크 위 평범한 마크다운으로 남습니다. 구독을 끊든, provider를 갈아타든, 완전히 로컬로 내려가든 — course-index도, patterns도, 오류 로그도, weakmap도, 치트시트도 그대로 열어 읽고 고치고 diff할 수 있습니다. 뼈대가 플러그인이고, 학습 그래프는 당신 것입니다.

기본 OCR은 에이전트 자신의 네이티브 비전(당신 hermes provider가 노출하는 멀티모달 모델)으로 돕니다. 손글씨 PDF를 기기 밖으로 내보내기 싫으시면, `ollama pull qwen3-vl:8b`로 약 6 GB를 한 번만 받아 두세요. 그다음부터 모든 OCR이 로컬 Qwen3-VL 추론으로 바뀝니다.

---

## 핵심 원리: 숙제 밀도가 곧 출제 확률입니다

"똑똑하게 공부하라"는 조언은 대개 약점을 사냥하라고 합니다. 그건 **거꾸로**입니다. 교수님은 숙제를 내주면서 시험 포인트가 어디인지 *이미 알려 주셨습니다*. 숙제가 두껍게 깔린 섹션은 🔥🔥 출제 핵심이고, 숙제가 하나도 없는 섹션은 "숨은 함정"이 아니라 ⚪ 저위험입니다. 교수님이 건드리지 않았다는 것 자체가, 그 주제가 시험에서 빠진다는 가장 강한 신호입니다.

Paideia의 등급은 이 원칙을 그대로 따르고, 드릴 명령도 기본값으로 이를 지킵니다.

| 티어 | 섹션 숙제 수 | 다루는 법 | 모의고사 배점 비중 |
|------|---------------------|-----------|---------------------------|
| 🔥🔥 출제 핵심 | 3+ | 가장 빡세게 드릴 | ≥70% |
| 🔥 출제 유력 | 2 | 그다음으로 드릴 | ~25% |
| 🟡 출제 가능 | 1 | 가볍게 훑기 | ≤5% |
| ⚪ 저위험 | 0 | 참고만 | 0 |

`/paideia quiz all`, `/paideia mock`, `/paideia hwmap hot`이 모두 이 티어로 출력을 가중합니다. ⚪ 섹션을 굳이 드릴하시겠다면 한 번은 따르되, 출제 확률이 낮다고 한마디 일러 둡니다. 상상 속 함정보다 당신의 한정된 시간이 더 귀하니까요.

---

## 형성 사이클, 한 단계씩

| 단계 | 하는 일 | 명령어 | 산출물 |
|-------|-------------|----------|----------|
| **만남** | 교수님의 신호를 읽는다 | `/paideia ingest` | `converted/**/*.md` — 강의·교재·숙제·풀이 전부를 깔끔한 LaTeX 마크다운으로 |
| **구조** | 과목의 문법을 뽑아낸다 | `/paideia analyze` | `course-index/{summary,patterns,coverage}.md` — 토픽 트리, 반복 패턴(P1..Pk), 숙제 밀도 출제 티어 |
| **연습** | 교수님이 실제로 내는 곳에 가중한 능동 회상 | `/paideia quiz`·`twin`·`blind`·`chain`·`mock` | `quizzes/`·`twins/`·`chain/`·`mock/` — 종이에 푸는 문제 |
| **성찰** | 손으로 쓴 풀이가 채점이 된다 | `/paideia grade` | `answers/converted/<name>.md` + `errors/log.md` — 에이전트 비전(기본)·Ollama·Tesseract로 OCR한 뒤 전략 채점 |
| **진단** | 오류를 우선순위 약점 리포트로 압축 | `/paideia weakmap` | `weakmap/weakmap_<ts>.md` — 덮어쓰지 않고 쌓이는 기록 |
| **증류** | 한 장으로, 오류에서 길어 올려, 인쇄까지 | `/paideia cheatsheet`·`derive`·`pattern` | `cheatsheet/final.md`, `derivations/<slug>.md` |

거드는 명령으로, `/paideia hwmap`은 숙제 밀도 출제 확률을 보여 주고, `/paideia status`는 지금 사이클 어디인지 알려 주며, `/paideia init`은 새 과목 폴더를 깔아 줍니다.

---

## 설치

### 사전 준비

**필수**

- [hermes-agent](https://github.com/NousResearch/hermes-agent), provider는 무엇이든(Nous Portal, OpenAI/Codex, Anthropic, OpenRouter, 로컬 …).
- Python 3 + Unix 계열 셸(`bash`/`zsh`; Windows는 WSL2).
- `poppler`(`pdftoppm`) — OCR 모든 티어가 씁니다.
  - **macOS**: `brew install poppler tesseract tesseract-lang`
  - **Linux**: `apt-get install poppler-utils tesseract-ocr tesseract-ocr-kor`
- Python 라이브러리(ingest/grade/cheatsheet 때만 필요): `pip install pypdf pdfplumber pdf2image pillow reportlab pytesseract`

**선택 — `--ocr=ollama` 쓸 때만(페이지 이미지가 기기에 머묾)**

- `ollama` + `qwen3-vl:8b`(약 6 GB). `ollama pull qwen3-vl:8b`.

언제든 `/paideia doctor`로 위 항목을 점검하세요(`/paideia doctor --fix`는 권한 없이 고칠 수 있는 것만 손봅니다). 에이전트의 `terminal`이 실제로 쓰는 바로 그 `python3`를 검사하므로, 정말 돌릴 수 있는지를 있는 그대로 알려 줍니다.

### 플러그인 설치

```bash
hermes plugins install OPTIMETA/PAIDEIA-Hermes
hermes plugins enable paideia
```

hermes를 다시 띄우면 모든 세션에서 `/paideia`가 보입니다. 다른 방법도 있습니다.

```bash
# B) 유저 플러그인 폴더에 바로 clone
git clone https://github.com/OPTIMETA/PAIDEIA-Hermes ~/.hermes/plugins/paideia
hermes plugins enable paideia

# C) 개발·로컬 체크아웃 (심링크 — 고친 내용이 다음 세션에 바로 반영)
git clone https://github.com/OPTIMETA/PAIDEIA-Hermes && ./PAIDEIA-Hermes/install.sh
```

`~/.hermes/config.yaml`은 건드릴 필요가 없습니다. 플러그인은 `~/.hermes/plugins/paideia/`에서 알아서 발견됩니다.

### 과목별 부트스트랩

이번 과목에 쓸 폴더 안에서 hermes를 열고, 마법사를 돌리거나

```
/paideia init
```

…한 줄로 비대화식으로 깔아도 됩니다.

```
/paideia init name="복소해석 MATH 405" exam=2026-12-15 type=final lang=ko ocr=claude weak="등각적분"
```

의존성을 점검하고, 인터페이스 언어 `en|ko`와 `COURSE_NAME`·`EXAM_DATE`·`EXAM_TYPE`·`USER_WEAK_ZONES`, OCR 엔진을 (인자로든 물어서든) 받은 다음, 디렉터리 골격과 `.course-meta`·`PAIDEIA.md`를 만들고 `errors/log.md`를 깔아 둡니다. 채점 한 번만 엔진을 바꾸려면 `/paideia grade --ocr=claude path/to/answer.pdf`처럼 덮어쓰세요.

---

## 과목 폴더 구조

`/paideia init` 직후 폴더 모양은 이렇습니다.

```
my-course/
├── .course-meta                     # 과목명, 시험일, 인터페이스 언어(en|ko), OCR 엔진
├── PAIDEIA.md                       # 에이전트가 읽는 과목별 워크플로 메모
├── .gitignore                       # 원본 스캔·OCR 임시물만 숨기고, 학습 그래프 본체는 커밋
│
├── materials/                       # 원본을 여기에 둔다 (PDF/MD)
│   ├── lectures/  textbook/  homework/  solutions/
├── converted/                       # 자동 생성 마크다운 — 손대지 말 것 (/paideia ingest 결과)
│   ├── lectures/  textbook/  homework/  solutions/
├── course-index/                    # 지식 베이스 — /paideia analyze 가 만든다
│   ├── summary.md  patterns.md  coverage.md  radar.md
├── answers/                         # 손글씨 스캔 PDF를 여기에 둔다
│   └── converted/                   # /paideia grade 가 OCR 마크다운을 쓰는 곳
├── errors/log.md                    # 쌓이기만 하는 YAML 오류 로그 (/weakmap·/cheatsheet 의 씨앗)
├── quizzes/  mock/  twins/  chain/  derivations/  cheatsheet/  weakmap/
```

**손으로 만질 폴더는 둘뿐입니다.** `materials/`(원본 PDF/MD)와 `answers/`(손글씨 스캔)이고요. 나머지는 `/paideia` 명령이 만들고, 언제든 다시 만들 수 있습니다. 이 구조는 **원본 [PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)와 바이트 단위로 호환**되어, 과목 폴더가 Claude Code 플러그인과 이 hermes 포트 사이를 그대로 오갑니다.

---

## 읽기 팁: Obsidian

Paideia는 모든 것을 LaTeX 수식(`$...$`, `$$...$$`)이 섞인 평범한 마크다운으로 씁니다. 아무 에디터로나 읽히지만, **[Obsidian](https://obsidian.md)**이 제일 잘 맞습니다. 설정 없이 MathJax로 수식을 렌더링하고, 백링크로 `quizzes/`에서 인용한 `converted/lectures/`로 바로 건너뛰며, 과목 폴더 전체를 검색되는 그래프 vault로 다룹니다. 오프라인·무료·로컬이라 Paideia의 결과도 같지요. 터미널은 수식에 약하니 거기서 싸우지 마세요.

## 그리고 강의 쪽 끝: Alt

Obsidian이 읽는 쪽 짝이라면, **[Alt](https://www.altalt.io/ko/)**는 강의가 들어오는 반대쪽 짝입니다. Alt가 강의를 녹음·전사하고, 그 안에서 OPTIMETA의 **Exam Radar** 플러그인이 교수님이 입으로 얼마나 강조했는지로 토픽을 매깁니다. 그걸 `/paideia alt`로 Paideia에 넣으면 고리가 닫힙니다. **강의를 듣고 → 담고 → 시험 신호를 뽑고 → 중요한 것만 공부한다**, 이렇게요.

---

## 전체 워크플로 — 예시

**Phase 0 — 과목당 한 번(15분).** `materials/{lectures,textbook,homework,solutions}/`에 PDF를 넣고 hermes에서:

```
/paideia ingest                     # 모든 PDF → 비전 파이프라인 (PDF당 서브에이전트, LaTeX 충실)
/paideia analyze <약점 힌트>        # patterns + coverage + summary 구축
/paideia hwmap hot                  # 🔥🔥 출제 핵심존 보기
```

**Phase 1 — 진단(40분).** `/paideia quiz all 20` → 종이에 풀어 `answers/diagnostic.pdf`로 스캔 → `/paideia grade`.

**Phase 2 — 집중 드릴(준비 시간의 대부분).** `/paideia weakmap` → `/paideia blind hw3-p2` · `/paideia twin hw3-p2` · `/paideia chain 3` · `/paideia quiz weakmap 5`.

**Phase 3 — 통합(약 90분).** `/paideia mock 90` → 종이에 풀고 스캔 → `/paideia grade`.

**Phase 4 — 압축(전날 밤).** `/paideia cheatsheet --pdf` · `/paideia weakmap`.

**Phase 5 — 쿨다운(시험 10분 전).** `/paideia weakmap` — 상위 3개만. 새로운 건 배우지 마세요.

---

## 명령어 (총 16개)

`/paideia <서브커맨드> [인자]` — 목록은 `/paideia help`로 바로 봅니다.

| 명령어 | 하는 일 |
|---------|---------|
| `/paideia init [name=… exam=… …]` | 새 과목 폴더 부트스트랩(마법사, 또는 인자 한 줄) |
| `/paideia doctor [--fix]` | 설치·워크스페이스 진단; `--fix`는 권한 없이 고칠 것만 손봄 |
| `/paideia status` | 한 줄 `과목 · D-N · 단계 · 최다 실수 패턴` |
| `/paideia ingest [--force]` | `materials/**`의 PDF → `converted/**` 마크다운(PDF당 서브에이전트) |
| `/paideia analyze [힌트]` | `course-index/{summary,patterns,coverage}.md` 구축 |
| `/paideia hwmap hot\|<§>` | 숙제 밀도순 🔥🔥 출제 핵심 섹션 |
| `/paideia pattern <§\|Pk\|키워드>` | course-index의 패턴 카드 |
| `/paideia derive <대상>` | `derivations/<slug>.md`에 깔끔한 참조 유도 |
| `/paideia quiz <주제\|§\|weakmap> [N]` | 연습문제 N개, 정답은 `_answers.md`에 숨김 |
| `/paideia blind <problem-id>` | 알려진 문제의 전략만 점검하는 드릴 |
| `/paideia twin <problem-id>` | 같은 패턴, 새 표면의 변형 |
| `/paideia chain <N>` | 패턴 N개를 엮은 통합 문제 |
| `/paideia mock <분>` | 숙제 밀도로 가중한 모의고사 |
| `/paideia grade [--ocr=<엔진>] [경로]` | 답안 PDF OCR + 전략 채점 + `errors/log.md` 기록 |
| `/paideia weakmap [개념]` | 우선순위 약점 리포트 → `weakmap/weakmap_<ts>.md` |
| `/paideia cheatsheet [--pdf]` | 오류에서 길어 올린 한 장 |
| `/paideia alt [붙여넣기]` | OPTIMETA Exam Radar(Alt) export 가져오기 → `radar.md` + `coverage.md` 강의 강조 열 |

---

## Slack, 그리고 다른 메시징 게이트웨이

PAIDEIA-Hermes는 CLI만이 아니라 hermes 메시징 게이트웨이(Slack·Discord·Telegram …)에서도 돕니다. 플랫폼의 타입드 커맨드 접두사를 쓰세요(Slack·Matrix는 `!`, 나머지는 대개 `/`).

- **결정형 명령** — `!paideia status`·`doctor`·`init …`·`help` — 텍스트로 바로 답합니다.
- **에이전트 구동 명령** — `!paideia ingest|analyze|quiz|grade|weakmap|mock|twin|…` — `pre_gateway_dispatch` 훅이 이걸 평범한 에이전트 턴으로 바꿔 줍니다(게이트웨이에는 CLI의 인세션 `inject_message`가 없거든요). 접두사 없는 문장도 됩니다: `paideia quiz §1.2 3`.

게이트웨이는 설정된 작업 디렉터리(`terminal.cwd`)에서 도니, 그 경로를 과목 폴더로 맞춰 두세요. 명령마다 `.course-meta`의 `INTERFACE_LANG`을 직접 읽으므로 Slack에서도 한국어·영어 문장이 그대로 유지됩니다.

---

## 안을 들여다보면

### Ingest 파이프라인: 모든 PDF를 비전으로

`/paideia ingest`는 `materials/**`의 모든 PDF를 하나의 비전 파이프라인으로 보냅니다. `pdfplumber`는 수식·그림·다단이 섞이면 산문 페이지조차 깨뜨려서 믿을 수 없었기에, 전부 비전으로 통일했습니다. `materials/**/*.md`는 출처 헤더를 달아 그대로 복사합니다.

페이지마다 `dpi=160` PNG로 렌더링하고, **에이전트가 읽기 전에** 긴 변을 1800px 이하로 줄입니다(큰 이미지는 멀티모달이 거부하니까요). 그다음 hermes가 **PDF 하나당 서브에이전트 하나를 위임**해, 각자 페이지를 *순서대로* 읽어 LaTeX 마크다운으로 옮깁니다. `ℏ ∂ p2 …` 대신 `$$\hat H = -\frac{\hbar^2}{2m}\partial_x^2 + V(x)$$`처럼요. 자세한 내용은 `skills/paideia-pdf/VISION.md`에 있습니다.

### 손글씨 OCR: 엔진 셋, 골라 쓰세요

채팅에 수식을 타이핑하지 않습니다. 종이에 풀고 스캔해 `answers/`에 넣은 뒤 `/paideia grade`만 부르면 됩니다. 엔진은 과목별로(`.course-meta`의 `OCR_ENGINE`) 정하고, 호출마다 `--ocr=`로 덮어씁니다.

| 엔진 | 기본? | 도는 방식 | 언제 고르나 |
|---|---|---|---|
| `claude` | **예** | `pdftoppm`로 페이지를 렌더링한 뒤, 에이전트가 자기 네이티브 비전으로 PNG를 읽어 마크다운으로 합칩니다. 추가 설치 없음. | 그냥 바로 쓰는 길. |
| `ollama` | 선택 | `pd_vision_ocr.py --engine=ollama` → 로컬 Qwen3-VL 8B, 실패하면 tesseract로 자동 폴백. | 페이지 이미지가 기기 밖으로 절대 안 나가야 할 때. |
| `tesseract` | 선택 | `pd_vision_ocr.py --engine=tesseract` → pytesseract(`eng`/`eng+kor`). | 가장 가볍고, 타이핑 스캔에 무난할 때. |

> 기본 엔진 이름이 `claude`인 건 원본 PAIDEIA와 디스크 구조를 맞추려는 것이고, hermes에서는 **"에이전트 자신의 네이티브 비전"**, 즉 당신 provider가 내주는 멀티모달 모델(예: `openai-codex`의 gpt-5.5)을 뜻합니다. Anthropic에 묶이지 않습니다.

### 줄 단위가 아니라 전략으로 채점

OCR 잡음 탓에 엄밀한 대수 채점은 쓸모가 없고, 어차피 시험의 진짜 병목은 **패턴 인식**입니다. 그래서 채점은 문제마다 세 가지를 봅니다. (1) **패턴** — 맞는 `Pk`를 골랐는가, (2) **변수** — 치환·기저·등고선을 제대로 잡았는가, (3) **최종 형태** — 마지막 식의 꼴이 맞는가. 오류는 타입(`pattern-missed | wrong-variable | wrong-end-form | algebraic | sign | definition`)과 함께 `errors/log.md`에 YAML로 적힙니다. 이 로그가 `/paideia weakmap`의 씨앗이자, `/paideia cheatsheet`의 유일한 입력입니다.

### 패턴은 *당신* 풀이에서 뽑습니다

`/paideia analyze`는 당신 과목의 진짜 풀이집을 읽어, 반복되는 수를 P1·P2…로 매기고 당신의 `converted/solutions/` 파일을 인용합니다. 복소해석이라면 P3가 "닫힌 등고선 + Jordan 보조정리 + 유수"일 테고, 선형시스템이라면 "부분분수 + 복소극 역라플라스"일 테지요. 그 과목만이 자기 관용구를 보여 줍니다.

### 상태와 세션 배너

hermes에는 프롬프트마다 뜨는 플러그인 statusline 슬롯이 없어, Paideia는 같은 신호를 두 갈래로 보여 줍니다.

- **`/paideia status`** — 부르면 `paideia · <과목> · D-N · <단계> · P<최다실수> ↑`를 찍습니다.
- **`on_session_start` 훅** — 과목 폴더에서 세션을 열면 같은 내용의 배너를 띄웁니다.

`<단계>`는 달력이 아니라 **디스크 위 활동**에서 나오므로, 산출물을 실제로 쓸 때 넘어갑니다. `setup`(아직 `patterns.md` 없음) → `diag`(패턴은 있으나 채점 기록 없음) → `drill`(퀴즈가 있고 `errors/log.md`에 채점 항목 하나 이상) → `mock`(모의 출처 항목이 등장) → `cram`(`cheatsheet/final.*` 존재) → `cool`(`D-0`) 순이고요. `<최다실수>`는 가장 최근 weakmap에서 제일 잦은 `pattern:` 태그입니다(없으면 `errors/log.md`로). 과목 폴더 밖에서는 둘 다 잠잠합니다.

---

## 무엇이 들어 있나

```
PAIDEIA-Hermes/                     # == ~/.hermes/plugins/paideia/
├── plugin.yaml  __init__.py        # 매니페스트 + register(ctx)
├── pd_meta/workspace/errlog/weakmap.py    # 결정형 엔진
├── pd_status/banner/doctor.py             # 상태 · 배너 · 진단
├── pd_render/vision_ocr.py                # PDF→PNG + 오프라인 OCR (단독 실행)
├── pd_prompts/commands.py                 # inject 프롬프트 + /paideia 디스패처
├── commands/                       # 에이전트용 명령 스펙 15개(.md)
├── skills/paideia-{pdf,vision-ocr,course-builder,exam-drill,answer-processing,alt-import}/
└── install.sh  LICENSE  README.md  README.ko.md
```

hermes 확장 표면으로의 매핑은 이렇습니다.

| PAIDEIA (Claude Code) | PAIDEIA-Hermes (hermes-agent) |
|---|---|
| `/paideia:*` 네임스페이스 16개 | 단일 `/paideia` + 서브커맨드 분기(`ctx.register_command`) |
| 자동 로드 skills | `skills/paideia-*/SKILL.md`, inject 프롬프트가 절대경로로 읽음 |
| 명령 `.md`를 직접 실행 | 핸들러의 `inject_message()`(CLI) / `pre_gateway_dispatch` 재작성(Slack 등) |
| `SessionStart` 훅 | `on_session_start` 훅 |
| `statusLine` 훅 | `/paideia status` + 세션 배너 |
| 병렬 ingest 에이전트 | hermes 서브에이전트 위임(PDF당 하나) |
| 과목별 `CLAUDE.md` | 과목별 `PAIDEIA.md` |

---

## 설계 신념

1. **터미널은 수식에 약하다.** 에이전트는 마크다운을 만들고, 당신은 (되도록 Obsidian에서) 읽는다.
2. **풀이를 타이핑하는 건 느리고 틀리기 쉽다.** 종이에 풀고 스캔하면, 플러그인이 로컬에서 OCR한다.
3. **OCR 잡음은 피할 수 없다.** 그래서 줄 단위 대수가 아니라 전략(패턴·변수·최종 형태)으로 채점한다. 실제 채점자가 보는 것도 그것이다.
4. **패턴은 *당신* 과목의 풀이에서 뽑아야 한다.** 범용 목록이 아니라.
5. **당신의 실수가 가장 값진 신호다.** 치트시트는 실러버스가 아니라 `errors/log.md`에서 나온다.
6. **숙제 밀도가 시험을 알려 준다.** 한정된 시간을 점수가 있는 곳에 쓴다.
7. **전부 당신이 고칠 수 있다.** 당신 git 기록 속 평범한 마크다운·YAML이다. 비계는 플러그인, 학습 그래프는 당신 것이다.
8. **태생부터 모델에 묶이지 않는다.** 같은 플러그인이 Codex·Nous·Anthropic·OpenRouter·로컬에서 돈다. 학습 그래프가 한 벤더에 매이지 않는다.

---

## FAQ

**수학 아닌 과목도 되나요?** 문제-패턴 추출이 중심이라 정량 과목(수학·물리·EE·CS 이론·통계)에서 빛납니다. 역사·문학도 ingest와 요약은 되지만, 드릴 명령은 문제에 풀이 패턴이 있다고 가정합니다.

**한국어와 영어가 섞인 자료는요?** 됩니다. OCR은 `eng+kor`로 잡고, 문장은 원래 언어를 지키며, 플러그인 서술 언어는 `INTERFACE_LANG`(`en|ko`)이 정합니다.

**어떤 모델이 돌리나요 — Codex가 꼭 있어야 하나요?** 당신 hermes provider에 달렸습니다. `provider: openai-codex`면 Codex(gpt-5.5)가 돌리고, `/model`로 바꿔도 Paideia는 그대로입니다. 기본 OCR 엔진 `claude`는 "에이전트 자신의 비전"을 가리킬 뿐, Anthropic 전용이 아닙니다.

**Slack에서 되나요?** 됩니다 — [Slack 게이트웨이](#slack-그리고-다른-메시징-게이트웨이) 항목을 보세요. 결정형 명령은 텍스트로 답하고, 에이전트 구동 명령은 `pre_gateway_dispatch` 훅이 턴으로 바꿔 줍니다.

**Ollama·Qwen3-VL이 꼭 필요한가요?** 아닙니다. 기본은 에이전트 비전입니다. Ollama는 이미지를 완전히 로컬에 두고 싶을 때 고르는 선택지입니다.

**패턴·치트시트·weakmap이 마음에 안 들면 고쳐도 되나요?** 됩니다. 평범한 마크다운으로 둔 이유가 그것입니다. `course-index/patterns.md`에서 `P3`를 고치면 다음 드릴이 그 수정을 따릅니다.

**여러 과목에 재사용할 수 있나요?** 됩니다. 과목마다 자기 `.course-meta`·`course-index/`·`errors/log.md`·`weakmap/`을 가진 독립 폴더입니다. 섞이거나 오염되지 않습니다.

**제 데이터는 사적인가요?** PDF·마크다운·오류·weakmap은 로컬 과목 폴더에 있습니다. 네트워크는 OCR 엔진에 따라 갈립니다. `claude`는 평소 hermes provider 경로로 이미지를 보내고, `ollama`·`tesseract`는 기기 밖으로 아무것도 내보내지 않습니다.

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

**MIT.** PAIDEIA-Hermes는 [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)의 hermes-agent 포트로, 같은 라이선스와 저작권(© 2026 Taewoo Park)을 그대로 따릅니다 — [`LICENSE`](./LICENSE)를 보세요. 자유롭게 쓰고, 당신 과목에 맞게 포크해 고치세요. 이 플러그인이 만드는 학습 그래프는 감수해야 할 고정 제품이 아니라, 당신이 빚어 가는 것 — 그게 핵심입니다.

크레딧: 원본 [PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)(Claude Code), 그리고 토대가 된 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)(MIT).

---

<p align="center">
  <em>범용 커리큘럼은 평균적인 학생을 가르친다. Παιδεία — 한 번에 한 사람씩, 빚어내는 일.</em>
</p>
