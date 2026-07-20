"""무통장입금 주문 + RTPay 입금 웹훅 자동 매칭.

흐름: 주문 생성 → 고객이 '입금자명+매칭코드'로 입금 → 주인 폰 케이뱅크 푸시
→ RTPay 앱이 감지해 웹훅 POST → 금액+입금자명 매칭 → 자동 승인.
미매칭 입금·문의는 Discord 웹훅으로 운영자에게 알림.

⚠️ RTPay 웹훅의 실제 페이로드 스펙은 가입 후에만 제공되므로,
수신부는 원본을 raw_webhooks에 전부 보관하고 필드 추출은
RTPAY_FIELD_MAP 환경변수(JSON)로 교체 가능하게 해뒀다.
첫 실입금 1건으로 매핑을 확정할 것.
"""

import json
import os
import re
import secrets
import threading
import urllib.request
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ratelimit import rate_limit
from sqlalchemy import (Boolean, Column, DateTime, Integer, String, Text,
                        create_engine)
from sqlalchemy.orm import declarative_base, sessionmaker

router = APIRouter()

# ── DB ───────────────────────────────────────────────────────
# Railway에서는 반드시 Postgres(DATABASE_URL) 사용 — 파일시스템은 재배포 시 날아감.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./orders.db")
if DATABASE_URL.startswith("postgres://"):  # Railway 구형 스킴 보정
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

KST = timezone(timedelta(hours=9))


def now_kst():
    return datetime.now(KST)


class Order(Base):
    __tablename__ = "orders"
    id = Column(String(32), primary_key=True)
    code = Column(String(8), index=True)          # 입금자명 뒤에 붙는 매칭코드
    product_key = Column(String(32))
    product_name = Column(String(64))
    amount = Column(Integer)
    buyer_name = Column(String(64))
    contact = Column(String(128))                 # 이메일 or 카톡 등
    question = Column(Text, default="")           # 궁금한 점 (심화풀이 입력)
    status = Column(String(24), default="pending", index=True)
    # pending → deposit_claimed(입금했어요 클릭) → paid / manual_review / expired
    matched_tx = Column(Text, default="")         # 매칭된 입금 원본
    created_at = Column(DateTime(timezone=True), default=now_kst)
    updated_at = Column(DateTime(timezone=True), default=now_kst, onupdate=now_kst)


class RawWebhook(Base):
    __tablename__ = "raw_webhooks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    received_at = Column(DateTime(timezone=True), default=now_kst)
    payload = Column(Text)
    matched_order_id = Column(String(32), default="")
    processed = Column(Boolean, default=False)


Base.metadata.create_all(engine)

# ── 상품 ─────────────────────────────────────────────────────
PRODUCTS = {
    "single": {"name": "집중 심층 리포트", "amount": 15000,
               "desc": "궁금한 주제 1개를 뿌리까지 — 시기 분석 + 3~6개월 행동 지침 PDF"},
    "package": {"name": "3영역 종합 리포트", "amount": 25000,
                "desc": "연애·재물·직업 3영역 심층 + 타로 연계 해석 PDF"},
    "premium": {"name": "VIP 풀 리포트", "amount": 45000,
                "desc": "전 영역 심층 + 10년 대운 로드맵 — 소장용 고급판 PDF"},
    "compat": {"name": "궁합보기", "amount": 26000,
               "desc": "두 사람 사주로 보는 관계 궁합 — 오행 상생·상극, 시기별 관계 온도, 궁합 점수와 조언 PDF"},
    # 🔴 코코 추가(2026-07-20): 몰입 퍼널 페이월(SajuFunnelPage/TarotFunnelPage)이 이미 화면에 광고 중인 가격 그대로 등록.
    "saju4": {"name": "사주 4대운 전체 풀이", "amount": 9900,
              "desc": "대박·조심·연애·결혼 4대 운 정확 연도 + 전체 풀이 PDF"},
    "tarot_spread": {"name": "타로 스프레드 전체 풀이", "amount": 7900,
                      "desc": "뽑은 스프레드 전체 카드 뜻 + 질문 종합 풀이 PDF"},
}

# ── 계좌/알림 설정 (전부 환경변수) ────────────────────────────
BANK_NAME = os.environ.get("BANK_NAME", "케이뱅크")
BANK_ACCOUNT = os.environ.get("BANK_ACCOUNT", "")      # 미설정 시 주문 생성 차단
BANK_HOLDER = os.environ.get("BANK_HOLDER", "")
DISCORD_ORDER_WEBHOOK = os.environ.get("DISCORD_ORDER_WEBHOOK", "")
RTPAY_WEBHOOK_TOKEN = os.environ.get("RTPAY_WEBHOOK_TOKEN", "")

