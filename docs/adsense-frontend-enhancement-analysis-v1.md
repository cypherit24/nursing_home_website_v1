# 에드센스 승인 리스크 해소 — 프론트엔드 강화 방안 분석

> 작성일: 2026-04-01 | 기준 문서: plan-v3.md | 판정: 대기 (PM 검토 필요)

---

## 1. 배경

plan-v3의 R11 리스크: **구글 AI 생성 콘텐츠 페널티 (발생 확률: 중, 영향도: 치명)**

현재 plan-v3 프론트엔드는 텍스트 중심 설계:
- SeoContent 템플릿 컴포넌트 (6필드 JSON → JSX)
- 시설 사진 없음 (R3: API 미제공, 홈페이지 링크 대체)
- 시각적 요소가 카드 리스트 + 텍스트 섹션뿐

**에드센스 승인 거부 사유 예상**: 2만 페이지 텍스트 전용 + AI 생성 의혹 → "thin content" / "auto-generated content" 판정

**제안된 3가지 강화 방안**:
1. Skeleton UI — 로딩 상태 시각적 완성도
2. Badge & Icon — 무료 벡터 아이콘으로 시각적 밀도 확보
3. Interactive Chart — 숫자 데이터 시각화로 고유 가치 증명

---

## 2. 핵심 데이터 소스 확인

차트에 사용할 숫자 데이터의 출처를 먼저 정리한다.

| 데이터 | 출처 | 저장 위치 | 비고 |
|---|---|---|---|
| 정원 (capacity) | B550928 API step2 | nursing_homes.capacity | 정수 |
| 현원 (current_occupancy) | B550928 API step2 | nursing_homes.current_occupancy | 정수 |
| 요양보호사 수 (caregiver_count) | B550928 API step2 | nursing_homes.caregiver_count | 정수 |
| 식비/일 (meal_cost_per_day) | B550928 API step2 | nursing_homes.meal_cost_per_day | 원 단위 |
| 1인실 비용 (room_cost_1person) | B550928 API step2 | nursing_homes.room_cost_1person | 원 단위 |
| 2인실 비용 (room_cost_2person) | B550928 API step2 | nursing_homes.room_cost_2person | 원 단위 |

**핵심 판단: 차트 데이터는 seo_content JSON이 아닌 nursing_homes 테이블 컬럼에서 가져온다.**
- seo_content JSON 스키마 변경 불필요 (S5 동기화 이슈 없음)
- AI 재생성 불필요 (비용 $0)
- 데이터가 공공 API 팩트이므로 "AI 생성 콘텐츠"가 아닌 **팩트 기반 시각화**

---

## 3. 4차원 분석

### 3.1 코드 호환성

#### A. Skeleton UI

| 항목 | 분석 |
|---|---|
| 아키텍처 호환 | **완전 호환**. Next.js 15 App Router의 `loading.tsx` 파일 기반 Suspense와 자연스럽게 통합 |
| SSG+ISR 호환 | **핵심 가치**. SSG 1,000건은 즉시 로드. ISR 19,000건은 첫 방문 시 서버 렌더링 대기 → 이때 스켈레톤이 UX 보완 |
| 기존 컴포넌트 | T15 카드 리스트, T16 상세 페이지에 각각 스켈레톤 변형 추가. SeoContent 컴포넌트는 변경 불필요 |
| 의존성 | **추가 패키지 없음**. Tailwind CSS `animate-pulse` 클래스로 구현 가능 |
| Server/Client | Server Component 유지 가능 (`loading.tsx`는 RSC 지원) |

**영향 태스크**: T15, T16에 스켈레톤 컴포넌트 추가 (각 +15분)

#### B. Badge & Icon (Lucide React 권장)

| 항목 | 분석 |
|---|---|
| 아키텍처 호환 | **완전 호환**. lucide-react는 Server Component 지원 (RSC compatible) |
| 기존 컴포넌트 | T15 카드에 이미 "빈자리뱃지" 개념 존재 → 아이콘 강화로 자연스러운 확장 |
| 의존성 | `lucide-react` 1개 추가. Tree-shakeable (사용한 아이콘만 번들에 포함) |
| 대안 비교 | Heroicons: Tailwind 팀 제작, RSC 지원. 그러나 아이콘 수가 lucide(1,500+)보다 적음(300+). 요양원 도메인 특화 아이콘(침대, 간호, 식사 등)은 lucide가 풍부 |

**영향 태스크**: T14에 lucide-react 설치 추가, T15/T16에 아이콘 적용

