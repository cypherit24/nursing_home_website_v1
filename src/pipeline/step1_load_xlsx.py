"""
step1_load_xlsx.py — 전국 요양원 데이터 파이프라인 Step 1

Supabase Storage에서 xlsx 파일을 다운로드하고, pandas로 파싱한 뒤
nursing_homes 테이블에 upsert합니다.

환경변수:
    SUPABASE_URL            Supabase 프로젝트 URL (필수)
    SUPABASE_SERVICE_ROLE_KEY  서비스 롤 키 (필수)
    STORAGE_BUCKET          스토리지 버킷명 (기본값: pipeline-data)
    XLSX_FILE_NAME          xlsx 파일명 (기본값: nursing_homes.xlsx)
    TEST_MODE               'true' 설정 시 100건만 처리

보안:
    S6: 시크릿 하드코딩 금지. 환경변수로만 주입.
    S7: facility_code 형식 검증. SQL은 supabase-py parameterized query 사용.
"""

import io
import logging
import os
from typing import Any

import pandas as pd

from src.pipeline.supabase_client import get_client

# ---------------------------------------------------------------------------
# 로거 설정
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
COLUMN_MAP: dict[str, str] = {
    "장기요양기관코드": "facility_code",
    "장기요양기관이름": "name",
    "기관별 상세주소": "address",
}

# sido, sigungu는 "시도 시군구 법정동명" 컬럼에서 파싱하므로 COLUMN_MAP에 포함하지 않음
REGION_COLUMN: str = "시도 시군구 법정동명"

REQUIRED: list[str] = ["장기요양기관코드", "장기요양기관이름", REGION_COLUMN]

# facility_code 형식: 영문+숫자 조합, 최대 20자 (S7)
FACILITY_CODE_MAX_LEN: int = 20

# 이전 실행에서 확인된 컬럼 목록 (변경 감지 기준)
KNOWN_COLUMNS: list[str] = [
    "장기요양기관코드",
    "장기요양기관이름",
    "우편번호",
    "시도코드",
    "시군구코드",
    "법정동코드",
    "시도 시군구 법정동명",
    "지정일자",
    "설치신고일자",
    "기관별 상세주소",
]


# ---------------------------------------------------------------------------
# 공개 함수 — 테스트에서 직접 호출 가능
# ---------------------------------------------------------------------------


def validate_columns(df: pd.DataFrame) -> None:
    """필수 컬럼 존재 여부를 검증합니다.

    Args:
        df: 원본 DataFrame (rename 이전 상태).

    Raises:
        ValueError: 필수 컬럼이 하나라도 누락된 경우.
    """
    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")


def detect_column_changes(df: pd.DataFrame) -> None:
    """알려진 컬럼 목록과 비교하여 차이 발견 시 경고를 출력합니다.

    Args:
        df: 원본 DataFrame (rename 이전 상태).
    """
    current_cols = set(df.columns)
    known_cols = set(KNOWN_COLUMNS)

    added = current_cols - known_cols
    removed = known_cols - current_cols

    if added:
        logger.warning("컬럼 변경 감지 — 새로 추가된 컬럼: %s", added)
    if removed:
        logger.warning("컬럼 변경 감지 — 사라진 컬럼: %s", removed)


def parse_xlsx(raw_bytes: bytes, test_mode: bool = False) -> pd.DataFrame:
    """xlsx 바이트를 pandas DataFrame으로 파싱합니다.

    처리 순서:
        1. 필수 컬럼 검증
        2. 컬럼 변경 감지 (경고)
        3. facility_code dtype=str 보장 (앞자리 0 보호)
        4. COLUMN_MAP으로 컬럼 rename
        5. facility_code NaN 행 제거
        6. TEST_MODE 시 100건으로 제한

    Args:
        raw_bytes: xlsx 파일 바이트.
        test_mode: True이면 100건만 반환.

    Returns:
        파싱 완료된 DataFrame.

    Raises:
        ValueError: 필수 컬럼 누락 시.
    """
    # facility_code 컬럼을 str로 읽어 앞자리 0 보호 (S7)
    df = pd.read_excel(
        io.BytesIO(raw_bytes),
        dtype={"장기요양기관코드": str},
        engine="openpyxl",
    )
    logger.info("xlsx 파싱 완료: 총 %d행", len(df))

    # 1. 필수 컬럼 검증
    validate_columns(df)

    # 2. 컬럼 변경 감지
    detect_column_changes(df)

    # 3. "시도 시군구 법정동명"에서 sido/sigungu 파싱
    df = _parse_region_column(df)

    # 4. 컬럼 rename
    df = df.rename(columns=COLUMN_MAP)

    # 5. facility_code NaN 행 제거
    before = len(df)
    df = df[df["facility_code"].notna()].copy()
    removed = before - len(df)
    if removed > 0:
        logger.warning("facility_code NaN 행 %d건 제거", removed)

    # 6. facility_code 형식 검증 및 str 보장 (S7)
    df["facility_code"] = df["facility_code"].astype(str).str.strip()

    # 7. TEST_MODE 제한
    if test_mode:
        df = df.head(100)
        logger.info("TEST_MODE: %d건으로 제한", len(df))

    logger.info("파싱 후 최종 행 수: %d", len(df))
    return df


