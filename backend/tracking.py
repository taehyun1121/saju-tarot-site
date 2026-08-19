"""크몽 전환 퍼널 클릭 트래킹 (2026-08-19, 소셜봇 요청 + 형 ㄱㄱ).

크몽은 개인 판매자용 공개 API가 없어 "사이트에서 크몽으로 몇 명이 실제로 넘어갔는지"를
크몽 쪽 데이터로는 확인할 수 없다(catalog R 0단계 진단이 계속 감(感)으로 머무는 원인).
그래서 크몽으로 넘어가기 직전에 우리 쪽에서 먼저 1건 기록한다 — UTM은 크몽이 실제로
그 값을 노출해줄지 불확실하지만, 이 로그는 100% 우리 소유라 확실하다.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, func

from orders import Base, SessionLocal, engine, now_kst

router = APIRouter()

KST = timezone(timedelta(hours=9))


class KmongClick(Base):
    __tablename__ = "kmong_clicks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    position = Column(String(32))      # "strip_banner" | "result_cta"
    gig_id = Column(String(16))        # "734044" | "778578"
    referrer = Column(String(256), default="")
    created_at = Column(DateTime(timezone=True), default=now_kst)


Base.metadata.create_all(engine)  # 신규 테이블만 생성(idempotent) — 기존 orders 테이블엔 영향 없음


class ClickIn(BaseModel):
    position: str
    gig_id: str
    referrer: str = ""


@router.post("/api/track/kmong-click")
def track_kmong_click(body: ClickIn):
    db = SessionLocal()
    try:
        db.add(KmongClick(position=body.position[:32], gig_id=body.gig_id[:16],
                           referrer=(body.referrer or "")[:256]))
        db.commit()
    finally:
        db.close()
    return {"ok": True}


@router.get("/api/track/kmong-click/summary")
def kmong_click_summary():
    """position·gig_id별 클릭수 + 최근 7일 합계 — 소셜봇/형이 curl 하나로 확인용."""
    db = SessionLocal()
    try:
        by_position = (
            db.query(KmongClick.position, KmongClick.gig_id, func.count(KmongClick.id))
            .group_by(KmongClick.position, KmongClick.gig_id)
            .all()
        )
        since = datetime.now(KST) - timedelta(days=7)
        recent = db.query(KmongClick).filter(KmongClick.created_at >= since).count()
        total = db.query(KmongClick).count()
        return {
            "total": total,
            "last_7_days": recent,
            "by_position_gig": [
                {"position": p, "gig_id": g, "count": c} for p, g, c in by_position
            ],
        }
    finally:
        db.close()
