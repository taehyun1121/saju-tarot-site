"""결제완료 리포트 PDF 생성 + 이메일 발송.

템플릿(디자인봇 제작, templates/report_saju.html · report_tarot.html)이
아직 없으면 조용히 no-op — 기존 Discord 수동알림 흐름은 그대로 유지되고,
템플릿 파일이 생기는 순간 자동으로 켜진다(고객 대상 코드 변경 불필요).
"""

import json
import os
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
TEMPLATES = {"saju4": "report_saju.html", "tarot_spread": "report_tarot.html"}

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GMAIL_SENDER_NAME = os.environ.get("GMAIL_SENDER_NAME", "고삼타로")


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


def _render_pdf(template_path: str, data: dict) -> bytes:
    # 무거운 라이브러리라 실사용 시점(템플릿 생기고 나서)에만 import —
    # 템플릿 없는 지금은 이 함수 자체가 안 불려서 부팅 비용도 없음.
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(os.path.basename(template_path))
    html_str = template.render(**data)
    return HTML(string=html_str, base_url=TEMPLATE_DIR).write_pdf()


def _send_email(to_email: str, subject: str, body_text: str, pdf_bytes: bytes, pdf_filename: str):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD):
        return False
    msg = MIMEMultipart()
    msg["From"] = f"{GMAIL_SENDER_NAME} <{GMAIL_ADDRESS}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    part = MIMEApplication(pdf_bytes, Name=pdf_filename)
    part["Content-Disposition"] = f'attachment; filename="{pdf_filename}"'
    msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [to_email], msg.as_string())
    return True


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

    pdf_bytes = _render_pdf(template_path, {
        "order": {"buyer_name": order.buyer_name, "product_name": order.product_name},
        **data,
    })
    _send_email(
        to_email,
        subject=f"[고삼타로] {order.product_name} 결과가 도착했습니다",
        body_text=f"{order.buyer_name}님, 신청하신 \"{order.product_name}\" 결과를 PDF로 첨부해 드립니다.\n\n고삼타로 드림",
        pdf_bytes=pdf_bytes,
        pdf_filename=f"gosamtarot_{order.id}.pdf",
    )
    return True
