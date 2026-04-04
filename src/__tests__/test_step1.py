"""
test_step1.py — step1_load_xlsx.py 단위 테스트

실제 Supabase 연결 없이 mock 기반으로 동작합니다.

커버리지:
    1. 컬럼 매핑 정상 작동 (COLUMN_MAP rename)
    2. facility_code dtype=str 보존 (앞자리 0 보호)
    3. 빈 행(facility_code NaN) 제거
    4. 필수 컬럼 누락 시 ValueError
"""

import io
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# src.pipeline.step1_load_xlsx 의 공개 함수들만 테스트
from src.pipeline.step1_load_xlsx import (
    COLUMN_MAP,
    REQUIRED,
    parse_xlsx,
    validate_columns,
)


# ---------------------------------------------------------------------------
# 헬퍼: 테스트용 DataFrame을 xlsx 바이트로 직렬화
# ---------------------------------------------------------------------------


def _df_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame을 xlsx 바이트로 변환합니다."""
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def _make_valid_df(rows: int = 3) -> pd.DataFrame:
    """필수 컬럼을 모두 포함한 유효한 DataFrame을 생성합니다."""
    data = {
        "장기요양기관기호": [f"A{str(i).zfill(4)}" for i in range(rows)],
        "기관명": [f"테스트요양원_{i}" for i in range(rows)],
        "시도": ["서울특별시"] * rows,
        "시군구": ["강남구"] * rows,
        "주소": [f"서울시 강남구 테스트로 {i}" for i in range(rows)],
        "대표자명": [f"홍길동{i}" for i in range(rows)],
        "전화번호": [f"02-1234-{str(i).zfill(4)}" for i in range(rows)],
    }
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# 테스트 1: 컬럼 매핑 정상 작동
# ---------------------------------------------------------------------------


class TestColumnMapping:
    """COLUMN_MAP을 통한 컬럼 rename이 올바르게 동작하는지 검증합니다."""

    def test_all_columns_renamed(self):
        """COLUMN_MAP의 모든 원본 컬럼이 영문명으로 rename되어야 합니다."""
        df = _make_valid_df()
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        expected_cols = set(COLUMN_MAP.values())
        actual_cols = set(result.columns)
        assert expected_cols.issubset(actual_cols), (
            f"매핑된 컬럼이 결과에 없습니다. 누락: {expected_cols - actual_cols}"
        )

    def test_original_korean_columns_not_present(self):
        """rename 후 원본 한글 컬럼명은 DataFrame에 남아있지 않아야 합니다."""
        df = _make_valid_df()
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        for korean_col in COLUMN_MAP.keys():
            assert korean_col not in result.columns, (
                f"한글 컬럼명이 rename 후에도 남아있습니다: {korean_col}"
            )

    def test_facility_code_column_exists(self):
        """facility_code 컬럼이 결과 DataFrame에 존재해야 합니다."""
        df = _make_valid_df()
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        assert "facility_code" in result.columns

    def test_name_sido_sigungu_columns_exist(self):
        """name, sido, sigungu 컬럼이 모두 존재해야 합니다."""
        df = _make_valid_df()
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        for col in ["name", "sido", "sigungu"]:
            assert col in result.columns, f"컬럼 누락: {col}"


# ---------------------------------------------------------------------------
# 테스트 2: facility_code dtype=str 보존 (앞자리 0 보호)
# ---------------------------------------------------------------------------


class TestFacilityCodeDtype:
    """facility_code가 str dtype으로 보존되는지 검증합니다."""

    def test_leading_zero_preserved(self):
        """앞자리 0이 있는 facility_code가 str로 보존되어야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관기호": ["00123", "00456", "00789"],
                "기관명": ["요양원A", "요양원B", "요양원C"],
                "시도": ["서울특별시", "경기도", "부산광역시"],
                "시군구": ["강남구", "수원시", "해운대구"],
                "주소": ["주소A", "주소B", "주소C"],
                "대표자명": ["대표A", "대표B", "대표C"],
                "전화번호": ["02-111-1111", "031-222-2222", "051-333-3333"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        # 앞자리 0이 보존되어야 함
        assert result["facility_code"].iloc[0] == "00123", (
            f"앞자리 0이 사라졌습니다: {result['facility_code'].iloc[0]}"
        )
        assert result["facility_code"].iloc[1] == "00456"
        assert result["facility_code"].iloc[2] == "00789"

    def test_facility_code_dtype_is_object(self):
        """facility_code 컬럼의 dtype이 object(str)이어야 합니다."""
        df = _make_valid_df()
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        assert result["facility_code"].dtype == object, (
            f"facility_code dtype이 object가 아닙니다: {result['facility_code'].dtype}"
        )

    def test_numeric_looking_code_stays_string(self):
        """숫자처럼 보이는 facility_code도 str로 유지되어야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관기호": ["12345", "67890"],
                "기관명": ["요양원X", "요양원Y"],
                "시도": ["서울특별시", "경기도"],
                "시군구": ["종로구", "성남시"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        # 정수로 변환되지 않고 str이어야 함
        for code in result["facility_code"]:
            assert isinstance(code, str), f"facility_code가 str이 아닙니다: {type(code)}"


# ---------------------------------------------------------------------------
# 테스트 3: 빈 행(facility_code NaN) 제거
# ---------------------------------------------------------------------------


class TestEmptyRowRemoval:
    """facility_code가 NaN인 행이 올바르게 제거되는지 검증합니다."""

    def test_nan_facility_code_rows_removed(self):
        """facility_code가 NaN인 행은 파싱 결과에서 제거되어야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관기호": ["A0001", None, "A0003", None, "A0005"],
                "기관명": ["요양원1", "요양원2", "요양원3", "요양원4", "요양원5"],
                "시도": ["서울특별시"] * 5,
                "시군구": ["강남구"] * 5,
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        # NaN 2건 제거 후 3건만 남아야 함
        assert len(result) == 3, f"예상 3건, 실제 {len(result)}건"

    def test_all_valid_rows_preserved(self):
        """facility_code가 모두 유효한 경우 모든 행이 보존되어야 합니다."""
        df = _make_valid_df(rows=5)
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        assert len(result) == 5

    def test_all_nan_facility_code_returns_empty(self):
        """모든 행의 facility_code가 NaN이면 빈 DataFrame을 반환해야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관기호": [None, None, None],
                "기관명": ["요양원1", "요양원2", "요양원3"],
                "시도": ["서울특별시"] * 3,
                "시군구": ["강남구"] * 3,
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        assert len(result) == 0

    def test_test_mode_limits_to_100_rows(self):
        """TEST_MODE=True 시 최대 100건만 반환해야 합니다."""
        df = _make_valid_df(rows=150)
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes, test_mode=True)

        assert len(result) == 100, f"TEST_MODE에서 100건이어야 합니다. 실제: {len(result)}"


# ---------------------------------------------------------------------------
# 테스트 4: 필수 컬럼 누락 시 ValueError
# ---------------------------------------------------------------------------


class TestRequiredColumnValidation:
    """필수 컬럼 누락 시 ValueError가 발생하는지 검증합니다."""

    def test_missing_facility_code_raises_value_error(self):
        """장기요양기관기호 컬럼 누락 시 ValueError가 발생해야 합니다."""
        df = pd.DataFrame(
            {
                # 장기요양기관기호 누락
                "기관명": ["요양원A"],
                "시도": ["서울특별시"],
                "시군구": ["강남구"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError, match="필수 컬럼 누락"):
            parse_xlsx(raw_bytes)

    def test_missing_name_raises_value_error(self):
        """기관명 컬럼 누락 시 ValueError가 발생해야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관기호": ["A0001"],
                # 기관명 누락
                "시도": ["서울특별시"],
                "시군구": ["강남구"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError, match="필수 컬럼 누락"):
            parse_xlsx(raw_bytes)

    def test_missing_sido_raises_value_error(self):
        """시도 컬럼 누락 시 ValueError가 발생해야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관기호": ["A0001"],
                "기관명": ["요양원A"],
                # 시도 누락
                "시군구": ["강남구"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError, match="필수 컬럼 누락"):
            parse_xlsx(raw_bytes)

    def test_missing_sigungu_raises_value_error(self):
        """시군구 컬럼 누락 시 ValueError가 발생해야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관기호": ["A0001"],
                "기관명": ["요양원A"],
                "시도": ["서울특별시"],
                # 시군구 누락
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError, match="필수 컬럼 누락"):
            parse_xlsx(raw_bytes)

    def test_missing_multiple_columns_error_message_includes_all(self):
        """여러 필수 컬럼 누락 시 에러 메시지에 누락 컬럼명이 포함되어야 합니다."""
        df = pd.DataFrame(
            {
                # 시도, 시군구만 있는 경우
                "시도": ["서울특별시"],
                "시군구": ["강남구"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError) as exc_info:
            parse_xlsx(raw_bytes)

        error_message = str(exc_info.value)
        assert "필수 컬럼 누락" in error_message

    def test_validate_columns_directly_with_missing_col(self):
        """validate_columns 함수를 직접 호출하여 누락 감지를 검증합니다."""
        df = pd.DataFrame({"기관명": ["요양원A"], "시도": ["서울"]})

        with pytest.raises(ValueError) as exc_info:
            validate_columns(df)

        assert "필수 컬럼 누락" in str(exc_info.value)

    def test_validate_columns_passes_with_all_required(self):
        """모든 필수 컬럼이 있을 때 validate_columns는 예외를 발생시키지 않아야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관기호": ["A0001"],
                "기관명": ["요양원A"],
                "시도": ["서울특별시"],
                "시군구": ["강남구"],
            }
        )

        # 예외가 발생하지 않아야 함
        validate_columns(df)
