# Project Contract — nursing_home_project_v1

## 프로젝트 설명
이 저장소는 nursing_home_project_v1 작업 공간이다.

## Commands
- test: `npm test`
- test:watch: `npm run test:watch`
- test:coverage: `npm run test:coverage`
- lint: `npm run lint`
- lint:fix: `npm run lint:fix`

## Safety Rules
- `.env` 파일과 `.env.*` 파일은 절대 읽거나 수정하지 않는다
- 파일을 삭제하기 전에 반드시 사람에게 먼저 확인한다
- 외부 패키지를 설치하기 전에 반드시 사람에게 먼저 확인한다
- `.devcontainer/` 폴더는 사람의 명시적 허가 없이 수정하지 않는다

## Structure
- 프로젝트 루트: `/workspaces/nursing_home_website_v1`
- 설정 파일: 프로젝트 루트에 위치
- 소스 코드: `src/` 폴더에 작성
- 설계 문서: 변경 계획을 확인 요청하기 **전에** 반드시 `docs/` 폴더에 .md 형식으로 저장한다 (읽기 전용, 파일명: 작업명-v1.md / 재작업 시 v2.md)
- 에이전트 구조 설계: `docs/agents/` 폴더에 저장
- 양식/템플릿: `docs/templates/` 폴더에 저장
- 작업 산출물: `outputs/` 폴더에 저장 (reviews/, handoff/ 등)
- 검증 결과물: `outputs/reviews/` 폴더에 저장
- 인수인계 기록: `outputs/handoff/` 폴더에 저장 (파일명: `from-to-작업명-v1.md`, 예: `opus-sonnet-schema-design-v1.md`)

## Security Rules (S1~S7)
- **S1 XSS**: `dangerouslySetInnerHTML` 절대 사용 금지. React JSX `{text}` 렌더링만 허용. ESLint `"react/no-danger": "error"` 적용
- **S2 RLS**: Supabase 테이블에 RLS 활성화 필수. anon=SELECT only, service_role=ALL. 새 테이블 생성 시 반드시 RLS 정책 포함
- **S3 CSP**: Next.js middleware에서 `script-src 'self'` 유지. `unsafe-inline`, `unsafe-eval` 금지
- **S4 개인정보**: `representative_name` 프론트엔드 렌더링 금지. 전화번호는 기관 대표번호만 표시
- **S5 스키마 동기화**: `src/pipeline/schemas/seo_content_schema.json` 변경 시 반드시 `src/frontend/types/seo-content.ts` 동시 업데이트. `additionalProperties: false` 유지
- **S6 시크릿**: `.github/workflows/` 내 하드코딩된 키/URL 금지. 반드시 `${{ secrets.* }}` 사용
- **S7 입력 검증**: `facility_code` 등 외부 입력은 형식 검증 후 사용. SQL은 parameterized query만 사용. 직접 문자열 연결 금지

## Agent Protocol
- **Agent B (Sonnet, 기본 CLI)**: `docs/` 읽기 전용 — 기획서 임의 수정 금지. `src/`, `supabase/`, `.github/` 쓰기 가능
- **Agent A (Opus)**: `.claude/agents/architect.md` 서브에이전트로 호출. 설계 리뷰 및 에스컬레이션 전용
- **Agent D (Haiku)**: `.claude/agents/devops.md` 서브에이전트로 호출. `supabase/`, `.github/` 인프라 전용
- **Agent C (Gemini)**: Continue IDE에서 PM이 직접 운용. `docs/templates/gemini-review-prompt.md` 프롬프트 사용
- **핸드오프**: `outputs/handoff/`에 `docs/templates/handoff_template.md` 양식으로 기록
- **에스컬레이션**: Sonnet+Gemini 2회 수정 루프 실패 시 PM이 Opus 투입 판단

## Test Rules
- **Python** (`src/pipeline/`): 각 step에 pytest 단위 테스트 필수. 외부 API는 mock 기반 테스트
- **Frontend** (`src/frontend/`): vitest 단위 테스트 작성 권장. 컴포넌트 렌더링 테스트 포함
- 테스트 없이 PR 승인 불가

## Accessibility (WCAG AA)
- 기본 폰트: `text-lg` (18px). 색상 대비: 4.5:1 이상
- 시맨틱 HTML: `<nav>`, `<main>`, `<article>`, `<footer>` 사용
- 이미지에 `alt` 속성 필수

## Legal
- 사이트 하단 면책 고지: "본 사이트는 공공데이터포털의 공공데이터를 활용하며, 공공데이터법에 의거하여 제공됩니다"
- footer에 삭제 요청 프로세스 안내 (24시간 내 처리)
- 비급여 금액 표시 시 "실제 금액과 다를 수 있습니다" 면책 문구 포함

## Working Style
- 수정 전에 항상 변경 계획을 먼저 보여준다
- 수정 후에는 무엇을 바꿨는지 5줄 이내로 요약한다
- 불확실한 부분이 있으면 추측하지 말고 askuserquestion으로 질문한다
