"""
test_step2.py — step2_fetch_api.py 단위 테스트

실제 Supabase/API 연결 없이 mock 기반으로 동작합니다.

커버리지:
    1. 정상 XML 응답 파싱 (OP1~OP5 구조)
    2. 빈/누락 응답 처리 (items가 None인 경우)
    3. 에러 응답 처리 (API resultCode != '00')
    4. 전화번호 조합 (locTelNo1+2+3)
    5. 비급여 전처리 (단일 dict vs 리스트, kind 코드 1/2/5/6)
    6. adminPttnCd 폴백 로직
    7. 원자적 업데이트 검증 (OP1 실패 → detail_fetched_at 미설정)

참고: pytest-asyncio 미설치 환경이므로 비동기 테스트는 asyncio.run()으로 래핑합니다.
"""

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.pipeline.step2_fetch_api import (
    _check_result_code,
    _extract_item,
    _parse_xml_response,
    assemble_phone,
    fetch_op1,
    fetch_op,
    parse_nonbenefit_items,
    process_facility,
    validate_facility_code,
)


def run_async(coro):
    """비동기 코루틴을 동기 테스트에서 실행하기 위한 헬퍼."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# 헬퍼: XML 빌더
# ---------------------------------------------------------------------------


def _make_xml(item_data: str, result_code: str = "00") -> str:
    """테스트용 API 응답 XML을 생성합니다."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>{result_code}</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      <item>
        {item_data}
      </item>
    </items>
  </body>
</response>"""


def _make_xml_list(items_xml: str, result_code: str = "00") -> str:
    """여러 item을 포함한 XML을 생성합니다."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>{result_code}</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items>
      {items_xml}
    </items>
  </body>
</response>"""


def _make_xml_empty(result_code: str = "00") -> str:
    """items가 없는 XML을 생성합니다."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
  <header>
    <resultCode>{result_code}</resultCode>
    <resultMsg>OK</resultMsg>
  </header>
  <body>
    <items/>
  </body>
