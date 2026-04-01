# plan-v4 태스크 목록 — 에이전트 배정 + Gemini 검증 프롬프트

---

## 의사결정 태스크

### DT01: 평가등급 데이터 확보 방안 결정
- 담당 에이전트: **PM (사람)** — 브라우저에서 의사결정
- Gemini 검증 프롬프트:
> DT01 결정 내용을 검토하라. (1) C안(등급 없이 런칭) 채택이 plan-v4의 R2 리스크 대응 방안과 일치하는지, (2) 향후 A안 병행 추진이 M6 이후 일정에 반영 가능한지 확인하라. 결정 누락 항목이 있으면 지적하라.

### DT02: 시설 사진 확보 방안 결정
- 담당 에이전트: **PM (사람)** — 브라우저에서 의사결정
- Gemini 검증 프롬프트:
> DT02 결정 내용을 검토하라. (1) A안(홈페이지 URL 링크 대체) 채택 시 S4(개인정보) 위반 가능성이 없는지, (2) v4 시각적 강화(lucide-react 아이콘 + recharts 차트)가 사진 부재를 충분히 보완하는지 R3 리스크 대응과 대조하여 검증하라.

### DT03: xlsx 갱신 주기 및 담당자 결정
- 담당 에이전트: **PM (사람)** — 브라우저에서 의사결정
- Gemini 검증 프롬프트:
> DT03 결정 내용을 검토하라. (1) 결정된 갱신 주기가 T22(스케줄 워크플로우)의 cron 일정과 정합하는지, (2) 담당자가 명확히 지정되었는지 확인하라.

### DT04: 도메인 구매 여부 결정
- 담당 에이전트: **PM (사람)** — 브라우저에서 의사결정
- Gemini 검증 프롬프트:
> DT04 결정 내용을 검토하라. (1) 도메인 미구매 시 T23 스킵 조건이 명확한지, (2) 구매 시 SEO 효과 근거가 타당한지, (3) 비용이 DT05 월간 운영 비용 상한선에 포함되는지 확인하라.

### DT05: 월간 운영 비용 상한선 합의
- 담당 에이전트: **PM (사람)** — 브라우저에서 의사결정
- Gemini 검증 프롬프트:
> DT05 결정 내용을 검토하라. (1) 합의된 상한선이 plan-v4의 비용 항목(OpenAI ~$12.10, 도메인 $10~20/년, Vercel Pro $20/월)을 모두 포괄하는지, (2) 무료 티어 → Pro 전환 트리거(월 10만 PV)가 명확한지 확인하라.

---

## 인프라 세팅 태스크

### T01: 외부 계정 생성
- 담당 에이전트: **PM (사람)** — 브라우저에서 수동 작업
- Gemini 검증 프롬프트:
> T01 완료 결과를 검토하라. (1) GitHub, Supabase, OpenAI, Vercel, 공공데이터포털 5개 서비스 계정이 모두 생성되었는지, (2) OpenAI 월 $20 하드리밋이 Settings > Billing > Usage limits에 설정되었는지, (3) B550928 API Decoding 키 발급 신청 상태를 확인하라. 누락 항목이 있으면 지적하라.

### T02: xlsx 파일 확보 및 Storage 업로드
- 담당 에이전트: **PM (사람)** — 브라우저 + Supabase 웹
- Gemini 검증 프롬프트:
> T02 완료 결과를 검토하라. (1) Supabase Storage > pipeline-data 버킷에 xlsx 파일이 존재하는지, (2) 파일명이 식별 가능한지(날짜 포함 권장), (3) 버킷의 public/private 설정이 적절한지(private 권장 — S6 시크릿 보호) 확인하라.

### T03: GitHub Secrets 및 Codespaces Secrets 등록
- 담당 에이전트: **PM (사람)** — 브라우저 (GitHub Settings)
- Gemini 검증 프롬프트:
> T03 완료 결과를 검토하라. (1) Repository Secrets 5개(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, PUBLIC_DATA_API_KEY, OPENAI_API_KEY, VERCEL_DEPLOY_HOOK_URL)가 모두 등록되었는지, (2) Codespaces Secrets 4개(VERCEL_DEPLOY_HOOK_URL 제외)가 등록되었는지, (3) S6 규칙 위반 여부 — .github/workflows/ 내 하드코딩된 키/URL이 없는지 코드베이스를 grep으로 확인하라.

