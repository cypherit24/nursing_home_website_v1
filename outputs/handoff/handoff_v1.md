# handoff.md
### 전국 요양원 SEO 자동화 시스템 — 프로젝트 인수인계 문서
> 마지막 업데이트: 2026년 3월 30일

---

## 계획

### Template

**서비스 개요**
전국 장기요양기관(요양원) 약 2만 곳의 공공데이터를 자동 수집하고,
AI가 기관별 SEO 소개글을 자동 생성해 정적 웹페이지로 배포하는
완전 자동화 콘텐츠 수익화 시스템.

**수익화 전략**
- 검색 트래픽 → 광고 수익 (애드센스 계열)
- 요양원 측 유료 상세 노출 / 프리미엄 배지
- 자부담금 계산기 → 상담 연결 리드 수익

**핵심 차별화 지표**
- 요양보호사 1인당 담당 어르신 수 (인력 충분성 지표)
- 현재 입소 가능 여부 실시간 뱃지
- 등급별 월 자부담금 실시간 계산기
- AI 생성 감성 소개글 (기관별 고유 콘텐츠)

---

### Competitor

**경쟁 서비스 분석**
- 국민건강보험공단 노인장기요양보험 포털 (longtermcare.or.kr)
  - 공식 데이터 보유, UX 구식, SEO 취약, 계산기 없음
- 네이버 지식iN / 블로그
  - 단편 정보만 존재, 체계적 비교 불가
- 민간 요양원 중개 플랫폼 (케어닥, 실버홈 등)
  - 가입 기관 중심, 전국 2만 곳 전수 데이터 없음

**우리 서비스의 우위**
- 전국 2만 곳 전수 데이터 (공공데이터, 최신 자동 갱신)
- 기관별 독립 URL → 구글 색인 2만 페이지
- 실제 비급여 비용 기반 계산기 (타 서비스 없음)
- 인력 현황 수치 공개 (요양보호사 수, 간호사 수)

---

### Coding Technology

#### 전체 아키텍처 개요
```
[공공데이터]
기관목록.xlsx ──→ Supabase Storage 보관
                         ↓
[파이프라인 - GitHub Actions]
step1: xlsx 파싱 → DB 기본정보 적재
step2: B550928 API 비동기 호출 → 상세정보 수집
step3: OpenAI gpt-4o-mini → SEO 소개글 생성
                         ↓
[Supabase - nursing_homes 테이블]
RLS: anon=읽기만 / service_role=모두
                         ↓
[프론트엔드 - Vercel]
Next.js 15 SSG + ISR(30일)
Server Components (DB 쿼리 서버에서만)
Vercel KV Rate Limiting (60회/분)
                         ↓
[방문자 브라우저]
순수 HTML 수신 (키/쿼리 노출 없음)
```

#### 개발 환경 (PC방 대응 완전 클라우드 구조)
- **코드 작성**: GitHub Codespaces (브라우저 VS Code)
  - Python 3.11 + Node.js 20 자동 설치 (.devcontainer/devcontainer.json)
  - API 키는 Codespaces Secrets에서 자동 주입 (.env 파일 불필요)
- **전체 실행**: GitHub Actions (PC 꺼도 계속 실행)
- **프론트 확인**: Vercel Preview URL (로컬 서버 불필요)
- **파일 보관**: Supabase Storage (xlsx 클라우드 보관)

#### 데이터 수집 구조

**공공데이터 출처 2종**
| 데이터 | 출처 | 방식 |
|---|---|---|
| 기관코드 + 기본정보 | 공공데이터포털 파일 다운로드 | xlsx 수동 다운로드 후 Storage 업로드 |
| 상세정보 9종 | B550928 API (국민건강보험공단) | 기관코드 입력 → XML 응답 |

**B550928 API 핵심 특성**
- 응답 형식: XML 전용 (JSON 불가) → xmltodict 파싱 필수
- 호출 방식: 목록 조회 불가, 기관코드 1건 입력 → 1건 반환
- 초당 한도: 30tps → Semaphore(10)으로 안전하게 제한
- 평가등급: **API 제공 불가** (명시적 제공 불가 항목)
- 사진 정보: **API 제공 불가** (명시적 제공 불가 항목)

