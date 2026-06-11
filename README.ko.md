# PAIDEIA-Hermes

**내 강의 자료로 만드는 시험 대비 — [hermes-agent](https://github.com/NousResearch/hermes-agent) 네이티브 플러그인.**

> 내 강의. 내 패턴. 내 실수. 내 치트시트.

PAIDEIA-Hermes는 [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA)(Claude Code
플러그인)를 hermes-agent로 이식한 버전입니다. 강의·교재·숙제·풀이 폴더를 지속 가능한
학습 그래프로 바꾸고, **숙제 빈도(HW density)** — 즉 실제로 시험에 나오는 부분 — 에
가중치를 두어 드릴합니다. 일반 강의계획서가 아니라 *당신의* 자료 기준입니다.

**모델 비종속적**입니다. hermes가 가리키는 provider 위에서 그대로 동작합니다.
`~/.hermes/config.yaml`이 `provider: openai-codex`라면 PAIDEIA-Hermes는 Codex로
구동되며, `/model`로 바꿔도 PAIDEIA 쪽은 아무것도 바뀌지 않습니다.

> **상태 (v0.2.0):** 실제 Codex(gpt-5.5)로 hermes를 구동하여 전체 라이프사이클
> (`init → ingest → analyze → hwmap → quiz → grade → weakmap → mock →
> cheatsheet --pdf → twin → derive → chain`)을 종단 검증했습니다. phase 머신
> (setup→diag→drill→cram), `errors/log.md` 스키마 계약, en/ko i18n 모두 확인.
> 실사용 중 발견된 버그는 패치 완료(커밋 로그 참고).

---

## 설치 (기존 hermes 유저 — 한 줄)

```bash
hermes plugins install TaewoooPark/PAIDEIA-Hermes   # 프라이빗 레포: GitHub 인증 사용
hermes plugins enable paideia
# hermes 재시작 후, 코스 폴더에서:
/paideia init
```

대안:

```bash
# B) 유저 플러그인 디렉터리에 직접 clone
git clone https://github.com/TaewoooPark/PAIDEIA-Hermes ~/.hermes/plugins/paideia
hermes plugins enable paideia

# C) 개발/로컬 (심링크 — 수정이 다음 세션에 바로 반영)
git clone https://github.com/TaewoooPark/PAIDEIA-Hermes
ln -s "$PWD/PAIDEIA-Hermes" ~/.hermes/plugins/paideia
hermes plugins enable paideia

# 또는 동봉 설치 스크립트
./install.sh
```

`~/.hermes/config.yaml`은 손댈 필요가 없습니다. 플러그인은 `~/.hermes/plugins/paideia/`
에서 자동 발견됩니다.

## 요구 사항

- hermes-agent (provider 무관)
- `poppler` (`pdftoppm`) — 모든 OCR 티어 필수 · `brew install poppler`
- Python 라이브러리 (ingest/grade/cheatsheet 시 지연 설치): `pypdf pdfplumber pdf2image pillow reportlab pytesseract`
- 선택적 오프라인 OCR: `tesseract` (+ 한국어 `tesseract-lang`), 또는 `ollama` + `qwen3-vl:8b`

언제든 `/paideia doctor`로 위 항목을 점검(그리고 `--fix`로 안전한 항목 자동 수정)하세요.

---

## 명령어

`/paideia <서브커맨드> [인자]` (전체 목록은 `/paideia help`).

| 서브커맨드 | 설명 |
|---|---|
| `init` | 코스 폴더 부트스트랩 (인자 또는 대화형) |
| `doctor [--fix]` | 설치 + 워크스페이스 진단 |
| `status` | 한 줄: `코스 · D-N · 단계 · 최다 실수` |
| `ingest` | `materials/*.pdf` → `converted/*.md` (LaTeX 충실 변환) |
| `analyze` | `course-index/` 생성 (summary, patterns, coverage) |
| `hwmap [hot\|§N\|all]` | 숙제 빈도순 시험 핵심 섹션 |
| `pattern [§/Pk/키워드]` | 풀이 패턴 카드 |
| `quiz <주제\|weakmap> [N]` | 연습문제 N개 (weakmap → 약점 집중) |
| `blind <id>` | 전략만 점검하는 블라인드 드릴 |
| `twin <id>` | 같은 기법, 새 표면의 변형문제 |
| `chain` | 여러 패턴 통합문제 |
| `mock` | 숙제 가중 모의고사 |
| `derive <주제>` | 깔끔한 참조 유도 저장 |
| `grade [--ocr=…] [경로]` | 스캔 답안 PDF OCR + 전략 채점 |
| `weakmap [개념]` | 우선순위 약점 리포트 |
| `cheatsheet [--pdf]` | 오류 기반 한 페이지 치트시트 |
| `alt [경로]` | Exam Radar(Alt) 강의 강조 신호 가져오기 |

드릴 루프: PAIDEIA가 문제를 생성 → **종이에 풀고** → `answers/`에 스캔 →
`/paideia grade`가 OCR 후 *전략* 기준(패턴 인식, 변수 선택, 최종 형태)으로 채점하며
실수를 `errors/log.md`에 기록 → `/paideia weakmap`이 우선순위화 →
`/paideia quiz weakmap`이 바로 그 약점을 드릴.

---

## PAIDEIA → hermes-agent 매핑

| PAIDEIA (Claude Code) | PAIDEIA-Hermes (hermes-agent) |
|---|---|
| `/paideia:*` 네임스페이스 16개 | 단일 `/paideia` + 서브커맨드 디스패치 |
| 자동 로드 skills 6개 | `skills/paideia-*/SKILL.md`, inject 시 절대경로로 읽힘 |
| 결정적 스크립트 | flat `pd_*.py` 모듈 |
| 커맨드 `.md` 직접 실행 | 핸들러가 `inject_message()`로 턴 주입 |
| `SessionStart` 훅 배너 | `on_session_start` 훅 (stderr 배너) |
| `statusLine` 훅 | `/paideia status` + 세션 배너 |
| 병렬 ingest 에이전트 | hermes subagent delegation |

온디스크 데이터 모델(`.course-meta`, `course-index/`, `errors/log.md` YAML,
`weakmap/`, 티어 마커 🔥🔥/🔥/🟡/⚪)은 업스트림 PAIDEIA와 호환되어 산출물이 서로 이동합니다.

## 크레딧

- [OPTIMETA/PAIDEIA](https://github.com/OPTIMETA/PAIDEIA) (TaewoooPark) — 원본
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) — 호스트 플랫폼

MIT 라이선스.
