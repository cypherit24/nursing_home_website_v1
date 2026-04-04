"""
test_step1.py — step1_load_xlsx.py 단위 테스트

실제 Supabase 연결 없이 mock 기반으로 동작합니다.

커버리지:
    1. 컬럼 매핑 정상 작동 (COLUMN_MAP rename + sido/sigungu 파싱)
    2. facility_code dtype=str 보존 (앞자리 0 보호)
    3. 빈 행(facility_code NaN) 제거
    4. 필수 컬럼 누락 시 ValueError
    5. sido/sigungu 파싱 정확성
"""

import io
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.pipeline.step1_load_xlsx import (
    COLUMN_MAP,
    REGION_COLUMN,
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
        "장기요양기관코드": [f"A{str(i).zfill(4)}" for i in range(rows)],
        "장기요양기관이름": [f"테스트요양원_{i}" for i in range(rows)],
        "우편번호": [f"{10000 + i}" for i in range(rows)],
        "시도코드": [11] * rows,
        "시군구코드": [110] * rows,
        "법정동코드": [182] * rows,
        "시도 시군구 법정동명": ["서울특별시 종로구 구기동"] * rows,
        "지정일자": [20080625] * rows,
        "설치신고일자": [20080625] * rows,
        "기관별 상세주소": [f"서울특별시 종로구 테스트로 {i}" for i in range(rows)],
    }
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# 테스트 1: 컬럼 매핑 정상 작동
# ---------------------------------------------------------------------------


class TestColumnMapping:
    """COLUMN_MAP을 통한 컬럼 rename + sido/sigungu 파싱이 올바르게 동작하는지 검증합니다."""

    def test_all_columns_renamed(self):
        """COLUMN_MAP의 모든 원본 컬럼이 영문명으로 rename되어야 합니다."""
        df = _make_valid_df()
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        expected_cols = set(COLUMN_MAP.values()) | {"sido", "sigungu"}
        actual_cols = set(result.columns)
        assert expected_cols.issubset(actual_cols), (
            f"매핑된 컬럼이 결과에 없습니다. 누락: {expected_cols - actual_cols}"
        )

    def test_original_korean_columns_not_present(self):
        """rename 후 원본 한글 컬럼명(COLUMN_MAP 키)은 DataFrame에 남아있지 않아야 합니다."""
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
                "장기요양기관코드": ["00123", "00456", "00789"],
                "장기요양기관이름": ["요양원A", "요양원B", "요양원C"],
                "시도 시군구 법정동명": ["서울특별시 강남구 역삼동", "경기도 수원시 팔달구", "부산광역시 해운대구 우동"],
                "기관별 상세주소": ["주소A", "주소B", "주소C"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

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
                "장기요양기관코드": ["12345", "67890"],
                "장기요양기관이름": ["요양원X", "요양원Y"],
                "시도 시군구 법정동명": ["서울특별시 종로구 구기동", "경기도 성남시 분당구"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

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
                "장기요양기관코드": ["A0001", None, "A0003", None, "A0005"],
                "장기요양기관이름": ["요양원1", "요양원2", "요양원3", "요양원4", "요양원5"],
                "시도 시군구 법정동명": ["서울특별시 강남구 역삼동"] * 5,
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

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
                "장기요양기관코드": [None, None, None],
                "장기요양기관이름": ["요양원1", "요양원2", "요양원3"],
                "시도 시군구 법정동명": ["서울특별시 강남구 역삼동"] * 3,
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
        """장기요양기관코드 컬럼 누락 시 ValueError가 발생해야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관이름": ["요양원A"],
                "시도 시군구 법정동명": ["서울특별시 강남구 역삼동"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError, match="필수 컬럼 누락"):
            parse_xlsx(raw_bytes)

    def test_missing_name_raises_value_error(self):
        """장기요양기관이름 컬럼 누락 시 ValueError가 발생해야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관코드": ["A0001"],
                "시도 시군구 법정동명": ["서울특별시 강남구 역삼동"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError, match="필수 컬럼 누락"):
            parse_xlsx(raw_bytes)

    def test_missing_region_raises_value_error(self):
        """시도 시군구 법정동명 컬럼 누락 시 ValueError가 발생해야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관코드": ["A0001"],
                "장기요양기관이름": ["요양원A"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError, match="필수 컬럼 누락"):
            parse_xlsx(raw_bytes)

    def test_missing_multiple_columns_error_message_includes_all(self):
        """여러 필수 컬럼 누락 시 에러 메시지에 누락 컬럼명이 포함되어야 합니다."""
        df = pd.DataFrame(
            {
                "시도 시군구 법정동명": ["서울특별시 강남구 역삼동"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        with pytest.raises(ValueError) as exc_info:
            parse_xlsx(raw_bytes)

        error_message = str(exc_info.value)
        assert "필수 컬럼 누락" in error_message

    def test_validate_columns_directly_with_missing_col(self):
        """validate_columns 함수를 직접 호출하여 누락 감지를 검증합니다."""
        df = pd.DataFrame({"장기요양기관이름": ["요양원A"]})

        with pytest.raises(ValueError) as exc_info:
            validate_columns(df)

        assert "필수 컬럼 누락" in str(exc_info.value)

    def test_validate_columns_passes_with_all_required(self):
        """모든 필수 컬럼이 있을 때 validate_columns는 예외를 발생시키지 않아야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관코드": ["A0001"],
                "장기요양기관이름": ["요양원A"],
                "시도 시군구 법정동명": ["서울특별시 강남구 역삼동"],
            }
        )

        validate_columns(df)


# ---------------------------------------------------------------------------
# 테스트 5: sido/sigungu 파싱 정확성
# ---------------------------------------------------------------------------


class TestRegionParsing:
    """'시도 시군구 법정동명'에서 sido/sigungu 파싱이 올바르게 동작하는지 검증합니다."""

    def test_standard_region_parsing(self):
        """표준 형식 '시도 시군구 법정동'에서 sido/sigungu가 정확히 파싱되어야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관코드": ["A0001", "A0002", "A0003"],
                "장기요양기관이름": ["요양원A", "요양원B", "요양원C"],
                "시도 시군구 법정동명": [
                    "서울특별시 종로구 구기동",
                    "경기도 수원시 팔달구",
                    "부산광역시 해운대구 우동",
                ],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        assert result["sido"].iloc[0] == "서울특별시"
        assert result["sigungu"].iloc[0] == "종로구"
        assert result["sido"].iloc[1] == "경기도"
        assert result["sigungu"].iloc[1] == "수원시"
        assert result["sido"].iloc[2] == "부산광역시"
        assert result["sigungu"].iloc[2] == "해운대구"

    def test_sejong_no_sigungu(self):
        """세종특별자치시처럼 시군구 없이 법정동만 있는 경우도 처리해야 합니다."""
        df = pd.DataFrame(
            {
                "장기요양기관코드": ["S0001"],
                "장기요양기관이름": ["세종요양원"],
                "시도 시군구 법정동명": ["세종특별자치시 한솔동"],
            }
        )
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        assert result["sido"].iloc[0] == "세종특별자치시"
        assert result["sigungu"].iloc[0] == "한솔동"

    def test_address_column_mapped(self):
        """기관별 상세주소가 address로 매핑되어야 합니다."""
        df = _make_valid_df()
        raw_bytes = _df_to_xlsx_bytes(df)

        result = parse_xlsx(raw_bytes)

        assert "address" in result.columns
        assert result["address"].iloc[0] == "서울특별시 종로구 테스트로 0"