# ── bankapi.co.kr 계좌조회 (입금 확인용) ─────────────────────
# 무료플랜 월 500건 — 호출은 claim 시 + 60초 간격 재확인으로 절약
BANKAPI_BASE = os.environ.get("BANKAPI_BASE", "https://api.bankapi.co.kr")
BANKAPI_API_KEY = os.environ.get("BANKAPI_API_KEY", "")
BANKAPI_SECRET_KEY = os.environ.get("BANKAPI_SECRET_KEY", "")
BANKAPI_BANK_CODE = os.environ.get("BANKAPI_BANK_CODE", "")        # NH | KB | WR
BANKAPI_ACCOUNT_NUMBER = os.environ.get("BANKAPI_ACCOUNT_NUMBER", "")
BANKAPI_ACCOUNT_PASSWORD = os.environ.get("BANKAPI_ACCOUNT_PASSWORD", "")
BANKAPI_RESIDENT_PREFIX = os.environ.get("BANKAPI_RESIDENT_PREFIX", "")  # 주민번호 앞 6자리

_bankapi_last_check: dict = {}   # order_id → epoch (호출 스로틀)


def _bankapi_enabled():
    return all([BANKAPI_API_KEY, BANKAPI_SECRET_KEY, BANKAPI_BANK_CODE,
                BANKAPI_ACCOUNT_NUMBER, BANKAPI_ACCOUNT_PASSWORD, BANKAPI_RESIDENT_PREFIX])