### T04: Supabase DB 테이블 생성 및 RLS 설정
- 담당 에이전트: **Agent D (Haiku)** — Supabase 마이그레이션 SQL 작성
- Gemini 검증 프롬프트:
> T04의 nursing_homes 테이블 SQL을 보안 관점에서 검토하라. (1) S2: RLS가 활성화되어 있는지, anon=SELECT only, service_role=ALL 정책이 설정되었는지, (2) seo_content 컬럼이 JSONB 타입인지, (3) facility_code UNIQUE 인덱스 + sido/sigungu 인덱스가 생성되었는지, (4) representative_name 컬럼이 존재하되 SELECT 정책에서 프론트엔드 노출 방지 방안이 있는지(S4), (5) SQL injection 가능성이 없는 파라미터화된 쿼리인지 확인하라.

### T04-b: pipeline_errors 테이블 생성
- 담당 에이전트: **Agent D (Haiku)** — Supabase 마이그레이션 SQL 작성
- Gemini 검증 프롬프트:
> T04-b의 pipeline_errors 테이블 SQL을 보안 관점에서 검토하라. (1) S2: RLS 활성화, service_role=쓰기+읽기, anon=SELECT only 정책 확인, (2) 컬럼 구조(id SERIAL, facility_code TEXT, step TEXT, error_message TEXT, created_at TIMESTAMPTZ DEFAULT NOW())가 plan-v4와 일치하는지, (3) error_message에 민감 정보(API 키, 시크릿)가 기록될 가능성이 없도록 설계되었는지 확인하라.

---

## 데이터 파이프라인 태스크

### T05: 프로젝트 폴더 구조 및 유틸리티 파일 생성
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, src/ 코드 작성
- Gemini 검증 프롬프트:
> T05 산출물을 검토하라. (1) 폴더 구조가 `src/pipeline/`, `src/pipeline/schemas/`, `src/frontend/`로 생성되었는지, (2) `seo_content_schema.json`이 plan-v4 §3의 6필드 스키마와 정확히 일치하는지(`additionalProperties: false` 포함), (3) requirements.txt에 xmltodict, openpyxl, pandas, aiohttp, openai, jsonschema가 포함되고 nh3가 제거되었는지, (4) Supabase 클라이언트 유틸리티가 환경변수를 통해 연결하는지(.env 하드코딩 없음 — S6), (5) S5 동기화 규칙에 대한 주석이 스키마 파일에 있는지 확인하라.

### T06: step1_load_xlsx.py 작성
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 파이프라인 코드 작성
- Gemini 검증 프롬프트:
> T06 코드를 보안 + 품질 관점에서 검토하라. (1) S7: facility_code 입력 검증이 있는지, SQL은 parameterized query만 사용하는지(문자열 연결 금지), (2) facility_code dtype=str 처리로 앞자리 0이 보존되는지, (3) COLUMN_MAP이 헤더명 기반 매핑인지(인덱스 A,B,G 아님), (4) REQUIRED 컬럼 검증이 파싱 시작 전에 실행되는지, (5) NULL 비율 정합성 검증 쿼리가 포함되었는지, (6) pytest 단위 테스트가 컬럼 매핑, dtype 보존, 빈 행 처리, 필수 컬럼 누락 에러 4가지를 커버하는지 확인하라.

### T07: step1 GitHub Actions 워크플로우 작성
- 담당 에이전트: **Agent D (Haiku)** — GitHub Actions YAML 작성
- Gemini 검증 프롬프트:
> T07의 `manual_step1.yml`을 보안 관점에서 검토하라. (1) S6: 모든 시크릿이 `${{ secrets.* }}`로 참조되는지, 하드코딩된 키/URL이 없는지, (2) workflow_dispatch 트리거에 confirm=yes 입력이 필수인지, (3) Python 환경 설정 + requirements 설치 스텝이 있는지, (4) 정합성 검증 쿼리 결과가 로그에 출력되는지 확인하라.

