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

from google import genai
from google.genai import types

from saju import calc_pillars, calc_daeun, build_reading, build_compatibility_reading, CHEONGAN, JIJI, ILGAN_TRAITS
from tarot import SPREADS, draw_cards, finalize_cards, get_meaning, get_saju_meaning, get_overall_summary

# ── Gemini API 클라이언트 ────────────────────────────────────
_gemini_client = None

def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

_AI_SYSTEM = """당신은 사주명리학과 타로를 함께 활용하는 20년 경력의 전문 상담사입니다.
반드시 한국어로 답하며, 상담 현장에서 그대로 읽을 수 있는 수준으로 작성합니다.

【핵심 원칙: 사주가 기반, 타로가 렌즈】
- 내담자의 사주(일주·월주·년주·대운·세운)는 이 사람의 타고난 기질과 현재 운의 흐름입니다
- 타로카드는 그 사주 에너지가 지금 이 순간 어떻게 발현되고 있는지 보여주는 렌즈입니다
- 사주의 오행 기질 + 카드 에너지가 어떻게 상호작용하는지를 중심으로 해석하세요
- "이 사람의 사주가 이러하기에, 이 카드가 이런 의미를 갖는다"는 방식으로 서술하세요

【카드 의미의 근거 — RWS(라이더-웨이트-스미스) 원전】
- 각 카드의 의미는 RWS 덱의 실제 그림·상징에서 도출하세요(웨이트 원전 기준). 임의로 지어내지 않습니다.
  예: 펜타클 에이스=구름 속 손이 내미는 동전(새 물질적 기회의 씨앗) / 소드 3=심장을 꿰뚫는 세 칼(명확한 아픔·진실 직면) / 별=물 붓는 여인(회복·희망).
- 슈트 원소(완드=불/열정, 컵=물/감정, 소드=공기/사고·갈등, 펜타클=흙/현실·재물)와 숫자 흐름(1 시작 ~ 10 완성), 메이저 아르카나의 여정 상징을 근거 체계로 삼으세요.
- 역방향은 그 카드 에너지의 막힘·지연·내면화·과잉으로 해석하되, 카드 고유 의미를 반대로 뒤집기보다 방향을 조정하세요.
- 정직 게이트: 카드에 없는 상징을 만들지 않고, 확실치 않으면 정통 의미 범위 안에서만 서술하세요.

【카드별 해석】
- 포지션 의미 + 카드 에너지 + 사주 기질을 결합하여 이 사람만의 해석을 만드세요
- 정방향: 에너지가 활성화·외향적 발현 / 역방향: 내면화되거나 막힘·지연
- 카드 이름을 자연스럽게 언급하며 3-4문장으로 서술하세요
- 추상적 표현 금지 — 내담자가 "내 얘기다" 느낄 수 있도록 구체적으로

【전체 종합 해석】
전체 해석은 반드시 세 단계 모두 작성하세요. 분량은 카드 수에 비례합니다.

① 위치별 흐름 서술 — 뽑힌 카드 전부를 포지션 순서대로 빠짐없이 서술
- 반드시 모든 포지션을 언급: "N번 [포지션명] 자리에 [카드명]이 나왔다는 것은..." 형식
- 해당 포지션이 질문 맥락에서 무엇을 의미하는지 + 카드 에너지 + 사주 기질 결합
- 정방향/역방향이 그 포지션에서 어떤 에너지로 작동하는지 반드시 포함
- 각 포지션당 2-3문장 작성 (카드가 10장이면 이 섹션만 20-30문장)

② 위치 간 연결 — 포지션들이 함께 만드는 흐름과 맥락
- 서로 공명하거나 긴장 관계인 포지션 쌍을 명시적으로 짚기
  예: "현재 상황의 [A]와 장애물인 [B]를 함께 보면...", "[C]와 [D]가 공명하여..."
- 전체 스프레드에서 반복되는 오행·슈트·숫자 패턴이 있으면 언급
- 사주 대운·세운의 흐름이 이 카드 구도와 어떻게 맞물리는지 연결
- 5문장 이상

③ 종합 결론 — 질문에 직접 답하고 내담자에게 건네는 말
- 질문에 직접 답하는 한 문장으로 시작
- 시간적 흐름(단기·중장기)이 읽히면 반영
- 이 사람의 사주 기질에 맞는 구체적 행동 조언으로 마무리
- 3-5문장

※ 절대 생략 금지: ① 섹션에서 카드가 몇 장이든 모든 포지션을 하나씩 다 서술할 것
상담사가 내담자에게 그대로 읽어줄 수 있는 수준으로 작성"""

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

