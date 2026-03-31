# 전국 요양원 SEO 자동화 시스템 — 실행 계획서 v3

---

## 변경 이력

### v3 변경 (plan-v2 대비)

> 변경일: 2026-03-31 | plan-v2-to-v3-review.md 기반 | 판정: 승인

#### 핵심 변경: SEO 콘텐츠 저장 형식 HTML → 구조화된 JSON

**변경 동기**: plan-v2에서 AI가 생성한 SEO 콘텐츠를 HTML로 저장하면, 프론트엔드 디자인/레이아웃 변경 시마다 2만 건을 AI로 재생성해야 한다 (~$12 + 수시간 + GitHub Actions 한도 72% 소진). JSON으로 전환하면 콘텐츠(재료)와 표현(템플릿)이 분리되어 프론트엔드 변경 시 재생성 없이 배포만으로 해결된다.

| 구분 | 변경 내용 | 근거 |
|---|---|---|
| 저장 형식 | seo_content: HTML TEXT → **구조화 JSON (JSONB)** | 콘텐츠/표현 분리, 유지보수 비용 구조적 절감 |
| AI 출력 | 순수 HTML → **6필드 JSON 스키마** | 필드별 정밀 품질 검증 가능 |
| 보안 모델 | 4단계 XSS 방어 → **1단계 (CSP only)** | dangerouslySetInnerHTML 제거로 공격 표면 자체 소멸 |
| Python 의존성 | nh3 제거, **jsonschema 추가** | HTML 정화 불필요, JSON 스키마 검증 필요 |
| Frontend 의존성 | **sanitize-html 제거** | 템플릿 컴포넌트가 React JSX 자동 이스케이핑 사용 |
| 렌더링 | dangerouslySetInnerHTML → **SeoContent 템플릿 컴포넌트** | XSS 원천 차단 |
| 신규 리스크 | R15(JSON 파싱 실패), R16(스키마 마이그레이션), R17(구조 제약 위반) | JSON 전환에 따른 신규 리스크 |

#### 변경 태스크 목록

| 태스크 | 변경 요약 |
|---|---|
| T04 | seo_content 컬럼 TEXT → JSONB |
| T05 | requirements.txt: nh3 제거, jsonschema 추가. seo_content_schema.json 추가 |
| T12 | AI 출력 JSON. nh3/regex 제거 → json.loads + jsonschema + 필드별 품질 검증 |
| T13-a | HTML 품질 확인 → JSON 구조/필드 품질 확인 |
| T13-c | 정합성 SQL JSONB 호환으로 수정 |
| T13-d | Python 스크립트로 JSON→HTML 간이 렌더링 추가 명시 |
| T14 | sanitize-html 제거. SeoContentJson TS 타입 추가. ESLint dangerouslySetInnerHTML 금지 규칙 추가 |
| T16 | dangerouslySetInnerHTML → SeoContent 템플릿 컴포넌트 |
| T25 | 검증 체크리스트 항목 조정 |

#### 변경하지 않은 태스크

T01~T03, T04-b, T06~T11, T13-b, T15, T17~T24, T26 — seo_content와 무관하거나 영향 없음

### v2 변경 (plan-v1 대비)

> 검증일: 2026-03-30 | plan-v1-review.md 기반 | 판정: 조건부 승인 → 3개 조건 모두 해결

| 구분 | 변경 내용 | 근거 |
|---|---|---|
| 일정 | 4주 → 6주 (2주 버퍼) | P7 |
| 아키텍처 | SSG 2만건 → SSG 1,000건 + ISR 19,000건 하이브리드 | P3, S3, C4 |
| 파이프라인 | Semaphore(10)→5, 지수 백오프, 4일 분할 실행 | P1 |
| 비용 KPI | "$0" → "$0 (트래픽 월 10만 PV 이하 기준)" | C3 |
| 보안 | XSS 이중 방어 (nh3 + sanitize-html + CSP 헤더) | P6 |
| 법적 준수 | 개인정보 비표시, 면책 고지, 삭제 요청 프로세스 | N2 |
| 품질 관리 | SEO 자동 품질 검증 + 100건 파일럿 배포 | N4, S1 |
| 에러 복구 | 원자적 업데이트, pipeline_errors 테이블, 정합성 검증 | N1, N5 |
| 테스트 | 각 step에 pytest/vitest 단위 테스트 명시 | N8 |
| 접근성 | 기본 폰트 18px, WCAG AA 색상대비, 시맨틱 HTML | N3 |
| 신규 태스크 | T04-b(pipeline_errors 테이블), T13-d(파일럿 배포) | S1, N1 |
| 선행조건 수정 | T05: T04→T01, T15: T14+T13-c→T14만 | C2, C5 |
| 체크리스트 | DT01, DT02, DT04 → [x] 완료 표시 | C1 |
| 롤백 계획 | Vercel/DB/Git 각각 명시 (신규 섹션) | N7 |

---

## 1. 프로젝트 개요

**한 줄 목표**: 전국 요양원 2만 곳의 공공데이터를 자동 수집·AI 소개글 생성·정적 웹페이지 배포하여 검색 트래픽 기반 수익화 시스템을 구축한다.

**핵심 성공 지표 (KPI)**

| # | 지표 | 목표 |
|---|---|---|
| 1 | 구글 색인 페이지 수 | 20,000페이지 이상 |
| 2 | 파이프라인 자동화율 | xlsx 업로드 외 100% 자동 |
| 3 | 월간 운영 비용 | $0 (트래픽 월 10만 PV 이하 기준) |

**전체 예상 기간**: 6주 (주 15~20시간 기준, 2주 버퍼 포함)

### 비용 총괄

**1회성 비용**

| 항목 | 금액 | 비고 |
|---|---|---|
| OpenAI gpt-4o-mini SEO 생성 (2만 건) | ~$11.10 | 입력 $1.50 + 출력 $9.60 |
| 품질 검증 실패 재생성 (5%) | ~$0.50 | 1,000건 재생성 가정 |
| JSON 스키마 미준수 재생성 (5%) | ~$0.50 | 1,000건 재생성 가정 |
| TEST_MODE 테스트 비용 | ~$0.05 | 소량 테스트 |
| **1회성 합계** | **~$12.15** | |

> 비용 산출 근거: gpt-4o-mini 입력 $0.15/1M tokens, 출력 $0.60/1M tokens. 건당 평균 입력 ~500 tokens, 출력 ~800 tokens. 총 입력 10M tokens × $0.15 = $1.50, 총 출력 16M tokens × $0.60 = $9.60. JSON 스키마 미준수 재시도 5% 추가.

**월간 운영 비용 (단계별)**

| 단계 | 월 PV | Vercel | Supabase | 기타 | 월 합계 |
|---|---|---|---|---|---|
| 초기 (0~6개월) | < 10만 | $0 (Hobby) | $0 (Free) | $0 | **$0/월** |
| 성장기 (6~12개월) | 10만~50만 | $20 (Pro) | $0 (Free) | $0 | **$20/월** |
| 확장기 (12개월~) | 50만+ | $20 (Pro) | $25 (Pro) | 도메인 ~$1.5/월 | **$46.50/월** |

**선택적 비용**

| 항목 | 금액 | 조건 |
|---|---|---|
| 커스텀 도메인 (.com) | ~$12/년 | DT04에서 무료 도메인 확정이므로 초기 불필요 |
| 커스텀 도메인 (.co.kr) | ~$15,000원/년 | 한국 도메인 선택 시 |
| Vercel Pro 업그레이드 | $20/월 | 대역폭 100GB 초과 시 |
| Supabase Pro 업그레이드 | $25/월 | DB 500MB 초과 시 (현재 ~40MB 예상이므로 당분간 불필요) |

---