### T08: step1 TEST_MODE 검증 (100건)
- 담당 에이전트: **Agent B (Sonnet)** + **PM (사람)** 결과 확인 — Codespaces
- Gemini 검증 프롬프트:
> T08 검증 결과를 검토하라. (1) Supabase에 정확히 100건이 적재되었는지, (2) 2회 연속 실행 후 건수 변화가 없는지(upsert 안전성), (3) 필수 컬럼(facility_code, name, sido, sigungu)에 NULL이 없는지, (4) 정합성 검증 로그가 정상인지 확인하라.

### T09: step2_fetch_api.py 작성
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 파이프라인 코드 작성
- Gemini 검증 프롬프트:
> T09 코드를 보안 + 복원력 관점에서 검토하라. (1) S7: 외부 API 응답에 대한 입력 검증이 있는지, facility_code가 형식 검증 후 사용되는지, (2) Semaphore(5) 동시성 제한이 적용되었는지, (3) 지수 백오프(5초→15초→45초→135초)가 429/503에 대해 구현되었는지, (4) 원자적 업데이트 — 5개 OP 모두 성공 시에만 detail_fetched_at 업데이트인지, (5) 실패 건이 pipeline_errors에 기록되는지, (6) API 응답 스키마 레퍼런스 저장 + 구조 변경 감지 로직이 있는지, (7) 95% 성공 판정 기준이 구현되었는지, (8) pytest mock 기반 테스트가 정상/빈/에러 응답 3가지를 커버하는지 확인하라.

### T10: step2 TEST_MODE 검증 (5건)
- 담당 에이전트: **Agent B (Sonnet)** + **PM (사람)** 결과 확인 — Codespaces
- Gemini 검증 프롬프트:
> T10 검증 결과를 검토하라. (1) 5건의 detail_fetched_at이 NOT NULL인지, (2) capacity, caregiver_count, meal_cost_per_day 등 주요 컬럼에 데이터가 존재하는지, (3) adminPttnCd 폴백 로직이 정상 작동했는지(로그 확인), (4) pipeline_errors 테이블 기록 확인, (5) schemas/ 디렉토리에 API 응답 레퍼런스 파일이 생성되었는지 확인하라.

### T11: step2 GitHub Actions 워크플로우 작성
- 담당 에이전트: **Agent D (Haiku)** — GitHub Actions YAML 작성
- Gemini 검증 프롬프트:
> T11의 `manual_step2.yml`과 `scheduled_step2.yml`을 보안 관점에서 검토하라. (1) S6: 모든 시크릿이 `${{ secrets.* }}`로 참조되는지, (2) manual에 test_mode + offset 파라미터가 있는지, (3) scheduled에 매월 3일 cron + 4일 분할 실행 + matrix 5 Job + timeout 300분이 설정되었는지, (4) 정합성 검증 쿼리 결과 로그 출력 + 임계치 미달 시 실패 처리가 있는지 확인하라.

### T12: step3_generate_seo.py 작성
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 파이프라인 코드 작성
- Gemini 검증 프롬프트:
> T12 코드를 보안 + 품질 관점에서 검토하라. (1) S1/S7: AI 출력이 순수 JSON 텍스트인지, HTML 태그가 포함되지 않도록 프롬프트에 명시되었는지, (2) `response_format={"type": "json_object"}` 사용 확인, (3) jsonschema.validate로 6필드 스키마 검증이 있는지, (4) validate_seo_json 품질 검증 함수가 시설명/지역명 포함, 300자 이상, AI 암시 문구 필터링을 수행하는지, (5) 마크다운 코드 펜스 자동 제거 로직이 있는지, (6) 실패 시 1회 재생성 + 원자적 업데이트 + pipeline_errors 로깅이 구현되었는지, (7) nh3 정화와 정규식 XSS 검증이 **제거**되었는지(v3 변경), (8) pytest 테스트가 JSON 파싱(유효/펜스/잘못된), 스키마 검증, 품질 검증 3가지를 커버하는지 확인하라.

