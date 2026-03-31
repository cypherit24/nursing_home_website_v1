# 전국 요양원 SEO 자동화 시스템 — 실행 계획서

---

## 1. 프로젝트 개요

**한 줄 목표**: 전국 요양원 2만 곳의 공공데이터를 자동 수집·AI 소개글 생성·정적 웹페이지 배포하여 검색 트래픽 기반 수익화 시스템을 구축한다.

**핵심 성공 지표 (KPI)**

| # | 지표 | 목표 |
|---|---|---|
| 1 | 구글 색인 페이지 수 | 20,000페이지 이상 |
| 2 | 파이프라인 자동화율 | xlsx 업로드 외 100% 자동 |
| 3 | 월간 운영 비용 | $0 (트래픽 폭증 전까지) |

**전체 예상 기간**: 4주 (주 15~20시간 기준)

---

## 2. 의사결정 선행 항목

코딩 착수 전에 반드시 결정해야 할 사항들:

| ID | 결정 내용 | 옵션 | 추천안 | 결정 기한 |
|---|---|---|---|---|
| DT01 | 평가등급 데이터 확보 방안 | ~~A / B~~ / **C: 등급 없이 런칭** | ✅ **C안 확정** | 확정 |
| DT02 | 시설 사진 확보 방안 | **A: 홈페이지 링크** (1차) → 추후 동의 기반 사진 등록 | ✅ **A안 확정** (크롤링은 저작권 리스크로 보류) | 확정 |
| DT03 | xlsx 갱신 주기 및 담당자 | 월 1회 / 분기 1회 / 반기 1회 | **분기 1회** (공공데이터 업데이트 주기 확인 후 조정) | 미정 |
| DT04 | 도메인 구매 여부 | ~~.com / .co.kr~~ / **Vercel 무료 도메인** | ✅ **무료 도메인으로 시작**, 성공 시 이전 | 확정 |
| DT05 | 월간 운영 비용 상한선 | 무료 유지 / $10 이하 / $30 이하 | **무료 유지** (도메인 비용 없음) | 미정 |

---

## 3. 마일스톤

| # | 마일스톤 | 포함 태스크 | 완료 기준 | 예상 기간 |
|---|---|---|---|---|
| M1 | 인프라 세팅 및 의사결정 | DT01~DT05, T01~T04 | 계정 생성 완료, Secrets 등록 완료, DB 테이블 생성 완료 | 1주차 |
| M2 | 데이터 파이프라인 구축 및 검증 | T05~T13 | step1~3 TEST_MODE 검증 통과 + 전체 실행 완료 | 2주차 |
| M3 | 프론트엔드 구축 | T14~T19 | Next.js 로컬 프리뷰에서 목록·상세·계산기·Rate Limiting 정상 작동 | 3주차 |
| M4 | 배포 및 자동화 | T20~T23 | Vercel 배포 완료, GitHub Actions 스케줄 등록 완료 | 4주차 전반 |
| M5 | 런칭 후 검증 | T24~T26 | Google Search Console 등록, sitemap 제출, 색인 요청 완료 | 4주차 후반 |

---

## 4. 태스크 목록

### 의사결정 태스크

### DT01: 평가등급 데이터 확보 방안 결정
- 마일스톤: M1
- 실행 환경: 브라우저 (논의)
- 선행 조건: 없음
- 작업 내용: B550928 API에서 평가정보 제공 불가 확인됨. C안(등급 없이 런칭) 채택 여부 결정. 향후 A안(공단 포털 파일) 병행 추진 일정 협의.
- 완료 확인: 결정 내용을 이 문서에 기록
- 예상 소요: 10분
- 비용: 없음

### DT02: 시설 사진 확보 방안 결정
- 마일스톤: M1
- 실행 환경: 브라우저 (논의)
- 선행 조건: 없음
- 작업 내용: API에서 사진정보 제공 불가 확인됨. A안(홈페이지 URL 링크 대체) 채택 여부 결정.
- 완료 확인: 결정 내용을 이 문서에 기록
- 예상 소요: 10분
- 비용: 없음

### DT03: xlsx 갱신 주기 및 담당자 결정
- 마일스톤: M1
- 실행 환경: 브라우저 (논의)
- 선행 조건: 없음
- 작업 내용: 공공데이터포털 파일은 자동 다운로드 불가. 수동 갱신 주기(분기/반기)와 담당자 결정.
- 완료 확인: 결정 내용을 이 문서에 기록
- 예상 소요: 10분
- 비용: 없음

