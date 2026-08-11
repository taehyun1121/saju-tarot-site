from dotenv import load_dotenv
load_dotenv()  # .env 파일에서 환경변수 자동 로드

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from ratelimit import rate_limit
from pydantic import BaseModel
from typing import Optional
import random
import os
import json
import re

from saju import calc_pillars, calc_daeun, build_reading, build_compatibility_reading, CHEONGAN, JIJI, ILGAN_TRAITS
from tarot import SPREADS, draw_cards, finalize_cards, get_meaning, get_saju_meaning, get_overall_summary
from saju_rule_engine import Pillars as _EnginePillars, ohaeng_count
from saju_fortune_curve import score_curve
from saju_narrative import rule_based_ai_reading, rule_based_decade_reading, ohaeng_legend, radar_svg, lifegraph_svg

# 🔴 2026-08-12 — Gemini 직접호출 전면 제거 (형 확정: "이전에 엔진을 따로 제미니 안쓰게 만들었는데").
#    ai_consultant.py(전화상담)는 이미 saju_rule_engine/saju_narrative(결정론적 룰엔진)로 계산하고
#    tarot.py도 완전 룰베이스라 Gemini가 필요 없다. 그런데 사이트 경로(main.py)만 옛 Gemini 직접호출이
#    남아 있었다(_AI_SYSTEM 이하 3개 generate_* 함수, 아래 전부 삭제) — 그게 53초 지연의 원인이었다.
#    아래 구 프롬프트 원문은 gbrain benchmark-source-catalog T항목·git log 48d70a0/e602d3e에 남아있다.

app = FastAPI(title="사주타로 API")

# 🔒 CORS: 기본 전체(*) 제거 → 프론트 origin 화이트리스트. 필요 시 CORS_ORIGINS 환경변수로 오버라이드(콤마구분).
_CORS_DEFAULT = "https://taehyun1121.github.io,https://gosamtarot.com,https://www.gosamtarot.com,https://talddung.com,http://localhost:5173"
_CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", _CORS_DEFAULT).split(",") if o.strip()]
# Netlify 프리뷰(gosamtarot-funnel-preview 사이트)만 정규식으로 허용 — draft 배포마다 해시 서브도메인이 바뀌어서
# 정확매칭 리스트로는 못 잡음. 이 사이트 하나로 스코프 한정(*.netlify.app 전체 허용 아님).
_CORS_PREVIEW_REGEX = r"^https://([a-z0-9]+--)?gosamtarot-funnel-preview\.netlify\.app$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_origin_regex=_CORS_PREVIEW_REGEX,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

from orders import router as orders_router
app.include_router(orders_router)

# ── 사주 ───────────────────────────────────────────────────
class SajuRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: Optional[int] = None
    gender: str  # "남" | "여"

