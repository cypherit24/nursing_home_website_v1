# 멀티 에이전트 하네스 엔지니어링 설계서 v1

> 작성일: 2026-03-31 | 기준 문서: plan-v3.md, folder_agents_plan_v1_review.md, claude-md-draft-review-v1.md

---

## 0. 개요 및 파일 맵

4대 에이전트(Opus/Sonnet/Gemini/Haiku)가 Claude Code CLI + Continue IDE 환경에서 충돌 없이 협업하기 위한 하네스(harness) 설정 일체를 정의한다.

### 생성/수정 파일 목록

| # | 경로 | 상태 | 역할 |
|---|---|---|---|
| 1 | `CLAUDE.md` | 수정 | 전역 보안 S1~S7 + 에이전트 프로토콜 + 테스트 의무 + 접근성 + 법적 고지 |
| 2 | `.claude/rules/pipeline.md` | 신규 | `src/pipeline/**` 조건부 로드. T05~T12 코딩 가이드 |
| 3 | `.claude/rules/frontend.md` | 신규 | `src/frontend/**` 조건부 로드. T14~T19 코딩 가이드 |
| 4 | `.claude/rules/infra.md` | 신규 | `supabase/**`, `.github/**` 조건부 로드 |
| 5 | `.claude/agents/architect.md` | 신규 | Agent A (Opus) 설계 리뷰/에스컬레이션 서브에이전트 |
| 6 | `.claude/agents/devops.md` | 신규 | Agent D (Haiku) 인프라 전용 서브에이전트 |
| 7 | `docs/templates/gemini-review-prompt.md` | 신규 | Agent C (Gemini) Continue IDE 리뷰 프롬프트 템플릿 |
| 8 | `.claude/settings.json` | 수정 | Hooks 추가 (dangerouslySetInnerHTML 차단) |

### 연결 관계

```
CLAUDE.md (전역: S1~S7, 에이전트 프로토콜, 테스트, 접근성)
  |
  +-- .claude/rules/pipeline.md  --> src/pipeline/** 작업 시 자동 로드
  +-- .claude/rules/frontend.md  --> src/frontend/** 작업 시 자동 로드
  +-- .claude/rules/infra.md     --> supabase/**, .github/** 작업 시 자동 로드
  |
  +-- .claude/agents/architect.md --> /architect 로 호출 (Opus, 설계 전용)
  +-- .claude/agents/devops.md    --> /devops 로 호출 (Haiku, 인프라 전용)
  |
  +-- .claude/settings.json       --> 도구 allow/deny + Hooks (보안 자동 검사)
  |
  +-- docs/templates/
       +-- gemini-review-prompt.md --> PM이 Continue IDE에 복사하여 Gemini에게 전달
       +-- handoff_template.md     --> 핸드오프 기록 양식 (기존)
```

---

## 1. CLAUDE.md 계층 설계

### 1.1 루트 CLAUDE.md

기존 프로젝트 규칙(Safety Rules, Structure, Working Style) 유지. 아래 4개 섹션 추가:

- **Security Rules (S1~S7)**: plan-v3 SS7 + folder_agents_plan_v1_review + claude-md-draft-review I1 반영
- **Agent Protocol**: 에이전트별 권한/역할/핸드오프/에스컬레이션 규칙
- **Test Rules**: 각 step pytest 필수, vitest 권장 (N8)
- **Accessibility + Legal**: WCAG AA, 면책 고지, 삭제 요청 (N1, N2)

### 1.2 .claude/rules/ (경로별 조건부 로드)

Claude Code는 `.claude/rules/` 내 파일의 `paths` frontmatter를 기반으로, 해당 경로의 파일을 작업할 때만 규칙을 컨텍스트에 주입한다.

| 파일 | 활성 조건 | 핵심 내용 |
|---|---|---|
| pipeline.md | `src/pipeline/**` | Python 3.11+, Semaphore(5), 4일 분할, 원자적 업데이트 |
| frontend.md | `src/frontend/**` | Next.js 15, SeoContent 컴포넌트, SSG+ISR, WCAG AA |
| infra.md | `supabase/**`, `.github/**` | RLS 필수, workflow_dispatch+confirm, 시크릿 관리 |

---

## 2. 에이전트 정의 및 설정

### 2.1 Agent A: Opus (architect.md)

- **도구**: Read, Glob, Grep, Bash(git log/diff만)
- **투입 트리거**: 마일스톤 전환 / 스키마 재설계 / 에스컬레이션
- **출력**: docs/에 구조화된 설계 문서

### 2.2 Agent B: Sonnet (기본 CLI)

별도 정의 불필요. CLAUDE.md + rules/ 자동 주입.

### 2.3 Agent C: Gemini (프롬프트 템플릿)

Continue IDE 전용. `docs/templates/gemini-review-prompt.md` 참조.

### 2.4 Agent D: Haiku (devops.md)

- **도구**: Read, Edit, Write, Glob, Grep, Bash(npm test/lint)
- **제한**: src/ 접근 금지
- **담당**: SQL 마이그레이션, GitHub Actions YAML

---

## 3. 마일스톤별 워크플로우

```
M1 --- Haiku(주) + Sonnet(보조) --- DB/인프라 세팅
  |
M2 --- Sonnet(주) + Haiku(보조) --- 파이프라인 착수
  |
  +-- [Opus 정합성 리뷰] M2->M3 전환
  |
M3 --- Sonnet(주) + Gemini(리뷰) --- 파이프라인 완성
  |
  +-- [Opus 정합성 리뷰] M3->M4 전환 (스키마<->타입 동기화)
  |
M4 --- Sonnet(주) + Gemini(리뷰) --- 프론트엔드
  |
M5 --- Haiku(주) + Sonnet(보조) --- 배포/자동화
  |
M6 --- Sonnet + Gemini + [Opus 최종 리뷰] --- 런칭 검증
```

### 표준 워크 루프

```
PM 지시 -> Sonnet 코드 작성 -> PM 핸드오프 기록
  -> Gemini 리뷰 (Continue IDE) -> 승인/수정/블로커
  -> 수정: PM -> Sonnet (Fix Instruction)
  -> 블로커: PM -> Opus (/architect)
```

### Opus 에스컬레이션 트리거

| 트리거 | 판단 주체 |
|---|---|
| 마일스톤 전환 | PM (자동) |
| 스키마/API/아키텍처 변경 | PM |
| Sonnet+Gemini 2회 수정 루프 실패 | PM |

---

## 4. 설계 근거

| 결정 | 근거 |
|---|---|
| sub-directory CLAUDE.md 대신 .claude/rules/ 사용 | 경로 기반 조건부 로드로 불필요한 컨텍스트 소비 방지 |
| Gemini를 .claude/agents/에 정의하지 않음 | Continue IDE에서 동작하므로 Claude Code 서브에이전트 불가 |
| Agent B(Sonnet) 별도 정의 생략 | 기본 CLI 세션이 곧 Agent B. 중복 정의 불필요 |
| Hooks로 dangerouslySetInnerHTML 차단 | ESLint(빌드 시) + Hook(작성 시) 이중 방어 |
| settings.json 기존 deny 유지 | .env 보호, npm install/rm/sudo 차단은 그대로 필요 |