### DT04: 도메인 구매 여부 결정
- 마일스톤: M1
- 실행 환경: 브라우저 (논의)
- 선행 조건: 없음
- 작업 내용: SEO 효과를 위한 커스텀 도메인 구매 여부 결정. Vercel 무료 도메인 vs .com/.co.kr.
- 완료 확인: 결정 내용을 이 문서에 기록
- 예상 소요: 10분
- 비용: 구매 시 연 $10~20

### DT05: 월간 운영 비용 상한선 합의
- 마일스톤: M1
- 실행 환경: 브라우저 (논의)
- 선행 조건: 없음
- 작업 내용: 무료 티어 범위 내 운영 가능 확인. 트래픽 폭증 시 Vercel Pro 전환 기준 합의.
- 완료 확인: 결정 내용을 이 문서에 기록
- 예상 소요: 10분
- 비용: 없음

---

### 인프라 세팅 태스크

### T01: 외부 계정 생성
- 마일스톤: M1
- 실행 환경: 브라우저
- 선행 조건: 없음
- 작업 내용: GitHub, Supabase, OpenAI, Vercel 계정 생성. 공공데이터포털 B550928 API Decoding 키 발급 신청 (승인 1~2일 소요).
- 완료 확인: 각 서비스 대시보드 로그인 확인. API 키 발급 신청 완료 확인.
- 예상 소요: 1시간
- 비용: 없음

### T02: xlsx 파일 확보 및 Storage 업로드
- 마일스톤: M1
- 실행 환경: 브라우저 + Supabase 웹
- 선행 조건: T01
- 작업 내용: 공공데이터포털에서 장기요양기관 현황 xlsx 다운로드. Supabase Storage에 pipeline-data 버킷 생성 후 업로드.
- 완료 확인: Supabase Storage > pipeline-data 버킷에서 파일 확인
- 예상 소요: 30분
- 비용: 없음

### T03: GitHub Secrets 및 Codespaces Secrets 등록
- 마일스톤: M1
- 실행 환경: 브라우저 (GitHub Settings)
- 선행 조건: T01
- 작업 내용: Repository Secrets 5개 등록 (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, PUBLIC_DATA_API_KEY, OPENAI_API_KEY, VERCEL_DEPLOY_HOOK_URL). Codespaces Secrets 4개 등록 (VERCEL_DEPLOY_HOOK_URL 제외).
- 완료 확인: GitHub > Settings > Secrets에서 5개 항목 확인. Codespaces 환경에서 `echo $SUPABASE_URL` 출력 확인.
- 예상 소요: 30분
- 비용: 없음

### T04: Supabase DB 테이블 생성 및 RLS 설정
- 마일스톤: M1
- 실행 환경: Supabase 웹 (SQL Editor)
- 선행 조건: T01
- 작업 내용: nursing_homes 테이블 생성 SQL 실행. RLS 정책 설정 (anon=읽기만, service_role=모두). facility_code UNIQUE 인덱스 + sido/sigungu 인덱스 생성.
- 완료 확인: Supabase Table Editor에서 nursing_homes 테이블 확인. RLS 정책 활성화 확인. `SELECT count(*) FROM nursing_homes` 실행 시 0 반환.
- 예상 소요: 30분
- 비용: 없음

---

### 데이터 파이프라인 태스크

### T05: 프로젝트 폴더 구조 및 유틸리티 파일 생성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T04
- 작업 내용: src/ 하위 폴더 구조 생성 (pipeline/, frontend/). 공통 유틸리티 파일 작성 (Supabase 클라이언트, 로깅, 환경변수 로드). Python requirements.txt 작성.
- 완료 확인: `ls -R src/` 로 폴더 구조 확인. `python -c "from src.pipeline.utils import ..."` 에러 없음.
- 예상 소요: 30분
- 비용: 없음

### T06: step1_load_xlsx.py 작성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T05
- 작업 내용: Supabase Storage에서 xlsx 다운로드 → pandas로 파싱 → nursing_homes 테이블에 upsert. facility_code dtype=str 필수 (앞자리 0 보호). xlsx 컬럼 매핑 적용 (A→facility_code, B→name, G→sido/sigungu 등).
- 완료 확인: `python src/pipeline/step1_load_xlsx.py` 에러 없음. Supabase에서 `SELECT count(*) FROM nursing_homes` 약 20,000건 확인.
- 예상 소요: 1시간
- 비용: 없음

