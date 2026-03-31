# folder_agents_plan_v1 설계검증 결과서

> 검증일: 2026-03-31 | 기준 문서: plan-v3.md, folder_agents_plan_v1.md | 판정: **조건부 승인**

---

## 1. 정합성 검증 — plan-v3.md 기술 스택/목표와의 충돌

### 판정: 충돌 3건 발견 → 수정 필요

| # | 충돌 항목 | folder_agents_plan_v1 | plan-v3.md / 현행 repo | 해결 방안 |
|---|---|---|---|---|
| C1 | 계획 문서 경로 | `docs/plan-v3.md` | `plans/plan-v3.md` | **PM 결정: 제안 구조(docs/)로 이관**. plans/ → docs/ 마이그레이션. plans_verificated/ → docs/reviews/로 이동 |
| C2 | 핸드오프 경로 | `.ai/handoff/` | `handoff/handoff_v1.md` | **PM 결정: 제안 구조(.ai/handoff/)로 이관**. 기존 handoff_v1.md → .ai/handoff/로 이동 |
| C3 | 누락 폴더 | outputs/, agents_folder_plan/ 미정의 | 현행 repo에 존재 | agents_folder_plan/ → docs/agents/ 로 통합. outputs/ → 프로젝트 루트 유지 (연습용, 에이전트 권한 밖) |

### 정합성 확인 (충돌 없음)
- ✅ src/pipeline/, src/pipeline/schemas/, src/frontend/ 구조 일치
- ✅ CLAUDE.md 루트 위치 일치
- ✅ supabase/migrations/, .github/workflows/ 구조 일치
- ✅ 기술 스택(Next.js 15, Supabase, Python, GitHub Actions, Vercel) 충돌 없음
- ✅ JSON 스키마 방식(v3 핵심 변경) 반영됨 — schemas/ 디렉토리 Gemini 검증 대상 명시

### 이관 후 최종 디렉토리 구조

```text
nursing-home-seo/
├── CLAUDE.md
├── .ai/
│   └── handoff/              # 에이전트 간 인수인계 기록
├── docs/                     # 기획/설계 문서 (구 plans/ + plans_verificated/ + agents_folder_plan/)
│   ├── plan-v3.md
│   ├── agents/               # 에이전트 구조 설계
│   └── reviews/              # 검증 결과물 (구 plans_verificated/)
├── src/
│   ├── pipeline/
│   │   └── schemas/
│   └── frontend/
│       ├── app/
│       ├── components/
│       └── types/
├── supabase/migrations/
├── .github/workflows/
└── outputs/                  # 연습 결과물 (에이전트 권한 밖)
```

---

## 2. 가성비 검증 — API 토큰 비용 최적화

### 판정: 적정. 단, Opus 투입 기준 명확화 필요 → PM 합의 완료

| 에이전트 | 모델 | 비용 수준 | 투입 빈도 | 판정 |
|---|---|---|---|---|
| A: Opus | claude-opus-4-6 | $15/$75 (in/out per 1M) | 낮음 | ✅ 적정 — 고추론 설계 작업에만 한정 |
| B: Sonnet | claude-sonnet-4-6 | $3/$15 | 높음 (메인 코더) | ✅ 적정 — 가성비 최적 구간 |
| C: Gemini | gemini-2.5-pro | Google 과금 | 중간 (리뷰) | ✅ 적정 — 교차검증 + 보안감사 통합 |
| D: Haiku | claude-haiku-4-5 | $0.25/$1.25 | 낮음 (DevOps) | ✅ 적정 — 단순 YAML/SQL에 최저가 |

### Opus 투입 기준 (PM 합의 완료)

| 트리거 | 설명 | 예시 |
|---|---|---|
| 마일스톤 전환 | M1→M2, M3→M4 등 단계 전환 시 아키텍처 정합성 리뷰 | M3 완료 후 프론트엔드 착수 전 스키마-타입 정합성 확인 |
| 재설계 필요 | 스키마/API 명세/아키텍처 수준 변경 | seo_content_schema.json 필드 추가/변경 |
| 에스컬레이션 | Sonnet+Gemini가 해결 못한 오류 | 복잡한 ISR 캐싱 버그, 아키텍처 충돌 |