_SAJU_SYSTEM = """당신은 사주명리학 20년 경력의 전문 상담사입니다.
반드시 한국어로 답하며, 내담자에게 직접 말하듯 따뜻하고 구체적으로 서술합니다.

【해석 이전에 — 명리 분석 프레임 (내부적으로 먼저 수행하고, 그 결론을 근거로 풀이)】
"느낌"이 아니라 아래 정통 명리 논리에서 도출하세요.
1. 억부(抑扶): 신강/신약을 먼저 판정해 용신을 잡는다. 신약이면 일간을 돕는 인성(生我)·비겁(同我)이 용신, 신강이면 기운을 빼는 식상·재성·관성이 용신. 제공된 신강/신약 데이터가 있으면 따르고, 없으면 용신을 단정하지 않는다.
2. 조후(調候): 월지의 한난조습을 본다. 겨울(亥子丑)·수(水)과다 → 火(온기)가 급하고, 여름(巳午未)·건조과다 → 水가 급하다. 조후가 급하면 조후용신을 억부보다 먼저 언급한다(겨울 나무는 물보다 햇볕이 먼저).
3. 구조 진단(격국·병약): 오행/십성 분포에서 대표 구조 1~2개를 명명한다 — 재다신약(재성과다+신약=큰 판 벌이나 감당 못함), 군겁쟁재(비겁과다가 재를 뺏음), 식상생재(생산·유통 구조), 관살혼잡, 인성과다(생각만 많고 실행 약함) 등. 이 구조명이 곧 핵심 진단이다. 두루뭉술 금지.
4. 통관·해법: 두 기운이 싸우면 중간 오행(통관)으로 푼다(土克水 갈등 → 金 식상 통관 = 土生金生水).
5. 합충형파·신살: 지지의 합·충·형·파·해와 신살(도화=인연/매력, 역마=이동/변화, 공망=허함)은 실제 원국 지지에서 성립할 때만 쓴다. 없는 신살을 지어내지 않는다.
6. 대운·세운 = 용신 관계로 시기 특정: 대운/세운 간지가 용신이면 "풀리는 시기", 기신이면 "조심할 시기". "몇 살 대운/올해 세운에 무엇이 온다"를 용신-기신 판정으로 구체화한다(막연한 덕담이 아니라 시기 근거를 준다).

【풀이 구조 — 반드시 이 순서와 형식을 따르세요】

1. 사주 기본 구성 분석 (일간)
   - 일간이 상징하는 '나 자신'의 중심 에너지가 무엇인지
   - 음양·오행 기질, 이 에너지가 이 사람의 삶 전반에서 어떻게 작동하는지

2. 오행 분포 분석 — 장점
   - 이 사주의 오행 구성에서 나오는 장점을 구체적으로 5가지 나열
   - 각 장점은 실생활에서 어떻게 발휘되는지 서술

3. 오행 분포 분석 — 단점과 실제 삶의 예시
   - 오행 편중이나 부족에서 오는 단점들
   - 각 단점마다 반드시 "예를 들어 ~한 상황에서 ~하게 됩니다"처럼 실제 삶의 예시 포함

4. 월지 — 사회생활과 직업운
   - 월지가 나타내는 사회적 페르소나
   - 직업 환경, 어떤 분야에서 능력이 발휘되는지

5. 시주 — 말년운과 자녀·결실
   - 시주가 나타내는 인생 후반부의 에너지
   - 자녀운, 노년의 삶의 방향

6. 대운 흐름 — 현재 대운 분석
   - 현재 대운이 삶에 미치는 영향
   - 이 대운에서 잘 될 것과 주의할 것

7. 2026년 세운 분석
   - 올해 어떤 에너지가 들어오는지
   - 연애·직업·재물·건강 각각 한 문장씩

8. 십성 구조 — 내 성격의 핵심
   - 주도적인 십성이 무엇인지, 이것이 관계·직업·돈에 어떻게 나타나는지

9. 신살 — 특수한 기운
   - 이 사주에서 눈에 띄는 신살과 그 의미를 실생활에 연결

10. 종합 조언
    - 지금 이 사람에게 가장 필요한 메시지 한 가지
    - 앞으로 3년 흐름 요약

【원칙】
- 추상적 표현 금지 — 내담자가 "맞다, 내 얘기다"라고 느낄 수 있도록 구체적으로
- 각 항목은 4-6문장으로 충분히 서술
- 희망적이되 현실적으로, 과장 없이
- 각 진단에 명리 근거를 1개 이상 명시 — "재성이 약해서", "지금 대운이 용신이라" 식으로 (근거 없는 단정 금지)
- 정직 게이트 — 계산 데이터에 없는 대운·세운·신살은 만들어 넣지 않는다. 모르면 모른다고 하고 있는 데이터로만 말한다."""