</response>"""


# ---------------------------------------------------------------------------
# 테스트 1: 정상 XML 파싱
# ---------------------------------------------------------------------------


class TestXmlParsing:
    """xmltodict를 통한 XML 파싱 및 item 추출이 올바르게 동작하는지 검증합니다."""

    def test_parse_valid_xml(self):
        """정상 XML이 dict로 파싱되어야 합니다."""
        xml = _make_xml("<locTelNo1>02</locTelNo1><locTelNo2>123</locTelNo2><locTelNo3>4567</locTelNo3>")
        result = _parse_xml_response(xml)

        assert result is not None
        assert "response" in result

    def test_extract_item_from_normal_response(self):
        """정상 응답에서 item dict가 추출되어야 합니다."""
        xml = _make_xml("<locTelNo1>02</locTelNo1>")
        parsed = _parse_xml_response(xml)
        item = _extract_item(parsed)

        assert item is not None
        assert isinstance(item, dict)
        assert item.get("locTelNo1") == "02"

    def test_extract_item_returns_none_on_empty_items(self):
        """items가 비어있을 때 None을 반환해야 합니다."""
        xml = _make_xml_empty()
        parsed = _parse_xml_response(xml)
        item = _extract_item(parsed)

        assert item is None

    def test_parse_invalid_xml_returns_none(self):
        """유효하지 않은 XML은 None을 반환해야 합니다."""
        result = _parse_xml_response("이것은 XML이 아닙니다 <<<")
        assert result is None

    def test_check_result_code_success(self):
        """resultCode가 '00'이면 True를 반환해야 합니다."""
        xml = _make_xml("<dummy>test</dummy>")
        parsed = _parse_xml_response(xml)
        assert _check_result_code(parsed) is True

    def test_check_result_code_failure(self):
        """resultCode가 '00'이 아니면 False를 반환해야 합니다."""
        xml = _make_xml("<dummy>test</dummy>", result_code="99")
        parsed = _parse_xml_response(xml)
        assert _check_result_code(parsed) is False

    def test_op1_full_item_parsing(self):
        """OP1 응답의 adminPttnCd, locTelNo1/2/3이 파싱되어야 합니다."""
        xml = _make_xml(
            "<adminPttnCd>A03</adminPttnCd>"
            "<locTelNo1>031</locTelNo1>"
            "<locTelNo2>456</locTelNo2>"
            "<locTelNo3>7890</locTelNo3>"
        )
        parsed = _parse_xml_response(xml)
        item = _extract_item(parsed)

        assert item["adminPttnCd"] == "A03"
        assert item["locTelNo1"] == "031"
        assert item["locTelNo2"] == "456"
        assert item["locTelNo3"] == "7890"

    def test_op2_item_parsing(self):
        """OP2 응답의 instlPsncnt, nowPsncnt가 파싱되어야 합니다."""
        xml = _make_xml("<instlPsncnt>30</instlPsncnt><nowPsncnt>25</nowPsncnt>")
        parsed = _parse_xml_response(xml)
        item = _extract_item(parsed)

        assert item["instlPsncnt"] == "30"
        assert item["nowPsncnt"] == "25"

    def test_op4_item_parsing(self):
        """OP4 응답의 crgrPsncnt가 파싱되어야 합니다."""
        xml = _make_xml("<crgrPsncnt>10</crgrPsncnt>")
        parsed = _parse_xml_response(xml)
        item = _extract_item(parsed)

        assert item["crgrPsncnt"] == "10"


# ---------------------------------------------------------------------------
# 테스트 2: 빈/누락 응답 처리
# ---------------------------------------------------------------------------


class TestEmptyResponseHandling:
    """items가 None이거나 비어있는 경우 처리를 검증합니다."""

    def test_extract_item_on_missing_items_key(self):
        """items 키 자체가 없는 경우 None을 반환해야 합니다."""
        parsed = {"response": {"header": {"resultCode": "00"}, "body": {}}}
        result = _extract_item(parsed)
        assert result is None

    def test_extract_item_on_none_items(self):
        """items가 None인 경우 None을 반환해야 합니다."""
        parsed = {"response": {"header": {"resultCode": "00"}, "body": {"items": None}}}
        result = _extract_item(parsed)
        assert result is None

    def test_extract_item_on_missing_item_key(self):
        """items 안에 item 키가 없는 경우 None을 반환해야 합니다."""
        parsed = {"response": {"header": {"resultCode": "00"}, "body": {"items": {"other": "val"}}}}
        result = _extract_item(parsed)
        assert result is None

    def test_parse_nonbenefit_items_empty_input(self):
        """item이 None인 경우 모두 None인 dict를 반환해야 합니다."""
        result = parse_nonbenefit_items(None)
        assert result["meal_cost_per_day"] is None
        assert result["room_cost_1person"] is None
        assert result["room_cost_2person"] is None

    def test_parse_nonbenefit_items_empty_list(self):
        """빈 리스트인 경우 모두 None인 dict를 반환해야 합니다."""
        result = parse_nonbenefit_items([])
        assert result["meal_cost_per_day"] is None
        assert result["room_cost_1person"] is None
        assert result["room_cost_2person"] is None


# ---------------------------------------------------------------------------
# 테스트 3: 에러 응답 처리
# ---------------------------------------------------------------------------


class TestErrorResponseHandling:
    """API 에러 응답 처리를 검증합니다."""

    def test_error_result_code_returns_none_item(self):
        """resultCode가 '00'이 아닌 경우 item 추출 후 None 처리해야 합니다."""
        xml = _make_xml("<dummy>val</dummy>", result_code="30")
        parsed = _parse_xml_response(xml)
        assert _check_result_code(parsed) is False

    def test_none_xml_text_results_in_none_parse(self):
        """None 입력 시 _parse_xml_response가 None을 반환해야 합니다."""
        result = _parse_xml_response(None)  # type: ignore[arg-type]
        assert result is None

    def test_check_result_code_on_none_parsed(self):
        """None 파싱 결과에 대해 _check_result_code가 False를 반환해야 합니다."""
        assert _check_result_code(None) is False  # type: ignore[arg-type]

    def test_check_result_code_on_malformed_dict(self):
        """구조가 잘못된 dict에 대해 _check_result_code가 False를 반환해야 합니다."""
        assert _check_result_code({"wrong": "structure"}) is False


# ---------------------------------------------------------------------------
# 테스트 4: 전화번호 조합
# ---------------------------------------------------------------------------


class TestPhoneAssembly:
    """전화번호 조합 함수를 검증합니다."""

    def test_normal_phone_assembly(self):
        """세 부분이 모두 있을 때 'v1-v2-v3' 형식으로 반환해야 합니다."""
        assert assemble_phone("02", "123", "4567") == "02-123-4567"

    def test_mobile_phone_assembly(self):
        """휴대폰 번호도 동일 패턴으로 조합해야 합니다."""
        assert assemble_phone("010", "1234", "5678") == "010-1234-5678"

    def test_missing_part1_returns_none(self):
        """v1이 None이면 None을 반환해야 합니다."""
        assert assemble_phone(None, "123", "4567") is None

    def test_missing_part2_returns_none(self):
        """v2가 None이면 None을 반환해야 합니다."""
        assert assemble_phone("02", None, "4567") is None

    def test_missing_part3_returns_none(self):
        """v3가 None이면 None을 반환해야 합니다."""
        assert assemble_phone("02", "123", None) is None

    def test_empty_string_part_returns_none(self):
        """빈 문자열 부분이 있으면 None을 반환해야 합니다."""
        assert assemble_phone("02", "", "4567") is None
        assert assemble_phone("", "123", "4567") is None
        assert assemble_phone("02", "123", "") is None

    def test_whitespace_only_part_returns_none(self):
        """공백만 있는 부분은 None으로 처리해야 합니다."""
        assert assemble_phone("02", "  ", "4567") is None


# ---------------------------------------------------------------------------
# 테스트 5: 비급여 전처리
# ---------------------------------------------------------------------------


class TestNonbenefitParsing:
    """비급여 정보(OP3) 전처리를 검증합니다."""

    def test_single_dict_meal_cost(self):
        """단일 dict에서 식재료비(kind=1)가 meal_cost_per_day에 매핑되어야 합니다."""
        item = {"nonpayKind": "1", "nonpayTgtAmt": "10000"}
        result = parse_nonbenefit_items(item)

        assert result["meal_cost_per_day"] == 10000
        assert result["room_cost_1person"] is None
        assert result["room_cost_2person"] is None

    def test_list_with_multiple_kinds(self):
        """리스트에서 kind 1+5는 합산, 2→1인실, 6→2인실에 매핑되어야 합니다."""
        items = [
            {"nonpayKind": "1", "nonpayTgtAmt": "8000"},   # 식재료비
            {"nonpayKind": "5", "nonpayTgtAmt": "2000"},   # 간식비
            {"nonpayKind": "2", "nonpayTgtAmt": "50000"},  # 1인실
            {"nonpayKind": "6", "nonpayTgtAmt": "30000"},  # 2인실
        ]
        result = parse_nonbenefit_items(items)

        assert result["meal_cost_per_day"] == 10000  # 8000 + 2000
        assert result["room_cost_1person"] == 50000
        assert result["room_cost_2person"] == 30000

    def test_snack_only_kind5(self):
        """간식비(kind=5)만 있는 경우 meal_cost_per_day에 매핑되어야 합니다."""
        item = {"nonpayKind": "5", "nonpayTgtAmt": "3000"}
        result = parse_nonbenefit_items(item)

        assert result["meal_cost_per_day"] == 3000

    def test_kind2_only(self):
        """1인실 비용(kind=2)만 있는 경우 room_cost_1person에만 매핑되어야 합니다."""
        item = {"nonpayKind": "2", "nonpayTgtAmt": "40000"}
        result = parse_nonbenefit_items(item)

        assert result["room_cost_1person"] == 40000
        assert result["meal_cost_per_day"] is None
        assert result["room_cost_2person"] is None

    def test_kind6_only(self):
        """2인실 비용(kind=6)만 있는 경우 room_cost_2person에만 매핑되어야 합니다."""
        item = {"nonpayKind": "6", "nonpayTgtAmt": "20000"}
        result = parse_nonbenefit_items(item)

        assert result["room_cost_2person"] == 20000
        assert result["meal_cost_per_day"] is None
        assert result["room_cost_1person"] is None

    def test_unknown_kind_ignored(self):
        """알 수 없는 kind 코드는 무시되어야 합니다."""
        item = {"nonpayKind": "99", "nonpayTgtAmt": "99999"}
        result = parse_nonbenefit_items(item)

        assert result["meal_cost_per_day"] is None
        assert result["room_cost_1person"] is None
        assert result["room_cost_2person"] is None

    def test_single_dict_treated_as_single_item(self):
        """단일 dict 입력이 리스트와 동일하게 처리되어야 합니다."""
        item_dict = {"nonpayKind": "1", "nonpayTgtAmt": "5000"}
        item_list = [{"nonpayKind": "1", "nonpayTgtAmt": "5000"}]

        result_dict = parse_nonbenefit_items(item_dict)
        result_list = parse_nonbenefit_items(item_list)

        assert result_dict == result_list

    def test_invalid_amount_defaults_to_zero(self):
        """금액 변환 실패 시 0으로 처리해야 합니다."""
        item = {"nonpayKind": "1", "nonpayTgtAmt": "invalid"}
        result = parse_nonbenefit_items(item)

        assert result["meal_cost_per_day"] == 0

    def test_none_amount_defaults_to_zero(self):
        """금액이 None인 경우 0으로 처리해야 합니다."""
        item = {"nonpayKind": "1", "nonpayTgtAmt": None}
        result = parse_nonbenefit_items(item)

        assert result["meal_cost_per_day"] == 0


# ---------------------------------------------------------------------------
# 테스트 6: adminPttnCd 폴백 로직
# ---------------------------------------------------------------------------


class TestAdminPttnCdFallback:
    """adminPttnCd 폴백 로직을 검증합니다."""

    def test_validate_facility_code_valid(self):
        """유효한 facility_code는 True를 반환해야 합니다."""
        assert validate_facility_code("A1234567890") is True
        assert validate_facility_code("ABC123") is True
        assert validate_facility_code("12345678") is True

    def test_validate_facility_code_invalid(self):
        """유효하지 않은 facility_code는 False를 반환해야 합니다."""
        assert validate_facility_code("") is False
        assert validate_facility_code(None) is False  # type: ignore[arg-type]
        assert validate_facility_code("한글코드") is False
        assert validate_facility_code("A" * 21) is False  # 21자 초과

    def test_fetch_op1_success_without_fallback(self):
        """OP1 최초 시도가 성공하면 폴백 없이 결과를 반환해야 합니다."""
        op1_xml = _make_xml(
            "<adminPttnCd>A03</adminPttnCd>"
            "<locTelNo1>02</locTelNo1>"
            "<locTelNo2>111</locTelNo2>"
            "<locTelNo3>2222</locTelNo3>"
        )

        mock_session = MagicMock()

        # _fetch_with_backoff를 직접 패치하여 복잡한 aiohttp 컨텍스트 매니저 mock 불필요
        with patch(
            "src.pipeline.step2_fetch_api._fetch_with_backoff",
            new=AsyncMock(return_value=op1_xml),
        ):
            with patch("src.pipeline.step2_fetch_api._save_schema_reference"):
                item, admin_cd = run_async(fetch_op1(mock_session, "A0001", "TEST_KEY"))

        assert item is not None
        assert admin_cd == "A03"

    def test_fetch_op1_uses_fallback_on_empty_items(self):
        """OP1 최초 시도가 빈 items를 반환하면 폴백을 시도해야 합니다."""
        empty_xml = _make_xml_empty()
        fallback_xml = _make_xml("<adminPttnCd>A01</adminPttnCd>")

        call_count = 0

        async def mock_fetch(session, url, facility_code, op_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return empty_xml
            return fallback_xml

        mock_session = MagicMock()

        with patch("src.pipeline.step2_fetch_api._fetch_with_backoff", side_effect=mock_fetch):
            with patch("src.pipeline.step2_fetch_api._save_schema_reference"):
                item, admin_cd = run_async(fetch_op1(mock_session, "A0001", "TEST_KEY"))

        assert item is not None
        # 첫 번째 폴백 코드는 ADMIN_PTTN_FALLBACK[0] = "A03"
        assert admin_cd == "A03"

    def test_fetch_op1_returns_none_when_all_fail(self):
        """OP1과 모든 폴백이 실패하면 (None, None)을 반환해야 합니다."""
        empty_xml = _make_xml_empty()

        mock_session = MagicMock()

        with patch(
            "src.pipeline.step2_fetch_api._fetch_with_backoff",
            new=AsyncMock(return_value=empty_xml),
        ):
            with patch("src.pipeline.step2_fetch_api._save_schema_reference"):
                item, admin_cd = run_async(fetch_op1(mock_session, "A0001", "TEST_KEY"))

        assert item is None
        assert admin_cd is None


# ---------------------------------------------------------------------------
# 테스트 7: 원자적 업데이트 검증
# ---------------------------------------------------------------------------


class TestAtomicUpdate:
    """OP1 실패 시 detail_fetched_at이 설정되지 않음을 검증합니다."""

    def test_no_db_update_when_op1_fails(self):
        """OP1이 실패하면 DB 업데이트 없이 False를 반환해야 합니다."""
        semaphore = asyncio.Semaphore(5)

        # fetch_op1은 async 함수이므로 AsyncMock 사용
        with patch(
            "src.pipeline.step2_fetch_api.fetch_op1",
            new=AsyncMock(return_value=(None, None)),
        ):
            with patch("src.pipeline.step2_fetch_api._log_pipeline_error") as mock_log:
                with patch("src.pipeline.step2_fetch_api.get_client") as mock_get_client:
                    mock_session = MagicMock()
                    result = run_async(
                        process_facility(mock_session, "A0001", "TEST_KEY", semaphore)
                    )

        assert result is False
        # DB 업데이트(get_client 호출)는 발생하지 않아야 함
        mock_get_client.assert_not_called()
        # 에러가 pipeline_errors에 기록되어야 함
        mock_log.assert_called_once()

    def test_db_update_called_when_op1_succeeds(self):
        """OP1이 성공하면 DB 업데이트가 호출되어야 합니다."""
        semaphore = asyncio.Semaphore(5)

        op1_item = {
            "adminPttnCd": "A03",
            "locTelNo1": "02",
            "locTelNo2": "111",
            "locTelNo3": "2222",
        }

        # Supabase mock
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock()

        mock_client = MagicMock()
        mock_client.table.return_value = mock_table

        with patch(
            "src.pipeline.step2_fetch_api.fetch_op1",
            new=AsyncMock(return_value=(op1_item, "A03")),
        ):
            with patch(
                "src.pipeline.step2_fetch_api.fetch_op",
                new=AsyncMock(return_value=None),
            ):
                with patch("src.pipeline.step2_fetch_api.get_client", return_value=mock_client):
                    mock_session = MagicMock()
                    result = run_async(
                        process_facility(mock_session, "A0001", "TEST_KEY", semaphore)
                    )

        assert result is True
        mock_table.update.assert_called_once()
        # detail_fetched_at이 update 호출에 포함되어야 함
        call_args = mock_table.update.call_args[0][0]
        assert "detail_fetched_at" in call_args

    def test_invalid_facility_code_skips_api_call(self):
        """유효하지 않은 facility_code는 API 호출 없이 False를 반환해야 합니다."""
        semaphore = asyncio.Semaphore(5)

        with patch(
            "src.pipeline.step2_fetch_api.fetch_op1",
            new=AsyncMock(return_value=(None, None)),
        ) as mock_op1:
            with patch("src.pipeline.step2_fetch_api._log_pipeline_error"):
                mock_session = MagicMock()
                result = run_async(
                    process_facility(mock_session, "한글코드!!!", "TEST_KEY", semaphore)
                )

        assert result is False
        mock_op1.assert_not_called()

    def test_db_failure_returns_false(self):
        """DB 업데이트 실패 시 False를 반환하고 에러를 기록해야 합니다."""
        semaphore = asyncio.Semaphore(5)

        op1_item = {
            "adminPttnCd": "A03",
            "locTelNo1": "02",
            "locTelNo2": "111",
            "locTelNo3": "2222",
        }

        # DB 업데이트 실패 mock
        mock_table = MagicMock()
        mock_table.update.return_value.eq.return_value.execute.side_effect = Exception("DB 연결 실패")

        mock_client = MagicMock()
        mock_client.table.return_value = mock_table

        with patch(
            "src.pipeline.step2_fetch_api.fetch_op1",
            new=AsyncMock(return_value=(op1_item, "A03")),
        ):
            with patch(
                "src.pipeline.step2_fetch_api.fetch_op",
                new=AsyncMock(return_value=None),
            ):
                with patch("src.pipeline.step2_fetch_api.get_client", return_value=mock_client):
                    with patch("src.pipeline.step2_fetch_api._log_pipeline_error") as mock_log:
                        mock_session = MagicMock()
                        result = run_async(
                            process_facility(mock_session, "A0001", "TEST_KEY", semaphore)
                        )

        assert result is False
        mock_log.assert_called_once()