def _bankapi_fetch_today():
    """오늘(±하루) 거래내역 조회. 실패 시 None."""
    today = now_kst()
    payload = json.dumps({
        "bankCode": BANKAPI_BANK_CODE,
        "accountNumber": BANKAPI_ACCOUNT_NUMBER.replace("-", ""),
        "accountPassword": BANKAPI_ACCOUNT_PASSWORD,
        "residentNumber": BANKAPI_RESIDENT_PREFIX,
        "startDate": (today - timedelta(days=1)).strftime("%Y%m%d"),
        "endDate": today.strftime("%Y%m%d"),
    }).encode()
    req = urllib.request.Request(
        f"{BANKAPI_BASE}/v1/transactions", data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {BANKAPI_API_KEY}:{BANKAPI_SECRET_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            data = json.loads(res.read().decode())
    except Exception as e:
        print(f"[bankapi] 조회 실패: {e}")
        return None
    if not data.get("success"):
        print(f"[bankapi] 오류 응답: {data.get('error')} {data.get('message')}")
        return None
    return data.get("transactions", [])


def _check_bankapi(db, order, throttle_sec=60):
    """bankapi 거래내역에서 이 주문의 입금을 찾아 승인. 성공 시 True."""
    import time
    if not _bankapi_enabled():
        return False
    last = _bankapi_last_check.get(order.id, 0)
    if time.time() - last < throttle_sec:
        return False
    _bankapi_last_check[order.id] = time.time()

    txs = _bankapi_fetch_today()
    if txs is None:
        return False
    for tx in txs:
        if tx.get("type") != "deposit":
            continue
        try:
            amount = int(tx.get("amount") or 0)
        except (TypeError, ValueError):
            continue
        if amount != order.amount:
            continue
        name = re.sub(r"\s", "", f"{tx.get('displayName','')}{tx.get('counterparty','')}")
        buyer = re.sub(r"\s", "", order.buyer_name or "")
        if (order.code and order.code in name) or (buyer and buyer in name):
            _approve(db, order, json.dumps(tx, ensure_ascii=False))
            return True
    return False

# RTPay 페이로드 필드 매핑 — 실스펙 확인 후 환경변수로 교정
# 기본값은 흔한 키 후보들을 순서대로 시도
DEFAULT_FIELD_CANDIDATES = {
    "name": ["name", "in_name", "depositor", "print_content", "content", "memo"],
    "amount": ["amount", "in_amount", "money", "price", "input_amount"],
    "type": ["type", "in_out", "gubun", "flag"],
}
try:
    FIELD_MAP = json.loads(os.environ.get("RTPAY_FIELD_MAP", "{}"))
except json.JSONDecodeError:
    FIELD_MAP = {}


def _extract(payload: dict, kind: str):
    """FIELD_MAP 우선, 없으면 후보 키 순회로 값 추출."""
    if kind in FIELD_MAP and FIELD_MAP[kind] in payload:
        return payload[FIELD_MAP[kind]]
    for key in DEFAULT_FIELD_CANDIDATES.get(kind, []):
        if key in payload:
            return payload[key]
    return None


def _discord_notify(content: str):
    """운영자 Discord 알림 (실패해도 주문 흐름은 계속)."""
    if not DISCORD_ORDER_WEBHOOK:
        return
    def _send():
        try:
            req = urllib.request.Request(
                DISCORD_ORDER_WEBHOOK,
                data=json.dumps({"content": content}).encode(),
                headers={"Content-Type": "application/json",
                         "User-Agent": "saju-order-bot/1.0"},
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


# ── 매칭 엔진 ─────────────────────────────────────────────────
def _try_match(db, tx_name: str, tx_amount: int, raw: str):
    """입금자명·금액으로 대기 주문 매칭. 성공 시 Order 반환."""
    if not tx_name or not tx_amount:
        return None
    candidates = (
        db.query(Order)
        .filter(Order.status.in_(["pending", "deposit_claimed"]),
                Order.amount == tx_amount)
        .order_by(Order.created_at.desc())
        .all()
    )
    tx_name_norm = re.sub(r"\s", "", str(tx_name))
    for order in candidates:
        # 1순위: 매칭코드 포함 (입금자명 규칙: 이름+코드)
        if order.code and order.code in tx_name_norm:
            return order
        # 2순위: 금액 유일 + 이름 일치
        name_norm = re.sub(r"\s", "", order.buyer_name or "")
        if name_norm and name_norm in tx_name_norm and len(candidates) == 1:
            return order
    return None


def _approve(db, order: Order, raw: str):
    order.status = "paid"
    order.matched_tx = raw[:2000]
    db.commit()
    _discord_notify(
        f"✅ **입금 확인 — 자동 승인**\n"
        f"주문 `{order.id}` | {order.product_name} ₩{order.amount:,}\n"
        f"입금자: {order.buyer_name} (코드 {order.code}) | 연락처: {order.contact}\n"
        f"→ 심화풀이 전달 필요"
    )


# ── API ──────────────────────────────────────────────────────
class OrderCreate(BaseModel):
    product: str
    buyer_name: str
    contact: str
    question: str = ""


@router.post("/api/orders")
def create_order(body: OrderCreate, request: Request):
    rate_limit(request, "order", limit=8, window_sec=300)   # IP당 5분 8건 — 스팸·DB팽창 방지
    if body.product not in PRODUCTS:
        raise HTTPException(400, "알 수 없는 상품입니다")
    if not BANK_ACCOUNT:
        raise HTTPException(503, "입금 계좌가 아직 설정되지 않았습니다")
    name = body.buyer_name.strip()
    if not name or len(name) > 20:
        raise HTTPException(400, "입금자명을 확인해주세요")
    if not body.contact.strip():
        raise HTTPException(400, "결과를 받을 연락처를 입력해주세요")

    product = PRODUCTS[body.product]
    order = Order(
        id=secrets.token_hex(8),
        code=str(secrets.randbelow(9000) + 1000),   # 1000~9999
        product_key=body.product,
        product_name=product["name"],
        amount=product["amount"],
        buyer_name=name,
        contact=body.contact.strip()[:128],
        question=body.question.strip()[:2000],
    )
    with SessionLocal() as db:
        db.add(order)
        db.commit()
        return {
            "order_id": order.id,
            "amount": order.amount,
            "product_name": order.product_name,
            "bank": BANK_NAME,
            "account": BANK_ACCOUNT,
            "holder": BANK_HOLDER,
            "deposit_name": f"{name}{order.code}",
            "notice": "입금자명을 반드시 위 형식으로 입력해주세요. 금액이 다르면 자동 확인이 안 됩니다.",
        }


@router.get("/api/orders/{order_id}")
def get_order(order_id: str):
    with SessionLocal() as db:
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(404, "주문을 찾을 수 없습니다")
        # 입금 확인 대기 중이면 60초 간격으로 bankapi 재확인 (프론트 폴링에 편승)
        if order.status == "deposit_claimed":
            _check_bankapi(db, order)
        return {"order_id": order.id, "status": order.status,
                "product_name": order.product_name, "amount": order.amount}


@router.post("/api/orders/{order_id}/claim")
def claim_deposit(order_id: str):
    """고객이 '입금했어요' 클릭 — 이미 도착한 웹훅과 재대조 후 대기 전환."""
    with SessionLocal() as db:
        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(404, "주문을 찾을 수 없습니다")
        if order.status == "paid":
            return {"status": "paid"}

        # 웹훅이 먼저 도착했을 수 있으니 최근 미처리분과 재대조
        recent = (
            db.query(RawWebhook)
            .filter(RawWebhook.processed.is_(False))
            .order_by(RawWebhook.id.desc()).limit(50).all()
        )
        for hook in recent:
            try:
                payload = json.loads(hook.payload)
            except json.JSONDecodeError:
                continue
            tx_name = _extract(payload, "name")
            try:
                tx_amount = int(re.sub(r"[^\d]", "", str(_extract(payload, "amount") or "")) or 0)
            except ValueError:
                tx_amount = 0
            matched = _try_match(db, tx_name, tx_amount, hook.payload)
            if matched and matched.id == order.id:
                hook.processed = True
                hook.matched_order_id = order.id
                _approve(db, order, hook.payload)
                return {"status": "paid"}

        # 웹훅에 없으면 bankapi 계좌조회로 직접 확인
        if _check_bankapi(db, order, throttle_sec=0):
            return {"status": "paid"}

        order.status = "deposit_claimed"
        db.commit()
        _discord_notify(
            f"🔔 **입금 확인 요청** (아직 웹훅 미도착)\n"
            f"주문 `{order.id}` | {order.product_name} ₩{order.amount:,}\n"
            f"입금자명(예정): {order.buyer_name}{order.code} | 연락처: {order.contact}\n"
            f"→ 몇 분 내 웹훅 오면 자동 승인, 안 오면 수동 확인 필요"
        )
        return {"status": "deposit_claimed",
                "message": "입금 확인 중입니다. 확인되는 대로 처리됩니다 (보통 1~2분)."}


@router.post("/api/webhook/rtpay")
async def rtpay_webhook(request: Request, token: str = ""):
    """RTPay 입금 알림 수신. 원본 무조건 보관 → 필드 추출 → 매칭."""
    # 🔒 토큰 필수(fail-closed): 미설정이면 웹훅 자체를 거부 → 위조 입금 자동승인 차단.
    #    토큰은 헤더(X-Webhook-Token) 우선, 쿼리(?token=)는 폴백(로그 유출 위험). 상수시간 비교로 타이밍공격 차단.
    if not RTPAY_WEBHOOK_TOKEN:
        raise HTTPException(503, "webhook not configured")
    supplied = request.headers.get("X-Webhook-Token") or token
    if not supplied or not secrets.compare_digest(str(supplied), RTPAY_WEBHOOK_TOKEN):
        raise HTTPException(403, "invalid token")

    body_bytes = await request.body()
    raw = body_bytes.decode("utf-8", errors="replace")[:4000]

    # JSON이 아니어도(폼 등) 원본은 남긴다
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            payload = {}
    except json.JSONDecodeError:
        try:
            form = await request.form()
            payload = dict(form)
            raw = json.dumps(payload, ensure_ascii=False)[:4000]
        except Exception:
            payload = {}

    with SessionLocal() as db:
        hook = RawWebhook(payload=raw)
        db.add(hook)
        db.commit()

        tx_type = str(_extract(payload, "type") or "")
        if tx_type and any(k in tx_type for k in ("출금", "out", "OUT")):
            hook.processed = True
            db.commit()
            return {"ok": True, "result": "ignored_withdrawal"}

        tx_name = _extract(payload, "name")
        try:
            tx_amount = int(re.sub(r"[^\d]", "", str(_extract(payload, "amount") or "")) or 0)
        except ValueError:
            tx_amount = 0

        matched = _try_match(db, tx_name, tx_amount, raw)
        if matched:
            hook.processed = True
            hook.matched_order_id = matched.id
            _approve(db, matched, raw)
            return {"ok": True, "result": "matched", "order_id": matched.id}

        _discord_notify(
            f"⚠️ **미매칭 입금 감지**\n"
            f"입금자: `{tx_name}` | 금액: ₩{tx_amount:,}\n"
            f"대기 주문과 자동 매칭 실패 — 수동 확인 필요 (raw #{hook.id})"
        )
        return {"ok": True, "result": "unmatched"}