**호출 오퍼레이션 5개 (기관당 순차 호출)**
| 번호 | 오퍼레이션명 | 수집 데이터 | DB 컬럼 |
|---|---|---|---|
| OP1 | getGeneralSttusDetailInfoItem02 | 기관유형코드, 전화번호 | admin_pttn_cd, phone |
| OP2 | getAceptncNmprDetailInfoItem02 | 정원, 현원, 대기인원 | capacity, current_occupancy, waiting_count |
| OP3 | getNonBenefitSttusDetailInfoList02 | 식재료비(1), 간식비(5), 1인실(2), 2인실(6) | meal_cost_per_day, room_cost_1/2_person |
| OP4 | getStaffSttusDetailInfoItem02 | 요양보호사1급, 간호사+간호조무사, 물리치료사 | caregiver_count, nurse_count, physical_therapist |
| OP5 | getInsttEtcDetailInfoItem02 | 홈페이지, 교통편, 주차 | homepage_url, traffic_info, parking_info |

**비급여 데이터 전처리 주의사항**
- nonpayKind 코드 1(식재료비) + 5(간식비) 합산 → meal_cost_per_day
- nonpayTgtAmt 단위 불명확 (일별/월별 혼재 가능) → 면책 고지 필수
- item이 단건이면 dict, 복수이면 list → 분기 처리 필수

**전화번호 조합**
- API 응답: locTelNo1(지역번호) + locTelNo2(국번) + locTelNo3(번호)
- DB 저장: f"{v1}-{v2}-{v3}" 형태로 합산

#### DB 설계 (Supabase)

```sql
-- 핵심 컬럼 요약
nursing_homes 테이블:
  facility_code TEXT UNIQUE NOT NULL  -- 11자리 기관코드 (PK 역할)
  admin_pttn_cd TEXT                  -- 기관유형코드 (API 호출 필수값)
  name, sido, sigungu, address        -- 기본 위치 정보
  capacity, current_occupancy         -- 정원/현원 (빈자리 계산)
  waiting_count                       -- 대기인원
  meal_cost_per_day                   -- 일일 식대 (계산기)
  room_cost_1_person                  -- 1인실 추가비용 (계산기)
  room_cost_2_person                  -- 2인실 추가비용 (계산기)
  caregiver_count, nurse_count        -- 인력 지표
  detail_fetched_at                   -- API 수집 완료 여부 판단
  seo_title, seo_content              -- AI 생성 콘텐츠
  seo_generated_at                    -- SEO 글 완료 여부 판단
```

#### xlsx 파일 컬럼 매핑 (확인 완료)
```
A열: 장기요양기관코드 → facility_code (dtype=str 필수, 앞자리 0 보호)
B열: 장기요양기관이름 → name
C열: 우편번호 → postal_code
G열: 시도 시군구 법정동명 → split(" ")[0]=sido, split(" ")[1]=sigungu
H열: 지정일자 (YYYYMMDD) → designated_at
I열: 설치신고일자 (YYYYMMDD) → established_at
J열: 기관별 상세주소 → address
```

#### 파이프라인 재실행 안전 장치
- step1: facility_code UNIQUE + upsert → 중복 실행 안전
- step2: detail_fetched_at IS NULL 조건 → 완료된 것 자동 제외
- step3: seo_generated_at IS NULL 조건 → 완료된 것 자동 제외, 중복 AI 비용 없음

#### AI SEO 글 생성 설정
```
model: gpt-4o-mini
max_tokens: 1500
temperature: 0.7
동시 처리: Semaphore(20)
비용 예상: 2만 건 기준 $10~15
출력 형식: 순수 HTML (h1·h2·p·ul·li)
보안 정화: nh3 라이브러리 (bleach 대체재, 2023년 bleach 유지보수 중단)
재시도: 429 오류 시 10초→30초→90초 지수 백오프
```

