"""
step2_fetch_api.py — 전국 요양원 데이터 파이프라인 Step 2

nursing_homes 테이블에서 미완료 시설 목록을 가져와
B550928 공공데이터 API 5개 OP를 순차 호출한 뒤 상세 정보를 업데이트합니다.

환경변수:
    SUPABASE_URL                Supabase 프로젝트 URL (필수)
    SUPABASE_SERVICE_ROLE_KEY   서비스 롤 키 (필수)
    PUBLIC_DATA_API_KEY         B550928 공공데이터 API 디코딩 키 (필수)
    TEST_MODE                   'true' 설정 시 5건만 처리
    OFFSET                      분할 실행 시 시작 오프셋 (기본값: 0)
    DAILY_LIMIT                 1회 실행당 최대 처리 건수 (기본값: 5000)

보안:
    S6: 시크릿 하드코딩 금지. 환경변수로만 주입.
    S7: facility_code 형식 검증 후 사용. SQL은 supabase-py parameterized query 사용.

API:
    B550928 getLtcInsttDetailInfoService02
    Base URL: https://apis.data.go.kr/B550928/getLtcInsttDetailInfoService02
"""

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Optional
from urllib.parse import urlencode

import aiohttp
import xmltodict

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
BASE_URL = "https://apis.data.go.kr/B550928/getLtcInsttDetailInfoService02"

ENDPOINTS: dict[str, str] = {
    "op1": "/getGeneralSttusDetailInfoItem02",
    "op2": "/getAceptncNmprDetailInfoItem02",
    "op3": "/getNonBenefitSttusDetailInfoList02",
    "op4": "/getStaffSttusDetailInfoItem02",
    "op5": "/getInsttEtcDetailInfoItem02",
}

# adminPttnCd 폴백 순서 (OP1 실패 시 순서대로 시도)
ADMIN_PTTN_FALLBACK: list[str] = ["A03", "A01", "A04", "B03", "C06"]

# 지수 백오프 대기 시간 (초): 5 → 15 → 45 → 135
BACKOFF_DELAYS: list[int] = [5, 15, 45, 135]

# 동시 처리 세마포어 최대값 (절대 10 이상 사용 금지)
MAX_CONCURRENCY = 5

# facility_code 형식 검증 정규식 (S7): 영문·숫자·하이픈 조합, 1~20자
FACILITY_CODE_PATTERN = re.compile(r"^[A-Za-z0-9\-]{1,20}$")

# 스키마 레퍼런스 저장 경로
SCHEMA_REFERENCE_PATH = os.path.join(
    os.path.dirname(__file__), "schemas", "step2_api_reference.json"
)

# 전역: OP별 스키마 레퍼런스 저장 여부
_saved_ops: set[str] = set()


# ---------------------------------------------------------------------------
# 입력 검증 (S7)
# ---------------------------------------------------------------------------


def validate_facility_code(facility_code: str) -> bool:
    """facility_code 형식을 검증합니다.

    Args:
        facility_code: 검증할 시설 코드.

    Returns:
        유효하면 True, 그렇지 않으면 False.
    """
    if not facility_code or not isinstance(facility_code, str):
        return False
    return bool(FACILITY_CODE_PATTERN.match(facility_code.strip()))


# ---------------------------------------------------------------------------
# API 호출 공통 유틸리티
# ---------------------------------------------------------------------------


def _build_url(endpoint: str, params: dict[str, Any]) -> str:
    """API URL을 조립합니다.

    Args:
        endpoint: 엔드포인트 경로 (예: '/getGeneralSttusDetailInfoItem02').
        params: 쿼리 파라미터 딕셔너리.

    Returns:
        완성된 URL 문자열.
    """
    return f"{BASE_URL}{endpoint}?{urlencode(params)}"


def _parse_xml_response(xml_text: str) -> Optional[dict[str, Any]]:
    """XML 응답을 dict로 파싱합니다.

    Args:
        xml_text: 원시 XML 문자열.

    Returns:
        파싱된 dict 또는 None (파싱 실패 시).
    """
    try:
        return xmltodict.parse(xml_text)
    except Exception as exc:  # noqa: BLE001
        logger.error("XML 파싱 실패: %s", exc)
        return None


