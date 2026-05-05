#!/bin/bash
echo "✦ 사주풀이 & 타로 사이트 시작 ✦"

# 백엔드
cd "$(dirname "$0")/backend"
/tmp/tarot_env/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "백엔드 실행 중 (PID: $BACKEND_PID) → http://localhost:8000"

# 프론트엔드
cd "$(dirname "$0")/frontend"
npm run dev &
FRONTEND_PID=$!
echo "프론트엔드 실행 중 (PID: $FRONTEND_PID) → http://localhost:5173"

echo ""
echo "브라우저에서 http://localhost:5173 열어주세요"
echo "종료: Ctrl+C"

wait