#### 프론트엔드 설계
```
프레임워크: Next.js 15 (App Router)
스타일링: Tailwind CSS
DB 연동: @supabase/supabase-js (ANON KEY만 사용)

메인 페이지 (/):
  - Server Component (DB 쿼리 서버에서만)
  - 지역 필터 (시도/시군구 드롭다운)
  - 카드: 기관명·주소·정원/현원·빈자리뱃지·요양보호사수
  - 20건 페이지네이션

상세 페이지 (/[facility_code]):
  - Server Component
  - generateStaticParams: 1000건씩 전체 수집 (메모리 초과 방지)
  - revalidate: 2592000 (30일 ISR)
  - 현황 카드 3개: 입소현황·인력현황·요양보호사 지표
  - dangerouslySetInnerHTML로 AI HTML 렌더링
  - CostCalculator 클라이언트 컴포넌트 삽입

자부담금 계산기 (CostCalculator.tsx):
  - "use client" 클라이언트 컴포넌트
  - Props: mealCostPerDay, roomCost1Person, roomCost2Person, capacity
  - 2025년 등급별 본인부담: 1등급 655,000 / 2등급 607,000 / 3~5등급 524,000
  - 이용일수 슬라이더 (15~31일)
  - 병실유형 토글 (다인실/2인실/1인실, 비용 0이면 비활성화)
  - transition 애니메이션 + 면책 고지
```

#### Rate Limiting (Vercel KV 필수)
```
미들웨어: src/middleware.ts
저장소: Vercel KV (메모리 Map 사용 불가 — 서버리스 환경 특성)
정책: 1분 60회 초과 시 429 반환
봇 예외: Googlebot·Bingbot·Yandexbot·DuckDuckBot
KV 장애 시: 차단 없이 정상 통과 (서비스 무중단 우선)
```

#### GitHub Actions 자동화 스케줄
```
매월 1일  → GitHub Issue 자동 생성 (xlsx 갱신 확인 알림)
매월 3일  → scheduled_step2.yml (API 수집, 5 Job 병렬, timeout 300분)
매월 5일  → scheduled_step3.yml (SEO 생성, 5 Job 병렬, timeout 300분)
매월 6일  → redeploy_vercel.yml (Deploy Hook 호출 → 재빌드)

수동 트리거 (workflow_dispatch):
  manual_step1.yml: xlsx 적재 (confirm=yes 입력 필요)
  manual_step2.yml: API 수집 (test_mode 선택)
  manual_step3.yml: SEO 생성 (test_mode 선택)
```

#### GitHub Secrets 등록 목록 (총 5개)
```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
PUBLIC_DATA_API_KEY
OPENAI_API_KEY
VERCEL_DEPLOY_HOOK_URL
```
- Repository Secrets: GitHub Actions 실행용
- Codespaces Secrets: 터미널 직접 실행용 (별도 등록 필요)

---

## 막힌 점

### 🔴 [해결됨] 원본 로드맵의 구조적 오류들
아래 문제들은 분석 과정에서 발견되어 이미 수정 완료됨.

1. **B550928 API가 목록 조회 API가 아님**
   - 기관코드 입력 → 단건 반환 구조
   - 해결: 공공데이터포털에서 xlsx 파일 별도 확보 → 기관코드 추출

2. **응답 형식이 JSON이 아닌 XML 전용**
   - 해결: xmltodict 라이브러리 추가

3. **bleach 라이브러리 2023년 유지보수 중단**
   - 해결: nh3 라이브러리로 교체

4. **supabase-py의 완전한 async 미지원**
   - 해결: run_in_executor(threadpool)로 우회

5. **Vercel 서버리스에서 메모리 Map 기반 Rate Limiting 작동 불가**
   - 해결: Vercel KV (Redis 호환) 사용

6. **GitHub Actions 무료 플랜 6시간 제한**
   - 2만 건 AI 글쓰기를 단일 Job으로 실행 시 초과
   - 해결: matrix 전략으로 5개 Job 병렬 분할 (각 4000건)

7. **generateStaticParams로 2만 건 한 번에 로드 시 메모리 초과**
   - 해결: 1000건씩 페이지네이션하며 전체 수집

### 🔴 [미해결] 평가등급 데이터 확보 불가
- B550928 API 공식 문서에 **"평가정보 제공 불가"** 명시
- 현재 DB에 grade 컬럼 없음 (로드맵에서 완전 제거)
- 별도 방안이 필요함 (아래 합의 필요 항목 참고)

### 🔴 [미해결] 시설 사진 데이터 확보 불가
- B550928 API 공식 문서에 **"사진정보 제공 불가"** 명시
- 카드 및 상세 페이지에 이미지 없음
- 텍스트 중심 디자인으로 현재 설계됨