### 비용 절감 포인트
- Opus 미사용 시 세션당 ~$2~5 절감 (설계 문서 1건 기준)
- Haiku를 SQL 마이그레이션에 활용 → Sonnet 대비 세션당 ~90% 절감
- Gemini 보안감사 통합 → 별도 보안 에이전트 대비 추가 비용 0

---

## 3. 효율성 검증 — 핸드오프 비용 및 병목

### 판정: PM 병목 리스크 존재. 구조화된 핸드오프 양식으로 완화

| 병목 포인트 | 심각도 | 원인 | 완화 방안 |
|---|---|---|---|
| PM 직렬화 | **중** | 모든 에이전트 통신이 PM 경유 | 핸드오프 양식 표준화 → 복붙 비용 최소화 |
| 컨텍스트 재로딩 | **낮** | 각 에이전트가 CLAUDE.md + 관련 파일 재로딩 | CLAUDE.md 간결 유지 (현재 적정). 에이전트별 필수 컨텍스트 최소화 |
| Gemini→PM→Sonnet 루프 | **중** | 리뷰 결과 전달에 2단계 | Gemini 출력을 구조화된 Fix Instruction 형식으로 표준화 |

### 표준 핸드오프 양식 (.ai/handoff/)

```markdown
# Handoff: [작업명]
- **From**: Agent [X] → **To**: Agent [Y]
- **Date**: YYYY-MM-DD
- **Status**: 완료 / 수정필요 / 블로커

## 완료 사항
- (bullet)

## 수정 요청 (Gemini→Sonnet 전용)
| 파일 | 라인 | 이슈 | 수정 지시 |
|---|---|---|---|

## 블로커 (에스컬레이션 → Opus)
- (bullet)
```

### 효율성 수치 추정
- 핸드오프 1건당 PM 소요: ~2~5분 (양식 표준화 시)
- 마일스톤당 핸드오프: ~3~5건
- 전체 6주 총 핸드오프: ~20~30건 → PM 총 투입 ~1~2시간 (수용 가능)

---

## 4. 보안성 — Gemini 보안감사 역할 확장 설계

### 판정: Gemini Reviewer에 보안 체크리스트 오버레이 추가

### Agent C 확장: Gemini 3.1 Pro (Reviewer + **Security Auditor**)

#### 기존 역할 (유지)
- 코드 품질 리뷰
- plan-v3.md 대비 정합성 검증
- 프론트엔드 타입 ↔ 파이프라인 스키마 교차 검증

#### 신규 역할: 보안 감사 (추가)

| # | 감시 영역 | 트리거 조건 | 필수 컨텍스트 | 검증 기준 |
|---|---|---|---|---|
| S1 | XSS 방어 | src/frontend/components/ 변경 시 | @CLAUDE.md + 해당 파일 | `dangerouslySetInnerHTML` 미사용. JSX `{text}` 렌더링만 허용 |
| S2 | RLS 정책 | supabase/migrations/ 변경 시 | @docs/plan-v3.md §T04 | anon=SELECT only, service_role=ALL. 새 테이블에 RLS 활성화 확인 |
| S3 | CSP 헤더 | src/frontend/middleware 변경 시 | @docs/plan-v3.md §7.1 | `script-src 'self'` 유지. unsafe-inline/unsafe-eval 금지 |
| S4 | 개인정보 비표시 | src/frontend/ 내 DB 조회 코드 변경 시 | @docs/plan-v3.md §7.2 | representative_name 프론트엔드 렌더링 금지. 전화번호=기관 대표번호만 |
| S5 | JSON 스키마 무결성 | src/pipeline/schemas/ 변경 시 | @src/pipeline/schemas/seo_content_schema.json + @src/frontend/types/seo-content.ts | Python 스키마 ↔ TS 타입 동기화. additionalProperties: false 유지 |
| S6 | 시크릿 노출 | .github/workflows/ 변경 시 | 해당 YAML | 하드코딩된 키/URL 없음. ${{ secrets.* }} 사용 확인 |
| S7 | 의존성 보안 | requirements.txt 또는 package.json 변경 시 | 변경 diff | 알려진 취약 패키지 경고. 불필요 패키지 추가 감지 |