def _extract_item(parsed: dict[str, Any]) -> Optional[Any]:
    """파싱된 dict에서 response > body > items > item을 추출합니다.

    Args:
        parsed: xmltodict.parse() 결과.

    Returns:
        item 값 (dict, list, None).
    """
    try:
        items = parsed["response"]["body"]["items"]
        if not items:
            return None
        item = items.get("item")
        return item
    except (KeyError, TypeError):
        return None


def _check_result_code(parsed: dict[str, Any]) -> bool:
    """API 응답 결과 코드가 정상(00)인지 확인합니다.

    Args:
        parsed: xmltodict.parse() 결과.

    Returns:
        정상이면 True.
    """
    try:
        code = parsed["response"]["header"]["resultCode"]
        return str(code) == "00"
    except (KeyError, TypeError):
        return False


# ---------------------------------------------------------------------------
# 스키마 레퍼런스 저장 및 변경 감지
# ---------------------------------------------------------------------------


def _save_schema_reference(op_name: str, item: dict[str, Any]) -> None:
    """최초 성공 응답의 키 목록을 JSON 파일로 저장합니다.

    Args:
        op_name: 오퍼레이션 이름 (예: 'op1').
        item: API 응답 item dict.
    """
    global _saved_ops

    if op_name in _saved_ops:
        return

    # 기존 레퍼런스가 있으면 로드하여 비교
    existing: dict[str, Any] = {}
    if os.path.exists(SCHEMA_REFERENCE_PATH):
        try:
            with open(SCHEMA_REFERENCE_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:  # noqa: BLE001
            pass

    # item이 list인 경우 첫 번째 원소 사용
    sample = item[0] if isinstance(item, list) else item
    current_keys = sorted(sample.keys()) if isinstance(sample, dict) else []

    ref_entry = {op_name: current_keys}

    # 변경 감지
    if op_name in existing:
        prev_keys = existing[op_name]
        added = set(current_keys) - set(prev_keys)
        removed = set(prev_keys) - set(current_keys)
        if added:
            logger.warning("API 스키마 변경 감지 — %s 새로운 키: %s", op_name, added)
        if removed:
            logger.warning("API 스키마 변경 감지 — %s 사라진 키: %s", op_name, removed)

    # 저장
    existing.update(ref_entry)
    try:
        os.makedirs(os.path.dirname(SCHEMA_REFERENCE_PATH), exist_ok=True)
        with open(SCHEMA_REFERENCE_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        logger.info("스키마 레퍼런스 저장 완료 (%s): %s", op_name, SCHEMA_REFERENCE_PATH)
        _saved_ops.add(op_name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("스키마 레퍼런스 저장 실패: %s", exc)


# ---------------------------------------------------------------------------
# 비급여 정보 전처리 (OP3)
# ---------------------------------------------------------------------------


def parse_nonbenefit_items(
    item: Any,
) -> dict[str, Optional[int]]:
    """비급여(OP3) 응답 item을 파싱하여 meal/room 비용을 추출합니다.

    nonpayKind 코드 매핑:
        1 (식재료비) + 5 (간식비) → sum → meal_cost_per_day
        2 (1인실 추가비용) → room_cost_1person
        6 (2인실 추가비용) → room_cost_2person

    Args:
        item: OP3 응답 item (dict 또는 list 모두 처리).

    Returns:
        {'meal_cost_per_day': int|None, 'room_cost_1person': int|None, 'room_cost_2person': int|None}
    """
    # item을 항상 리스트로 정규화
    items_list: list[dict[str, Any]]
    if isinstance(item, dict):
        items_list = [item]
    elif isinstance(item, list):
        items_list = item
    else:
        return {
            "meal_cost_per_day": None,
            "room_cost_1person": None,
            "room_cost_2person": None,
        }

    meal_cost_sum = 0
    meal_found = False
    room_cost_1: Optional[int] = None
    room_cost_2: Optional[int] = None

    for entry in items_list:
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get("nonpayKind", "")).strip()
        try:
            amount = int(entry.get("nonpayTgtAmt") or 0)
        except (ValueError, TypeError):
            amount = 0

        if kind in ("1", "5"):
            meal_cost_sum += amount
            meal_found = True
        elif kind == "2":
            room_cost_1 = amount
        elif kind == "6":
            room_cost_2 = amount

    return {
        "meal_cost_per_day": meal_cost_sum if meal_found else None,
        "room_cost_1person": room_cost_1,
        "room_cost_2person": room_cost_2,
    }


# ---------------------------------------------------------------------------
# 전화번호 조합
# ---------------------------------------------------------------------------


def assemble_phone(v1: Optional[str], v2: Optional[str], v3: Optional[str]) -> Optional[str]:
    """전화번호 세 부분을 조합합니다.

    Args:
        v1: 지역번호 (locTelNo1).
        v2: 국번 (locTelNo2).
        v3: 번호 (locTelNo3).

    Returns:
        'v1-v2-v3' 형식의 전화번호 또는 None (부분 누락 시).
    """
    if not v1 or not v2 or not v3:
        return None
    v1 = str(v1).strip()
    v2 = str(v2).strip()
    v3 = str(v3).strip()
    if not v1 or not v2 or not v3:
        return None
    return f"{v1}-{v2}-{v3}"


# ---------------------------------------------------------------------------
# API 호출 (지수 백오프 포함)
# ---------------------------------------------------------------------------


class RateLimitError(Exception):
    """429/503 응답으로 모든 재시도가 실패했음을 나타냅니다."""


async def _fetch_with_backoff(
    session: aiohttp.ClientSession,
    url: str,
    facility_code: str,
    op_name: str,
) -> Optional[str]:
    """지수 백오프를 적용하여 URL을 GET으로 요청합니다.

    429/503 응답 시 5s → 15s → 45s → 135s 대기 후 재시도합니다.

    Args:
        session: aiohttp 클라이언트 세션.
        url: 요청 URL.
        facility_code: 로깅용 시설 코드.
        op_name: 로깅용 오퍼레이션 이름.

    Returns:
        응답 텍스트 또는 None (모든 재시도 실패 시).

    Raises:
        RateLimitError: 429/503 응답으로 모든 재시도가 실패한 경우.
    """
    hit_rate_limit = False
    for attempt, delay in enumerate(BACKOFF_DELAYS):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status in (429, 503):
                    hit_rate_limit = True
                    logger.warning(
                        "%s — HTTP %d, %ds 대기 후 재시도 (attempt=%d)",
                        facility_code, resp.status, delay, attempt + 1,
                    )
                    await asyncio.sleep(delay)
                    continue
                if resp.status != 200:
                    logger.error(
                        "%s — %s HTTP 오류: %d", facility_code, op_name, resp.status
                    )
                    return None
                return await resp.text(encoding="utf-8")
        except asyncio.TimeoutError:
            logger.warning("%s — %s 타임아웃, %ds 대기", facility_code, op_name, delay)
            await asyncio.sleep(delay)
        except Exception as exc:  # noqa: BLE001
            logger.error("%s — %s 네트워크 오류: %s", facility_code, op_name, exc)
            await asyncio.sleep(delay)

    logger.error("%s — %s 모든 재시도 실패", facility_code, op_name)
    if hit_rate_limit:
        raise RateLimitError(f"{facility_code} — {op_name} rate limited")
    return None


# ---------------------------------------------------------------------------
# OP1: 기관 일반정보 (adminPttnCd 탐색 포함)
# ---------------------------------------------------------------------------


async def fetch_op1(
    session: aiohttp.ClientSession,
    facility_code: str,
    api_key: str,
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """OP1 — 기관일반정보를 조회하고 adminPttnCd를 반환합니다.

    adminPttnCd 없이 먼저 호출하고, 실패 시 ADMIN_PTTN_FALLBACK 순서로 재시도합니다.

    Args:
        session: aiohttp 클라이언트 세션.
        facility_code: 시설 코드.
        api_key: 공공데이터 API 키.

    Returns:
        (item dict, adminPttnCd 문자열) 또는 (None, None) 실패 시.
    """
    base_params = {
        "serviceKey": api_key,
        "numOfRows": 10,
        "pageNo": 1,
        "ltcInsttCd": facility_code,
    }

    # 1차 시도: adminPttnCd 없이
    url = _build_url(ENDPOINTS["op1"], base_params)
    xml_text = await _fetch_with_backoff(session, url, facility_code, "op1")

    if xml_text:
        parsed = _parse_xml_response(xml_text)
        if parsed and _check_result_code(parsed):
            item = _extract_item(parsed)
            if item:
                admin_cd = None
                if isinstance(item, dict):
                    admin_cd = item.get("adminPttnCd")
                elif isinstance(item, list) and item:
                    admin_cd = item[0].get("adminPttnCd")
                logger.debug("%s — OP1 성공 (adminPttnCd=%s)", facility_code, admin_cd)
                _save_schema_reference("op1", item)
                return item, admin_cd

    # 2차 시도: ADMIN_PTTN_FALLBACK 순서대로
    for fallback_cd in ADMIN_PTTN_FALLBACK:
        params = {**base_params, "adminPttnCd": fallback_cd}
        url = _build_url(ENDPOINTS["op1"], params)
        xml_text = await _fetch_with_backoff(session, url, facility_code, f"op1-fallback-{fallback_cd}")

        if not xml_text:
            continue

        parsed = _parse_xml_response(xml_text)
        if parsed and _check_result_code(parsed):
            item = _extract_item(parsed)
            if item:
                logger.info(
                    "%s — OP1 폴백 성공 (adminPttnCd=%s)", facility_code, fallback_cd
                )
                _save_schema_reference("op1", item)
                return item, fallback_cd

    logger.error("%s — OP1 모든 시도 실패", facility_code)
    return None, None


# ---------------------------------------------------------------------------
# OP2~OP5: 세부 정보 조회
# ---------------------------------------------------------------------------


async def fetch_op(
    session: aiohttp.ClientSession,
    op_key: str,
    facility_code: str,
    api_key: str,
    admin_pttn_cd: Optional[str] = None,
) -> Optional[Any]:
    """OP2~OP5 단일 엔드포인트를 호출합니다.

    Args:
        session: aiohttp 클라이언트 세션.
        op_key: 오퍼레이션 키 ('op2', 'op3', 'op4', 'op5').
        facility_code: 시설 코드.
        api_key: 공공데이터 API 키.
        admin_pttn_cd: 기관유형코드 (None이면 파라미터 미포함).

    Returns:
        item 값 (dict or list) 또는 None.
    """
    params: dict[str, Any] = {
        "serviceKey": api_key,
        "numOfRows": 10,
        "pageNo": 1,
        "ltcInsttCd": facility_code,
    }
    if admin_pttn_cd:
        params["adminPttnCd"] = admin_pttn_cd

    url = _build_url(ENDPOINTS[op_key], params)
    xml_text = await _fetch_with_backoff(session, url, facility_code, op_key)

    if not xml_text:
        return None

    parsed = _parse_xml_response(xml_text)
    if not parsed or not _check_result_code(parsed):
        logger.warning("%s — %s 응답 오류", facility_code, op_key)
        return None

    item = _extract_item(parsed)
    if item is not None:
        _save_schema_reference(op_key, item)

    return item


# ---------------------------------------------------------------------------
# 단일 시설 전체 처리
# ---------------------------------------------------------------------------


async def process_facility(
    session: aiohttp.ClientSession,
    facility_code: str,
    api_key: str,
    semaphore: asyncio.Semaphore,
) -> tuple[bool, bool]:
    """단일 시설에 대해 OP1~OP4를 호출하고 DB를 업데이트합니다.

    OP1~OP4 모두 성공 시에만 detail_fetched_at을 설정합니다 (원자적 업데이트).
    OP5는 현재 DB 컬럼이 없으므로 호출하지 않습니다.

    Args:
        session: aiohttp 클라이언트 세션.
        facility_code: 시설 코드.
        api_key: 공공데이터 API 키.
        semaphore: 동시 처리 세마포어.

    Returns:
        (성공 여부, HTTP 429 발생 여부) 튜플.
    """
    async with semaphore:
        # S7: facility_code 형식 검증
        if not validate_facility_code(facility_code):
            logger.error("유효하지 않은 facility_code 형식: %s", facility_code)
            _log_pipeline_error(
                facility_code=facility_code,
                step="step2",
                error_message=f"유효하지 않은 facility_code 형식: {facility_code}",
            )
            return False, False

        try:
            return await _process_facility_ops(session, facility_code, api_key)
        except RateLimitError:
            logger.warning("%s — 429/503 rate limit으로 실패", facility_code)
            _log_pipeline_error(
                facility_code=facility_code,
                step="step2",
                error_message="429/503 rate limit 초과",
            )
            return False, True


async def _process_facility_ops(
    session: aiohttp.ClientSession,
    facility_code: str,
    api_key: str,
) -> tuple[bool, bool]:
    """process_facility 내부 로직. RateLimitError를 전파합니다."""
    logger.info("처리 시작: %s", facility_code)
    update_data: dict[str, Any] = {}

    # OP1: 기관일반정보 + adminPttnCd 탐색
    op1_item, admin_pttn_cd = await fetch_op1(session, facility_code, api_key)
    if op1_item is None:
        error_msg = f"OP1 실패: facility_code={facility_code}"
        logger.error(error_msg)
        _log_pipeline_error(facility_code=facility_code, step="step2", error_message=error_msg)
        return False, False

    # 전화번호 조합
    if isinstance(op1_item, dict):
        phone = assemble_phone(
            op1_item.get("locTelNo1"),
            op1_item.get("locTelNo2"),
            op1_item.get("locTelNo3"),
        )
    else:
        phone = None
    if phone:
        update_data["phone"] = phone

    # OP2: 입소인원정보 (필수)
    op2_item = await fetch_op(session, "op2", facility_code, api_key, admin_pttn_cd)
    if op2_item is None:
        error_msg = f"OP2 실패: facility_code={facility_code}"
        logger.error(error_msg)
        _log_pipeline_error(facility_code=facility_code, step="step2", error_message=error_msg)
        return False, False
    if isinstance(op2_item, dict):
        try:
            cap = op2_item.get("instlPsncnt")
            occ = op2_item.get("nowPsncnt")
            if cap is not None:
                update_data["capacity"] = int(cap)
            if occ is not None:
                update_data["current_occupancy"] = int(occ)
        except (ValueError, TypeError) as exc:
            logger.warning("%s — OP2 숫자 변환 실패: %s", facility_code, exc)

    # OP3: 비급여정보 (필수)
    op3_item = await fetch_op(session, "op3", facility_code, api_key, admin_pttn_cd)
    if op3_item is None:
        error_msg = f"OP3 실패: facility_code={facility_code}"
        logger.error(error_msg)
        _log_pipeline_error(facility_code=facility_code, step="step2", error_message=error_msg)
        return False, False
    nonbenefit = parse_nonbenefit_items(op3_item)
    for key, val in nonbenefit.items():
        if val is not None:
            update_data[key] = val

    # OP4: 인력정보 (필수)
    op4_item = await fetch_op(session, "op4", facility_code, api_key, admin_pttn_cd)
    if op4_item is None:
        error_msg = f"OP4 실패: facility_code={facility_code}"
        logger.error(error_msg)
        _log_pipeline_error(facility_code=facility_code, step="step2", error_message=error_msg)
        return False, False
    if isinstance(op4_item, dict):
        try:
            cgr = op4_item.get("crgrPsncnt")
            if cgr is not None:
                update_data["caregiver_count"] = int(cgr)
        except (ValueError, TypeError) as exc:
            logger.warning("%s — OP4 숫자 변환 실패: %s", facility_code, exc)

    # 원자적 업데이트: OP1~OP4 모두 성공 시에만 detail_fetched_at 설정
    update_data["detail_fetched_at"] = "now()"

    # DB 업데이트 (supabase-py parameterized upsert — S7)
    try:
        client = get_client()
        client.table("nursing_homes").update(update_data).eq(
            "facility_code", facility_code
        ).execute()
        logger.info("%s — DB 업데이트 완료: %s", facility_code, list(update_data.keys()))
        return True, False
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)
        logger.error("%s — DB 업데이트 실패: %s", facility_code, error_msg)
        _log_pipeline_error(
            facility_code=facility_code,
            step="step2",
            error_message=f"DB 업데이트 실패: {error_msg}",
        )
        return False, False


# ---------------------------------------------------------------------------
# 오류 로깅
# ---------------------------------------------------------------------------


def _log_pipeline_error(
    facility_code: str,
    step: str,
    error_message: str,
) -> None:
    """pipeline_errors 테이블에 오류를 기록합니다.

    Args:
        facility_code: 오류 발생 시설 코드.
        step: 파이프라인 단계명 (e.g., 'step2').
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


# ---------------------------------------------------------------------------
# 정합성 검증
# ---------------------------------------------------------------------------


def verify_data_integrity() -> None:
    """step2 완료 후 detail_fetched_at 기준 성공률을 검증합니다.

    95% 이상 성공 시 정상으로 판단합니다.
    """
    client = get_client()
    table = client.table("nursing_homes")

    try:
        total_result = table.select("id", count="exact").execute()
        total = total_result.count or 0

        fetched_result = (
            table.select("id", count="exact")
            .not_.is_("detail_fetched_at", "null")
            .execute()
        )
        fetched = fetched_result.count or 0

        if total == 0:
            logger.warning("정합성 검증 — 레코드 없음")
            return

        ratio = fetched / total * 100
        logger.info(
            "정합성 검증 — total=%d, fetched=%d, ratio=%.1f%%",
            total, fetched, ratio,
        )

        if ratio < 95.0:
            logger.warning(
                "정합성 경고: detail_fetched_at 완료율 %.1f%% (기준: 95%%)", ratio
            )
        else:
            logger.info("정합성 검증 통과: %.1f%%", ratio)

    except Exception as exc:  # noqa: BLE001
        logger.error("정합성 검증 실패: %s", exc)


# ---------------------------------------------------------------------------
# 시설 목록 조회
# ---------------------------------------------------------------------------


def fetch_pending_facilities(
    offset: int = 0,
    limit: int = 5000,
    test_mode: bool = False,
) -> list[str]:
    """detail_fetched_at이 NULL인 시설 코드 목록을 조회합니다.

    Args:
        offset: 시작 오프셋 (4일 분할 실행용).
        limit: 최대 반환 건수.
        test_mode: True이면 5건으로 제한.

    Returns:
        facility_code 리스트.
    """
    actual_limit = 5 if test_mode else limit
    client = get_client()

    try:
        result = (
            client.table("nursing_homes")
            .select("facility_code")
            .is_("detail_fetched_at", "null")
            .range(offset, offset + actual_limit - 1)
            .execute()
        )
        codes = [row["facility_code"] for row in (result.data or [])]
        logger.info(
            "미처리 시설 목록 조회: offset=%d, limit=%d, 결과=%d건",
            offset, actual_limit, len(codes),
        )
        return codes
    except Exception as exc:  # noqa: BLE001
        logger.error("시설 목록 조회 실패: %s", exc)
        return []


# ---------------------------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------------------------


async def run() -> None:
    """step2 메인 실행 함수.

    1. 환경변수 로드
    2. 미처리 시설 목록 조회
    3. aiohttp 세션으로 비동기 API 호출
    4. DB 업데이트
    5. 정합성 검증
    """
    api_key = os.environ.get("PUBLIC_DATA_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "PUBLIC_DATA_API_KEY 환경변수가 설정되지 않았습니다. "
            ".env 파일 또는 CI/CD 시크릿을 확인하세요."
        )

    test_mode = os.environ.get("TEST_MODE", "").lower() == "true"
    offset = int(os.environ.get("OFFSET", "0"))
    daily_limit = int(os.environ.get("DAILY_LIMIT", "5000"))

    if test_mode:
        logger.info("TEST_MODE 활성화: 5건만 처리합니다")

    # 1. 미처리 시설 목록 조회
    facility_codes = fetch_pending_facilities(
        offset=offset,
        limit=daily_limit,
        test_mode=test_mode,
    )

    if not facility_codes:
        logger.info("처리할 시설이 없습니다. 종료합니다.")
        return

    logger.info("처리 대상: %d건 (offset=%d)", len(facility_codes), offset)

    # 2. 비동기 처리
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    success_count = 0
    error_count = 0

    consecutive_429_count = 0
    MAX_CONSECUTIVE_429 = 10  # 연속 429 시 자동 중단 임계값

    async with aiohttp.ClientSession() as session:
        tasks = [
            process_facility(session, code, api_key, semaphore)
            for code in facility_codes
        ]

        for coro in asyncio.as_completed(tasks):
            try:
                success, was_rate_limited = await coro
                if success:
                    success_count += 1
                    consecutive_429_count = 0
                else:
                    error_count += 1
                    if was_rate_limited:
                        consecutive_429_count += 1
                    else:
                        consecutive_429_count = 0
            except Exception as exc:  # noqa: BLE001
                logger.error("처리 중 예외 발생: %s", exc)
                error_count += 1

            # 일일 제한 자동 중단
            if consecutive_429_count >= MAX_CONSECUTIVE_429:
                logger.warning(
                    "연속 %d회 실패. 일일 제한 도달 가능성. 조기 종료합니다.",
                    MAX_CONSECUTIVE_429,
                )
                break

    logger.info(
        "step2 완료 — 성공: %d건, 실패: %d건", success_count, error_count
    )

    # 3. 정합성 검증
    verify_data_integrity()


if __name__ == "__main__":
    asyncio.run(run())
