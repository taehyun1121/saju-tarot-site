from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random

from saju import calc_pillars, calc_daeun, build_reading, CHEONGAN, JIJI
from tarot import SPREADS, draw_cards, finalize_cards

app = FastAPI(title="사주타로 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ── 사주 ───────────────────────────────────────────────────
class SajuRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: Optional[int] = None
    gender: str  # "남" | "여"

@app.post("/api/saju")
def calculate_saju(req: SajuRequest):
    yp, mp, dp, hp = calc_pillars(req.year, req.month, req.day, req.hour)
    daeun = calc_daeun(req.year, req.month, req.day, req.gender)
    reading = build_reading(req.year, req.month, req.day, req.hour,
                            req.gender, yp, mp, dp, hp)

    # 현재 세운 (병오 2026)
    current_year = 2026
    sy_idx = (current_year - 4) % 10
    sj_idx = (current_year - 4) % 12
    seun = CHEONGAN[sy_idx] + JIJI[sj_idx]

    return {
        "pillars": {
            "year":  {"korean": yp[0]+yp[1], "hanja": yp[2]},
            "month": {"korean": mp[0]+mp[1], "hanja": mp[2]},
            "day":   {"korean": dp[0]+dp[1], "hanja": dp[2]},
            "hour":  {"korean": hp[0]+hp[1], "hanja": hp[2]} if hp else None,
        },
        "ilgan": dp[0],
        "daeun": daeun,
        "seun": seun,
        "reading": [{"title": t, "content": c} for t, c in reading],
    }

# ── 타로 ───────────────────────────────────────────────────
class TarotRequest(BaseModel):
    spread_id: str
    question: Optional[str] = ""
    saju_context: Optional[dict] = None  # 사주 데이터 연동 시

@app.post("/api/tarot/draw")
def draw_tarot(req: TarotRequest):
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
        result_cards.append({
            "position_num": pos["num"],
            "position_name": pos["name"],
            "position_desc": pos["desc"],
            "card_name": card["name"],
            "reversed": card["reversed"],
            "image": card["image"],
            "keyword": card["keyword"],
            "col": layout["col"],
            "row": layout["row"],
            "cross": layout.get("cross", False),
        })

    return {
        "spread_id": req.spread_id,
        "spread_name": spread["name"],
        "question": req.question,
        "cards": result_cards,
        "grid_cols": spread["gridCols"],
        "grid_rows": spread["gridRows"],
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