**배지 활용 예시**:
| 배지 | 아이콘 | 데이터 소스 |
|---|---|---|
| 빈자리 | `BedDouble` | capacity - current_occupancy > 0 |
| 시설 규모 | `Building2` | capacity 기준 (소/중/대) |
| 요양보호사 비율 | `HeartPulse` | caregiver_count / current_occupancy |
| 식비 수준 | `UtensilsCrossed` | meal_cost_per_day 범위별 |

#### C. Interactive Chart

| 항목 | 분석 |
|---|---|
| 아키텍처 호환 | **조건부 호환**. 차트 라이브러리는 `"use client"` 필수 → plan-v3의 "Server Components 기본" 원칙에서 예외 |
| SSG+ISR 호환 | 호환. 서버에서 데이터를 props로 전달 → 클라이언트에서 차트 렌더링. ISR revalidate 주기에 영향 없음 |
| 의존성 | **recharts 권장** (SVG 기반, CSP 호환, React 네이티브) |
| 대안 비교 | chart.js: Canvas 기반 → CSP `unsafe-eval` 필요할 수 있음 (**S3 위반 위험**). uplot: 경량이나 React 래퍼 미성숙. Recharts: SVG 기반으로 CSP 호환 확인 |
| 번들 영향 | recharts ~45KB gzipped. 그러나 `"use client"` 컴포넌트에서만 로드 → 메인 페이지 번들에 포함되지 않음 (코드 스플리팅) |

**영향 태스크**: T14에 recharts 설치, T16 상세 페이지에 차트 컴포넌트 추가

**차트 적용 예시**:
| 차트 유형 | 데이터 | 렌더링 |
|---|---|---|
| 비용 비교 바 차트 | 식비, 1인실, 2인실 비용 | 해당 시설 vs 시도 평균 |
| 입소 현황 도넛 차트 | 현원 / 잔여 정원 | capacity 대비 점유율 |
| 인력 비율 바 차트 | 요양보호사 수 / 입소자 수 | 권장 비율 대비 시각화 |

---

### 3.2 비용

| 항목 | 추가 비용 | 근거 |
|---|---|---|
| **Skeleton UI** | **$0** | Tailwind CSS 내장 기능. 추가 패키지 없음 |
| **Badge & Icon** | **$0** | lucide-react: MIT 라이선스, 무료 |
| **Interactive Chart** | **$0** | recharts: MIT 라이선스, 무료 |
| AI 재생성 | **$0** | seo_content JSON 스키마 변경 없음. 차트 데이터는 DB 컬럼 직접 사용 |
| 빌드 시간 | **무시할 수준** | 클라이언트 컴포넌트 추가로 빌드 시간 1~2분 증가 예상 (45분 제한 내 충분) |
| 번들 크기 → 대역폭 | **무시할 수준** | recharts ~45KB + lucide 아이콘 ~5KB = ~50KB. Vercel 무료 100GB 대역폭에 영향 미미 |
| 개발 시간 | **+3~5시간** | 스켈레톤(+30분), 배지/아이콘(+1시간), 차트 컴포넌트(+2~3시간) |

**비용 총괄: plan-v3 §1 비용 총괄 변경 없음**

---

### 3.3 효율성

| 항목 | 영향 | 상세 |
|---|---|---|
| **페이지 로드 속도** | +-0 (스켈레톤), -미미 (차트) | 스켈레톤은 체감 속도 향상. 차트는 클라이언트 렌더링이지만 코드 스플리팅으로 메인 페이지 영향 없음. 상세 페이지에서 ~50KB 추가 다운로드 |
| **빌드 효율** | 변경 없음 | SSG 1,000건 + ISR 19,000건 전략 유지 |
| **SEO 크롤링** | **긍정적** | 차트는 SVG로 렌더링 → Googlebot이 정적 HTML로 인식. 배지/아이콘은 Server Component에서 렌더링 → 크롤러에 바로 노출 |
| **개발 효율** | **미미한 증가** | 기존 T15/T16 작업에 추가 구현. 별도 태스크 불필요 |
| **에드센스 승인 효율** | **핵심 가치** | 텍스트 전용 → 시각적 풍부함 전환. "unique value" 증거 강화 |

**LCP/CLS 영향 분석**:
- Skeleton UI: CLS 0 유지 (스켈레톤이 실제 콘텐츠와 동일한 레이아웃 점유)
- Badge/Icon: SVG → 고정 크기, CLS 영향 없음
- Chart: `"use client"` 로딩 시 레이아웃 시프트 가능 → **차트 영역에 고정 높이(h-64 등) 지정 필수**

---

### 3.4 보안성

