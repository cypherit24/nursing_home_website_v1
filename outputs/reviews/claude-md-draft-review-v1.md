# CLAUDE.md 초안 검증 결과

- **검증 대상**: CLAUDE.md 초안 (사용자 제출, .github/workflows · supabase/* · src/* 코딩 가이드라인)
- **검증 기준**: docs/plan-v3.md (승인본)
- **검증 방법**: plan-review-example.md 6관점 프레임워크 적용
- **Date**: 2026-03-31

---

## 1. 전제 검증

초안이 암묵적으로 가정하는 전제들:

| # | 전제 | 틀릴 경우 파급도 | 비고 |
|---|---|---|---|
| P1 | plan-v3.md의 모든 기술 결정이 그대로 유지된다 | 상 | 합리적 전제 |
| P2 | Maker(Sonnet)가 CLAUDE.md를 자동 로드하여 행동 지침으로 삼는다 | 상 | Claude CLI 동작 원리에 부합 |
| P3 | ESLint `react/no-danger` 규칙만으로 dangerouslySetInnerHTML 차단이 충분하다 | 중 | 맞음, 다만 초안에서 ESLint 규칙명이 plan-v3과 일치하는지 확인 필요 (아래 5번 참고) |

**소결**: 전제 자체에 치명적 문제 없음.

---

## 2. 실행 가능성

초안은 코딩 가이드라인이지 일정 계획이 아니므로, "Maker가 이 지침을 보고 코드를 작성할 수 있는가"로 판단.

- **S1~S6 보안 규칙**: plan-v3 §7과 정합. 실행 가능.
- **pipeline 가이드**: plan-v3 T05~T12와 정합. jsonschema 검증, 원자적 업데이트, pipeline_errors 로깅 모두 반영됨.
- **frontend 가이드**: plan-v3 T14~T19와 정합. SSG 1000건+ISR, SeoContent 템플릿 컴포넌트 방식 반영됨.
- **supabase 가이드**: plan-v3 T04, T04-b와 정합.
- **workflows 가이드**: plan-v3 T07, T11, T13-b, T22와 정합.

**소결**: 실행 가능성에 문제 없음.

---

## 3. 누락 분석

### 3-1. 누락 항목 (plan-v3에 명시되어 있으나 초안에 빠진 것)

| # | 누락 항목 | plan-v3 근거 | 심각도 | 권장 조치 |
|---|---|---|---|---|
| N1 | **접근성 규칙** — 기본 폰트 18px(text-lg), WCAG AA 색상대비 4.5:1, 시맨틱 HTML 태그 사용 | §7.3, T15, T16, T25-17 | 중 | `/src/frontend/*` 섹션에 접근성 항목 추가 |
| N2 | **면책 고지 및 삭제 요청 안내** — 사이트 하단 공공데이터법 면책 문구, footer에 삭제 요청 프로세스 안내 | §7.2, T15, T19, T25-18 | 중 | `/src/frontend/*` 섹션에 법적 고지 항목 추가 |
| N3 | **step2 Semaphore(5)** — API 동시 호출 제한이 10이 아닌 5 | T09 "Semaphore(5) (보수적 조정, 10→5)" | 중 | `/src/pipeline/*` 섹션에 Semaphore(5) 명시 |
| N4 | **step2 4일 분할 실행 + 일일 제한 자동 중단** | T09 "4일 분할 실행: 일 5,000건 처리, offset 파라미터" | 중 | `/src/pipeline/*` 또는 `.github/workflows/*` 섹션에 추가 |
| N5 | **step2 API 응답 스키마 레퍼런스 저장 + 구조 변경 감지** | T09 "최초 성공 응답의 XML 구조를 schemas/에 레퍼런스로 저장" | 중 | `/src/pipeline/*` 섹션에 추가 |
| N6 | **step1 필수 컬럼 검증 + 헤더명 기반 매핑** | T06 "COLUMN_MAP 헤더명 기반", "REQUIRED 컬럼 존재 확인" | 중 | `/src/pipeline/*` 섹션에 추가 |
| N7 | **step1/step2/step3 각 정합성 검증 SQL 실행** | T06, T09, T12 각각의 정합성 검증 쿼리 | 낮 | 이미 workflows 섹션에 "검증 로그 출력" 언급 있으나, pipeline 섹션에도 명시 권장 |
| N8 | **pytest/vitest 단위 테스트 작성 의무** | T06, T09, T12 각각 "pytest 단위 테스트 통과" | 낮 | 작업 프로세스 섹션 또는 별도 테스트 규칙으로 추가 |
| N9 | **sitemap.xml 동적 생성, robots.txt** | T19 | 낮 | 프론트엔드 섹션 또는 별도 SEO 섹션으로 추가 |

### 3-2. 불필요한 항목 (초안에 있으나 문제되는 것)

해당 없음. 초안의 모든 항목이 plan-v3에 근거가 있음.

---

## 4. 최악의 시나리오

| # | 시나리오 | 발생 확률 | 피해 | 초안 대응 여부 |
|---|---|---|---|---|
| W1 | Maker가 접근성 규칙 누락 상태로 전체 프론트엔드 구현 → 런칭 후 WCAG 미준수 발견 → 전면 재작업 | 중 | 중 | **미대응** (N1 누락) |
| W2 | Maker가 step2에서 Semaphore를 10 이상으로 설정 → API rate limit 초과 → IP 차단 | 낮 | 높 | **미대응** (N3 누락) |
| W3 | 면책 고지 없이 런칭 → 법적 리스크 | 낮 | 높 | **미대응** (N2 누락) |

---

## 5. 논리적 일관성

| # | 불일치 | 상세 | 심각도 |
|---|---|---|---|
| I1 | **S7 번호가 초안에 없음** — 초안 제목에 S2, S1, S6, S3, S5, S4를 사용하나, 입력 검증(S7)이 누락됨 | plan-v3 T25-19에 `grep -r "dangerouslySetInnerHTML"` 검증 있음. gemini-onboarding에 S7(입력 검증: facility_code 등) 정의됨. 초안에서 S7을 다루지 않음 | 낮 |
| I2 | **ESLint 규칙명 표기** — 초안 §1에서 "ESLint `no-dangerously-set-inner-html`"이라 했는데, plan-v3 T14는 `"react/no-danger": "error"`로 명시 | Maker가 혼동할 수 있음. 규칙명을 plan-v3과 통일해야 함 | 중 |
| I3 | **Rate Limiting 위치** — 초안에서 Rate Limiting을 `/src/frontend/*` 섹션에 넣었으나, 실제 파일은 `src/middleware.ts`로 프론트엔드 하위가 아닌 src/ 루트 | 정확하게는 Next.js middleware이므로 frontend 범주에 포함해도 무방하나, 파일 경로와 섹션 범위가 불일치 | 낮 |

---

## 6. 판정: 🟡 조건부 승인

### 근거

초안은 plan-v3의 핵심 보안 규칙(S1~S6)과 아키텍처 결정(JSON, 템플릿 컴포넌트, RLS)을 정확히 반영하고 있으며, 디렉토리별 가이드라인 구조가 명확하다. 그러나 plan-v3에 명시된 **접근성, 법적 고지, step2 세부 제약, 테스트 의무** 등이 누락되어 Maker가 이를 건너뛸 위험이 있다.

### 승인 조건 (반영 후 승인 가능)

| 우선순위 | 조건 | 관련 누락/불일치 |
|---|---|---|
| **필수** | 접근성 규칙 추가 (18px, WCAG AA, 시맨틱 HTML) | N1 |
| **필수** | 면책 고지 + 삭제 요청 안내 규칙 추가 | N2 |
| **필수** | ESLint 규칙명을 `"react/no-danger": "error"`로 통일 | I2 |
| 권장 | step2 Semaphore(5), 4일 분할, 스키마 레퍼런스 저장 명시 | N3, N4, N5 |
| 권장 | step1 헤더 기반 매핑 + 필수 컬럼 검증 명시 | N6 |
| 권장 | 각 step별 pytest/vitest 테스트 작성 의무 명시 | N8 |
| 선택 | S7(입력 검증) 항목 추가 | I1 |
