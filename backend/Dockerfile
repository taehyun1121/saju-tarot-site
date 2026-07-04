FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py saju.py tarot.py orders.py start.py ./
COPY static/ ./static/
CMD ["python", "start.py"]