| 규칙 | Skeleton UI | Badge & Icon | Interactive Chart |
|---|---|---|---|
| **S1 XSS** | **안전**. 순수 Tailwind 클래스 | **안전**. SVG React 컴포넌트, JSX 자동 이스케이핑 | **안전 (recharts)**. SVG 기반 렌더링, dangerouslySetInnerHTML 미사용. **주의: chart.js는 Canvas 기반으로 일부 플러그인에서 eval 사용 가능 → 사용 금지** |
| **S2 RLS** | 영향 없음 | 영향 없음 | 영향 없음. 차트 데이터는 기존 anon SELECT 쿼리로 조회 |
| **S3 CSP** | 영향 없음 | 영향 없음 | **recharts: 호환** (SVG, inline script 없음). **chart.js: 비호환 위험** (Canvas + eval) → recharts 선택 근거 |
| **S4 개인정보** | 영향 없음 | 영향 없음 | **주의**: 차트에 representative_name 노출 금지. 시설 통계 데이터만 시각화 |
| **S5 스키마 동기화** | 영향 없음 | 영향 없음 | **영향 없음**. 차트 데이터는 seo_content JSON이 아닌 nursing_homes 테이블 컬럼 사용 |
| **S6 시크릿** | 영향 없음 | 영향 없음 | 영향 없음 |
| **S7 입력 검증** | 영향 없음 | 영향 없음 | 차트 props는 서버에서 전달 → 외부 입력 아님 |

**보안 총평: 3가지 모두 기존 보안 모델과 완전 호환. recharts 선택 시 S1/S3 위반 없음.**

---

## 4. plan-v3.md 영향 범위 상세

### 4.1 변경이 필요한 태스크

| 태스크 | 현재 내용 | 변경 내용 | 변경 크기 |
|---|---|---|---|
| **T14** | Next.js 초기 설정 + SeoContentJson 타입 + ESLint | `lucide-react`, `recharts` 패키지 추가 설치 | 소 |
| **T15** | 메인 페이지 — 카드 리스트 + 필터 + 페이지네이션 | (1) 카드에 배지 아이콘 추가 (빈자리, 규모, 비율), (2) `loading.tsx` 스켈레톤 추가 | 중 |
| **T16** | 상세 페이지 — SeoContent + 현황 카드 3개 | (1) `loading.tsx` 스켈레톤, (2) 현황 카드에 아이콘 추가, (3) 비용/입소/인력 차트 컴포넌트 3개 추가 | 중 |
| **T25** | 최종 검증 체크리스트 19개 항목 | 차트 렌더링 정상 확인 항목 추가 (20번째) | 소 |

### 4.2 변경 불필요한 영역

| 영역 | 이유 |
|---|---|
| seo_content JSON 스키마 (§3) | 차트는 DB 컬럼 사용, 스키마 무관 |
| 파이프라인 (T05~T13) | 백엔드 변경 없음 |
| DB 마이그레이션 (T04) | 테이블/컬럼 추가 없음 |
| GitHub Actions (T07, T11, T13-b, T22) | 워크플로우 변경 없음 |
| 보안 모델 (§7) | recharts 선택 시 S1~S7 위반 없음 |
| 빌드 전략 (SSG+ISR) | 변경 없음 |
| 비용 총괄 (§1) | 추가 비용 $0 |
| 리스크 (§6) | R11 완화 효과. 신규 리스크 없음 |
| 롤백 계획 (§9) | 변경 없음 |
| 일정표 (§10) | 4주차 T15/T16 범위 내 흡수 가능 (+3~5시간) |

### 4.3 추가 권장 사항

| # | 항목 | 설명 |
|---|---|---|
| 1 | **차트 영역 고정 높이** | CLS 방지. `<div className="h-64">` 등으로 차트 컨테이너 크기 고정 |
| 2 | **차트 lazy loading** | `next/dynamic`으로 차트 컴포넌트 동적 임포트 → 초기 JS 번들에서 제외 |
| 3 | **시도 평균 데이터** | 비용 비교 차트에 "시도 평균"을 표시하려면, 별도 RPC 함수 또는 빌드 시 집계 필요 → T16 구현 시 결정 |
| 4 | **차트 접근성** | 차트에 `aria-label` 추가. 스크린리더용 텍스트 대체 (`<desc>` SVG 태그 활용) |
| 5 | **recharts SSR 호환** | recharts는 SSR에서 빈 div 렌더링 → 클라이언트 hydration 후 차트 표시. `loading.tsx` 스켈레톤으로 자연스럽게 연결 |

---

