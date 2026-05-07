from dotenv import load_dotenv
load_dotenv()  # .env 파일에서 환경변수 자동 로드

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import random
import os
import json
import re

import anthropic as anthropic_sdk

from saju import calc_pillars, calc_daeun, build_reading, build_compatibility_reading, CHEONGAN, JIJI, ILGAN_TRAITS
from tarot import SPREADS, draw_cards, finalize_cards, get_meaning, get_saju_meaning, get_overall_summary

# ── Claude API 클라이언트 ────────────────────────────────────
_anthropic_client = None

def get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            _anthropic_client = anthropic_sdk.Anthropic(api_key=api_key)
    return _anthropic_client

_AI_SYSTEM = """당신은 사주명리학과 타로를 함께 활용하는 20년 경력의 전문 상담사입니다.
반드시 한국어로 답하며, 상담 현장에서 그대로 읽을 수 있는 수준으로 작성합니다.

【핵심 원칙: 사주가 기반, 타로가 렌즈】
- 내담자의 사주(일주·월주·년주·대운·세운)는 이 사람의 타고난 기질과 현재 운의 흐름입니다
- 타로카드는 그 사주 에너지가 지금 이 순간 어떻게 발현되고 있는지 보여주는 렌즈입니다
- 사주의 오행 기질 + 카드 에너지가 어떻게 상호작용하는지를 중심으로 해석하세요
- "이 사람의 사주가 이러하기에, 이 카드가 이런 의미를 갖는다"는 방식으로 서술하세요

【카드별 해석】
- 포지션 의미 + 카드 에너지 + 사주 기질을 결합하여 이 사람만의 해석을 만드세요
- 정방향: 에너지가 활성화·외향적 발현 / 역방향: 내면화되거나 막힘·지연
- 카드 이름을 자연스럽게 언급하며 3-4문장으로 서술하세요
- 추상적 표현 금지 — 내담자가 "내 얘기다" 느낄 수 있도록 구체적으로

【전체 종합 해석】
- 질문에 직접 답하는 문장으로 시작하세요
- 내담자의 사주 흐름(대운·세운)과 카드 흐름을 연결하여 하나의 이야기로 엮으세요
- 카드 이름을 언급하며 각 카드가 어떤 역할(현재/장애물/조언/결과)인지 서술하세요
- 질문의 시간적 맥락("8월까지", "올해" 등)이 있으면 반드시 반영하세요
- 마지막은 이 사람의 사주 기질에 맞는 구체적 조언으로 마무리하세요
- 분량: 6-8문장, 상담사가 그대로 읽어줄 수 있는 수준"""

def _build_saju_profile(saju_context: dict) -> str:
    """saju_context에서 상담에 필요한 만세력 프로필을 텍스트로 구성"""
    if not saju_context:
        return ""

    lines = ["【내담자 사주 프로필】"]

    # 사주 기둥
    pillars = saju_context.get("pillars", {})
    pillar_names = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
    pillar_parts = []
    for k, label in pillar_names.items():
        p = pillars.get(k)
        if p:
            pillar_parts.append(f"{label} {p['hanja']}({p['korean']})")
    if pillar_parts:
        lines.append("사주 기둥: " + " / ".join(pillar_parts))

    # 일간
    ilgan = saju_context.get("ilgan", "")
    if ilgan:
        trait = ILGAN_TRAITS.get(ilgan, {})
        lines.append(f"일간: {ilgan}({trait.get('오행','')}) — 성격: {trait.get('성격','')}, 단점: {trait.get('단점','')}, 자존심: {trait.get('자존심','')}")

    # 현재 대운
    daeun = saju_context.get("daeun", [])
    if len(daeun) > 2:
        current = daeun[2]
        lines.append(f"현재 대운: {current['hanja']}({current.get('korean','')}) — {current['start']}~{current['end']}세")

    # 세운
    seun = saju_context.get("seun", "")
    if seun:
        lines.append(f"2026 세운: {seun}")

    # 사주 14항목 핵심 요약 (상위 5개)
    reading = saju_context.get("reading", [])
    if reading:
        key_items = ["전체 인생", "현재 상태", "현재 심리 상태", "연애 상태", "연애방식"]
        lines.append("사주 핵심 풀이:")
        for item in reading:
            if item.get("title") in key_items:
                lines.append(f"  · {item['title']}: {item['content']}")

    return "\n".join(lines)