### 🟡 [주의] adminPttnCd 미포함 문제
- 기관목록.xlsx에 기관유형코드(adminPttnCd)가 없음
- B550928 API 호출 시 필수 파라미터
- 해결 방안: OP1(getGeneralSttusDetailInfoItem02)을 파라미터 없이 먼저 호출
  → 응답에서 adminPttnCd 추출 후 이후 호출에 사용
  → 실패 시 A03→A01→A04→B03→C06 순서로 폴백

### 🟡 [주의] 비급여 금액 단위 불명확
- nonpayTgtAmt가 일별/월별 단위 혼재 가능성 있음
- prodBase(산출근거) 텍스트 파싱으로 역산해야 하나 불안정
- 현재: 금액을 그대로 저장 + 계산기에 면책 고지 강화로 처리

### 🟡 [주의] Codespaces 무료 한도
- 월 120 코어시간 (2코어 기준 60시간)
- 초과 시 시간당 $0.18 과금 또는 자동 정지
- 결제수단 미등록 시 한도 초과하면 정지만 되고 과금 없음
- 일반적인 개발 패턴에서는 초과하지 않음

### 🟡 [주의] PC방 환경 인터넷 의존성 100%
- 인터넷 끊기면 Codespaces 작업 완전 불가
- 느린 네트워크에서 Codespaces 타이핑 반응 지연 가능
- 안정적인 네트워크 환경 필수

---

## 합의가 필요한 점

### 1. 평가등급 데이터 확보 방안 결정 필요
현재 API로는 완전히 불가능. 아래 3가지 방안 중 하나를 선택해야 함.

| 방안 | 방법 | 난이도 | 비용 |
|---|---|---|---|
| A | 건강보험공단 포털에서 평가등급 데이터 별도 파일 다운로드 | 낮음 | 없음 |
| B | 장기요양기관 평가 결과 공개 데이터셋 활용 (data.go.kr 검색) | 낮음 | 없음 |
| C | 평가등급 없이 서비스 런칭 후 추후 추가 | 없음 | 없음 |

> 추천: C안으로 먼저 런칭 후 A안 병행 추진

### 2. 시설 사진 확보 방안 결정 필요
| 방안 | 방법 | 난이도 | 비용 |
|---|---|---|---|
| A | 각 기관 홈페이지 URL(homepage_url) 링크로 대체 | 없음 | 없음 |
| B | 시설 측이 직접 사진을 등록하는 관리자 페이지 개발 | 높음 | 개발 비용 |
| C | 지역 대표 이미지(카카오맵 API 정적 지도)로 대체 | 중간 | API 비용 |

> 추천: A안으로 먼저 런칭

### 3. xlsx 파일 갱신 주기 및 담당 결정 필요
- 공공데이터포털 파일은 자동 다운로드 API 없음
- 매월 1일 GitHub Issue로 알림 발송되나, 사람이 수동으로 다운로드 후 Storage에 업로드해야 함
- **누가, 얼마나 자주 갱신할 것인지** 결정 필요

| 항목 | 내용 |
|---|---|
| 갱신 주기 | 공공데이터 업데이트 주기 확인 필요 (추정: 분기 또는 반기) |
| 담당자 | 프로젝트 운영자 직접 수행 |
| 소요 시간 | 약 10분 (다운로드 → 파일명 변경 → Storage 업로드) |

### 4. 도메인 구매 여부 결정 필요
- 현재: Vercel 무료 도메인 (xxx.vercel.app)
- SEO 효과를 높이려면 .com 또는 .co.kr 도메인 구매 권장
- 도메인 구매 시: Vercel 프로젝트 설정에서 연결, NEXT_PUBLIC_SITE_URL 업데이트

### 5. 운영 비용 상한선 합의 필요
현재 예상 월간 비용 구조:

| 항목 | 비용 | 비고 |
|---|---|---|
| Supabase | 무료 | 500MB DB, 1GB Storage 이내 |
| GitHub Actions | 무료 | 월 2000분 이내 |
| Vercel | 무료 | 월 100GB 대역폭 이내 |
| Vercel KV | 무료 | 30MB 이내 |
| GitHub Codespaces | 무료 | 월 60시간 이내 |
| OpenAI API | 월 $0 (초기 구축 후) | 신규 기관만 발생, 갱신 시 건당 비용 |
| 도메인 | 연 $10~20 | 구매 시 |
| **합계** | **거의 무료** | 트래픽 폭증 시 Vercel Pro 전환 고려 |

