"""결제완료 리포트 PDF 생성 + 이메일 발송.

템플릿(디자인봇 제작, templates/report_saju.html · report_tarot.html)이
아직 없으면 조용히 no-op — 기존 Discord 수동알림 흐름은 그대로 유지되고,
템플릿 파일이 생기는 순간 자동으로 켜진다(고객 대상 코드 변경 불필요).
"""

import base64
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone

BACKEND_DIR = os.path.dirname(__file__)
TEMPLATE_DIR = os.path.join(BACKEND_DIR, "templates")
STATIC_DIR = os.path.join(BACKEND_DIR, "static")
TEMPLATES = {"saju4": "report_saju.html", "tarot_spread": "report_tarot.html"}

# 🔒 2026-07-21 실측 발견: Render 무료플랜이 2025-09부터 SMTP 465/587 아웃바운드를
# 아예 차단(공식 정책, "Network is unreachable" 직접 확인) — 직접 smtplib 불가능.
# bankapi.co.kr 우회와 동일 이유로 NCP 서버에 발송 릴레이(mail_proxy.py, 포트8003)를
# 세워서 그쪽에서 실제 SMTP 발송.
MAIL_RELAY_BASE = os.environ.get("MAIL_RELAY_BASE", "http://101.79.25.93:8003")
MAIL_RELAY_TOKEN = os.environ.get("MAIL_RELAY_TOKEN", "")
KST = timezone(timedelta(hours=9))

OHAENG_KR = {"갑": "목", "을": "목", "병": "화", "정": "화", "무": "토",
             "기": "토", "경": "금", "신": "금", "임": "수", "계": "수"}
OHAENG_EN = {"목": "wood", "화": "fire", "토": "earth", "금": "metal", "수": "water"}


def _template_path(product_key: str):
    name = TEMPLATES.get(product_key)
    if not name:
        return None
    path = os.path.join(TEMPLATE_DIR, name)
    return path if os.path.exists(path) else None


def _extract_email(contact: str):
    """OrderModal contact 포맷("010-1234-5678 / a@b.com")에서 이메일만 추출."""
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", contact or "")
    return m.group(0) if m else None


def _asset_file_url(rel_path: str) -> str:
    """`/static/...` 상대경로 → WeasyPrint가 읽을 수 있는 로컬 file:// 절대경로."""
    clean = rel_path.lstrip("/")
    if clean.startswith("static/"):
        clean = clean[len("static/"):]
    return "file://" + os.path.join(STATIC_DIR, clean)


def _pillar_ctx(entry, position_label):
    """pillars dict의 한 기둥({"korean":"경자","hanja":"庚子"}) → 템플릿 슬롯 형태.
    entry가 None(시주 모름)이면 '미상' 플레이스홀더로 안전 처리."""
    if not entry:
        return {"position": position_label, "stem": "−", "branch": "−", "reading": "시주 미상",
                "element": "−", "element_en": "unknown"}
    stem_kr = entry["korean"][0]
    elem_kr = OHAENG_KR.get(stem_kr, "−")
    return {
        "position": position_label,
        "stem": entry["hanja"][0], "branch": entry["hanja"][1],
        "reading": entry["korean"],
        "element": elem_kr, "element_en": OHAENG_EN.get(elem_kr, "unknown"),
    }


def _find_reading(ai_readings, prefix):
    for r in ai_readings:
        if r.get("title", "").startswith(prefix):
            return r["content"]
    return ""


PEAK_KIND = {"대박운": "good", "조심시기": "care", "연애운": "love", "결혼운": "marry"}


def _build_saju_context(order, data: dict) -> dict:
    birth = data.get("birth_input") or {}
    gender_kr = "여성" if birth.get("gender") == "여" else ("남성" if birth.get("gender") == "남" else "")
    birth_text = ""
    if birth.get("year") and birth.get("month") and birth.get("day"):
        birth_text = f"{birth['year']}년 {birth['month']}월 {birth['day']}일"
        birth_text += f" {birth['hour']}시생" if birth.get("hour") else " (시간 미상)"

    pillars = data.get("pillars") or {}
    ai_readings = data.get("ai_readings") or []
    fortune = data.get("fortune") or {}
    peaks = fortune.get("peaks") or {}

    luck_peaks = []
    for label, kind in PEAK_KIND.items():
        p = peaks.get(label)
        if not p or "미확정" in p:
            continue
        reason = p.get("근거", "")
        if p.get("주의"):
            reason = f"{reason} (주의: {p['주의']})" if reason else p["주의"]
        luck_peaks.append({"kind": kind, "label": label, "age": p["age"], "year": p["year"],
                            "score": round(p["score"]), "reason": reason})

    overall = data.get("ai_overall") or "지금 이 사주의 흐름을 마음에 새기고, 스스로에게 맞는 선택을 이어가시길 바랍니다."
    closing_body = overall if len(overall) < 200 else (overall[:180].rsplit(".", 1)[0] + ".")

    return {
        "user": {"name": order.buyer_name, "birth_text": birth_text, "gender": gender_kr},
        "issued_date": datetime.now(KST).strftime("%Y년 %m월 %d일"),
        "cover_bg_url": _asset_file_url("/static/images/bg_hanji.jpg"),
        "emblem_url": _asset_file_url("/static/images/em_saju_blue.jpg"),
        "saju": {
            "pillars": {
                "year": _pillar_ctx(pillars.get("year"), "년주"),
                "month": _pillar_ctx(pillars.get("month"), "월주"),
                "day": _pillar_ctx(pillars.get("day"), "일주"),
                "hour": _pillar_ctx(pillars.get("hour"), "시주"),
            },
            "daeun": _find_reading(ai_readings, "6.") or "대운 정보를 계산 중입니다.",
            "seun": _find_reading(ai_readings, "7.") or "세운 정보를 계산 중입니다.",
        },
        "ai_readings": ai_readings,
        "luck_peaks": luck_peaks,
        "closing": {"title": "당신의 사주가 전하는 이야기", "body": closing_body},
    }


