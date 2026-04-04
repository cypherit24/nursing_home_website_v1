---
paths:
  - "src/pipeline/**"
---

# Pipeline 코딩 가이드라인 (plan-v3 T05~T12 기반)

## 언어 및 환경
- Python 3.11+, asyncio, aiohttp
- 의존성: xmltodict, openpyxl, pandas, aiohttp, openai, jsonschema
- nh3 사용 금지 (v3에서 제거됨)

## step1: xlsx 로드 (T06)
- **COLUMN_MAP 헤더명 기반 매핑** — 인덱스(A,B,G) 대신 헤더명 사용
  ```python
  COLUMN_MAP = {
      "장기요양기관코드": "facility_code",
      "장기요양기관이름": "name",
      "기관별 상세주소": "address",
  }
  REGION_COLUMN = "시도 시군구 법정동명"  # → sido, sigungu 파싱
  ```
- **sido/sigungu 파싱**: `시도 시군구 법정동명` 컬럼을 공백 split하여 sido(첫 번째), sigungu(두 번째) 추출
- **필수 컬럼 검증**: 파싱 시작 전 REQUIRED 컬럼 존재 확인, 누락 시 ValueError
- **facility_code dtype=str 필수** (앞자리 0 보호)
- **변경 감지**: 기존 컬럼 목록과 비교, 차이 발견 시 GitHub Issue 자동 생성
- **정합성 검증 SQL**: step1 완료 후 NULL 비율 검증. 임계치 미달 시 실패

## step2: API 수집 (T09)
- **Semaphore(5)** — 절대 10 이상 사용 금지
- **지수 백오프**: 429/503 응답 시 5초 -> 15초 -> 45초 -> 135초
- **4일 분할 실행**: 일 5,000건 처리. GitHub Actions에서 offset 파라미터로 제어
- **일일 제한 자동 중단**: 한도 도달 시 자동 중단, 다음날 IS NULL 조건으로 이어서 실행
- **원자적 업데이트**: API 5개 OP 모두 성공 시에만 detail_fetched_at 업데이트. 부분 실패 시 NULL 유지
- **오류 로깅**: 실패 건은 pipeline_errors 테이블에 (facility_code, step='step2', error_message) 기록
- **스키마 레퍼런스 저장**: 최초 성공 응답의 XML 구조를 `src/pipeline/schemas/`에 레퍼런스로 저장
- **구조 변경 감지**: 응답 키 목록을 레퍼런스와 비교 -> 차이 발견 시 경고 로그 + GitHub Issue 생성
- **정합성 검증 SQL**: step2 완료 후 fetched/null 비율 검증. 95% 이상 성공 시 정상

## step3: SEO 생성 (T12)
- **OpenAI gpt-4o-mini**, `response_format={"type": "json_object"}`
- **Semaphore(20)** — step3는 OpenAI API이므로 20까지 허용
- **JSON 파싱**: `json.loads(response)`. 마크다운 코드 펜스 자동 제거 후 재시도
- **스키마 검증**: `jsonschema.validate(data, schema)` — seo_content_schema.json 기준
- **품질 자동 검증**: `validate_seo_json()` — 시설명/지역명 포함 확인, 300자 이상, AI 생성 암시 문구 검출
- **실패 시 1회 재생성**: 프롬프트 변형하여 1회 재시도. 2회 실패 시 pipeline_errors 기록
- **원자적 업데이트**: JSON 파싱 + 스키마 검증 + 품질 검증 모두 통과 시에만 seo_generated_at 업데이트
- **정합성 검증 SQL**: step3 완료 후 생성/미달 비율 검증
- 429 오류 시 지수 백오프 (10초 -> 30초 -> 90초)

## 스키마 관리
- JSON 스키마 위치: `src/pipeline/schemas/seo_content_schema.json`
- **스키마 변경 시 반드시 `src/frontend/types/seo-content.ts` 동시 업데이트** (S5)
- `additionalProperties: false` 유지 필수

## 테스트
- **각 step에 pytest 단위 테스트 필수**
- step1: 컬럼 매핑, dtype 보존, 빈 행 처리, 필수 컬럼 누락 에러
- step2: 정상 응답 파싱, 빈 응답 처리, 에러 응답 처리 (mock 기반)
- step3: JSON 파싱(유효/펜스포함/잘못된), 스키마 검증, 품질 검증 함수 (mock 기반)