### T13-a: step3 TEST_MODE 검증 (3건)
- 담당 에이전트: **Agent B (Sonnet)** + **PM (사람)** 결과 확인 — Codespaces
- Gemini 검증 프롬프트:
> T13-a 검증 결과를 검토하라. (1) 3건의 seo_content가 유효한 JSONB인지, (2) 6개 필드(intro, highlights, care_services, location_info, facility_info, summary) 모두 존재하는지, (3) highlights 배열이 3~6개인지, (4) 전체 텍스트 300자 이상인지, (5) 시설별 고유 데이터(정원, 인력 수 등)가 반영되어 차별화되었는지, (6) AI 암시 문구("AI가 생성한" 등)가 없는지, (7) seo_generated_at이 NOT NULL인지 확인하라.

### T13-b: step3 GitHub Actions 워크플로우 작성
- 담당 에이전트: **Agent D (Haiku)** — GitHub Actions YAML 작성
- Gemini 검증 프롬프트:
> T13-b의 `manual_step3.yml`과 `scheduled_step3.yml`을 보안 관점에서 검토하라. (1) S6: 시크릿 참조 방식 확인, (2) manual에 test_mode 선택 파라미터가 있는지, (3) scheduled에 매월 5일 cron + matrix 5 Job + timeout 300분이 설정되었는지, (4) 정합성 검증 쿼리(JSONB 유효성 포함)가 로그에 출력되는지 확인하라.

### T13-c: 전체 파이프라인 실행 (step1→step2→step3)
- 담당 에이전트: **PM (사람)** — GitHub Actions manual 트리거 + 승인
- Gemini 검증 프롬프트:
> T13-c 실행 결과를 검토하라. (1) `SELECT count(*) FROM nursing_homes WHERE detail_fetched_at IS NOT NULL` >= 19,000 (95%)인지, (2) `SELECT count(*) FROM nursing_homes WHERE seo_generated_at IS NOT NULL` >= 19,000인지, (3) `SELECT count(*) FROM nursing_homes WHERE seo_content IS NOT NULL AND jsonb_typeof(seo_content) = 'object'` >= 19,000인지(JSONB 유효성), (4) pipeline_errors 실패 건수가 5% 미만인지, (5) OpenAI 실제 비용이 ~$12.10 예산 범위 내인지 확인하라.

### T13-d: 파일럿 배포 (100건)
- 담당 에이전트: **Agent B (Sonnet)** 렌더링 스크립트 작성 + **PM (사람)** 배포/모니터링
- Gemini 검증 프롬프트:
> T13-d 산출물을 보안 + SEO 관점에서 검토하라. (1) S1: 간이 HTML 렌더링에 dangerouslySetInnerHTML이 사용되지 않았는지(Python Jinja2/문자열 포매팅 방식인지), (2) S4: representative_name이 HTML 출력에 포함되지 않는지, (3) sitemap.xml이 정상 생성되었는지, (4) 100건 HTML 페이지가 유효한 구조인지, (5) Search Console에 sitemap 제출이 완료되었는지 확인하라.

---

## 프론트엔드 태스크

### T14: Next.js 15 프로젝트 초기 설정
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 프론트엔드 코드 작성
- Gemini 검증 프롬프트:
> T14 산출물을 보안 + 설정 정합성 관점에서 검토하라. (1) package.json에 `lucide-react`, `recharts`, `@supabase/supabase-js`가 포함되고 `sanitize-html`과 `chart.js`가 **없는지**, (2) S1: ESLint에 `"react/no-danger": "error"` 규칙이 설정되었는지, (3) S3: CSP 관련 설정이 없는 상태에서 unsafe-inline/unsafe-eval이 사용되지 않는지, (4) SeoContentJson TypeScript 인터페이스가 plan-v4 §3 스키마 6필드와 일치하는지(S5 동기화), (5) 환경변수가 NEXT_PUBLIC_ 접두사로 설정되었는지 확인하라.