### T07: step1 GitHub Actions 워크플로우 작성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T06
- 작업 내용: `.github/workflows/manual_step1.yml` 작성. workflow_dispatch 트리거 + confirm=yes 입력 필수. Python 환경 설정 + requirements 설치 + step1 실행.
- 완료 확인: GitHub Actions 탭에서 워크플로우 표시 확인 (실행은 T02 이후)
- 예상 소요: 30분
- 비용: 없음

### T08: step1 TEST_MODE 검증 (100건)
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T06, T02, T03
- 작업 내용: TEST_MODE=true로 100건만 적재 테스트. facility_code 중복 실행 안전성 확인 (2회 연속 실행 → 건수 변화 없음).
- 완료 확인: Supabase에서 100건 확인. 재실행 시 건수 동일.
- 예상 소요: 30분
- 비용: 없음

### T09: step2_fetch_api.py 작성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T05
- 작업 내용: detail_fetched_at IS NULL인 기관 조회 → B550928 API 5개 오퍼레이션 비동기 호출 (Semaphore(10)). XML 응답 xmltodict 파싱. adminPttnCd 폴백 로직 구현 (OP1 먼저 → 실패 시 A03→A01→A04→B03→C06 순). 전화번호 조합, 비급여 전처리 포함.
- 완료 확인: 코드 린트 통과. 단위 테스트 통과.
- 예상 소요: 2시간
- 비용: 없음

### T10: step2 TEST_MODE 검증 (5건)
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T09, T08, T03 (API 키 승인 필수)
- 작업 내용: TEST_MODE=true로 5건만 API 수집 테스트. adminPttnCd 폴백 로직 정상 작동 확인. 수집 결과 DB 컬럼 값 육안 확인.
- 완료 확인: Supabase에서 5건의 detail_fetched_at 값 NOT NULL 확인. capacity, caregiver_count 등 주요 컬럼에 데이터 존재.
- 예상 소요: 30분
- 비용: 없음 (API 호출 무료)

### T11: step2 GitHub Actions 워크플로우 작성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T10
- 작업 내용: `manual_step2.yml` (수동, test_mode 선택) + `scheduled_step2.yml` (매월 3일, matrix 5 Job 병렬, timeout 300분) 작성.
- 완료 확인: GitHub Actions 탭에서 워크플로우 2개 표시 확인.
- 예상 소요: 30분
- 비용: 없음

### T12: step3_generate_seo.py 작성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T05
- 작업 내용: seo_generated_at IS NULL인 기관 조회 → OpenAI gpt-4o-mini로 SEO 소개글 생성 (Semaphore(20)). 출력: 순수 HTML (h1·h2·p·ul·li). nh3로 HTML 정화. 429 오류 시 지수 백오프 (10초→30초→90초).
- 완료 확인: 코드 린트 통과. 단위 테스트 통과.
- 예상 소요: 1시간
- 비용: 없음

### T13-a: step3 TEST_MODE 검증 (3건)
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T12, T10
- 작업 내용: TEST_MODE=true로 3건만 SEO 글 생성 테스트. 생성된 HTML 품질 육안 확인 (구조, 키워드, 자연스러움).
- 완료 확인: Supabase에서 3건의 seo_content 값 확인. HTML 구조 정상. seo_generated_at NOT NULL.
- 예상 소요: 30분
- 비용: ~$0.01 (3건)

### T13-b: step3 GitHub Actions 워크플로우 작성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T13-a
- 작업 내용: `manual_step3.yml` (수동, test_mode 선택) + `scheduled_step3.yml` (매월 5일, matrix 5 Job 병렬, timeout 300분) 작성.
- 완료 확인: GitHub Actions 탭에서 워크플로우 2개 표시 확인.
- 예상 소요: 30분
- 비용: 없음

### T13-c: 전체 파이프라인 실행 (step1→step2→step3)
- 마일스톤: M2
- 실행 환경: GitHub Actions (manual 트리거)
- 선행 조건: T13-a 검증 통과 + 사용자 실행 승인
- 작업 내용: step1 전체 실행 (약 30분) → step2 전체 실행 (2~3시간, 5 Job 병렬) → step3 전체 실행 (3~4시간, 5 Job 병렬). 각 단계 완료 후 다음 단계 실행.
- 완료 확인: `SELECT count(*) FROM nursing_homes WHERE detail_fetched_at IS NOT NULL` ≈ 20,000. `SELECT count(*) FROM nursing_homes WHERE seo_generated_at IS NOT NULL` ≈ 20,000.
- 예상 소요: 6~8시간 (자동 실행, PC 꺼도 됨)
- 비용: OpenAI API ~$10~15

