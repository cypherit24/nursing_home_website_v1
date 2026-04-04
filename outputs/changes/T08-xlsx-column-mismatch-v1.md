# T08 변경 기록: xlsx 컬럼명 불일치 수정

- **Date**: 2026-04-04
- **Task**: T08 (step1 TEST_MODE 검증)
- **Status**: 수정 필요 — 코드 변경 전 기록

---

## 1. 문제

step1_load_xlsx.py의 `COLUMN_MAP`이 실제 Supabase Storage의 xlsx 파일 컬럼과 일치하지 않아 `ValueError: 필수 컬럼 누락` 발생.

### 원인
T06에서 step1 코드를 작성할 때 xlsx 파일의 실제 컬럼을 확인하지 않고, 공공데이터포털의 일반적인 요양원 데이터 형식을 가정하여 코딩함.

### 코드가 기대한 컬럼 vs 실제 컬럼

| 코드 COLUMN_MAP (기대) | 실제 xlsx 컬럼 | DB 컬럼 |
|---|---|---|
| `장기요양기관기호` | `장기요양기관코드` | `facility_code` |
| `기관명` | `장기요양기관이름` | `name` |
| `시도` (문자열) | `시도코드` (숫자: 11) | `sido` |
| `시군구` (문자열) | `시군구코드` (숫자: 110) | `sigungu` |
| `주소` | `기관별 상세주소` | `address` |
| `대표자명` | **없음** | `representative_name` |
| `전화번호` | **없음** | `phone` |

### 실제 xlsx 전체 컬럼 (10개)
```
장기요양기관코드, 장기요양기관이름, 우편번호, 시도코드, 시군구코드,
법정동코드, 시도 시군구 법정동명, 지정일자, 설치신고일자, 기관별 상세주소
```

### 실제 데이터 예시
```
장기요양기관코드: 11111000006
장기요양기관이름: 청운노인요양원
시도코드: 11
시군구코드: 110
시도 시군구 법정동명: 서울특별시 종로구 구기동
기관별 상세주소: 서울특별시 종로구 비봉길 76 (구기동)
```

---

## 2. 수정 방안

### 2-a. step1_load_xlsx.py 변경

1. **COLUMN_MAP 업데이트** — 실제 컬럼명으로 매핑
   ```python
   COLUMN_MAP = {
       "장기요양기관코드": "facility_code",
       "장기요양기관이름": "name",
       "기관별 상세주소": "address",
   }
   ```

2. **sido/sigungu 파싱 로직 추가** — `시도 시군구 법정동명` 컬럼에서 추출
   - "서울특별시 종로구 구기동" → sido="서울특별시", sigungu="종로구"
   - 공백 split 후 첫 번째 = sido, 두 번째 = sigungu

3. **REQUIRED 업데이트** — `["장기요양기관코드", "장기요양기관이름", "시도 시군구 법정동명"]`

4. **KNOWN_COLUMNS 업데이트** — 실제 10개 컬럼 반영

5. **representative_name, phone 제거** — 이 xlsx에 없는 컬럼. DB에는 NULL 유지.

### 2-b. 테스트 파일 변경 (test_step1.py)
- 모든 테스트의 mock DataFrame 컬럼명을 실제 컬럼명으로 변경
- sido/sigungu 파싱 테스트 케이스 추가

### 2-c. GitHub Actions (manual_step1.yml)
- `XLSX_FILE_NAME` 환경변수 추가 (기본값 또는 워크플로우 입력)

---

## 3. 프로젝트 전반 영향

### 영향 있음
| 파일 | 영향 | 설명 |
|---|---|---|
| `src/pipeline/step1_load_xlsx.py` | **직접 수정** | COLUMN_MAP, REQUIRED, 파싱 로직 변경 |
| `src/__tests__/test_step1.py` | **직접 수정** | mock 데이터 컬럼명 변경, 파싱 테스트 추가 |
| `.github/workflows/manual_step1.yml` | **소폭 수정** | XLSX_FILE_NAME 환경변수 추가 |
| `.claude/rules/pipeline.md` | **문서 수정** | COLUMN_MAP 예시 업데이트 |

### 영향 없음
| 파일 | 이유 |
|---|---|
| `supabase/migrations/` | DB 스키마(nursing_homes 테이블)는 변경 불필요. representative_name, phone 컬럼은 nullable로 이미 존재. step2 API에서 채울 수 있음 |
| `src/pipeline/supabase_client.py` | 클라이언트 로직 변경 없음 |
| `src/pipeline/schemas/seo_content_schema.json` | step3 스키마, step1과 무관 |
| `src/frontend/types/seo-content.ts` | S5 대상이지만 이번 변경과 무관 |

### 주의사항
- `representative_name`, `phone`은 이 xlsx에 포함되어 있지 않음. step2 API 수집 단계(T09)에서 채우거나, 별도 데이터소스가 필요할 수 있음. PM 확인 필요.
- `시도코드`(11), `시군구코드`(110)는 숫자 코드이므로 사람이 읽을 수 있는 시도/시군구명은 `시도 시군구 법정동명`에서 파싱해야 함.

---

## 4. 파일명 이슈

Storage에 업로드된 파일명이 `Status_of_Facilities_20250401.xlsx`이며, 코드 기본값인 `nursing_homes.xlsx`와 다름.
- 해결: 환경변수 `XLSX_FILE_NAME`으로 오버라이드 (코드 기본값 변경하지 않음)
- GitHub Actions에서도 해당 환경변수 설정 필요