### T15: 메인 페이지 (/) 구현
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 프론트엔드 코드 작성
- Gemini 검증 프롬프트:
> T15 코드를 보안 + 접근성 + UX 관점에서 검토하라. (1) S1: dangerouslySetInnerHTML 미사용 확인 (`grep -r "dangerouslySetInnerHTML" src/`), (2) S4: representative_name이 카드에 렌더링되지 않는지, (3) 접근성: 기본 폰트 text-lg(18px), 시맨틱 HTML(`<nav>`, `<main>`, `<article>`, `<footer>`), WCAG AA 색상대비 4.5:1 확인, (4) loading.tsx 스켈레톤이 Tailwind animate-pulse로 구현되고 실제 카드와 동일 레이아웃(CLS 0)인지, (5) 배지 아이콘 4종(BedDouble, Building2, HeartPulse, UtensilsCrossed)이 올바른 데이터 로직으로 렌더링되는지, (6) 면책 고지 문구가 사이트 하단에 표시되는지, (7) Server Component로 구현되어 크롤러에 노출되는지 확인하라.

### T16: 상세 페이지 (/[facility_code]) 구현
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 프론트엔드 코드 작성
- Gemini 검증 프롬프트:
> T16 코드를 보안 + 성능 + 접근성 관점에서 **정밀 검토**하라 (v4 핵심 태스크). (1) S1: dangerouslySetInnerHTML 미사용 + SeoContent 템플릿 컴포넌트가 React JSX `{text}` 렌더링만 사용하는지, (2) S3: recharts가 SVG 기반이고 Canvas/eval을 사용하지 않는지, chart.js 임포트가 없는지, (3) S4: 차트 3종에 representative_name이 절대 노출되지 않는지, (4) SSR 가드: 차트 컴포넌트에 `next/dynamic({ ssr: false })`가 적용되었는지, (5) CLS 방지: 차트 컨테이너에 `h-64` 고정 높이가 지정되었는지, (6) null 처리: `detail_fetched_at IS NULL` 시설에서 차트 비표시 + "데이터 준비 중" 안내가 있는지, (7) 접근성: 차트에 `aria-label` + SVG `<desc>` 태그가 있는지, (8) 비용 차트 하단에 "실제 금액과 다를 수 있습니다" 면책 고지가 있는지, (9) generateStaticParams가 상위 1,000건만 반환하는지, (10) revalidate: 2592000(30일 ISR)이 설정되었는지, (11) 상세 페이지 loading.tsx 스켈레톤이 CLS 0을 유지하는지 확인하라.

### T17: 자부담금 계산기 (CostCalculator.tsx) 구현
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 프론트엔드 코드 작성 (MVP 후 추가 가능)
- Gemini 검증 프롬프트:
> T17 코드를 검토하라. (1) "use client" 클라이언트 컴포넌트로 선언되었는지, (2) 2025년 등급별 본인부담금(1등급 655,000 / 2등급 607,000 / 3~5등급 524,000)이 정확한지, (3) 이용일수 슬라이더 범위(15~31일)가 올바른지, (4) S4: representative_name이 노출되지 않는지, (5) 면책 고지("실제 금액과 다를 수 있습니다")가 포함되었는지 확인하라.

### T18: Rate Limiting 미들웨어 구현
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 미들웨어 코드 작성 (MVP 후 추가 가능)
- Gemini 검증 프롬프트:
> T18 코드를 보안 관점에서 검토하라. (1) 1분 60회 제한이 구현되었는지, (2) 429 응답이 올바르게 반환되는지, (3) 봇 예외(Googlebot, Bingbot, Yandexbot, DuckDuckBot)가 User-Agent 기반으로 구현되었는지, (4) KV 장애 시 정상 통과(fail-open)인지, (5) S3: middleware에서 CSP 헤더가 유지되는지 확인하라.