#### PM 프롬프팅 가이드 (보안 감사 요청 시)

```
@CLAUDE.md @docs/plan-v3.md 아래 보안 체크리스트로 검증해줘:
1. dangerouslySetInnerHTML 사용 여부
2. RLS 정책 정합성 (anon=읽기만)
3. CSP 헤더 유지 여부
4. 개인정보(대표자명) 비표시 준수
5. JSON 스키마 ↔ TS 타입 동기화
6. 시크릿 하드코딩 여부
7. 신규 의존성 보안 이슈
[첨부: 변경된 파일들]
```

#### 보안 감사 실행 시점

| 시점 | 감사 범위 | 비고 |
|---|---|---|
| 코드 리뷰 시 (상시) | 변경된 파일의 관련 S1~S7 항목만 | 기존 리뷰 워크플로우에 통합 |
| 마일스톤 완료 시 | S1~S7 전체 | Opus 정합성 리뷰와 동시 수행 |
| 배포 직전 (T20, T13-d) | S1~S7 전체 + 빌드 아티팩트 확인 | 최종 관문 |

---

## Patch Notes — folder_agents_plan_v1 → v2 반영 사항

### 변경 항목 (folder_agents_plan_v2 적용 시)

| # | 항목 | v1 | v2 (검증 후) |
|---|---|---|---|
| P1 | 계획 문서 경로 | `docs/plan-v3.md` (미이관) | `docs/plan-v3.md` (**plans/ → docs/ 이관 실행**) |
| P2 | 핸드오프 경로 | `.ai/handoff/` (미이관) | `.ai/handoff/` (**handoff/ → .ai/handoff/ 이관 실행**) |
| P3 | 검증 결과 경로 | 미정의 | `docs/reviews/` (**plans_verificated/ → docs/reviews/ 이관**) |
| P4 | 에이전트 설계 경로 | `agents_folder_plan/` | `docs/agents/` (**이관**) |
| P5 | Opus 투입 기준 | 미정의 | **마일스톤 전환 + 재설계 + 에스컬레이션** 3가지 트리거 명시 |
| P6 | 보안 에이전트 | 미정의 | **Gemini Reviewer에 Security Auditor 오버레이 추가** (S1~S7) |
| P7 | 핸드오프 양식 | 미정의 | **표준 양식 추가** (From/To/Status/수정요청 테이블/블로커) |
| P8 | outputs/ 폴더 | 미정의 | **루트 유지, 에이전트 권한 밖** |

### plan-v3.md 반영 필요 항목

| # | plan-v3.md 수정 대상 | 내용 |
|---|---|---|
| PP1 | 신규 섹션 추가 | "§12. 에이전트 운용 체계" — 4대 에이전트 역할/권한 + 보안감사 체크리스트 |
| PP2 | T05 폴더 구조 | `docs/`, `.ai/handoff/`, `docs/reviews/`, `docs/agents/` 추가 |
| PP3 | T25 체크리스트 | 보안감사 S1~S7 항목을 검증 체크리스트에 통합 (19개 → 최대 22개) |

### 실행하지 않는 항목 (본 검증 범위 밖)
- ❌ 폴더 이관 실제 실행 (별도 태스크로 분리)
- ❌ plan-v3.md 직접 수정 (PM 승인 후 별도 작업)
- ❌ CLAUDE.md 수정 (에이전트 권한 규칙 추가는 별도 승인 필요)
