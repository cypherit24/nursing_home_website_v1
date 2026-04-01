---
paths:
  - "src/frontend/**"
---

# Frontend 코딩 가이드라인 (plan-v3 T14~T19 기반)

## 프레임워크 및 설정
- Next.js 15 App Router + Tailwind CSS
- Server Components 기본. 클라이언트 컴포넌트는 "use client" 명시적 선언
- @supabase/supabase-js로 DB 접근

## 보안 (핵심)
- **dangerouslySetInnerHTML 절대 사용 금지** (S1)
- ESLint `"react/no-danger": "error"` 설정 필수
- **SeoContent 템플릿 컴포넌트**로 JSON 렌더링 — React JSX 자동 이스케이핑으로 XSS 원천 차단
- sanitize-html 사용 금지 (v3에서 제거됨 — JSON이므로 불필요)
- **representative_name 렌더링 금지** (S4). 전화번호는 기관 대표번호만

## 빌드 전략 (SSG + ISR)
- `generateStaticParams`: 상위 1,000건만 반환 (인구 밀집 지역 우선, `ORDER BY sido_population DESC LIMIT 1000`)
- `dynamicParams = true`
- `revalidate: 2592000` (30일 ISR)
- 나머지 19,000건은 첫 방문 시 서버 렌더링 -> 캐싱 -> 이후 정적 서빙
- 빌드 시간 목표: 45분 이내 (1,000페이지 기준 ~17분 예상)

## 타입 관리
- `SeoContentJson` 인터페이스: `src/frontend/types/seo-content.ts`
- **반드시 `src/pipeline/schemas/seo_content_schema.json`과 동기화** (S5)
- 6필드: intro, highlights(string[]), care_services, location_info, facility_info, summary

## 접근성 (WCAG AA)
- 기본 폰트: `text-lg` (18px)
- 색상 대비: 4.5:1 이상
- 시맨틱 HTML: `<nav>`, `<main>`, `<article>`, `<footer>`
- 이미지에 `alt` 속성 필수

## 법적 고지
- 사이트 하단 면책 고지: "본 사이트는 공공데이터포털의 공공데이터를 활용하며, 공공데이터법에 의거하여 제공됩니다"
- footer에 삭제 요청 프로세스 안내 (24시간 내 처리)
- 비급여 금액 표시 시 면책 문구 포함

## SEO
- 각 페이지별 title, description, og 태그 설정
- `sitemap.xml` 동적 생성 (2만 URL 포함)
- `robots.txt` 작성
- **CSP 헤더**: `src/middleware.ts`에서 `Content-Security-Policy: script-src 'self'` 설정 (S3)

## Rate Limiting
- 구현 위치: `src/middleware.ts` (프론트엔드 범주)
- Vercel KV 기반 1분 60회 제한. 429 반환
- 봇 예외: Googlebot, Bingbot, Yandexbot, DuckDuckBot
- KV 장애 시 정상 통과 (fail-open)
- MVP 후 추가 가능 (T18)

## 테스트
- vitest 단위 테스트 권장
- SeoContent 컴포넌트 렌더링 테스트 포함