def _build_tarot_context(order, data: dict) -> dict:
    cards = []
    for c in (data.get("cards") or []):
        cards.append({
            "position": c.get("position_name", ""),
            "name": c.get("card_name", ""),
            "orientation": "역위" if c.get("reversed") else "정위",
            "keywords": [c["keyword"]] if c.get("keyword") else [],
            "meaning": c.get("meaning", ""),
            # ai_reading이 meaning과 같은 문장 중복이 되지 않도록 — saju_meaning(사주연계)이
            # 진짜 다른 내용일 때만 보조 문단으로 쓰고, 없으면 빈칸(카드의미 한 번만 노출).
            "ai_reading": c.get("ai_reading") or (c.get("saju_meaning") if c.get("saju_meaning") != c.get("meaning") else ""),
            "image_url": _asset_file_url(c["image"]) if c.get("image") else "",
        })
    overall = data.get("overall_summary") or "카드가 전하는 메시지를 마음에 새겨보시길 바랍니다."
    closing_body = overall if len(overall) < 200 else (overall[:180].rsplit(".", 1)[0] + ".")

    return {
        "user": {"name": order.buyer_name},
        "issued_date": datetime.now(KST).strftime("%Y년 %m월 %d일"),
        "question": data.get("question", ""),
        "cover_bg_url": _asset_file_url("/static/images/bg_hanji.jpg"),
        "emblem_url": _asset_file_url("/static/images/em_tarot_blue.jpg"),
        "spread": {"name": data.get("spread_name", ""), "description": f"{len(cards)}장 스프레드로 살펴본 흐름입니다."},
        "cards": cards,
        "overall_summary": overall,
        "closing": {"title": "카드가 전하는 마지막 메시지", "body": closing_body},
    }


def _render_pdf(template_path: str, context: dict) -> bytes:
    # 무거운 라이브러리라 실사용 시점(템플릿 생기고 나서)에만 import —
    # 템플릿 없는 지금은 이 함수 자체가 안 불려서 부팅 비용도 없음.
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(os.path.basename(template_path))
    html_str = template.render(**context)
    return HTML(string=html_str, base_url=TEMPLATE_DIR).write_pdf()


def _send_email(to_email: str, subject: str, body_text: str, pdf_bytes: bytes, pdf_filename: str):
    if not MAIL_RELAY_TOKEN:
        return False
    payload = json.dumps({
        "to_email": to_email, "subject": subject, "body_text": body_text,
        "pdf_base64": base64.b64encode(pdf_bytes).decode(), "pdf_filename": pdf_filename,
    }).encode()
    req = urllib.request.Request(
        f"{MAIL_RELAY_BASE}/send", data=payload,
        headers={"Content-Type": "application/json", "X-Relay-Token": MAIL_RELAY_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        result = json.loads(res.read())
    return result.get("status") == "sent"


def send_report_email(order) -> bool:
    """주문 승인 시 호출. 템플릿·이메일주소 없거나 이미 보냈으면 False(no-op)."""
    if order.email_sent:
        return False
    template_path = _template_path(order.product_key)
    if not template_path:
        return False
    to_email = _extract_email(order.contact)
    if not to_email:
        return False
    if not order.reading_data:
        return False
    try:
        data = json.loads(order.reading_data)
    except json.JSONDecodeError:
        return False

    builder = _build_saju_context if order.product_key == "saju4" else _build_tarot_context
    context = builder(order, data)
    pdf_bytes = _render_pdf(template_path, context)
    _send_email(
        to_email,
        subject=f"[고삼타로] {order.product_name} 결과가 도착했습니다",
        body_text=f"{order.buyer_name}님, 신청하신 \"{order.product_name}\" 결과를 PDF로 첨부해 드립니다.\n\n고삼타로 드림",
        pdf_bytes=pdf_bytes,
        pdf_filename=f"gosamtarot_{order.id}.pdf",
    )
    return True
