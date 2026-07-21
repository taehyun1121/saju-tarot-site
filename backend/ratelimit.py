"""간이 in-memory rate limit (단일 인스턴스용).
무인증 엔드포인트(LLM 생성·주문 생성) 남용/비용폭탄/DoS 방지.
※ Railway 단일 인스턴스 기준. 다중 인스턴스로 확장 시 Redis 등으로 교체.
"""
import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException

_hits: dict = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # 🔒 2026-07-21: 첫 번째(leftmost) 항목은 클라이언트가 직접 X-Forwarded-For
    # 헤더에 임의값을 실어 보내면 그대로 통과되던 구멍(rate limit 전면 우회 가능).
    # Render 등 단일 리버스프록시는 실제 클라이언트 IP를 체인 맨 뒤에 append하므로
    # 신뢰 가능한 값은 마지막(rightmost) 항목이다.
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request, bucket: str, limit: int, window_sec: int):
    """bucket+IP 기준 슬라이딩 윈도우. 초과 시 429."""
    key = f"{bucket}:{_client_ip(request)}"
    now = time.time()
    dq = _hits[key]
    while dq and now - dq[0] > window_sec:
        dq.popleft()
    if len(dq) >= limit:
        raise HTTPException(429, "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.")
    dq.append(now)
    # 메모리 누수 방지: 오래된 빈 버킷 가끔 정리
    if len(_hits) > 5000:
        for k in [k for k, v in list(_hits.items()) if not v]:
            _hits.pop(k, None)