### T19: SEO 메타데이터, sitemap.xml, 보안 헤더 생성
- 담당 에이전트: **Agent B (Sonnet)** — Codespaces, 프론트엔드 코드 작성
- Gemini 검증 프롬프트:
> T19 산출물을 SEO + 보안 관점에서 검토하라. (1) 각 페이지별 title, description, og 태그가 동적으로 생성되는지, (2) sitemap.xml이 2만 URL을 포함하는지, (3) robots.txt가 올바르게 작성되었는지, (4) S3: CSP 헤더 `script-src 'self'`가 Next.js middleware에 설정되고 `unsafe-inline`/`unsafe-eval`이 없는지, (5) 삭제 요청 프로세스 안내(24시간 내 처리)가 footer에 포함되었는지 확인하라.

---

## 배포 및 자동화 태스크

### T20: Vercel 배포
- 담당 에이전트: **PM (사람)** — 브라우저 + Vercel 대시보드
- Gemini 검증 프롬프트:
> T20 배포 결과를 검토하라. (1) Vercel 대시보드에서 배포 성공 상태인지, (2) 빌드 시간이 45분 이내인지, (3) 환경변수(SUPABASE_URL, SUPABASE_ANON_KEY)가 설정되었는지, (4) 배포 URL에서 메인 페이지 + 상세 페이지 + 차트 3종이 정상 렌더링되는지, (5) v4 번들 추가(recharts ~45KB + lucide ~5KB)가 코드 스플리팅되어 메인 페이지 번들에 미포함인지 확인하라.

### T21: Vercel Deploy Hook 생성 및 등록
- 담당 에이전트: **PM (사람)** — 브라우저
- Gemini 검증 프롬프트:
> T21 완료 결과를 검토하라. (1) Vercel 프로젝트 설정에서 Deploy Hook URL이 생성되었는지, (2) GitHub Secrets에 VERCEL_DEPLOY_HOOK_URL이 등록되었는지, (3) `curl -X POST` 테스트로 새 배포가 트리거되는지 확인하라.

### T22: GitHub Actions 스케줄 워크플로우 완성
- 담당 에이전트: **Agent D (Haiku)** — GitHub Actions YAML 작성
- Gemini 검증 프롬프트:
> T22 산출물을 보안 + 정합성 관점에서 검토하라. (1) S6: 모든 워크플로우에서 시크릿이 `${{ secrets.* }}`로만 참조되는지, (2) 매월 1일 xlsx 갱신 알림 Issue 자동 생성 워크플로우가 있는지, (3) 매월 6일 redeploy_vercel.yml이 Deploy Hook을 호출하는지, (4) 전체 워크플로우 6개(manual 3개 + scheduled 3개)가 모두 존재하는지 확인하라.

### T23: 도메인 연결 (선택사항)
- 담당 에이전트: **PM (사람)** — 브라우저
- Gemini 검증 프롬프트:
> T23 완료 결과를 검토하라 (DT04에서 구매 결정 시에만). (1) 커스텀 도메인으로 접속 시 사이트가 정상 표시되는지, (2) HTTPS 인증서가 자동 발급되었는지, (3) DNS 설정이 올바른지, (4) NEXT_PUBLIC_SITE_URL이 업데이트되었는지 확인하라.

---

## 런칭 후 검증 태스크

### T24: Google Search Console 등록 및 색인 요청
- 담당 에이전트: **PM (사람)** — 브라우저
- Gemini 검증 프롬프트:
> T24 완료 결과를 검토하라. (1) Search Console에 사이트가 등록되었는지, (2) sitemap.xml이 제출되었는지, (3) "색인 생성 요청됨" 상태인지, (4) T13-d 파일럿 100건의 색인률이 80% 이상인지(2주 경과 후) 확인하라.

### T25: 최종 검증 체크리스트 실행
- 담당 에이전트: **Agent B (Sonnet)** 자동화 가능 항목 + **PM (사람)** 수동 확인
- Gemini 검증 프롬프트:
> T25의 22개 검증 항목 결과를 **전수 검토**하라. 특히 보안/v4 항목을 중점 확인: (1) S1 #19: 코드베이스에 dangerouslySetInnerHTML 미사용(`grep -r "dangerouslySetInnerHTML" src/` 결과 0건), (2) S3 #16: CSP 헤더 `script-src 'self'` 적용, (3) S4: 전체 프론트엔드에서 representative_name 비표시, (4) v4 #20: 차트 3종(비용비교/입소현황/인력비율) 정상 렌더링, (5) v4 #21: 차트 null 데이터 시 "데이터 준비 중" 표시, (6) v4 #22: 스켈레톤 로딩 정상 표시(메인+상세), (7) #14: RLS 정책 — anon으로 쓰기 시도 시 거부, (8) #17: 접근성 — 폰트 18px, 색상대비, 시맨틱 HTML, (9) #18: 면책 고지 + 삭제 요청 안내 표시. 22개 항목 중 미통과가 있으면 구체적 실패 사유와 수정 방안을 제시하라.