## 2. 의사결정 선행 항목

코딩 착수 전에 반드시 결정해야 할 사항들:

| ID | 결정 내용 | 옵션 | 추천안 | 상태 |
|---|---|---|---|---|
| DT01 | 평가등급 데이터 확보 방안 | ~~A / B~~ / **C: 등급 없이 런칭** | ✅ **C안 확정** | ✅ 확정 |
| DT02 | 시설 사진 확보 방안 | **A: 홈페이지 링크** | ✅ **A안 확정** (크롤링은 저작권 리스크로 보류) | ✅ 확정 |
| DT03 | xlsx 갱신 주기 및 담당자 | 분기 1회 | **분기 1회** (공공데이터 업데이트 주기 확인 후 조정) | 미정 |
| DT04 | 도메인 구매 여부 | ~~.com / .co.kr~~ / **Vercel 무료 도메인** | ✅ **무료 도메인으로 시작**, 성공 시 이전 | ✅ 확정 |
| DT05 | 월간 운영 비용 상한선 | 무료 유지 / $10 이하 / $30 이하 | **무료 유지** (10만 PV 이하 기준, 초과 시 Vercel Pro $20/월 전환) | 미정 |

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
- 작업 내용: 무료 티어 범위 내 운영 가능 확인. 트래픽 폭증 시 Vercel Pro 전환 기준 합의. 월 10만 PV 이하 $0, 초과 시 $20/월 전환 기준 합의.
- 완료 확인: 결정 내용을 이 문서에 기록
- 예상 소요: 10분
- 비용: 없음

---

## 3. SEO 콘텐츠 JSON 스키마 정의

> v3 신규 섹션. AI 출력 형식과 DB 저장 구조를 정의한다.

### 스키마 (6 필드)

```json
{
  "type": "object",
  "required": ["intro", "highlights", "care_services", "location_info", "facility_info", "summary"],
  "properties": {
    "intro": {
      "type": "string",
      "minLength": 80,
      "maxLength": 500,
      "description": "시설 소개 문단. 반드시 시설명, 시도, 시군구를 포함. 1~2문장."
    },
    "highlights": {
      "type": "array",
      "items": { "type": "string", "minLength": 10, "maxLength": 150 },
      "minItems": 3,
      "maxItems": 6,
      "description": "핵심 특징: 정원, 요양보호사 비율, 전문 프로그램 등."
    },
    "care_services": {
      "type": "string",
      "minLength": 80,
      "maxLength": 500,
      "description": "돌봄 서비스 설명: 요양보호사 수, 간호 인력, 프로그램, 비급여 요약."
    },
    "location_info": {
      "type": "string",
      "minLength": 50,
      "maxLength": 300,
      "description": "위치 및 접근성: 주소 맥락, 주변 환경, 교통편."
    },
    "facility_info": {
      "type": "string",
      "minLength": 80,
      "maxLength": 500,
      "description": "시설 환경: 정원/현원, 병실 유형, 건물 설명."
    },
    "summary": {
      "type": "string",
      "minLength": 50,
      "maxLength": 300,
      "description": "마무리 문단. 따뜻하고 신뢰감 있는 어조."
    }
  },
  "additionalProperties": false
}
```

### 필드 설계 근거

| 필드 | 프론트엔드 매핑 | SEO 가치 | 검증 기준 |
|---|---|---|---|
| intro | `<p>` 리드 문단 | 시설명+지역명 키워드 밀도 | 시설명, 시도 필수 포함 |
| highlights | `<ul><li>` 특징 목록 | 구조화 정보 → Featured Snippet 가능성 | 3~6개 항목 |
| care_services | `<h2>` + `<p>` 섹션 | "[시설명] 돌봄 서비스" 쿼리 대응 | 80자 이상 |
| location_info | `<h2>` + `<p>` 섹션 | "[지역] 요양원" 로컬 SEO | 50자 이상 |
| facility_info | `<h2>` + `<p>` 섹션 | 시설 규모/환경 정보 | 80자 이상 |
| summary | `<p>` 마무리 | 페이지 체류 시간 기여 | 50자 이상 |

### 스키마 관리 원칙

- **스키마 파일 위치**: `src/pipeline/schemas/seo_content_schema.json`
- **TypeScript 타입 위치**: `src/frontend/types/seo-content.ts` (SeoContentJson 인터페이스)
- **동기화 규칙**: 스키마 변경 시 반드시 Python 스키마와 TypeScript 타입을 동시 업데이트
- **부분 재생성**: MVP에서는 전체 JSON 재생성 방식 채택. 필드별 부분 재생성은 향후 최적화 과제

---

## 4. 마일스톤

| # | 마일스톤 | 포함 태스크 | 완료 기준 | 예상 기간 |
|---|---|---|---|---|
| M1 | 인프라 세팅 및 의사결정 | DT01~DT05, T01~T04, T04-b | 계정 생성, Secrets 등록, DB 테이블(nursing_homes + pipeline_errors) 생성 완료 | 1주차 |
| M2 | 데이터 파이프라인 (step1 + step2 착수) | T05~T08, T09 착수 | step1 전체 검증 통과, step2 코드 작성 착수 | 2주차 |
| M3 | 데이터 파이프라인 (step2 완성 + step3 + 전체 실행) | T09 완성~T13-c, T13-d | step2·3 TEST_MODE 검증 통과, 전체 파이프라인 실행 완료, 파일럿 100건 배포 | 3주차 |
| M4 | 프론트엔드 구축 | T14~T19 | Next.js 로컬 프리뷰에서 목록·상세 정상 작동 (T17 계산기, T18 Rate Limiting은 MVP 후 추가 가능) | 4주차 |
| M5 | 배포 및 자동화 | T20~T23 | Vercel 배포 완료, GitHub Actions 스케줄 등록 완료 | 5주차 |
| M6 | 런칭 후 검증 + 버퍼 | T24~T26 | Search Console 등록, 색인 요청, 파일럿 색인 확인, 잔여 이슈 해결 | 6주차 |

---

## 5. 태스크 목록

### 인프라 세팅 태스크

### T01: 외부 계정 생성
- 마일스톤: M1
- 실행 환경: 브라우저
- 선행 조건: 없음
- 작업 내용: GitHub, Supabase, OpenAI, Vercel 계정 생성. 공공데이터포털 B550928 API Decoding 키 발급 신청 (승인 1~2일 소요). **OpenAI 계정에 월 $20 하드리밋 설정** (Settings > Billing > Usage limits).
- 완료 확인: 각 서비스 대시보드 로그인 확인. API 키 발급 신청 완료 확인. OpenAI 하드리밋 설정 확인.
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

### T04: Supabase DB 테이블 생성 및 RLS 설정 ← v3 변경
- 마일스톤: M1
- 실행 환경: Supabase 웹 (SQL Editor)
- 선행 조건: T01
- 작업 내용: nursing_homes 테이블 생성 SQL 실행. **seo_content 컬럼 타입: JSONB** (v2: TEXT). RLS 정책 설정 (anon=읽기만, service_role=모두). facility_code UNIQUE 인덱스 + sido/sigungu 인덱스 생성. **대표자 성명(representative_name) 컬럼 포함하되, 프론트엔드에서 비표시**.
- 완료 확인: Supabase Table Editor에서 nursing_homes 테이블 확인. seo_content 컬럼이 JSONB 타입인지 확인. RLS 정책 활성화 확인. `SELECT count(*) FROM nursing_homes` 실행 시 0 반환.
- 예상 소요: 30분
- 비용: 없음