---

## 다음 단계

### 즉시 실행 가능 (오늘)

- [ ] **0단계 실행**: GitHub·Supabase·OpenAI·Vercel 계정 생성
- [ ] **API 키 발급**: 공공데이터포털 B550928 Decoding 키 발급 신청
  (승인까지 1~2일 소요될 수 있음)
- [ ] **xlsx 파일 확보**: 공공데이터포털에서 장기요양기관 현황 파일 다운로드
- [ ] **Supabase Storage 업로드**: 기관목록.xlsx → pipeline-data 버킷
- [ ] **GitHub Secrets 등록**: 5개 키 등록
- [ ] **Codespaces Secrets 등록**: 4개 키 등록

### 단기 (API 키 승인 후, 약 2~3일)

- [ ] **1단계**: Supabase 테이블 생성 SQL 실행 및 RLS 확인
- [ ] **2단계**: 프로젝트 폴더 구조 및 유틸리티 파일 생성
- [ ] **3단계**: step1_load_xlsx.py 작성 + TEST_MODE=true로 100건 테스트
- [ ] **4단계**: step2_fetch_api.py 작성 + TEST_MODE=true로 5건 테스트
  → adminPttnCd 폴백 로직 정상 작동 여부 확인 필수
- [ ] **5단계**: step3_generate_seo.py 작성 + TEST_MODE=true로 3건 테스트
  → 생성된 HTML 품질 육안 확인 필수

### 중기 (파이프라인 검증 후)

- [ ] **GitHub Actions manual 트리거로 전체 데이터 실행**
  - step1 전체 (30분, PC 켜놔야 함)
  - step2 전체 (2~3시간, PC 꺼도 됨)
  - step3 전체 (3~4시간, PC 꺼도 됨, 약 $15 비용 발생)
- [ ] **6~8단계**: Next.js 프론트엔드 + 계산기 + Rate Limiting 구축
- [ ] **9단계**: Vercel 배포 + Deploy Hook 생성 + Actions 스케줄 완성

### 장기 (런칭 후)

- [ ] **Google Search Console 등록** → sitemap.xml 제출 → 색인 요청
- [ ] **평가등급 데이터 추가** (합의된 방안으로)
- [ ] **트래픽 모니터링** → Vercel Analytics 활성화
- [ ] **애드센스 신청** → 월간 페이지뷰 기준 수익화 시작
- [ ] **매월 정기 점검**:
  - xlsx 파일 최신 버전 확인 및 교체
  - GitHub Actions 실행 결과 확인
  - OpenAI 크레딧 잔액 확인

---

## 부록: 프롬프트 실행 순서 요약

| 순서 | 프롬프트 | 실행 위치 | 예상 시간 |
|---|---|---|---|
| 0-A | devcontainer + gitignore + README | Codespaces | 30분 |
| 1 | DB 테이블 + RLS + 인덱스 SQL | Supabase SQL Editor | 30분 |
| 2 | 폴더 구조 + utils 파일들 | Codespaces | 30분 |
| 3 | step1_load_xlsx.py + manual_step1.yml | Codespaces | 1시간 |
| 4 | step2_fetch_api.py + 워크플로우 2개 | Codespaces | 2시간 |
| 5 | step3_generate_seo.py + 워크플로우 2개 | Codespaces | 1시간 |
| 6 | Next.js 프로젝트 + 4개 파일 | Codespaces | 2~3시간 |
| 7 | CostCalculator.tsx | Codespaces | 1시간 |
| 8 | Vercel KV + middleware.ts | Codespaces | 30분 |
| 9 | 배포 가이드 + 스케줄 워크플로우 | Codespaces + 브라우저 | 1시간 |
| 10 | 최종 검증 체크리스트 15개 | 브라우저 | 1시간 |
| **합계** | | | **약 12~15시간** |

> 모든 프롬프트 원문은 '코딩 지시사항 상세 확장 로드맵 v2' 문서에 수록되어 있음.