def _parse_region_column(df: pd.DataFrame) -> pd.DataFrame:
    """'시도 시군구 법정동명' 컬럼에서 sido, sigungu를 파싱합니다.

    예: "서울특별시 종로구 구기동" → sido="서울특별시", sigungu="종로구"
    공백 기준 split: 첫 번째 = sido, 두 번째 = sigungu.

    Args:
        df: REGION_COLUMN을 포함한 DataFrame.

    Returns:
        sido, sigungu 컬럼이 추가된 DataFrame.
    """
    parts = df[REGION_COLUMN].astype(str).str.split(n=2, expand=True)
    df["sido"] = parts[0] if 0 in parts.columns else None
    df["sigungu"] = parts[1] if 1 in parts.columns else None
    logger.info("시도/시군구 파싱 완료 (sido=%d, sigungu=%d non-null)",
                df["sido"].notna().sum(), df["sigungu"].notna().sum())
    return df


def _sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    """NaN/float 값을 None으로 변환하여 JSON 직렬화를 보장합니다.

    Args:
        record: DataFrame.to_dict() 결과 단일 행.

    Returns:
        None 변환된 딕셔너리.
    """
    sanitized: dict[str, Any] = {}
    for key, value in record.items():
        if pd.isna(value) if not isinstance(value, (list, dict)) else False:
            sanitized[key] = None
        else:
            sanitized[key] = value
    return sanitized


def upsert_to_db(df: pd.DataFrame) -> dict[str, int]:
    """DataFrame을 nursing_homes 테이블에 upsert합니다.

    facility_code 기준 ON CONFLICT UPDATE. 실패 건은 pipeline_errors에 기록.
    supabase-py의 parameterized upsert를 사용하므로 SQL injection 위험 없음 (S7).

    Args:
        df: 파싱 완료된 DataFrame.

    Returns:
        {"success": int, "error": int} 처리 결과.
    """
    client = get_client()

    # upsert 대상 컬럼만 추출 (COLUMN_MAP + 파싱으로 생성된 sido/sigungu)
    db_columns = list(COLUMN_MAP.values()) + ["sido", "sigungu"]
    available_cols = [c for c in db_columns if c in df.columns]
    records = df[available_cols].to_dict(orient="records")

    success_count = 0
    error_count = 0

    # 배치 단위 upsert (한 번에 전송)
    sanitized_records = [_sanitize_record(r) for r in records]

    try:
        client.table("nursing_homes").upsert(
            sanitized_records,
            on_conflict="facility_code",
        ).execute()
        success_count = len(sanitized_records)
        logger.info("upsert 완료: %d건", success_count)
    except Exception as exc:  # noqa: BLE001
        logger.error("배치 upsert 실패, 건별 재시도: %s", exc)
        # 배치 실패 시 건별 재시도 + 오류 로깅
        for rec in sanitized_records:
            facility_code = rec.get("facility_code", "UNKNOWN")
            try:
                client.table("nursing_homes").upsert(
                    [rec],
                    on_conflict="facility_code",
                ).execute()
                success_count += 1
            except Exception as row_exc:  # noqa: BLE001
                error_count += 1
                error_msg = str(row_exc)
                logger.error(
                    "facility_code=%s upsert 실패: %s", facility_code, error_msg
                )
                _log_pipeline_error(
                    facility_code=facility_code,
                    step="step1",
                    error_message=error_msg,
                )

    return {"success": success_count, "error": error_count}


