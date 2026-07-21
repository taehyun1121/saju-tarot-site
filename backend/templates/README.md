디자인봇이 만드는 리포트 PDF 템플릿(Jinja2+print CSS) 넣는 곳.

- `report_saju.html` — saju4 상품용
- `report_tarot.html` — tarot_spread 상품용

둘 중 하나라도 이 폴더에 있으면 `reports.py`가 자동으로 그 상품 결제승인 시
PDF 생성+이메일 발송을 켠다(코드 변경 불필요). 없으면 조용히 스킵되고
기존 Discord 수동알림 흐름만 동작.