## 5. 에드센스 승인 관점 종합 평가

### 적용 전 (현재 plan-v3)

| 에드센스 평가 항목 | 현재 상태 | 리스크 |
|---|---|---|
| **콘텐츠 독창성** | AI 생성 텍스트 2만 건 | 높음 — "auto-generated" 의심 |
| **시각적 완성도** | 텍스트 + 카드 리스트 | 중 — 이미지 없는 텍스트 사이트 |
| **사용자 가치** | 정보 조회 | 중 — 공공데이터 단순 재가공 의심 |
| **페이지 체류 시간** | 텍스트 읽기만 | 낮을 가능성 |
| **모바일 UX** | 반응형 텍스트 | 기본 수준 |

### 적용 후

| 에드센스 평가 항목 | 개선 상태 | 리스크 변화 |
|---|---|---|
| **콘텐츠 독창성** | AI 텍스트 + **팩트 기반 차트** + 배지 | **완화** — 차트는 공공 API 원본 데이터 시각화 (AI 아님) |
| **시각적 완성도** | 아이콘 배지 + 차트 + 스켈레톤 | **크게 개선** — 전문 웹서비스 수준 |
| **사용자 가치** | 비용 비교, 입소율 시각화, 인력 비율 비교 | **크게 개선** — 원본 데이터에 없는 파생 가치 제공 |
| **페이지 체류 시간** | 차트 인터랙션 + 비교 분석 | **개선** — 사용자 참여 증가 |
| **모바일 UX** | 스켈레톤 로딩 + SVG 차트 (반응형) | **개선** — 체감 속도 향상 |

---

## 6. 자체 검증 — 누락 항목 재검토

| # | 검토 항목 | 결과 | 비고 |
|---|---|---|---|
| 1 | seo_content 스키마 변경 필요 여부 | **변경 불필요** 확인 | 차트 데이터는 DB 컬럼 직접 사용 |
| 2 | S1~S7 위반 여부 | **전체 통과** | recharts 선택 전제 |
| 3 | CSP script-src 'self' 호환 | **recharts 호환** 확인 | chart.js 사용 시 위반 가능 → 배제 |
| 4 | 빌드 시간 45분 제한 영향 | **영향 미미** (+1~2분) | 코드 스플리팅으로 번들 분리 |
| 5 | 비용 증가 여부 | **$0** | 무료 라이브러리 + DB 데이터 재활용 |
| 6 | ISR revalidate 영향 | **영향 없음** | 차트 데이터도 30일 ISR 주기로 갱신 |
| 7 | 접근성 WCAG AA 영향 | **추가 조치 필요** | 차트 aria-label, 색상대비 확인 |
| 8 | 개인정보 S4 위반 가능성 | **차트에 representative_name 금지** 확인 | 시설 통계만 시각화 |
| 9 | T25 체크리스트 업데이트 | **필요** | 20번째 항목 추가 |
| 10 | 일정 영향 | **4주차 내 흡수 가능** | +3~5시간 |
| 11 | 차트 데이터 null 처리 | **추가 고려 필요** | step2 미완료 시설은 차트 비표시 또는 "데이터 없음" 표시 |
| 12 | recharts SSR hydration mismatch | **추가 고려 필요** | next/dynamic + ssr: false 또는 useEffect 가드 |

**누락 발견 2건**:
- **#11 차트 데이터 null 처리**: step2 미완료(detail_fetched_at IS NULL) 시설은 숫자 데이터가 없음. T16에서 조건부 렌더링 필요 (`capacity != null일 때만 차트 표시`)
- **#12 SSR hydration**: recharts는 서버에서 빈 div → 클라이언트에서 차트. `next/dynamic({ ssr: false })`로 hydration mismatch 방지 필요. T16 구현 시 반영

---

## 7. 최종 판정

| 방안 | 채택 권장 | 이유 |
|---|---|---|
| **Skeleton UI** | **강력 권장** | 비용 $0, 패키지 추가 없음, ISR UX 필수 요소, 에드센스 승인 도움 |
| **Badge & Icon** | **권장** | 비용 $0, lucide-react 1개 추가, 시각적 밀도 대폭 향상, 사진 부재 보완 |
| **Interactive Chart** | **권장 (조건부)** | 비용 $0, recharts 필수 (chart.js 금지), 에드센스 "unique value" 핵심 증거. 단, CLS 방지 + null 처리 + SSR 가드 구현 필수 |

**plan-v3 수정 필요 범위: T14, T15, T16, T25 (4개 태스크 범위 확장). 아키텍처/비용/보안 변경 없음.**