@app.post("/api/saju")
def calculate_saju(req: SajuRequest, request: Request):
    rate_limit(request, "saju", limit=10, window_sec=60)   # IP당 분당 10건 — LLM 비용폭탄 방지
    yp, mp, dp, hp = calc_pillars(req.year, req.month, req.day, req.hour)
    daeun = calc_daeun(req.year, req.month, req.day, req.gender)
    reading = build_reading(req.year, req.month, req.day, req.hour,
                            req.gender, yp, mp, dp, hp)

    current_year = 2026
    sy_idx = (current_year - 4) % 10
    sj_idx = (current_year - 4) % 12
    seun = CHEONGAN[sy_idx] + JIJI[sj_idx]

    pillars = {
        "year":  {"korean": yp[0]+yp[1], "hanja": yp[2]},
        "month": {"korean": mp[0]+mp[1], "hanja": mp[2]},
        "day":   {"korean": dp[0]+dp[1], "hanja": dp[2]},
        "hour":  {"korean": hp[0]+hp[1], "hanja": hp[2]} if hp else None,
    }
    reading_list = [{"title": t, "content": c} for t, c in reading]

    engine_pillars = _EnginePillars(
        (yp[0], yp[1]), (mp[0], mp[1]), (dp[0], dp[1]),
        (hp[0], hp[1]) if hp else None,
    )

    # 🔴 2026-08-12 — Gemini 직접호출 제거, 룰엔진(saju_narrative)을 유일한 소스로 사용.
    #    ai_consultant.py(전화상담)가 이미 이 룰엔진만 쓰고 있었고(왕쇠·용신·격국·구조진단을
    #    LLM 추론이 아니라 검증된 코드로 계산), 사이트 경로만 옛 Gemini 프롬프트가 남아있었다.
    ai = rule_based_ai_reading(pillars, dp[0], ILGAN_TRAITS.get(dp[0], {}), daeun, seun,
                                req.gender, engine_pillars, hp is not None)
    decades = rule_based_decade_reading(
        [{"label": f"{d}대", "age_range": f"{d}~{d+9}세", "years": f"{req.year+d}~{req.year+d+9}년",
          "daeun": " / ".join(f"{x['hanja']}({x['korean']}) {x['start']}~{x['end']}세"
                                for x in daeun if x['start'] < d + 9 and x['end'] > d) or "대운 정보 없음",
          "status": "과거" if req.year + d + 9 < 2026 else ("현재" if req.year + d <= 2026 <= req.year + d + 9 else "미래")}
         for d in range(10, 80, 10)],
        ILGAN_TRAITS.get(dp[0], {}), engine_pillars, req.gender)

    # 오행 레이더(무료 스포 티저용) — ohaeng_count()는 이미 검증된 판정, 새 로직 없음.
    ohaeng_items = ohaeng_legend(ohaeng_count(engine_pillars))
    radar = radar_svg(ohaeng_items, size=200)

    # 운세곡선 엔진(saju_fortune_curve) — AI 미사용, 결정론적 명리 룰. 4대운 피크(대박·조심·연애·결혼)
    # 실패해도 전체 API는 죽지 않게 격리(엔진은 부가 기능, saju 핵심 결과에 영향 없음).
    fortune = None
    life = None
    try:
        daewoon_su = daeun[0]["start"] if daeun else None
        result = score_curve(engine_pillars, req.gender, req.year, daewoon_su=daewoon_su, age_range=(3, 83))
        # 카테고리별 피크 주변 창(±3세, 1년 간격) — SajuFunnelPage 스포화면 미니그래프용.
        # curve_sample(5년 간격)은 전체 개관용이라 특정 피크 근처를 부드러운 곡선으로 못 그림 —
        # 이미 계산된 result["curve"](81개, 지어내기 아닌 실계산값)에서 슬라이스만 함.
        def _peak_window(peak, span=2):
            if not peak or "미확정" in peak:
                return None
            age = peak["age"]
            return [c for c in result["curve"] if age - span <= c["age"] <= age + span]

        fortune = {
            "peaks": result["peaks"],
            "flags": result["flags"],
            "meta": {"왕쇠": result["meta"]["왕쇠"].get("verdict"), "용신그룹": result["meta"]["용신그룹"]},
            # 그래프용 5년 간격 샘플(81개 전체는 과함 — 화면 그래프는 몇 개 점이면 충분)
            "curve_sample": [c for c in result["curve"] if c["age"] % 5 == 0 or c["age"] == req.year - req.year],
            "peak_windows": {k: _peak_window(v) for k, v in result["peaks"].items()},
        }
        life = lifegraph_svg([{"age": c["age"], "score": round(c["score"])} for c in result["curve"]], W=336, H=110)
    except Exception as e:
        print(f"[fortune curve error] {e}")

    return {
        "pillars": pillars,
        "ilgan": dp[0],
        "daeun": daeun,
        "seun": seun,
        "reading": reading_list,
        "ai_readings": ai.get("ai_readings", []),
        "ai_overall": ai.get("overall", ""),
        "decade_readings": decades,
        "ai_available": bool(ai.get("ai_readings")),
        "fortune": fortune,
        "ohaeng": ohaeng_items,
        "radar": radar,
        "life": life,
    }