---

### 프론트엔드 태스크

### T14: Next.js 15 프로젝트 초기 설정
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T04
- 작업 내용: Next.js 15 App Router 프로젝트 생성. Tailwind CSS 설정. @supabase/supabase-js 설치. 환경변수 설정 (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY).
- 완료 확인: `npm run dev` 정상 실행. localhost:3000에서 기본 페이지 표시.
- 예상 소요: 1시간
- 비용: 없음

### T15: 메인 페이지 (/) 구현
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T14, T13-c (DB에 데이터 필요)
- 작업 내용: Server Component로 구현. 시도/시군구 드롭다운 필터. 카드 리스트 (기관명·주소·정원/현원·빈자리뱃지·요양보호사수). 20건 페이지네이션.
- 완료 확인: 로컬 프리뷰에서 카드 20건 표시. 시도 필터 변경 시 결과 변경. 페이지네이션 작동.
- 예상 소요: 2시간
- 비용: 없음

### T16: 상세 페이지 (/[facility_code]) 구현
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T15
- 작업 내용: Server Component. generateStaticParams로 1000건씩 전체 수집. revalidate: 2592000 (30일 ISR). 현황 카드 3개 (입소·인력·요양보호사 지표). dangerouslySetInnerHTML로 AI HTML 렌더링.
- 완료 확인: 로컬 프리뷰에서 특정 기관 상세 페이지 정상 표시. SEO 소개글 렌더링 확인.
- 예상 소요: 2시간
- 비용: 없음

### T17: 자부담금 계산기 (CostCalculator.tsx) 구현
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T16
- 작업 내용: "use client" 클라이언트 컴포넌트. Props: mealCostPerDay, roomCost1Person, roomCost2Person, capacity. 2025년 등급별 본인부담 (1등급 655,000 / 2등급 607,000 / 3~5등급 524,000). 이용일수 슬라이더 (15~31일). 병실유형 토글 + transition 애니메이션 + 면책 고지.
- 완료 확인: 상세 페이지에서 계산기 정상 작동. 등급 변경·일수 변경·병실 변경 시 금액 실시간 변경.
- 예상 소요: 1시간
- 비용: 없음

### T18: Rate Limiting 미들웨어 구현
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T14
- 작업 내용: src/middleware.ts 작성. Vercel KV (Redis 호환) 기반 1분 60회 제한. 429 반환. 봇 예외 (Googlebot·Bingbot·Yandexbot·DuckDuckBot). KV 장애 시 정상 통과.
- 완료 확인: 로컬에서 60회 초과 요청 시 429 응답 확인. User-Agent에 Googlebot 포함 시 통과 확인.
- 예상 소요: 30분
- 비용: 없음

### T19: SEO 메타데이터 및 sitemap.xml 생성
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T16
- 작업 내용: 각 페이지별 title, description, og 태그 설정. sitemap.xml 동적 생성 (2만 URL 포함). robots.txt 작성.
- 완료 확인: `curl localhost:3000/sitemap.xml` 정상 출력. 메타 태그 확인.
- 예상 소요: 1시간
- 비용: 없음

---

### 배포 및 자동화 태스크

### T20: Vercel 배포
- 마일스톤: M4
- 실행 환경: 브라우저 + Codespaces
- 선행 조건: T15, T16, T17, T18, T19
- 작업 내용: Vercel에 GitHub 리포지토리 연결. 환경변수 설정 (SUPABASE_URL, SUPABASE_ANON_KEY, KV 연결). Vercel KV 인스턴스 생성 및 연결. 배포 실행.
- 완료 확인: Vercel 대시보드에서 배포 성공. 배포 URL에서 메인·상세·계산기 정상 작동.
- 예상 소요: 1시간
- 비용: 없음

### T21: Vercel Deploy Hook 생성 및 등록
- 마일스톤: M4
- 실행 환경: 브라우저
- 선행 조건: T20
- 작업 내용: Vercel 프로젝트 설정에서 Deploy Hook URL 생성. GitHub Secrets에 VERCEL_DEPLOY_HOOK_URL 등록.
- 완료 확인: `curl -X POST $VERCEL_DEPLOY_HOOK_URL` 시 새 배포 트리거 확인.
- 예상 소요: 15분
- 비용: 없음

