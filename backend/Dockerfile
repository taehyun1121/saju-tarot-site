FROM python:3.12-slim
WORKDIR /app
# WeasyPrint(HTML→PDF 리포트 자동생성)용 시스템 라이브러리 — pip만으론 안 됨(Pango/Cairo 바인딩).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libcairo2 \
    libffi-dev shared-mime-info fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./
COPY static/ ./static/
COPY templates/ ./templates/
CMD ["python", "start.py"]
