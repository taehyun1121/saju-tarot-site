#!/bin/bash
# gosamtarot.com 등록 감시 → 등록 감지 즉시 connect_domain.sh 자동 실행 → Discord 보고
# nohup 백그라운드용. 로그: watch_connect.log
DOMAIN="gosamtarot.com"
DIR="/mnt/c/Users/ha861/agents/projects/saju-tarot-pro"
DELIVER="/mnt/c/Users/ha861/agents/shared/skills/deliver-result/deliver.py"
source /mnt/c/Users/ha861/agents/shared/.env

MAX_TRIES=288  # 5분 x 288 = 24시간
for i in $(seq 1 $MAX_TRIES); do
  R=$(curl -s -o /dev/null -w "%{http_code}" "https://rdap.verisign.com/com/v1/domain/$DOMAIN" --max-time 15)
  Z=$(curl -s "https://api.cloudflare.com/client/v4/zones" -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" --max-time 15 \
      | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('result') or []))" 2>/dev/null || echo 0)
  echo "$(date '+%m-%d %H:%M:%S') try$i RDAP=$R zones=$Z"
  if [ "$R" = "200" ] || [ "$Z" != "0" ]; then
    echo "=== 등록 감지! 연결 실행 ==="
    if bash "$DIR/connect_domain.sh" > "$DIR/connect_run.log" 2>&1; then
      python3 "$DELIVER" main "[코코 자동보고] 🎉 gosamtarot.com 등록 감지 → 연결 자동 실행 완료!
- Cloudflare DNS: GitHub Pages A레코드 4개 + www CNAME 설정됨
- GitHub Pages 커스텀 도메인 + base '/' 재배포 트리거됨
- HTTPS 인증서는 몇 분~몇 시간 내 자동 발급
- 확인: https://gosamtarot.com (DNS 반영까지 수분~수시간)
상세 로그: saju-tarot-pro/connect_run.log"
    else
      python3 "$DELIVER" main "[코코 자동보고] ⚠️ gosamtarot.com 등록은 감지됐는데 연결 스크립트가 중간에 실패했습니다. connect_run.log 확인 필요 — 코코 채널에 지시 주시면 이어서 처리합니다.
$(tail -5 "$DIR/connect_run.log")"
    fi
    exit 0
  fi
  sleep 300
done
python3 "$DELIVER" main "[코코 자동보고] gosamtarot.com 등록 감시 24시간 만료 — 여전히 레지스트리 미등록입니다. Cloudflare 결제가 완료되지 않은 것으로 보입니다. 대시보드 Domain Registration + Billing 확인 부탁드립니다."