### T04-b: pipeline_errors 테이블 생성
- 마일스톤: M1
- 실행 환경: Supabase 웹 (SQL Editor)
- 선행 조건: T01
- 작업 내용: pipeline_errors 테이블 생성 (id SERIAL, facility_code TEXT, step TEXT, error_message TEXT, created_at TIMESTAMPTZ DEFAULT NOW()). RLS 정책: service_role=쓰기+읽기, anon=읽기만.
- 완료 확인: Supabase에서 pipeline_errors 테이블 확인. `SELECT count(*) FROM pipeline_errors` 실행 시 0 반환.
- 예상 소요: 15분
- 비용: 없음

---

### 데이터 파이프라인 태스크

### T05: 프로젝트 폴더 구조 및 유틸리티 파일 생성 ← v3 변경
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: **T01** (변경: T04→T01. 폴더 구조 생성에 DB 테이블 불필요)
- 작업 내용: src/ 하위 폴더 구조 생성 (pipeline/, **pipeline/schemas/**, frontend/). 공통 유틸리티 파일 작성 (Supabase 클라이언트, 로깅, 환경변수 로드). Python requirements.txt 작성 (**~~nh3~~(제거)**, xmltodict, openpyxl, pandas, aiohttp, openai, **jsonschema(추가)** 포함). **src/pipeline/schemas/ 디렉토리에 `seo_content_schema.json` 파일 생성** (본 문서 3장의 JSON 스키마 정의 내용).
  - **스키마 동기화 주의**: seo_content_schema.json 변경 시 반드시 프론트엔드 TypeScript 타입(SeoContentJson)도 동시 업데이트할 것.
- 완료 확인: `ls -R src/` 로 폴더 구조 확인. schemas/ 디렉토리에 seo_content_schema.json 존재 확인. `python -c "from src.pipeline.utils import ..."` 에러 없음. `python -c "import jsonschema"` 에러 없음.
- 예상 소요: 35분
- 비용: 없음

### T06: step1_load_xlsx.py 작성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T05
- 작업 내용:
  - Supabase Storage에서 xlsx 다운로드 → pandas로 파싱 → nursing_homes 테이블에 upsert
  - facility_code dtype=str 필수 (앞자리 0 보호)
  - **컬럼 매핑: 헤더명 기반** (인덱스 A,B,G 대신)
    ```python
    COLUMN_MAP = {
        "장기요양기관기호": "facility_code",
        "기관명": "name",
        "시도": "sido",
        "시군구": "sigungu",
        # ...
    }
    df = df.rename(columns=COLUMN_MAP)
    ```
  - **필수 컬럼 검증**: 파싱 시작 전 REQUIRED 컬럼 존재 확인, 누락 시 ValueError
    ```python
    REQUIRED = ["장기요양기관기호", "기관명", "시도", "시군구"]
    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")
    ```
  - **변경 감지**: 기존 컬럼 목록과 비교, 차이 있으면 GitHub Issue 자동 생성
  - **데이터 정합성 검증**: step1 완료 후 NULL 비율 검증 쿼리 실행, 임계치 미달 시 실패
    ```sql
    SELECT count(*) as total,
      count(CASE WHEN facility_code IS NULL THEN 1 END) as null_code,
      count(CASE WHEN name IS NULL THEN 1 END) as null_name,
      count(CASE WHEN sido IS NULL THEN 1 END) as null_sido
    FROM nursing_homes;
    ```
- 완료 확인: 코드 린트 통과. **pytest 단위 테스트 통과**: 컬럼 매핑, dtype 보존, 빈 행 처리, 필수 컬럼 누락 시 에러 테스트.
- 예상 소요: 1.5시간 (테스트 포함)
- 비용: 없음

### T07: step1 GitHub Actions 워크플로우 작성
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T06
- 작업 내용: `.github/workflows/manual_step1.yml` 작성. workflow_dispatch 트리거 + confirm=yes 입력 필수. Python 환경 설정 + requirements 설치 + step1 실행. **정합성 검증 쿼리 결과를 로그에 출력**.
- 완료 확인: GitHub Actions 탭에서 워크플로우 표시 확인 (실행은 T02 이후)
- 예상 소요: 30분
- 비용: 없음

### T08: step1 TEST_MODE 검증 (100건)
- 마일스톤: M2
- 실행 환경: Codespaces
- 선행 조건: T06, T02, T03
- 작업 내용: TEST_MODE=true로 100건만 적재 테스트. facility_code 중복 실행 안전성 확인 (2회 연속 실행 → 건수 변화 없음). **필수 컬럼 검증 + 정합성 검증 정상 작동 확인**.
- 완료 확인: Supabase에서 100건 확인. 재실행 시 건수 동일. 정합성 검증 로그 정상.
- 예상 소요: 30분
- 비용: 없음

### T09: step2_fetch_api.py 작성
- 마일스톤: **M2 착수 → M3 완성**
- 실행 환경: Codespaces
- 선행 조건: T05
- 작업 내용:
  - detail_fetched_at IS NULL인 기관 조회 → B550928 API 5개 오퍼레이션 비동기 호출
  - **Semaphore(5)** (보수적 조정, 10→5)
  - **지수 백오프**: 429/503 응답 시 5초→15초→45초→135초
  - **일일 제한 자동 중단**: 일일 제한 도달 시 자동 중단 + 다음날 이어서 실행 (IS NULL 조건 활용)
  - **4일 분할 실행**: 일 5,000건 처리, GitHub Actions에서 offset 파라미터로 제어
  - XML 응답 xmltodict 파싱. adminPttnCd 폴백 로직 구현 (OP1 먼저 → 실패 시 A03→A01→A04→B03→C06 순)
  - 전화번호 조합, 비급여 전처리 포함
  - **원자적 업데이트**: API 5개 OP 모두 성공 시에만 detail_fetched_at 업데이트. 부분 실패 시 해당 행은 NULL 유지
  - **오류 로깅**: 실패 건은 pipeline_errors 테이블에 facility_code + step='step2' + error_message 기록
  - **API 응답 스키마 저장**: 최초 성공 응답의 XML 구조를 src/pipeline/schemas/에 레퍼런스로 저장
  - **구조 변경 감지**: 응답 키 목록을 레퍼런스와 비교 → 차이 발견 시 경고 로그 + GitHub Issue 자동 생성
  - **데이터 정합성 검증**: step2 완료 후 fetched/null 비율 검증
    ```sql
    SELECT count(*) as total,
      count(CASE WHEN detail_fetched_at IS NOT NULL THEN 1 END) as fetched,
      count(CASE WHEN capacity IS NULL AND detail_fetched_at IS NOT NULL THEN 1 END) as fetched_but_no_capacity
    FROM nursing_homes;
    ```
  - **95% 이상 성공 시 정상 완료 판정**
- 완료 확인: 코드 린트 통과. **pytest 단위 테스트 통과**: 정상 응답 파싱, 빈 응답 처리, 에러 응답 처리 (mock 기반).
- 예상 소요: 3시간 (테스트 포함, 복잡도 증가 반영)
- 비용: 없음

### T10: step2 TEST_MODE 검증 (5건)
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T09, T08, T03 (API 키 승인 필수)
- 작업 내용: TEST_MODE=true로 5건만 API 수집 테스트. adminPttnCd 폴백 로직 정상 작동 확인. 수집 결과 DB 컬럼 값 육안 확인. **원자적 업데이트 정상 작동 확인. pipeline_errors 테이블 기록 확인. 스키마 레퍼런스 파일 생성 확인**.
- 완료 확인: Supabase에서 5건의 detail_fetched_at 값 NOT NULL 확인. capacity, caregiver_count 등 주요 컬럼에 데이터 존재. schemas/ 디렉토리에 레퍼런스 파일 존재.
- 예상 소요: 30분
- 비용: 없음 (API 호출 무료)

### T11: step2 GitHub Actions 워크플로우 작성
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T10
- 작업 내용: `manual_step2.yml` (수동, test_mode + **offset** 선택) + `scheduled_step2.yml` (매월 3일, **4일 분할 실행**, matrix 5 Job 병렬, timeout 300분) 작성. **정합성 검증 쿼리 결과를 로그에 출력. 임계치 미달 시 워크플로우 실패 처리**.
- 완료 확인: GitHub Actions 탭에서 워크플로우 2개 표시 확인.
- 예상 소요: 30분
- 비용: 없음

### T12: step3_generate_seo.py 작성 ← v3 변경
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T05
- 작업 내용:
  - seo_generated_at IS NULL인 기관 조회 → OpenAI gpt-4o-mini로 SEO 소개글 생성 (Semaphore(20))
  - **출력: 구조화된 JSON** (v2: 순수 HTML)
  - **`response_format={"type": "json_object"}`** 사용하여 유효 JSON 출력 보장
  - **프롬프트 설계**:
    - 시설별 고유 데이터(정원, 현원, 인력 수, 비급여 항목) 구체적 수치 포함
    - JSON 스키마 6개 필드(intro, highlights, care_services, location_info, facility_info, summary) 명시
    - 구체적 예시 JSON 포함
    - "각 섹션이 서로 다른 정보를 다루고, 전체적으로 자연스럽게 이어지도록" 지시
  - **JSON 파싱**: `json.loads(response)`. 마크다운 코드 펜스(` ```json ... ``` `) 자동 제거 후 재시도
  - **스키마 검증**: `jsonschema.validate(data, schema)` — 필드 존재, 타입, 문자열 길이, 배열 크기 자동 검증
  - **품질 자동 검증** (필드별 정밀 검증):
    ```python
    def validate_seo_json(data: dict, facility: dict) -> bool:
        # 시설명이 intro에 포함되어야 함
        if facility["name"] not in data["intro"]: return False
        # 지역명이 intro 또는 location_info에 포함되어야 함
        if facility["sido"] not in data["intro"] and facility["sido"] not in data["location_info"]: return False
        # 전체 텍스트 길이 300자 이상
        total_text = data["intro"] + " ".join(data["highlights"]) + data["care_services"] + data["location_info"] + data["facility_info"] + data["summary"]
        if len(total_text) < 300: return False
        # AI 생성 암시 문구 검출
        forbidden = ["AI가 생성한", "자동으로 작성된", "인공지능이"]
        if any(f in total_text for f in forbidden): return False
        return True
    ```
  - **~~nh3 정화~~** (v3 제거): JSON은 순수 텍스트이므로 HTML 정화 불필요
  - **~~정규식 XSS 검증~~** (v3 제거): HTML 태그가 없으므로 script/on*/javascript: 검출 불필요
  - **실패 시 1회 재생성**: 스키마 검증 또는 품질 검증 실패 건은 프롬프트 변형하여 1회 재시도
  - **원자적 업데이트**: JSON 파싱 + 스키마 검증 + 품질 검증 모두 통과 시에만 seo_generated_at 업데이트
  - **오류 로깅**: 실패 건은 pipeline_errors 테이블에 facility_code + step='step3' + error_message 기록
  - **데이터 정합성 검증**: step3 완료 후 생성/미달 비율 검증
    ```sql
    SELECT count(*) as total,
      count(CASE WHEN seo_generated_at IS NOT NULL THEN 1 END) as generated,
      count(CASE WHEN seo_content IS NULL OR seo_content = '{}' THEN 1 END) as empty_json,
      count(CASE WHEN jsonb_array_length(seo_content->'highlights') < 3 THEN 1 END) as too_few_highlights
    FROM nursing_homes
    WHERE seo_generated_at IS NOT NULL;
    ```
  - 429 오류 시 지수 백오프 (10초→30초→90초)
- 완료 확인: 코드 린트 통과. **pytest 단위 테스트 통과**: JSON 파싱 테스트(유효 JSON, 마크다운 펜스 포함 JSON, 잘못된 JSON), 스키마 검증 테스트, 품질 검증 함수 테스트 (mock 기반).
- 예상 소요: 2시간 (테스트 포함)
- 비용: 없음

### T13-a: step3 TEST_MODE 검증 (3건) ← v3 변경
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T12, T10
- 작업 내용: TEST_MODE=true로 3건만 SEO 글 생성 테스트. **생성된 JSON 구조 검증** (6개 필드 존재, highlights 배열 3~6개). 각 필드 내용의 품질 육안 확인 (자연스러움, 시설별 차별화). **jsonschema 검증 통과 확인. 시설별 고유 데이터 반영 확인**.
- 완료 확인: Supabase에서 3건의 seo_content가 유효한 JSONB인지 확인. 각 필드에 의미 있는 텍스트 존재. seo_generated_at NOT NULL. 전체 텍스트 300자 이상. 시설별 차별화 확인.
- 예상 소요: 30분
- 비용: ~$0.01 (3건)

### T13-b: step3 GitHub Actions 워크플로우 작성
- 마일스톤: M3
- 실행 환경: Codespaces
- 선행 조건: T13-a
- 작업 내용: `manual_step3.yml` (수동, test_mode 선택) + `scheduled_step3.yml` (매월 5일, matrix 5 Job 병렬, timeout 300분) 작성. **정합성 검증 쿼리 결과를 로그에 출력**.
- 완료 확인: GitHub Actions 탭에서 워크플로우 2개 표시 확인.
- 예상 소요: 30분
- 비용: 없음

### T13-c: 전체 파이프라인 실행 (step1→step2→step3) ← v3 변경
- 마일스톤: M3
- 실행 환경: GitHub Actions (manual 트리거)
- 선행 조건: T13-a 검증 통과 + **사용자 실행 승인** + **TEST_MODE 실제 토큰 사용량 측정 후 전체 비용 재산정**
- 작업 내용:
  - step1 전체 실행 (약 30분)
  - → step2 전체 실행 (**4일 분할, 일 5,000건**)
  - → step3 전체 실행 (3~4시간, 5 Job 병렬)
  - 각 단계 완료 후 **데이터 정합성 검증 쿼리 자동 실행**
  - **95% 이상 성공 시 정상 완료 판정**
- 완료 확인:
  - `SELECT count(*) FROM nursing_homes WHERE detail_fetched_at IS NOT NULL` >= 19,000 (95%)
  - `SELECT count(*) FROM nursing_homes WHERE seo_generated_at IS NOT NULL` >= 19,000 (95%)
  - **`SELECT count(*) FROM nursing_homes WHERE seo_content IS NOT NULL AND jsonb_typeof(seo_content) = 'object'` >= 19,000** (JSONB 유효성)
  - pipeline_errors 테이블에서 실패 건수 확인
- 예상 소요: step2 4일(자동) + step3 3~4시간(자동)
- 비용: OpenAI API ~$11.10 + 재생성 ~$1.00 (품질+스키마) = **~$12.10**

### T13-d: 파일럿 배포 (100건) ← v3 변경
- 마일스톤: M3
- 실행 환경: Codespaces + Vercel
- 선행 조건: T13-c (100건 이상 SEO 생성 완료)
- 작업 내용:
  - SEO 생성 완료된 100건으로 간이 정적 사이트 배포
  - **Python 스크립트로 JSON→HTML 간이 렌더링** (v3 추가): Jinja2 또는 문자열 포매팅으로 JSON 필드를 간단한 HTML 페이지로 변환. Next.js 프론트엔드(T16)와 독립적으로 동작.
    ```python
    # 간이 렌더링 예시
    html = f"""
    <h1>{facility['name']} 소개</h1>
    <p>{seo['intro']}</p>
    <h2>주요 특징</h2>
    <ul>{''.join(f'<li>{h}</li>' for h in seo['highlights'])}</ul>
    <h2>돌봄 서비스</h2>
    <p>{seo['care_services']}</p>
    """
    ```
  - Google Search Console에 sitemap 제출
  - **2주간 색인 상태 모니터링** (M4 프론트엔드 개발과 병행)
  - 색인 정상 확인 후 전체 확장 승인
  - 색인 거부 시: 프롬프트 개선 → 100건 재생성 → 재배포 → 재확인
- 완료 확인: Search Console에서 100건 중 80% 이상 색인 확인
- 예상 소요: 배포 1시간 + 모니터링 2주 (프론트엔드 개발과 병행)
- 비용: 없음

---

### 프론트엔드 태스크

### T14: Next.js 15 프로젝트 초기 설정 ← v3 변경
- 마일스톤: M4
- 실행 환경: Codespaces
- 선행 조건: T04
- 작업 내용: Next.js 15 App Router 프로젝트 생성. Tailwind CSS 설정. @supabase/supabase-js 설치. **~~sanitize-html 설치~~** (v3 제거: JSON 템플릿 방식으로 불필요). 환경변수 설정 (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY). **SeoContentJson TypeScript 인터페이스 생성** (v3 추가):
  ```typescript
  // src/frontend/types/seo-content.ts
  export interface SeoContentJson {
    intro: string;
    highlights: string[];
    care_services: string;
    location_info: string;
    facility_info: string;
    summary: string;
  }
  ```
  **ESLint `no-dangerously-set-inner-html` 규칙 추가** (v3 추가): `.eslintrc`에 `"react/no-danger": "error"` 설정. 향후 개발자가 실수로 dangerouslySetInnerHTML을 사용하는 것을 방지.
- 완료 확인: `npm run dev` 정상 실행. localhost:3000에서 기본 페이지 표시. ESLint에서 dangerouslySetInnerHTML 사용 시 에러 발생 확인.
- 예상 소요: 50분
- 비용: 없음

### T15: 메인 페이지 (/) 구현
- 마일스톤: M4
- 실행 환경: Codespaces
- 선행 조건: **T14** (변경: T13-c 제거. 개발 시 TEST_MODE 100건 데이터로 충분)
- 작업 내용:
  - Server Component로 구현
  - 시도/시군구 드롭다운 필터
  - 카드 리스트 (기관명·주소·정원/현원·빈자리뱃지·요양보호사수)
  - 20건 페이지네이션
  - **접근성**: 기본 폰트 text-lg(18px), 시맨틱 HTML (`<nav>`, `<main>`, `<article>`, `<footer>`), WCAG AA 색상대비 4.5:1 준수
  - **면책 고지**: 사이트 하단에 "본 사이트는 공공데이터포털의 공공데이터를 활용하며, 공공데이터법에 의거하여 제공됩니다" 문구 게시
  - **대표자 성명 비표시**: DB에서 조회하되 프론트엔드에 렌더링하지 않음. 기관 대표번호만 표시
- 완료 확인: 로컬 프리뷰에서 카드 20건 표시. 시도 필터 변경 시 결과 변경. 페이지네이션 작동. 폰트 18px 확인. 면책 고지 표시 확인.
- 예상 소요: 2시간
- 비용: 없음

### T16: 상세 페이지 (/[facility_code]) 구현 ← v3 변경
- 마일스톤: M4
- 실행 환경: Codespaces
- 선행 조건: T15
- 작업 내용:
  - Server Component
  - **generateStaticParams: 상위 1,000건만 반환** (인구 밀집 지역 우선)
    ```typescript
    // ORDER BY sido_population DESC LIMIT 1000
    ```
  - **dynamicParams = true** + **revalidate: 2592000** (30일 ISR)
  - 나머지 19,000건은 첫 방문 시 서버 렌더링 → 캐싱 → 이후 정적 서빙
  - 예상 빌드 시간: 1,000페이지 × ~1초 = ~17분 (45분 제한 내 충분)
  - 현황 카드 3개 (입소·인력·요양보호사 지표)
  - **SeoContent 템플릿 컴포넌트로 JSON 렌더링** (v3 변경: dangerouslySetInnerHTML + sanitize-html 제거):
    ```tsx
    // components/SeoContent.tsx
    import { SeoContentJson } from '@/types/seo-content';

    export function SeoContent({ content }: { content: SeoContentJson }) {
      return (
        <article>
          <p className="text-lg leading-relaxed">{content.intro}</p>

          <h2 className="text-xl font-bold mt-6 mb-3">주요 특징</h2>
          <ul className="list-disc pl-6 space-y-1">
            {content.highlights.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>

          <h2 className="text-xl font-bold mt-6 mb-3">돌봄 서비스</h2>
          <p>{content.care_services}</p>

          <h2 className="text-xl font-bold mt-6 mb-3">위치 안내</h2>
          <p>{content.location_info}</p>

          <h2 className="text-xl font-bold mt-6 mb-3">시설 환경</h2>
          <p>{content.facility_info}</p>

          <p className="text-lg font-medium mt-6">{content.summary}</p>
        </article>
      );
    }
    ```
  - **React JSX 자동 이스케이핑으로 XSS 원천 차단** — dangerouslySetInnerHTML 미사용
  - **접근성**: 시맨틱 HTML, 색상대비 WCAG AA 준수
- 완료 확인: 로컬 프리뷰에서 특정 기관 상세 페이지 정상 표시. JSON 기반 SEO 소개글의 6개 섹션 모두 렌더링 확인. 코드베이스에 dangerouslySetInnerHTML 미사용 확인 (`grep -r "dangerouslySetInnerHTML" src/` 결과 0건).
- 예상 소요: 2시간
- 비용: 없음

### T17: 자부담금 계산기 (CostCalculator.tsx) 구현 — MVP 후 추가 가능
- 마일스톤: M4
- 실행 환경: Codespaces
- 선행 조건: T16
- 작업 내용: "use client" 클라이언트 컴포넌트. Props: mealCostPerDay, roomCost1Person, roomCost2Person, capacity. 2025년 등급별 본인부담 (1등급 655,000 / 2등급 607,000 / 3~5등급 524,000). 이용일수 슬라이더 (15~31일). 병실유형 토글 + transition 애니메이션 + 면책 고지.
- 완료 확인: 상세 페이지에서 계산기 정상 작동. 등급 변경·일수 변경·병실 변경 시 금액 실시간 변경.
- 예상 소요: 1시간
- 비용: 없음
- **비고**: 크리티컬 패스에서 제외. 일정 압박 시 6주차 버퍼에서 구현 가능.

### T18: Rate Limiting 미들웨어 구현 — MVP 후 추가 가능
- 마일스톤: M4
- 실행 환경: Codespaces
- 선행 조건: T14
- 작업 내용: src/middleware.ts 작성. **Vercel KV (Redis 호환) 기반** 1분 60회 제한. 429 반환. 봇 예외 (Googlebot·Bingbot·Yandexbot·DuckDuckBot). KV 장애 시 정상 통과. **Vercel KV 무료 한도: 30,000 req/day** (Pro 전환 시 100,000 req/day).
- 완료 확인: 로컬에서 60회 초과 요청 시 429 응답 확인. User-Agent에 Googlebot 포함 시 통과 확인.
- 예상 소요: 30분
- 비용: 없음
- **비고**: 크리티컬 패스에서 제외. 런칭 후 트래픽 증가 시 추가.

### T19: SEO 메타데이터, sitemap.xml, 보안 헤더 생성
- 마일스톤: M4
- 실행 환경: Codespaces
- 선행 조건: T16
- 작업 내용:
  - 각 페이지별 title, description, og 태그 설정
  - sitemap.xml 동적 생성 (2만 URL 포함)
  - robots.txt 작성
  - **CSP 헤더 설정**: Next.js middleware에서 `Content-Security-Policy: script-src 'self'` 설정 — defense-in-depth로 유지 (v3: JSON 방식으로 XSS 공격 표면이 근본적으로 제거되었으나, CSP는 추가 보호 계층으로 유지)
  - **삭제 요청 연락처**: footer 또는 별도 페이지에 "시설 정보 삭제 요청" 프로세스 안내 (24시간 내 처리)
- 완료 확인: `curl localhost:3000/sitemap.xml` 정상 출력. 메타 태그 확인. CSP 헤더 확인. 삭제 요청 안내 표시 확인.
- 예상 소요: 1.5시간
- 비용: 없음

---

### 배포 및 자동화 태스크

### T20: Vercel 배포
- 마일스톤: M5
- 실행 환경: 브라우저 + Codespaces
- 선행 조건: T15, T16, T19 (T17, T18은 선택)
- 작업 내용: Vercel에 GitHub 리포지토리 연결. 환경변수 설정 (SUPABASE_URL, SUPABASE_ANON_KEY, KV 연결). Vercel KV 인스턴스 생성 및 연결 (T18 구현 시). 배포 실행. **빌드 시간 45분 이내 확인** (SSG 1,000건 기준 ~17분 예상).
- 완료 확인: Vercel 대시보드에서 배포 성공. 빌드 시간 45분 이내. 배포 URL에서 메인·상세 정상 작동.
- **빌드 초과 시 대안**: generateStaticParams 반환을 빈 배열로 축소 → 완전 ISR 전환 (빌드 ~1분, 첫 방문 시 지연)
- 예상 소요: 1시간
- 비용: 없음

### T21: Vercel Deploy Hook 생성 및 등록
- 마일스톤: M5
- 실행 환경: 브라우저
- 선행 조건: T20
- 작업 내용: Vercel 프로젝트 설정에서 Deploy Hook URL 생성. GitHub Secrets에 VERCEL_DEPLOY_HOOK_URL 등록.
- 완료 확인: `curl -X POST $VERCEL_DEPLOY_HOOK_URL` 시 새 배포 트리거 확인.
- 예상 소요: 15분
- 비용: 없음

### T22: GitHub Actions 스케줄 워크플로우 완성
- 마일스톤: M5
- 실행 환경: Codespaces
- 선행 조건: T21, T11, T13-b
- 작업 내용: 매월 1일 GitHub Issue 자동 생성 워크플로우 작성 (xlsx 갱신 알림). 매월 6일 redeploy_vercel.yml (Deploy Hook 호출) 작성. 기존 scheduled_step2/step3 최종 확인.
- 완료 확인: GitHub Actions 탭에서 전체 워크플로우 목록 확인 (6개: manual 3개 + scheduled 3개).
- 예상 소요: 30분
- 비용: 없음

### T23: 도메인 연결 (선택사항)
- 마일스톤: M5
- 실행 환경: 브라우저
- 선행 조건: T20, DT04 (도메인 구매 결정 시)
- 작업 내용: 도메인 구매 후 Vercel 프로젝트에 커스텀 도메인 연결. DNS 설정. NEXT_PUBLIC_SITE_URL 업데이트.
- 완료 확인: 커스텀 도메인으로 접속 시 사이트 정상 표시. HTTPS 인증서 자동 발급 확인.
- 예상 소요: 30분
- 비용: 연 $10~20

---

### 런칭 후 검증 태스크

### T24: Google Search Console 등록 및 색인 요청
- 마일스톤: M6
- 실행 환경: 브라우저
- 선행 조건: T20
- 작업 내용: Google Search Console에 사이트 등록 (전체). sitemap.xml 제출. 색인 요청. **T13-d 파일럿 100건 색인 최종 확인** (2주 경과 후).
- 완료 확인: Search Console에서 sitemap 제출 성공. "색인 생성 요청됨" 상태 확인. 파일럿 100건 색인 80% 이상 확인.
- 예상 소요: 30분
- 비용: 없음

### T25: 최종 검증 체크리스트 실행 ← v3 변경
- 마일스톤: M6
- 실행 환경: 브라우저
- 선행 조건: T20
- 작업 내용: 아래 19개 항목 검증:
  1. 메인 페이지 로드 정상
  2. 시도/시군구 필터 작동
  3. 페이지네이션 작동
  4. 상세 페이지 진입 정상
  5. **SEO 소개글 JSON 템플릿 렌더링 정상 — 6개 섹션 모두 표시 확인** (v3 변경)
  6. 자부담금 계산기 작동 (구현된 경우)
  7. 모바일 반응형 확인
  8. 메타 태그 (title, description, og) 확인
  9. sitemap.xml 접근 가능
  10. robots.txt 접근 가능
  11. Rate Limiting 429 응답 확인 (구현된 경우)
  12. 봇 User-Agent 예외 확인 (구현된 경우)
  13. Vercel Analytics 활성화
  14. DB RLS 정책 작동 확인 (anon으로 쓰기 시도 → 거부)
  15. 전체 페이지 로드 속도 < 3초
  16. **CSP 헤더 정상 적용 확인**
  17. **접근성 확인: 폰트 크기 18px, 색상대비, 시맨틱 HTML**
  18. **면책 고지 및 삭제 요청 안내 표시 확인**
  19. **코드베이스에 dangerouslySetInnerHTML 미사용 확인** (v3 추가: `grep -r "dangerouslySetInnerHTML" src/` 결과 0건)
- 완료 확인: 19개 항목 모두 통과
- 예상 소요: 1시간
- 비용: 없음

### T26: 모니터링 및 수익화 준비
- 마일스톤: M6
- 실행 환경: 브라우저
- 선행 조건: T24, T25
- 작업 내용: Vercel Analytics 활성화. 트래픽 모니터링 기준 설정. 애드센스 신청 준비 (월간 페이지뷰 기준 충족 시). **비용 전환 트리거 확인: 월 10만 PV 초과 시 Vercel Pro 전환 계획**.
- 완료 확인: Vercel Analytics 대시보드에서 트래픽 데이터 수집 시작 확인.
- 예상 소요: 30분
- 비용: 없음

---

## 6. 리스크 관리

| # | 리스크 | 발생 확률 | 영향도 | 대응 방안 |
|---|---|---|---|---|
| R1 | B550928 API 키 승인 지연 (1~2일 이상) | 중 | 높음 | step1(xlsx 적재)은 API 키 없이 진행 가능. 프론트엔드 Mock 데이터 선행 개발. 3일+ 지연 시 고객센터 독촉 (02-3279-3700). |
| R2 | 평가등급 데이터 확보 불가 | 확정 | 중 | C안 채택 (등급 없이 런칭). 향후 공단 포털 파일 확보 시 추가. |
| R3 | 시설 사진 데이터 확보 불가 | 확정 | 중 | A안 채택 (홈페이지 URL 링크). 텍스트 중심 디자인으로 보완. |
| R4 | adminPttnCd 폴백 로직 실패 | 낮 | 중 | A03→A01→A04→B03→C06 순서 폴백. 전체 실패 시 해당 기관 건너뛰기 + pipeline_errors 로깅. |
| R5 | 비급여 금액 단위 불일치 (일별/월별 혼재) | 중 | 낮 | 금액 그대로 저장 + 계산기에 면책 고지 강화. |
| R6 | GitHub Actions 6시간 제한 초과 | 낮 | 중 | matrix 5 Job 병렬 분할 + timeout 300분 + 4일 분할 실행. |
| R7 | generateStaticParams 메모리 초과 | 낮 | 중 | 1,000건만 반환 + pagination 조회. |
| R8 | Codespaces 무료 한도 초과 (월 60시간) | 낮 | 낮 | 결제수단 미등록 시 정지만 됨 (과금 없음). 사용 시간 모니터링. |
| R9 | OpenAI API 비용 초과 | 낮 | 중 | 월 $20 하드리밋 설정. TEST_MODE 검증 후 비용 재산정. ~$12.15 예상. |
| R10 | Vercel 무료 대역폭 (100GB) 초과 | 낮 | 중 | 트래픽 모니터링 후 Pro $20/월 전환 검토. ISR 캐싱 극대화. |
| **R11** | **구글 AI 생성 콘텐츠 페널티** | **중** | **치명** | **100건 파일럿 배포(T13-d) → 2주 색인 확인 → 전체 확장. 실제 데이터 수치 중심 콘텐츠 차별화. 대안 수익모델 (시설 직접 마케팅, 네이버 유입).** |
| **R12** | **B550928 API 응답 구조 변경/중단** | **중** | **높음** | **최초 응답 스키마 저장(schemas/). 구조 변경 감지→GitHub Issue. 그레이스풀 디그레이드(xlsx 기본 데이터로 렌더링). DB 영구 캐싱.** |
| **R13** | **개인정보보호법 위반 리스크** | **낮** | **높음** | **공공데이터법 3조 근거. 대표자 성명 비표시(DB만 보관). 기관 대표번호만 표시. 면책 고지. 삭제 요청 24시간 처리.** |
| **R14** | **xlsx 컬럼 구조 변경** | **중** | **중** | **헤더 기반 매핑. 필수 컬럼 검증. 변경 감지→GitHub Issue.** |
| **R15** | **AI JSON 스키마 미준수** (v3 추가) | **낮** | **중** | **`response_format={"type":"json_object"}` 사용으로 유효 JSON 보장. jsonschema.validate로 스키마 검증. 프롬프트에 예시 JSON 포함. 실패 시 1회 재시도. 5% 재시도 비용 ~$0.50 예산 반영.** |
| **R16** | **JSON 스키마 마이그레이션** (v3 추가) | **낮** | **중** | **스키마 보수적 설계 + `additionalProperties: false`. 필드 추가 필요 시 JSONB `jsonb_set()`으로 부분 업데이트 가능. 프론트엔드에서 optional 처리.** |
| **R17** | **JSON 필드 분리로 인한 SEO 품질 저하** (v3 추가) | **낮** | **높음** | **프롬프트에 "각 섹션이 서로 다른 정보를 다루고 자연스럽게 이어지도록" 지시. T13-d 파일럿 100건에서 최종 렌더링 품질 면밀 검토. 프롬프트 조정으로 대응.** |

---

## 7. 보안 및 법적 준수

### 7.1 XSS 방어 ← v3 변경

> v2의 4단계 방어에서 v3의 **아키텍처적 안전성 + 1단계 defense-in-depth**로 변경

**아키텍처적 안전성 (v3 핵심)**

v3에서는 AI 생성 콘텐츠가 **순수 텍스트 JSON**으로 저장되고, 프론트엔드에서 **React JSX `{text}`**로 렌더링된다. React는 JSX 표현식 내의 문자열을 자동으로 HTML 이스케이핑하므로, `<script>`, `on*=` 속성, `javascript:` URL 등이 렌더링되더라도 브라우저에서 실행되지 않는다.

`dangerouslySetInnerHTML`을 사용하지 않으므로 **XSS 공격 표면 자체가 존재하지 않는다**.

| 계층 | 도구 | 적용 시점 | 역할 |
|---|---|---|---|
| 아키텍처 | React JSX 자동 이스케이핑 | 렌더링 시 | **XSS 원천 차단** (HTML 문자열을 텍스트로 표시) |
| Defense-in-depth | CSP 헤더 (script-src 'self') | Next.js middleware | 만일의 경우를 위한 추가 보호 |
| 코드 품질 | ESLint `react/no-danger` 규칙 | 개발 시 | dangerouslySetInnerHTML 실수 사용 방지 |

**v2 대비 제거된 항목:**
- ~~1차: nh3 화이트리스트 정화~~ → HTML을 생성하지 않으므로 불필요
- ~~2차: 정규식 XSS 검증~~ → JSON 순수 텍스트에 HTML 태그가 없으므로 불필요
- ~~3차: sanitize-html 프론트엔드 재정화~~ → dangerouslySetInnerHTML을 사용하지 않으므로 불필요

### 7.2 개인정보보호

- **법적 근거**: 공공데이터의 제공 및 이용 활성화에 관한 법률(공공데이터법) 제3조
- **대표자 성명**: 수집하되 웹에 비표시 (DB에만 보관)
- **전화번호**: 기관 대표번호만 표시 (개인 휴대폰 번호 제외)
- **주소**: 사업장 주소는 공개 정보이므로 표시 가능
- **면책 고지**: 사이트 하단에 "본 사이트는 공공데이터포털의 공공데이터를 활용하며, 공공데이터법에 의거하여 제공됩니다" 게시
- **삭제 요청**: 시설 측 정보 삭제 요청 시 24시간 내 처리. footer 또는 별도 페이지에 프로세스 안내

### 7.3 접근성

**MVP 포함 항목**:
- 기본 폰트: text-lg (18px) — 고령자/보호자 가독성 확보
- 색상 대비: WCAG AA 기준 4.5:1 준수 (Tailwind 기본 색상 팔레트 대부분 충족)
- 시맨틱 HTML: `<nav>`, `<main>`, `<article>`, `<footer>` 사용
- 이미지 alt 텍스트: 현재 이미지 없으므로 해당 없음

**런칭 후 개선 항목**:
- 글자 크기 조절 버튼
- 고대비 모드 토글
- 키보드 내비게이션 완전 지원

---

## 8. 에러 복구 전략

### 8.1 원자적 업데이트

- **step2**: API 5개 오퍼레이션 모두 성공 시에만 `detail_fetched_at` 업데이트. 부분 실패 시 해당 행은 NULL 유지.
- **step3**: **JSON 파싱 + 스키마 검증 + 품질 검증** 모두 통과 시에만 `seo_generated_at` 업데이트. (v2: SEO 생성 + nh3 정화 + 품질 검증)
- **재실행 안전성**: `WHERE detail_fetched_at IS NULL` / `WHERE seo_generated_at IS NULL` 조건으로 자동 이어서 실행. 중간에 실패해도 완료된 건은 재처리하지 않음.

### 8.2 pipeline_errors 테이블

실패한 기관의 추적 정보를 별도 테이블에 기록:
- `facility_code`: 실패한 기관 코드
- `step`: 'step2' 또는 'step3'
- `error_message`: 에러 메시지 (API 타임아웃, 파싱 실패, **JSON 스키마 미준수**, 품질 검증 실패 등)
- `created_at`: 실패 발생 시각

수동 재실행 또는 다음 주기에 자동 재시도 (IS NULL 조건).

### 8.3 데이터 정합성 검증

각 step 완료 후 자동 실행되는 검증 쿼리:

**step1 완료 후**:
```sql
SELECT count(*) as total,
  count(CASE WHEN facility_code IS NULL THEN 1 END) as null_code,
  count(CASE WHEN name IS NULL THEN 1 END) as null_name,
  count(CASE WHEN sido IS NULL THEN 1 END) as null_sido
FROM nursing_homes;
```

**step2 완료 후**:
```sql
SELECT count(*) as total,
  count(CASE WHEN detail_fetched_at IS NOT NULL THEN 1 END) as fetched,
  count(CASE WHEN capacity IS NULL AND detail_fetched_at IS NOT NULL THEN 1 END) as fetched_but_no_capacity
FROM nursing_homes;
```

**step3 완료 후** (v3 변경: JSONB 호환):
```sql
SELECT count(*) as total,
  count(CASE WHEN seo_generated_at IS NOT NULL THEN 1 END) as generated,
  count(CASE WHEN seo_content IS NULL OR seo_content = '{}' THEN 1 END) as empty_json,
  count(CASE WHEN jsonb_array_length(seo_content->'highlights') < 3 THEN 1 END) as too_few_highlights
FROM nursing_homes
WHERE seo_generated_at IS NOT NULL;
```

검증 결과를 GitHub Actions 로그에 출력. 임계치 미달 시 워크플로우 실패 처리.

### 8.4 부분 실패 허용 기준

전체 2만 건 중 **95% 이상 성공 시 정상 완료** 판정.
5% 미만 실패 건은 pipeline_errors에서 확인 후 수동 재실행 또는 다음 주기 자동 재시도.

---

## 9. 롤백 계획

### 9.1 Vercel 즉시 롤백
Vercel 대시보드에서 이전 배포로 원클릭 롤백 (내장 기능). 30초 이내 완료.

### 9.2 DB 롤백
Supabase Free는 Point-in-Time Recovery 미지원. 대안:
1. step1/2/3 실행 전 주요 컬럼의 **row count + checksum**을 GitHub Actions 로그에 기록
2. 심각한 문제 발견 시: nursing_homes 테이블 TRUNCATE → step1부터 재실행
3. xlsx 원본이 Supabase Storage에 보관되어 있으므로 완전 복원 가능

### 9.3 코드 롤백
`git revert` 또는 이전 커밋 체크아웃 → Vercel 자동 재배포.

---

## 10. 일정표 (6주)

```
1주차 ─────────────────────────────────────────────
  DT01~DT05  의사결정 완료
  T01        계정 생성 + API 키 발급 신청 + OpenAI 하드리밋 설정
  T02        xlsx 확보 + Storage 업로드
  T03        Secrets 등록
  T04        DB 테이블 + RLS 생성 (seo_content JSONB)
  T04-b      pipeline_errors 테이블 생성

2주차 ─────────────────────────────────────────────
  T05        폴더 구조 + 유틸리티 + schemas/ (seo_content_schema.json 포함)
  T06        step1 코드 작성 (헤더 기반 매핑 + pytest)
  T07        step1 워크플로우
  T08        step1 TEST_MODE 검증 (100건)
  T09        step2 코드 작성 착수 (Semaphore(5), 원자적 업데이트)

3주차 ─────────────────────────────────────────────
  T09        step2 코드 완성 + pytest
  T10        step2 TEST_MODE 검증 (5건, API 키 승인 필요)
  T11        step2 워크플로우
  T12        step3 코드 작성 (JSON 출력 + 스키마 검증 + 품질 검증 + pytest)
  T13-a      step3 TEST_MODE 검증 (3건, JSON 구조 확인)
  T13-b      step3 워크플로우
  T13-c      전체 파이프라인 실행 (step2: 4일 분할, step3: 3~4시간)
  T13-d      파일럿 배포 (100건, Python 간이 렌더링) → 색인 모니터링 시작

4주차 ─────────────────────────────────────────────
  T14        Next.js 초기 설정 (SeoContentJson 타입 + ESLint no-danger 규칙)
  T15        메인 페이지 (접근성 + 면책 고지 + 대표자명 비표시)
  T16        상세 페이지 (SSG 1,000건 + ISR + SeoContent 템플릿 컴포넌트)
  T17        자부담금 계산기 (MVP 후 추가 가능)
  T18        Rate Limiting (MVP 후 추가 가능)
  T19        SEO 메타 + sitemap + CSP 헤더 + 삭제 요청 안내
             [병행] 파일럿 100건 색인 모니터링 계속

5주차 ─────────────────────────────────────────────
  T20        Vercel 배포 (빌드 시간 확인, ~17분 예상)
  T21        Deploy Hook
  T22        스케줄 워크플로우 완성
  T23        도메인 연결 (선택)

6주차 (검증 + 버퍼) ──────────────────────────────
  T24        Search Console 등록 (전체) + 파일럿 색인 최종 확인
  T25        최종 검증 체크리스트 (19개 항목, dangerouslySetInnerHTML 미사용 확인 포함)
  T26        모니터링 + 수익화 준비
  [버퍼]      잔여 이슈 해결, T17/T18 미완 시 구현
```

---

## 11. 체크리스트

### 의사결정
- [x] DT01: 평가등급 데이터 확보 방안 결정 → C안 확정
- [x] DT02: 시설 사진 확보 방안 결정 → A안 확정
- [ ] DT03: xlsx 갱신 주기 및 담당자 결정
- [x] DT04: 도메인 구매 여부 결정 → 무료 도메인 확정
- [ ] DT05: 월간 운영 비용 상한선 합의

### M1: 인프라 세팅
- [ ] T01: 외부 계정 생성 + OpenAI 하드리밋 설정
- [ ] T02: xlsx 파일 확보 및 Storage 업로드
- [ ] T03: GitHub Secrets 및 Codespaces Secrets 등록
- [ ] T04: Supabase DB 테이블 생성 및 RLS 설정 (seo_content JSONB)
- [ ] T04-b: pipeline_errors 테이블 생성

### M2: 데이터 파이프라인 (step1 + step2 착수)
- [ ] T05: 프로젝트 폴더 구조 및 유틸리티 파일 생성 (jsonschema, seo_content_schema.json)
- [ ] T06: step1_load_xlsx.py 작성 (헤더 기반 매핑 + pytest)
- [ ] T07: step1 GitHub Actions 워크플로우 작성
- [ ] T08: step1 TEST_MODE 검증 (100건)
- [ ] T09: step2_fetch_api.py 착수

### M3: 데이터 파이프라인 (step2 완성 + step3 + 전체 실행)
- [ ] T09: step2_fetch_api.py 완성 (Semaphore(5) + 원자적 업데이트 + pytest)
- [ ] T10: step2 TEST_MODE 검증 (5건)
- [ ] T11: step2 GitHub Actions 워크플로우 작성
- [ ] T12: step3_generate_seo.py 작성 (JSON 출력 + 스키마 검증 + 품질 검증 + pytest)
- [ ] T13-a: step3 TEST_MODE 검증 (3건, JSON 구조 확인)
- [ ] T13-b: step3 GitHub Actions 워크플로우 작성
- [ ] T13-c: 전체 파이프라인 실행 (승인 후)
- [ ] T13-d: 파일럿 배포 (100건, Python 간이 렌더링) + 색인 모니터링 시작

### M4: 프론트엔드
- [ ] T14: Next.js 15 프로젝트 초기 설정 (SeoContentJson 타입 + ESLint no-danger)
- [ ] T15: 메인 페이지 구현 (접근성 + 면책 고지)
- [ ] T16: 상세 페이지 구현 (SSG 1,000건 + ISR + SeoContent 템플릿 컴포넌트)
- [ ] T17: 자부담금 계산기 구현 (MVP 후 추가 가능)
- [ ] T18: Rate Limiting 미들웨어 구현 (MVP 후 추가 가능)
- [ ] T19: SEO 메타데이터 + sitemap.xml + CSP 헤더

### M5: 배포 및 자동화
- [ ] T20: Vercel 배포
- [ ] T21: Vercel Deploy Hook 생성
- [ ] T22: GitHub Actions 스케줄 워크플로우 완성
- [ ] T23: 도메인 연결 (선택)

### M6: 런칭 후 검증 + 버퍼
- [ ] T24: Google Search Console 등록 (전체)
- [ ] T25: 최종 검증 체크리스트 실행 (19개 항목)
- [ ] T26: 모니터링 및 수익화 준비
- [ ] 파일럿 100건 색인 최종 확인
