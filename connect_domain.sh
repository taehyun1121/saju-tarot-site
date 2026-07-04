#!/bin/bash
# gosamtarot.com → GitHub Pages(saju-tarot-site) 연결 원샷 스크립트
# 전제: 도메인 구입 완료. Cloudflare에서 샀으면 존이 이미 있음 / 타사면 존 생성 후 NS 변경 필요.
# 사용: bash connect_domain.sh
set -e
DOMAIN="gosamtarot.com"
GH_PAGES_HOST="taehyun1121.github.io"
REPO="taehyun1121/saju-tarot-site"
source /mnt/c/Users/ha861/agents/shared/.env
CF="https://api.cloudflare.com/client/v4"
AUTH=(-H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json")

echo "== 1. 도메인 등록 확인 =="
if ! curl -s -o /dev/null -w "%{http_code}" "https://rdap.verisign.com/com/v1/domain/$DOMAIN" | grep -q 200; then
  echo "❌ $DOMAIN 아직 미등록. 구입 먼저."; exit 1
fi
echo "✅ 등록 확인"

echo "== 2. Cloudflare 존 확인/생성 =="
ZONE_ID=$(curl -s "${AUTH[@]}" "$CF/zones?name=$DOMAIN" | python3 -c "import json,sys; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")
if [ -z "$ZONE_ID" ]; then
  ZONE_ID=$(curl -s -X POST "${AUTH[@]}" "$CF/zones" -d "{\"name\":\"$DOMAIN\",\"jump_start\":false}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['result']['id'] if d['success'] else '')")
  [ -z "$ZONE_ID" ] && { echo "❌ 존 생성 실패 (토큰에 Zone 생성 권한 필요)"; exit 1; }
fi
echo "✅ zone: $ZONE_ID"
echo "-- 네임서버 (타사 구입 시 등록기관에서 이걸로 변경) --"
curl -s "${AUTH[@]}" "$CF/zones/$ZONE_ID" | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['result'].get('name_servers',[])))"

echo "== 3. DNS 레코드 (GitHub Pages) =="
for ip in 185.199.108.153 185.199.109.153 185.199.110.153 185.199.111.153; do
  curl -s -X POST "${AUTH[@]}" "$CF/zones/$ZONE_ID/dns_records" \
    -d "{\"type\":\"A\",\"name\":\"@\",\"content\":\"$ip\",\"proxied\":false,\"ttl\":1}" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print('A @ ' + ('OK' if d['success'] else str(d['errors'])))"
done
curl -s -X POST "${AUTH[@]}" "$CF/zones/$ZONE_ID/dns_records" \
  -d "{\"type\":\"CNAME\",\"name\":\"www\",\"content\":\"$GH_PAGES_HOST\",\"proxied\":false,\"ttl\":1}" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('CNAME www ' + ('OK' if d['success'] else str(d['errors'])))"

echo "== 4. GitHub Pages 커스텀 도메인 + base 전환 =="
gh api -X PUT "repos/$REPO/pages" -f cname="$DOMAIN" --silent && echo "✅ Pages cname=$DOMAIN"
gh variable set CUSTOM_DOMAIN --repo "$REPO" --body "1" && echo "✅ CUSTOM_DOMAIN=1"
gh workflow run deploy.yml --repo "$REPO" && echo "✅ 재배포 트리거 (base '/')"

echo "== 5. 남은 일 =="
echo "- 타사 구입이면: 등록기관에서 위 네임서버로 변경 (반영 수분~48h)"
echo "- DNS 반영 후: gh api -X PUT repos/$REPO/pages -F https_enforced=true  (인증서 발급 후)"
echo "- 확인: curl -sI https://$DOMAIN"
