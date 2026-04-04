# T07 보안 리뷰: manual_step1.yml

- **리뷰어**: Agent A (Opus)
- **대상 파일**: `.github/workflows/manual_step1.yml`
- **참조 파일**: `src/pipeline/step1_load_xlsx.py`
- **일자**: 2026-04-04

---

## (1) S6: 시크릿 하드코딩 여부

**판정: 통과**

- `SUPABASE_URL`: `${{ secrets.SUPABASE_URL }}` (L27)
- `SUPABASE_SERVICE_ROLE_KEY`: `${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}` (L28)
- yml 전체 및 `.github/workflows/` 디렉토리 전체에서 `supabase.co`, `eyJ`, `sb-`, `apikey` 패턴 grep 결과 0건
- 워크플로우 파일은 `manual_step1.yml` 1개만 존재 (다른 워크플로우 미생성 상태)

---

## (2) workflow_dispatch confirm 입력 필수 여부

**판정: 통과**

- `inputs.confirm`: `required: true`, `type: choice`, `options: ['yes']` (L6-11)
- choice 타입에 옵션이 'yes' 단일값이므로 실수로 다른 값 입력 불가
- `test_mode` 입력도 choice 타입으로 'false'/'true'만 허용 (L12-19)

---

## (3) Python 환경 설정 + requirements 설치

**판정: 통과**

- `actions/setup-python@v5`, `python-version: '3.11'`, `cache: 'pip'` (L35-39)
- `pip install -r requirements.txt` 스텝 존재 (L41-42)

---

## (4) 정합성 검증 쿼리 결과 로그 출력 여부

**판정: 통과 (단, 주의사항 1건)**

- `step1_load_xlsx.py`의 `run()` 함수가 마지막에 `verify_data_integrity()`를 호출 (L352)
- `verify_data_integrity()`는 `logger.info`/`logger.warning`으로 NULL 건수를 출력 (L283-294)
- 워크플로우의 `python -m src.pipeline.step1_load_xlsx` 실행 시 stdout/stderr가 GitHub Actions 로그에 자동 캡처됨
- logging.basicConfig의 기본 출력이 stderr이므로 Actions 로그에 정상 표시

**주의사항**: `verify_data_integrity()`에서 NULL이 발견되어도 `logger.warning`만 출력하고 프로세스는 정상 종료(exit 0)됨. `infra.md` 규칙에 명시된 "임계치 미달 시 워크플로우 실패 처리"가 현재 구현되어 있지 않음. 이 부분은 T07 태스크 범위 내에서 `sys.exit(1)` 또는 예외 발생으로 보강이 필요함.

---

## 추가 보안 검토

- `.github/workflows/` 디렉토리에 `manual_step1.yml` 외 다른 파일 없음 (정상 — 나머지는 아직 미생성)
- `actions/checkout@v4`, `actions/setup-python@v5` 모두 메이저 버전 태그 사용 (권장 패턴)
- `timeout-minutes: 30` 설정되어 있어 무한 실행 방지됨

---

## 종합 판정

| 항목 | 결과 |
|---|---|
| S6 시크릿 하드코딩 | 통과 |
| confirm=yes 필수 | 통과 |
| Python 환경 + requirements | 통과 |
| 정합성 검증 로그 출력 | 조건부 통과 |

**미해결 1건**: `verify_data_integrity()`에서 NULL 임계치 초과 시 비정상 종료(exit 1) 처리 미구현.

### 권장 수정 (Agent B 대상)

`step1_load_xlsx.py`의 `verify_data_integrity()` 함수 말미에 NULL 건수가 0보다 큰 필수 컬럼이 있으면 `raise RuntimeError("정합성 검증 실패")` 추가. 이렇게 하면 워크플로우가 자동으로 실패 상태로 전환됨.

```python
# verify_data_integrity() 끝부분에 추가
has_null = any(count > 0 for count in null_counts.values())
if has_null:
    raise RuntimeError(
        f"정합성 검증 실패: NULL 행 존재 — {null_counts}"
    )
```

이 수정은 `manual_step1.yml` 변경 없이 Python 코드만으로 해결 가능.
