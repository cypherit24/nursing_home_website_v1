---
paths:
  - "supabase/**"
  - ".github/**"
---

# 인프라 코딩 가이드라인 (plan-v3 T04, T07, T11, T13-b, T22 기반)

## Supabase DB

### 테이블: nursing_homes
- `seo_content` 컬럼: **JSONB** (TEXT 아님)
- `facility_code`: UNIQUE 인덱스 + dtype=str (앞자리 0 보호)
- `sido`, `sigungu`: 인덱스 생성
- `representative_name`: DB에 저장하되 프론트엔드 비표시 (S4)

### 테이블: pipeline_errors
- `id SERIAL`, `facility_code TEXT`, `step TEXT`, `error_message TEXT`, `created_at TIMESTAMPTZ DEFAULT NOW()`

### RLS 정책 (S2)
- **모든 테이블에 RLS 활성화 필수**
- nursing_homes: `anon` = SELECT only, `service_role` = ALL
- pipeline_errors: `service_role` = INSERT + SELECT, `anon` = SELECT only
- 새 테이블 생성 시 반드시 RLS 정책 포함

## GitHub Actions Workflows

### 공통 규칙
- **workflow_dispatch 트리거**: `confirm=yes` 입력 필수 (실수 방지)
- **시크릿**: 하드코딩 금지. 반드시 `${{ secrets.* }}` 사용 (S6)
- **정합성 검증**: 각 step 완료 후 검증 쿼리 결과를 로그에 출력. 임계치 미달 시 워크플로우 실패 처리

### step1 워크플로우 (T07)
- `manual_step1.yml`: workflow_dispatch, confirm=yes
- Python 환경 + requirements 설치 + step1 실행
- 정합성 검증 SQL 결과 로그 출력

### step2 워크플로우 (T11)
- `manual_step2.yml`: workflow_dispatch, test_mode + offset 선택
- `scheduled_step2.yml`: 매월 3일, 4일 분할 실행, matrix 5 Job 병렬, timeout 300분
- 정합성 검증 로그 출력

### step3 워크플로우 (T13-b)
- `manual_step3.yml`: workflow_dispatch, test_mode 선택
- `scheduled_step3.yml`: 매월 5일, matrix 5 Job 병렬, timeout 300분
- 정합성 검증 로그 출력

### 스케줄 워크플로우 (T22)
- 매월 1일: GitHub Issue 자동 생성 (xlsx 갱신 알림)
- 매월 6일: `redeploy_vercel.yml` (Deploy Hook 호출, `VERCEL_DEPLOY_HOOK_URL` 시크릿)

### 워크플로우 총 목록 (6개)
| 파일 | 트리거 | 용도 |
|---|---|---|
| manual_step1.yml | workflow_dispatch | step1 수동 실행 |
| manual_step2.yml | workflow_dispatch | step2 수동 실행 (offset) |
| manual_step3.yml | workflow_dispatch | step3 수동 실행 |
| scheduled_step2.yml | cron (매월 3일) | step2 자동 실행 |
| scheduled_step3.yml | cron (매월 5일) | step3 자동 실행 |
| redeploy_vercel.yml | cron (매월 6일) | Vercel 재배포 |