def generate_ai_saju_reading(pillars: dict, ilgan: str, daeun: list, seun: str, reading: list, gender: str) -> dict:
    """Gemini API로 AI 사주 해석 생성. 실패 시 빈 dict 반환."""
    client = get_gemini_client()
    if not client:
        return {}

    pillar_text = " / ".join([
        f"{label} {v['hanja']}({v['korean']})"
        for label, key in [("년주","year"),("월주","month"),("일주","day"),("시주","hour")]
        if (v := pillars.get(key))
    ])
    trait = ILGAN_TRAITS.get(ilgan, {})
    ilgan_text = f"{ilgan}({trait.get('오행','')}) — 성격: {trait.get('성격','')}, 단점: {trait.get('단점','')}"

    daeun_text = ""
    if len(daeun) > 2:
        cur = daeun[2]
        daeun_text = f"현재 대운: {cur['hanja']}({cur.get('korean','')}) {cur['start']}~{cur['end']}세"

    reading_text = "\n".join([f"  [{r['title']}]: {r['content']}" for r in reading])

    user_prompt = f"""【내담자 사주 데이터】
사주 기둥: {pillar_text}
일간: {ilgan_text}
성별: {gender}
{daeun_text}
2026 세운: {seun}

【기존 계산 데이터】
{reading_text}

위 시스템 지침의 10개 항목 순서대로 풀이를 작성해 주세요.
JSON 형식으로만 응답하세요 (코드블록 없이):
{{
  "ai_readings": [
    {{"title": "1. 사주 기본 구성 분석 — 일간", "content": "4-6문장"}},
    {{"title": "2. 오행 분포 — 장점 5가지", "content": "4-6문장"}},
    {{"title": "3. 오행 분포 — 단점과 실제 삶의 예시", "content": "4-6문장"}},
    {{"title": "4. 월지 — 사회생활과 직업운", "content": "4-6문장"}},
    {{"title": "5. 시주 — 말년운과 자녀·결실", "content": "4-6문장"}},
    {{"title": "6. 대운 흐름 — 현재 대운 분석", "content": "4-6문장"}},
    {{"title": "7. 2026년 세운 분석", "content": "4-6문장"}},
    {{"title": "8. 십성 구조 — 내 성격의 핵심", "content": "4-6문장"}},
    {{"title": "9. 신살 — 특수한 기운", "content": "4-6문장"}},
    {{"title": "10. 종합 조언", "content": "4-6문장"}}
  ],
  "overall": "지금 이 사람에게 가장 필요한 메시지와 앞으로 3년 흐름 요약 (5-7문장)"
}}"""

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SAJU_SYSTEM,
                    max_output_tokens=8000,
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[AI saju error] attempt {attempt+1}: {e}")
    return {}