### T22: GitHub Actions 스케줄 워크플로우 완성
- 마일스톤: M4
- 실행 환경: Codespaces
- 선행 조건: T21, T11, T13-b
- 작업 내용: 매월 1일 GitHub Issue 자동 생성 워크플로우 작성. 매월 6일 redeploy_vercel.yml (Deploy Hook 호출) 작성. 기존 scheduled_step2/step3 최종 확인.
- 완료 확인: GitHub Actions 탭에서 전체 워크플로우 목록 확인 (6개: manual 3개 + scheduled 3개).
- 예상 소요: 30분
- 비용: 없음

### T23: 도메인 연결 (선택사항)
- 마일스톤: M4
- 실행 환경: 브라우저
- 선행 조건: T20, DT04 (도메인 구매 결정 시)
- 작업 내용: 도메인 구매 후 Vercel 프로젝트에 커스텀 도메인 연결. DNS 설정. NEXT_PUBLIC_SITE_URL 업데이트.
- 완료 확인: 커스텀 도메인으로 접속 시 사이트 정상 표시. HTTPS 인증서 자동 발급 확인.
- 예상 소요: 30분
- 비용: 연 $10~20

---

### 런칭 후 검증 태스크

### T24: Google Search Console 등록 및 색인 요청
- 마일스톤: M5
- 실행 환경: 브라우저
- 선행 조건: T20
- 작업 내용: Google Search Console에 사이트 등록. sitemap.xml 제출. 색인 요청.
- 완료 확인: Search Console에서 sitemap 제출 성공. "색인 생성 요청됨" 상태 확인.
- 예상 소요: 30분
- 비용: 없음

### T25: 최종 검증 체크리스트 실행
- 마일스톤: M5
- 실행 환경: 브라우저
- 선행 조건: T20
- 작업 내용: 아래 15개 항목 검증:
  1. 메인 페이지 로드 정상
  2. 시도/시군구 필터 작동
  3. 페이지네이션 작동
  4. 상세 페이지 진입 정상
  5. SEO 소개글 렌더링 정상
  6. 자부담금 계산기 작동
  7. 모바일 반응형 확인
  8. 메타 태그 (title, description, og) 확인
  9. sitemap.xml 접근 가능
  10. robots.txt 접근 가능
  11. Rate Limiting 429 응답 확인
  12. 봇 User-Agent 예외 확인
  13. Vercel Analytics 활성화
  14. DB RLS 정책 작동 확인 (anon으로 쓰기 시도 → 거부)
  15. 전체 페이지 로드 속도 < 3초
- 완료 확인: 15개 항목 모두 통과
- 예상 소요: 1시간
- 비용: 없음

### T26: 모니터링 및 수익화 준비
- 마일스톤: M5
- 실행 환경: 브라우저
- 선행 조건: T24, T25
- 작업 내용: Vercel Analytics 활성화. 트래픽 모니터링 기준 설정. 애드센스 신청 준비 (월간 페이지뷰 기준 충족 시).
- 완료 확인: Vercel Analytics 대시보드에서 트래픽 데이터 수집 시작 확인.
- 예상 소요: 30분
- 비용: 없음

---

## 5. 리스크 관리

| # | 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|---|---|---|---|---|
| R1 | B550928 API 키 승인 지연 (1~2일 이상) | 중 | 높음 | step1(xlsx 적재)은 API 키 없이 진행 가능. 프론트엔드 작업 병행. |
| R2 | 평가등급 데이터 확보 불가 | 확정 | 중 | C안 채택 (등급 없이 런칭). 향후 공단 포털 파일 확보 시 추가. |
| R3 | 시설 사진 데이터 확보 불가 | 확정 | 중 | A안 채택 (홈페이지 URL 링크). 텍스트 중심 디자인으로 보완. |
| R4 | adminPttnCd 폴백 로직 실패 | 낮 | 중 | A03→A01→A04→B03→C06 순서 폴백. 전체 실패 시 해당 기관 건너뛰기 + 로그 기록. |
| R5 | 비급여 금액 단위 불일치 (일별/월별 혼재) | 중 | 낮 | 금액 그대로 저장 + 계산기에 면책 고지 강화. |
| R6 | GitHub Actions 6시간 제한 초과 | 낮 | 중 | matrix 5 Job 병렬 분할로 대응 완료. timeout 300분 설정. |
| R7 | generateStaticParams 2만 건 메모리 초과 | 낮 | 중 | 1000건씩 페이지네이션 수집으로 대응 완료. |
| R8 | Codespaces 무료 한도 초과 (월 60시간) | 낮 | 낮 | 결제수단 미등록 시 정지만 됨 (과금 없음). 사용 시간 모니터링. |
| R9 | OpenAI API 비용 초과 | 낮 | 중 | TEST_MODE 검증 후에만 전체 실행. gpt-4o-mini 사용으로 비용 최소화 (~$15). |
| R10 | Vercel 무료 대역폭 (100GB) 초과 | 낮 | 중 | 트래픽 모니터링 후 Pro 전환 검토. SSG로 CDN 캐싱 극대화. |

