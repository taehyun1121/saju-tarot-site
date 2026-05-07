#!/bin/bash
echo "✦ 사주풀이 & 타로 사이트 시작 ✦"

# 백엔드
cd "$(dirname "$0")/backend"
/home/ha861/.cache/uv/archive-v0/T86QVR2xLFBIbgH0L6-dz/bin/uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
echo "백엔드 실행 중 (PID: $BACKEND_PID) → http://localhost:8001"

# 프론트엔드
cd "$(dirname "$0")/frontend"
npm run dev &
FRONTEND_PID=$!
echo "프론트엔드 실행 중 (PID: $FRONTEND_PID) → http://localhost:5173"

# ngrok 터널 (3초 후 시작)
sleep 3
/home/ha861/.local/bin/ngrok http 5173 --log=stdout &
NGROK_PID=$!

echo ""
echo "잠시 후 ngrok URL이 위에 표시됩니다 (https://xxxx.ngrok-free.app)"
echo "종료: Ctrl+C"

trap "kill $BACKEND_PID $FRONTEND_PID $NGROK_PID 2>/dev/null" EXIT
wait