def generate_ai_tarot_reading(result_cards: list, spread_name: str, question: str = "", saju_context: dict = None) -> dict:
    """Claude API로 AI 타로 해석 생성. 실패 시 빈 dict 반환."""
    client = get_anthropic_client()
    if not client:
        return {}

    saju_profile = _build_saju_profile(saju_context)
    ilgan = saju_context.get("ilgan") if saju_context else None

    cards_text = "\n".join([
        f"  {i+1}. [{c['position_name']}] {c['card_name']} ({'역방향 ↺' if c['reversed'] else '정방향 ↑'}) — 포지션: {c['position_desc']}"
        for i, c in enumerate(result_cards)
    ])

    saju_field = (
        '"saju_insight": "이 카드가 내담자 사주 기질과 어떻게 공명하는지 1-2문장"'
        if saju_profile else '"saju_insight": ""'
    )

    overall_guide = (
        f'"{question}"에 직접 답하는 문장으로 시작 → 사주 흐름과 카드 흐름을 연결한 내러티브 → 카드 이름 언급 → 이 사람 기질에 맞는 조언으로 마무리, 6-8문장'
        if question else
        "사주 흐름과 카드 흐름을 연결한 내러티브, 카드 이름 언급, 6-8문장"
    )

    user_prompt = f"""{saju_profile}

배열법: {spread_name}
질문: {question if question else "없음"}

뽑힌 카드:
{cards_text}

JSON 형식으로만 응답하세요 (코드블록 없이):
{{
  "card_readings": [
    {{"idx": 0, "reading": "사주 기질+카드 에너지+포지션 결합, 3-4문장", {saju_field}}},
    ...총 {len(result_cards)}개
  ],
  "overall_summary": "{overall_guide}"
}}"""

    try:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8000,
            system=[{
                "type": "text",
                "text": _AI_SYSTEM,
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[{"role": "user", "content": user_prompt}]
        )
        text = response.content[0].text.strip()
        text = re.sub(r'^```[a-z]*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'```$', '', text, flags=re.MULTILINE)
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            return json.loads(m.group())
    except Exception as e:
        print(f"[AI reading error] {e}")
    return {}

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

# ── 궁합 ───────────────────────────────────────────────────
class CompatibilityRequest(BaseModel):
    person1: SajuRequest
    person2: SajuRequest

@app.post("/api/compatibility")
def calculate_compatibility(req: CompatibilityRequest):
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
    static_overall = get_overall_summary(result_cards, ilgan=ilgan, question=req.question or "")

    # Claude AI 해석 생성 (실패 시 기존 정적 해석 유지)
    ai = generate_ai_tarot_reading(
        result_cards, spread["name"],
        question=req.question or "",
        saju_context=req.saju_context
    )

    # AI 해석을 카드별로 병합
    if ai.get("card_readings"):
        ai_map = {r["idx"]: r for r in ai["card_readings"] if "idx" in r}
        for i, card in enumerate(result_cards):
            ai_card = ai_map.get(i, {})
            card["ai_reading"] = ai_card.get("reading", "")
            card["ai_saju_insight"] = ai_card.get("saju_insight", "")

    return {
        "spread_id": req.spread_id,
        "spread_name": spread["name"],
        "question": req.question,
        "cards": result_cards,
        "grid_cols": spread["gridCols"],
        "grid_rows": spread["gridRows"],
        "overall_summary": ai.get("overall_summary") or static_overall,
        "ai_available": bool(ai),
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
