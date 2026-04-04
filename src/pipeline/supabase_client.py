"""
Supabase 클라이언트 유틸리티 모듈.

S6: 시크릿 하드코딩 금지. SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY는
반드시 환경변수로 주입해야 합니다.

사용 예:
    from supabase_client import get_client

    client = get_client()
    response = client.table("nursing_homes").select("*").execute()
"""

import os
from functools import lru_cache

from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_client() -> Client:
    """환경변수에서 자격증명을 읽어 Supabase 클라이언트를 반환합니다.

    Returns:
        supabase.Client: 초기화된 Supabase 클라이언트 인스턴스.

    Raises:
        EnvironmentError: SUPABASE_URL 또는 SUPABASE_SERVICE_ROLE_KEY가
                          환경변수에 설정되지 않은 경우.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url:
        raise EnvironmentError(
            "SUPABASE_URL 환경변수가 설정되지 않았습니다. "
            ".env 파일 또는 CI/CD 시크릿을 확인하세요."
        )
    if not key:
        raise EnvironmentError(
            "SUPABASE_SERVICE_ROLE_KEY 환경변수가 설정되지 않았습니다. "
            ".env 파일 또는 CI/CD 시크릿을 확인하세요."
        )

    return create_client(url, key)