# ── 궁합 ───────────────────────────────────────────────────
class CompatibilityRequest(BaseModel):
    person1: SajuRequest
    person2: SajuRequest

@app.post("/api/compatibility")
def calculate_compatibility(req: CompatibilityRequest, request: Request):
    rate_limit(request, "compat", limit=10, window_sec=60)   # IP당 분당 10건 — LLM 비용폭탄 방지
    def saju_data(p):
        yp, mp, dp, hp = calc_pillars(p.year, p.month, p.day, p.hour)
        return {
            "pillars": {
                "year":  {"korean": yp[0]+yp[1], "hanja": yp[2]},
                "month": {"korean": mp[0]+mp[1], "hanja": mp[2]},
                "day":   {"korean": dp[0]+dp[1], "hanja": dp[2]},
                "hour":  {"korean": hp[0]+hp[1], "hanja": hp[2]} if hp else None,
            },
            "ilgan": dp[0],
        }

    s1 = saju_data(req.person1)
    s2 = saju_data(req.person2)
    reading = build_compatibility_reading(
        req.person1.gender, req.person2.gender,
        s1["ilgan"], s2["ilgan"]
    )
    return {
        "person1": s1,
        "person2": s2,
        "reading": [{"title": t, "content": c} for t, c in reading],
    }

# ── 타로 ───────────────────────────────────────────────────
class TarotRequest(BaseModel):
    spread_id: str
    question: Optional[str] = ""
    saju_context: Optional[dict] = None  # 사주 데이터 연동 시

@app.post("/api/tarot/draw")
def draw_tarot(req: TarotRequest, request: Request):
    rate_limit(request, "tarot", limit=10, window_sec=60)   # IP당 분당 10건 — LLM 비용폭탄 방지
    spread = SPREADS.get(req.spread_id)
    if not spread:
        return {"error": "존재하지 않는 스프레드"}

    cards = draw_cards(spread["cards"])
    cards = finalize_cards(cards)

    # 포지션 정보 + 카드 매핑
    result_cards = []
    for i, pos in enumerate(spread["positions"]):
        card = cards[i]
        layout = spread["layout"][i]
        ilgan = req.saju_context.get("ilgan") if req.saju_context else None
        result_cards.append({
            "position_num": pos["num"],
            "position_name": pos["name"],
            "position_desc": pos["desc"],
            "card_name": card["name"],
            "reversed": card["reversed"],
            "image": card["image"],
            "keyword": card["keyword"],
            "meaning": get_meaning(card["name"], card["reversed"], pos["name"]),
            "saju_meaning": get_saju_meaning(card["name"], card["reversed"], ilgan) if ilgan else "",
            "col": layout["col"],
            "row": layout["row"],
            "cross": layout.get("cross", False),
        })

    ilgan = req.saju_context.get("ilgan") if req.saju_context else None
    # 🔴 2026-08-12 — Gemini 직접호출 제거. tarot.py는 이미 완전 룰베이스(카드조합·패턴카운트·
    # 포지션흐름을 코드로 계산)라 result_cards의 meaning/saju_meaning, overall이 그 자체로 최종
    # 결과다 — ai_consultant.py의 tool_draw_tarot과 동일한 소스를 쓴다.
    overall = get_overall_summary(result_cards, ilgan=ilgan, question=req.question or "")

    return {
        "spread_id": req.spread_id,
        "spread_name": spread["name"],
        "question": req.question,
        "cards": result_cards,
        "grid_cols": spread["gridCols"],
        "grid_rows": spread["gridRows"],
        "overall_summary": overall,
        "ai_available": False,
    }

@app.get("/api/spreads")
def get_spreads():
    return [
        {"id": k, "name": v["name"], "cards": v["cards"], "description": v["description"]}
        for k, v in SPREADS.items()
    ]

@app.get("/")
def root():
    return {"status": "사주타로 API 실행 중"}

@app.get("/health")
def health():
    return {"status": "ok"}