### T26: 모니터링 및 수익화 준비
- 담당 에이전트: **PM (사람)** — 브라우저
- Gemini 검증 프롬프트:
> T26 완료 결과를 검토하라. (1) Vercel Analytics가 활성화되고 트래픽 데이터 수집이 시작되었는지, (2) 비용 전환 트리거(월 10만 PV 초과 → Vercel Pro)가 모니터링 기준에 포함되었는지, (3) 에드센스 신청 준비 사항(월간 PV 기준, 콘텐츠 품질)이 정리되었는지 확인하라.

---

## 에이전트 배정 요약표

| 태스크 | 담당 에이전트 | 실행 환경 |
|---|---|---|
| DT01~DT05 | PM (사람) | 브라우저 |
| T01 | PM (사람) | 브라우저 |
| T02 | PM (사람) | 브라우저 + Supabase 웹 |
| T03 | PM (사람) | 브라우저 (GitHub Settings) |
| T04 | Agent D (Haiku) | Supabase SQL |
| T04-b | Agent D (Haiku) | Supabase SQL |
| T05 | Agent B (Sonnet) | Codespaces |
| T06 | Agent B (Sonnet) | Codespaces |
| T07 | Agent D (Haiku) | Codespaces |
| T08 | Agent B (Sonnet) + PM | Codespaces |
| T09 | Agent B (Sonnet) | Codespaces |
| T10 | Agent B (Sonnet) + PM | Codespaces |
| T11 | Agent D (Haiku) | Codespaces |
| T12 | Agent B (Sonnet) | Codespaces |
| T13-a | Agent B (Sonnet) + PM | Codespaces |
| T13-b | Agent D (Haiku) | Codespaces |
| T13-c | PM (사람) | GitHub Actions |
| T13-d | Agent B (Sonnet) + PM | Codespaces + Vercel |
| T14 | Agent B (Sonnet) | Codespaces |
| T15 | Agent B (Sonnet) | Codespaces |
| T16 | Agent B (Sonnet) | Codespaces |
| T17 | Agent B (Sonnet) | Codespaces |
| T18 | Agent B (Sonnet) | Codespaces |
| T19 | Agent B (Sonnet) | Codespaces |
| T20 | PM (사람) | 브라우저 + Vercel |
| T21 | PM (사람) | 브라우저 |
| T22 | Agent D (Haiku) | Codespaces |
| T23 | PM (사람) | 브라우저 |
| T24 | PM (사람) | 브라우저 |
| T25 | Agent B (Sonnet) + PM | 브라우저 |
| T26 | PM (사람) | 브라우저 |

### 에이전트별 담당 태스크 수

| 에이전트 | 역할 | 담당 태스크 수 |
|---|---|---|
| PM (사람) | 의사결정, 브라우저 작업, 승인, 모니터링 | 16개 (DT01~05, T01~03, T13-c, T20~21, T23~24, T26) |
| Agent B (Sonnet) | src/ 코드 작성 (파이프라인 + 프론트엔드) | 15개 (T05~06, T08~10, T12~13a, T13-d~19, T25) |
| Agent D (Haiku) | 인프라 (SQL + GitHub Actions YAML) | 6개 (T04, T04-b, T07, T11, T13-b, T22) |
| Agent A (Opus) | 마일스톤 전환 리뷰 (PM 판단 시 투입) | 대기 |
| Agent C (Gemini 3.1 Pro) | 각 태스크 완료 후 검증/보안 리뷰 | 전체 31개 태스크 검증 |