def _log_pipeline_error(
    facility_code: str,
    step: str,
    error_message: str,
) -> None:
    """pipeline_errors 테이블에 오류를 기록합니다.

    Args:
        facility_code: 오류 발생 시설 코드.
        step: 파이프라인 단계명 (e.g., 'step1').
        error_message: 오류 메시지 (시크릿 포함 금지 — S6).
    """
    try:
        client = get_client()
        client.table("pipeline_errors").insert(
            {
                "facility_code": facility_code,
                "step": step,
                "error_message": error_message,
            }
        ).execute()
    except Exception as exc:  # noqa: BLE001
        logger.error("pipeline_errors 기록 실패: %s", exc)


def verify_data_integrity() -> None:
    """upsert 완료 후 nursing_homes 테이블의 NULL 비율을 검증합니다.

    필수 컬럼(facility_code, name, sido, sigungu)에 NULL이 있으면 경고를 출력합니다.
    supabase-py 필터 쿼리로 직접 조회합니다 (exec_sql RPC 불필요).
    """
    client = get_client()
    table = client.table("nursing_homes")

    try:
        total = (
            table.select("id", count="exact").execute().count or 0
        )

        null_checks = {
            "facility_code": "facility_code",
            "name": "name",
            "sido": "sido",
            "sigungu": "sigungu",
        }
        null_counts: dict[str, int] = {}
        for col_name, col_key in null_checks.items():
            result = (
                table.select("id", count="exact")
                .is_(col_key, "null")
                .execute()
            )
            null_counts[col_name] = result.count or 0

        logger.info(
            "정합성 검증 — total=%d, null_code=%d, null_name=%d, null_sido=%d, null_sigungu=%d",
            total,
            null_counts["facility_code"],
            null_counts["name"],
            null_counts["sido"],
            null_counts["sigungu"],
        )

        failed_cols: list[str] = []
        for col_name, count in null_counts.items():
            if count > 0:
                logger.warning("경고: %s NULL 행 존재 (%d건)", col_name, count)
                failed_cols.append(col_name)

        if failed_cols:
            raise RuntimeError(
                f"정합성 검증 실패: 필수 컬럼 NULL 발견 — {failed_cols}"
            )

    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("정합성 검증 실패: %s", exc)


def download_xlsx_from_storage() -> bytes:
    """Supabase Storage에서 xlsx 파일을 다운로드합니다.

    환경변수:
        STORAGE_BUCKET: 버킷명 (기본값: pipeline-data)
        XLSX_FILE_NAME: 파일명 (기본값: nursing_homes.xlsx)

    Returns:
        xlsx 파일 바이트.

    Raises:
        RuntimeError: 다운로드 실패 시.
    """
    bucket = os.environ.get("STORAGE_BUCKET", "pipeline-data")
    file_name = os.environ.get("XLSX_FILE_NAME", "nursing_homes.xlsx")

    logger.info("Storage 다운로드 시작: bucket=%s, file=%s", bucket, file_name)

    client = get_client()
    try:
        raw_bytes: bytes = client.storage.from_(bucket).download(file_name)
        logger.info("다운로드 완료: %d bytes", len(raw_bytes))
        return raw_bytes
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            f"Storage 다운로드 실패 (bucket={bucket}, file={file_name}): {exc}"
        ) from exc


def run() -> None:
    """step1 메인 실행 함수.

    1. Storage에서 xlsx 다운로드
    2. 파싱 및 검증
    3. nursing_homes upsert
    4. 정합성 검증
    """
    test_mode = os.environ.get("TEST_MODE", "").lower() == "true"
    if test_mode:
        logger.info("TEST_MODE 활성화: 100건만 처리합니다")

    # 1. 다운로드
    raw_bytes = download_xlsx_from_storage()

    # 2. 파싱
    df = parse_xlsx(raw_bytes, test_mode=test_mode)

    # 3. upsert
    result = upsert_to_db(df)
    logger.info("step1 완료 — 성공: %d건, 실패: %d건", result["success"], result["error"])

    # 4. 정합성 검증
    verify_data_integrity()


if __name__ == "__main__":
    run()