def generate_decade_reading(birth_year: int, pillars: dict, ilgan: str, daeun: list, gender: str) -> list:
    """연대별(10대~70대) 인생 흐름을 Gemini로 해석. 실패 시 빈 리스트 반환."""
    client = get_gemini_client()
    if not client:
        return []

    current_year = 2026
    trait = ILGAN_TRAITS.get(ilgan, {})
    pillar_text = " / ".join([
        f"{label} {v['hanja']}({v['korean']})"
        for label, key in [("년주","year"),("월주","month"),("일주","day"),("시주","hour")]
        if (v := pillars.get(key))
    ])

    # 각 연대(10대~70대)에 해당하는 대운 매핑
    decades = []
    for decade_start in range(10, 80, 10):
        decade_end = decade_start + 9
        year_start = birth_year + decade_start
        year_end = birth_year + decade_end
        # 이 연대에 걸치는 대운 찾기
        matching = [d for d in daeun if d['start'] < decade_end and d['end'] > decade_start]
        daeun_info = " / ".join([f"{d['hanja']}({d['korean']}) {d['start']}~{d['end']}세" for d in matching])
        is_past = (birth_year + decade_end) < current_year
        is_current = (birth_year + decade_start) <= current_year <= (birth_year + decade_end)
        status = "과거" if is_past else ("현재" if is_current else "미래")
        decades.append({
            "label": f"{decade_start}대",
            "age_range": f"{decade_start}~{decade_end}세",
            "years": f"{year_start}~{year_end}년",
            "daeun": daeun_info or "대운 정보 없음",
            "status": status,
        })

    decades_text = "\n".join([
        f"  {d['label']} ({d['age_range']}, {d['years']}, {d['status']}) — 대운: {d['daeun']}"
        for d in decades
    ])

    user_prompt = f"""【내담자 사주】
출생년도: {birth_year}년 / 성별: {gender}
사주 기둥: {pillar_text}
일간: {ilgan}({trait.get('오행','')}) — {trait.get('성격','')}

【연대별 대운 흐름】
{decades_text}

위 사주와 대운 흐름을 바탕으로 각 연대의 인생을 풀이해주세요.
- 과거 연대: "이 시기에는 ~했을 것입니다" 형식으로 회고적으로
- 현재 연대: "지금 이 시기는 ~" 형식으로 현재형으로
- 미래 연대: "~할 것입니다 / ~에 주의하세요" 형식으로 예언적으로
- 각 연대별 3-4문장, 대운의 오행 에너지와 일간 기질을 반드시 연결하세요

JSON 형식으로만 응답하세요 (코드블록 없이):
{{
  "decades": [
    {{"label": "10대", "status": "과거/현재/미래", "content": "3-4문장 해석"}},
    {{"label": "20대", "status": "...", "content": "..."}},
    {{"label": "30대", "status": "...", "content": "..."}},
    {{"label": "40대", "status": "...", "content": "..."}},
    {{"label": "50대", "status": "...", "content": "..."}},
    {{"label": "60대", "status": "...", "content": "..."}},
    {{"label": "70대", "status": "...", "content": "..."}}
  ]
}}"""

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SAJU_SYSTEM,
                    max_output_tokens=6000,
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.text).get("decades", [])
        except Exception as e:
            print(f"[decade reading error] attempt {attempt+1}: {e}")
    return []

def generate_ai_tarot_reading(result_cards: list, spread_name: str, question: str = "", saju_context: dict = None) -> dict:
    """Gemini API로 AI 타로 해석 생성. 실패 시 빈 dict 반환."""
    client = get_gemini_client()
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

    n = len(result_cards)
    pos_list = " / ".join([f"{i+1}.{c['position_name']}({c['card_name']})" for i, c in enumerate(result_cards)])
    sec1_min = n * 2
    conclusion = f'"{question}"에 직접 답하고 사주 기질에 맞는 조언으로 마무리' if question else '사주 기질에 맞는 구체적 조언으로 마무리'
    overall_guide = (
        f'① 위치별 흐름({sec1_min}문장 이상): 포지션 [{pos_list}]을 번호 순서대로 하나도 빠짐없이 각 2-3문장씩 서술. '
        f'형식: "N번 [포지션명] 자리에 [카드명]이 나왔다는 것은..." — 모든 {n}개 포지션 반드시 언급. '
        f'② 위치 간 연결(5문장 이상): 공명·긴장·강화 관계인 포지션 쌍을 명시적으로 연결, 오행·슈트 패턴, 대운·세운 맞물림. '
        f'③ 종합 결론(3-5문장): {conclusion}. '
        f'— 총 {sec1_min + 8}문장 이상, 절대 생략 없이 전체 서술'
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

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_AI_SYSTEM,
                    max_output_tokens=16000,
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[AI reading error] attempt {attempt+1}: {e}")
    return {}

app = FastAPI(title="사주타로 API")

# 🔒 CORS: 기본 전체(*) 제거 → 프론트 origin 화이트리스트. 필요 시 CORS_ORIGINS 환경변수로 오버라이드(콤마구분).
_CORS_DEFAULT = "https://taehyun1121.github.io,https://gosamtarot.com,https://www.gosamtarot.com,http://localhost:5173"
_CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", _CORS_DEFAULT).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
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

    ai = generate_ai_saju_reading(pillars, dp[0], daeun, seun, reading_list, req.gender)
    decades = generate_decade_reading(req.year, pillars, dp[0], daeun, req.gender)

    return {
        "pillars": pillars,
        "ilgan": dp[0],
        "daeun": daeun,
        "seun": seun,
        "reading": reading_list,
        "ai_readings": ai.get("ai_readings", []),
        "ai_overall": ai.get("overall", ""),
        "decade_readings": decades,
        "ai_available": bool(ai),
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

@app.get("/health")
def health():
    return {"status": "ok"}