---

## 6. 일정표 (주차별)

```
1주차 ─────────────────────────────────────────────
  DT01~DT05  의사결정 완료
  T01        계정 생성 + API 키 발급 신청
  T02        xlsx 확보 + Storage 업로드
  T03        Secrets 등록
  T04        DB 테이블 + RLS 생성

2주차 ─────────────────────────────────────────────
  T05        폴더 구조 + 유틸리티
  T06        step1 코드 작성
  T07        step1 워크플로우
  T08        step1 TEST_MODE 검증
  T09        step2 코드 작성
  T10        step2 TEST_MODE 검증 (API 키 승인 필요)
  T11        step2 워크플로우
  T12        step3 코드 작성
  T13-a      step3 TEST_MODE 검증
  T13-b      step3 워크플로우
  T13-c      전체 파이프라인 실행 (백그라운드, 6~8시간)

3주차 ─────────────────────────────────────────────
  T14        Next.js 초기 설정
  T15        메인 페이지
  T16        상세 페이지
  T17        자부담금 계산기
  T18        Rate Limiting
  T19        SEO 메타 + sitemap

4주차 전반 ─────────────────────────────────────────
  T20        Vercel 배포
  T21        Deploy Hook
  T22        스케줄 워크플로우 완성
  T23        도메인 연결 (선택)

4주차 후반 ─────────────────────────────────────────
  T24        Search Console 등록
  T25        최종 검증 체크리스트
  T26        모니터링 + 수익화 준비
```

---

## 7. 체크리스트

### 의사결정
- [ ] DT01: 평가등급 데이터 확보 방안 결정
- [ ] DT02: 시설 사진 확보 방안 결정
- [ ] DT03: xlsx 갱신 주기 및 담당자 결정
- [ ] DT04: 도메인 구매 여부 결정
- [ ] DT05: 월간 운영 비용 상한선 합의

### M1: 인프라 세팅
- [ ] T01: 외부 계정 생성
- [ ] T02: xlsx 파일 확보 및 Storage 업로드
- [ ] T03: GitHub Secrets 및 Codespaces Secrets 등록
- [ ] T04: Supabase DB 테이블 생성 및 RLS 설정

### M2: 데이터 파이프라인
- [ ] T05: 프로젝트 폴더 구조 및 유틸리티 파일 생성
- [ ] T06: step1_load_xlsx.py 작성
- [ ] T07: step1 GitHub Actions 워크플로우 작성
- [ ] T08: step1 TEST_MODE 검증 (100건)
- [ ] T09: step2_fetch_api.py 작성
- [ ] T10: step2 TEST_MODE 검증 (5건)
- [ ] T11: step2 GitHub Actions 워크플로우 작성
- [ ] T12: step3_generate_seo.py 작성
- [ ] T13-a: step3 TEST_MODE 검증 (3건)
- [ ] T13-b: step3 GitHub Actions 워크플로우 작성
- [ ] T13-c: 전체 파이프라인 실행 (승인 후)

### M3: 프론트엔드
- [ ] T14: Next.js 15 프로젝트 초기 설정
- [ ] T15: 메인 페이지 구현
- [ ] T16: 상세 페이지 구현
- [ ] T17: 자부담금 계산기 구현
- [ ] T18: Rate Limiting 미들웨어 구현
- [ ] T19: SEO 메타데이터 및 sitemap.xml 생성

### M4: 배포 및 자동화
- [ ] T20: Vercel 배포
- [ ] T21: Vercel Deploy Hook 생성
- [ ] T22: GitHub Actions 스케줄 워크플로우 완성
- [ ] T23: 도메인 연결 (선택)

### M5: 런칭 후 검증
- [ ] T24: Google Search Console 등록
- [ ] T25: 최종 검증 체크리스트 실행
- [ ] T26: 모니터링 및 수익화 준비
