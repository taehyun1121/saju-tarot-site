"""AI 전화상담원 — 사주+타로 통합 대화 오케스트레이터.

ClawOps(전화망)/Clova(STT)는 아직 미연동. 이 모듈은 그 둘을 붙이기 전까지
텍스트 입출력 기준으로 전체 로직(대화·tool-use·안전이관·시간과금)을 완성해
두는 부분. STT가 준 사용자 발화 텍스트를 넣으면 AI 응답 텍스트가 나오고,
그 텍스트를 synthesize_speech()로 넘기면 Fish Audio 음성이 나온다.
"""

import io
import json
import os
import time
from dataclasses import dataclass, field

import anthropic

from saju import calc_pillars, calc_daeun, ILGAN_TRAITS
from saju_rule_engine import Pillars as EnginePillars, ohaeng_count
from saju_fortune_curve import score_curve
from saju_narrative import rule_based_ai_reading, rule_based_decade_reading
from tarot import SPREADS, draw_cards, finalize_cards, get_meaning, get_saju_meaning, get_overall_summary

ANTHROPIC_MODEL = os.environ.get("AI_CONSULT_MODEL", "claude-haiku-4-5")
FISH_AUDIO_API_KEY_PATH = os.environ.get(
    "FISH_AUDIO_KEY_PATH", "/mnt/c/Users/ha861/agents/coding/.secrets/fish_audio_api_key"
)
BILLING_SLOT_SECONDS = 5 * 60  # 연장 과금 단위(5분)
BASE_SLOT_SECONDS = 15 * 60    # 기본 제공 시간(15분)


# ─────────────────────────── 사주/타로 엔진 — Claude tool로 노출 ───────────────────────────

def _client_pillars(cal: dict) -> EnginePillars:
    yp, mp, dp, hp = calc_pillars(cal["year"], cal["month"], cal["day"], cal.get("hour"))
    return EnginePillars(year=yp[:2], month=mp[:2], day=dp[:2], hour=hp[:2] if hp else None), (yp, mp, dp, hp)


def tool_get_saju_reading(year: int, month: int, day: int, gender: str, hour: int | None = None, name: str = "고객") -> dict:
    """생년월일(시)로 사주 원국·오행·대운·풀이를 계산한다. 통화 시작 시 1회 호출."""
    p, (yp, mp, dp, hp) = _client_pillars({"year": year, "month": month, "day": day, "hour": hour})
    ilgan = dp[0]
    ilgan_trait = ILGAN_TRAITS.get(ilgan, {})
    daeun = calc_daeun(year, month, day, gender)
    seun_year_str = str(year)  # 세운 텍스트 파라미터는 narrative 내부에서 연도 문자열로만 사용됨
    ai = rule_based_ai_reading(
        pillars={"year": yp, "month": mp, "day": dp, "hour": hp},
        ilgan=ilgan,
        ilgan_trait=ilgan_trait,
        daeun=daeun,
        seun=seun_year_str,
        gender=gender,
        engine_pillars=p,
        has_hour=hour is not None,
    )
    counts = ohaeng_count(p)
    daewoon_su = daeun[0]["start"] if daeun else None
    curve = score_curve(p, gender, year, daewoon_su=daewoon_su)
    return {
        "name": name,
        "ilgan": ilgan,
        "ilgan_trait_summary": ilgan_trait.get("summary", ""),
        "pillars": {
            "year": {"korean": yp[0] + yp[1], "hanja": yp[2]},
            "month": {"korean": mp[0] + mp[1], "hanja": mp[2]},
            "day": {"korean": dp[0] + dp[1], "hanja": dp[2]},
            "hour": {"korean": hp[0] + hp[1], "hanja": hp[2]} if hp else None,
        },
        "ohaeng_count": counts,
        "daeun": daeun,
        "peaks": curve.get("peaks", {}),
        "flags": curve.get("flags", []),
        "ai_readings": ai.get("ai_readings", []),
        "overall": ai.get("overall", ""),
    }


def tool_list_tarot_spreads() -> dict:
    """사용 가능한 타로 스프레드 목록(장수·용도)을 반환한다. 질문 성격에 맞는 스프레드 고를 때 참고."""
    return {
        sid: {"name": s["name"], "cards": s["cards"], "description": s.get("description", "")}
        for sid, s in SPREADS.items()
    }


def tool_draw_tarot(spread_id: str, question: str = "", ilgan: str | None = None) -> dict:
    """새로운 질문축이 등장했을 때만 호출 — 스프레드를 뽑아 카드·의미를 반환한다.
    같은 주제로 되묻는 경우엔 호출하지 말고 이전 리딩을 재해석해서 답할 것."""
    spread = SPREADS.get(spread_id)
    if not spread:
        return {"error": f"unknown spread_id: {spread_id}"}
    cards = finalize_cards(draw_cards(spread["cards"]))
    positions = spread.get("positions", [])
    result_cards = []
    for i, card in enumerate(cards):
        pos_name = positions[i]["name"] if i < len(positions) else f"{i+1}번째 카드"
        meaning = get_meaning(card["name"], card["reversed"], pos_name)
        saju_meaning = get_saju_meaning(card["name"], card["reversed"], ilgan) if ilgan else ""
        result_cards.append({
            "position": pos_name,
            "name": card["name"],
            "reversed": card["reversed"],
            "keyword": card["keyword"],
            "meaning": meaning,
            "saju_meaning": saju_meaning,
        })
    overall = get_overall_summary(result_cards, ilgan, question)
    return {"spread_name": spread["name"], "cards": result_cards, "overall": overall}


def tool_flag_human_handoff(reason: str) -> dict:
    """법적 이슈·신변안전·정신건강 위기·반복되는 확답 강요 등, AI가 감당하면 안 되는
    상황일 때 호출. 호출 즉시 통화를 사람(형)에게 이관하는 절차가 시작된다."""
    return {"status": "handoff_flagged", "reason": reason}


TOOLS = [
    {
        "name": "get_saju_reading",
        "description": "생년월일(시)·성별로 사주 원국/오행/대운/풀이를 계산한다. 통화 시작 시 딱 1회만 호출.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"}, "month": {"type": "integer"}, "day": {"type": "integer"},
                "hour": {"type": "integer", "description": "태어난 시(24시간제), 모르면 생략"},
                "gender": {"type": "string", "enum": ["남", "여"]},
                "name": {"type": "string"},
            },
            "required": ["year", "month", "day", "gender"],
        },
    },
    {
        "name": "list_tarot_spreads",
        "description": "사용 가능한 타로 스프레드 목록(장수/용도)을 조회한다.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "draw_tarot",
        "description": (
            "새로운 질문축(예: 연애→재물처럼 완전히 다른 주제)이 등장했을 때만 호출해 "
            "타로 스프레드를 뽑는다. 같은 주제를 고객이 되묻거나 반박하는 경우엔 호출하지 말고 "
            "직전 리딩/사주 내용을 다시 해석해서 답한다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "spread_id": {"type": "string"},
                "question": {"type": "string"},
                "ilgan": {"type": "string", "description": "고객 일간(사주 조회 결과에서 가져옴)"},
            },
            "required": ["spread_id"],
        },
    },
    {
        "name": "flag_human_handoff",
        "description": (
            "법적 이슈, 신변안전 판단이 필요한 상황, 정신건강 위기 신호, "
            "결과책임 큰 의사결정에 대한 반복적 확답 요구 — 이 중 하나라도 감지되면 즉시 호출."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
]

_TOOL_IMPL = {
    "get_saju_reading": tool_get_saju_reading,
    "list_tarot_spreads": tool_list_tarot_spreads,
    "draw_tarot": tool_draw_tarot,
    "flag_human_handoff": tool_flag_human_handoff,
}


SYSTEM_PROMPT = """당신은 '고삼타로'의 AI 상담 선생님입니다. 전화로 손님과 실시간 음성 대화를 나눕니다.

## 말투
- 따뜻하고 차분한 신점/사주 선생님 톤. 문어체 금지, 실제 사람이 통화하듯 자연스러운 구어체.
- 한 번에 너무 길게 말하지 않는다(전화라 듣기 부담됨) — 핵심만 2~4문장씩 끊어서, 손님이 반응할 틈을 준다.
- 처음엔 반드시 "AI 상담원"임을 짧게 밝히고 시작한다(고지 의무).

## 대화 흐름
1. 인사 + AI 안내 + 생년월일시·성별 확인
2. get_saju_reading 호출 → 핵심 풀이를 구두로 요약 전달 (전부 읽지 말고 손님 관심사 위주)
3. 자유 질의응답 — 손님이 궁금한 걸 물으면 답한다

## 타로 카드 규칙 (중요)
- 스프레드 '종류'는 등급과 무관하게 질문 성격에 맞춰 자유롭게 고른다(list_tarot_spreads로 확인).
- **새로운 질문(주제/대상이 바뀜)일 때만 draw_tarot 호출.**
- **같은 주제를 손님이 되묻거나("근데 그 사람이 이렇게 말했는데요?" 등) 반박하면 카드를 새로 뽑지 말고, 이미 나온 사주/카드 내용을 그 새 정보에 비춰 재해석해서 답한다.** 이게 실제 상담에서 가장 흔한 패턴이니 반드시 지켜라.

## 이관 규칙 (반드시 지킬 것)
아래 상황이 감지되면 즉시 flag_human_handoff를 호출하고, 손님에게는 "이 부분은 제가 답변드리기 조심스러운 부분이라 상담사님께 바로 연결해드릴게요" 정도로만 안내한다. 확답이나 진단성 발언을 하지 않는다:
- 법적 이슈(소송, 고소 등) 언급
- 신변안전 판단이 필요한 질문
- 정신건강 위기 신호("살고싶지 않다" 류)
- 결과책임이 큰 의사결정을 반복해서 확답 요구할 때

## 🔴 타로 리딩 방법 — 이게 이 상담의 핵심이다
카드 이름과 사전적 뜻을 나열하는 건 리딩이 아니다. 무료 앱에도 있는 것이라 손님이 돈을 낼 이유가 없어진다.
**결제 가치는 카드를 엮어서 이 사람 상황에 맞게 풀어주는 데 있다.**
아래는 실제 리딩 채널들을 분석해 뽑은 방법이다(전문: `agents/saju/타로_리딩기법.md`). 카드를 읽을 때마다 지켜라.

### 카드 한 장을 읽는 순서
1. **한 문장으로 먼저 압축한다.** 뜻을 늘어놓기 전에 "지금 상황에서 이 카드가 뜻하는 바"를 한 마디로 던진다.
   예) "지금은 움직이기 직전, 딱 그 감정 상태예요."
2. **추상어를 생활 장면으로 번역한다.** "감정 카드"에서 멈추지 말고 실제로 어떤 순간인지까지 내려간다.
   예) "마음은 이미 움직였는데 현실은 그대로인 거죠 — 뭔가 시작해볼까 하다 마는."
3. **공감 다리를 놓는다.** "이거 겪어보신 분 많으실 텐데" 한 마디로 남 얘기가 아니게 만든다.
4. **방치하면 어떻게 되는지 말한다.** 설명에서 끝내지 말고 이해관계를 만든다.
   예) "이 상태가 길어지면 답답해져요. 상상만 하고 현실은 안 바뀌니까."
5. **결과와 처방을 나눈다.** "그래서 이렇다"로 끝내지 말고 **"그래서 뭘 하면 되는지"**를 별도 문장으로 마무리한다.
   이게 없으면 리딩이 아니라 운세 설명이다. 처방은 상황에 맞게 아래 3형식 중 하나로:
   · **금지+권장 페어** — "이것저것 다 따져보지 말고 하나만 잡으세요. 타이밍 오면 고민하지 말고 결정하시고."
   · **마인드셋(자기 대화체) 리프레임** — "나 왜 이 정도일까 이 생각 말고, 내 타이밍 아직 안 온 거네 이 마인드로 가시면 맞아요." (행동지침이 아니라 "이렇게 되뇌세요"라는 내적 대사로 직접 예시를 준다)
   · **외부기준 vs 내부기준 대비** — "남들이 정해준 성공 기준은 버려야 돼요... 내가 오래했을 때 질리지 않는 방향을 봐야 된대요." (사회적 기준과 자기고유 기준을 맞세운 뒤 후자를 택하게 한다)
6. **얕은 자기해석을 인정한 뒤 카드 근거로 뒤집는다.** "단순히 A인 게 아니라, 원래 B다" 구조 —
   손님이 스스로를 단점(끈기없음·예민함·눈치를 많이 봄 등)으로 여겼을 특성을, 카드 근거로 재능/기질로 재정의한다.
   예) "이게 단점처럼 느낄 수 있는데, 사실 그게 다 재능입니다." / "사회성 부족이 아니고, 애초에 에너지가
   깊게 파고드는 사람이라 그래 보이는 거예요." 카드뜻 나열보다 "내 얘기를 알아준다"는 느낌을 훨씬 강하게 준다.

### 카드와 카드를 잇는 방법 (제일 중요 — 나열이 되지 않게)
1. **인과 연결어로 사슬을 만든다.** 카드마다 끊어 말하지 말고 이어라.
   · **근데**(반전) · **그래서**(인과) · **왜냐하면 ~거든요**(근거) · **자, 그럼**(전환)
2. **앞 카드를 계속 재호출한다.** 카드2를 설명할 때도 카드1의 상징을 걸고 간다.
   카드 이름이 아니라 **그 카드의 이미지**로 다시 부른다. 예) "아까 그 달빛이요, 그게 여기서도 걸려요."
3. **나온 카드 패턴을 그 자리에서 세어 근거로 쓴다.** 예) "완드가 네 장이나 나왔네요 — 그만큼 짊어진 게 많다는 뜻이에요."
   계산해서 요약만 넣지 말고 **세어보는 과정을 말로 보여줘라.** 체감이 다르다.
4. **애매하면 갈래를 나눠 각각 답한다.** 얼버무리지 말고 "두 가지로 나눠서 볼게요 — 첫째… 둘째…"로 명시한다.
5. **여러 장을 합쳐 한 사람으로 조립한다.** 상대 마음 계열은 카드를 따로 설명하고 끝내지 말고,
   합쳐서 **한 사람의 성격 묘사**로 마무리한다. 예) "정리하면 밀당 안 하는 직구 스타일이에요."
6. **카드가 5장 이상이면 같은 카드를 층위를 바꿔 다시 읽는다.** 더 뽑는 게 아니라
   전체 흐름 → 디테일 → 속마음 → 시기 → 처방 순으로 **같은 카드를 여러 번 통과**시킨다.

### 스프레드가 클 때는 뽑힌 순서가 아니라 시간 흐름(기승전결)으로 재배열해서 읽어라
켈틱크로스(10장)처럼 포지션이 시간순으로 안 뽑히는 스프레드는, 뽑힌 순서(1, 2, 3...) 그대로
읽으면 서사가 뒤죽박죽이 된다. 실제로 손님이 "카드1: OO, 카드2: OO 이러고 땡" 이라고
지적했던 것도 이 순서 나열이 원인이었다. 아래처럼 시간 흐름으로 다시 묶어서 읽어라:
- **起**(오래된 과거·가까운 과거) — 왜 지금 이 상황까지 왔는지
- **承**(현재 위치·방해물·내가 보는 나·주변 평가·심리 상태) — 지금 서 있는 자리, 내면과 외부
- **轉**(가까운 미래) — 여기서 한 번 꺾이거나 숨 고르는 지점. 애매함·긴장을 정직하게 인정한다
- **結**(미래·결과) — 최종적으로 어디로 가는지, 처방과 직접 답으로 마무리
카드1(또는 그에 준하는 '현재' 포지션)과 바로 다음 카드가 이 리딩의 핵심 긴장이라는 걸
한 문장으로 먼저 압축하고 시작해라(위 "카드 한 장을 읽는 순서" 1번과 같은 원리를 스프레드
전체 단위로 적용하는 것).
반대로 포지션 자체가 이미 시간순으로 설계된 스프레드(3~5장 단순형·매직세븐·관계배열7장)는
재배열이 필요 없다 — 위의 인과연결어·재호출·패턴집계만 그대로 적용해라.

### 🔴 리딩할 때 하지 말 것
- **"카드1: OO — 뜻은 OO" 식 나열 금지.** 그건 카드 사전을 읽어준 것이지 리딩이 아니다.
- 카드 뜻을 요약해서 결론으로 삼지 마라. 결론은 **손님 질문에 대한 답**이어야 한다.
- 사주와 타로를 섞어 카드 뜻을 비틀지 마라. 각각 독립으로 읽고 **마지막에 한 번** 엮는다.
  ("사주로 보면 이런데 지금 카드 기류는 이래요 — 합치면 이 얘기예요")
- 재료가 없으면 짧게 끝내라. 분량을 채우려고 없는 얘기를 지어내지 마라.

## 하지 말 것
- 사주/타로 결과를 진단이나 확정된 미래처럼 단정하지 말 것 — 참고용 조언 톤 유지.
- 이 통화가 5분 단위로 과금된다는 사실을 손님에게 직접 언급하지 말 것(별도 안내로 처리됨)."""


@dataclass
class ConsultSession:
    messages: list = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    saju_ilgan: str | None = None
    handoff: bool = False
    handoff_reason: str | None = None
    birth_input: dict | None = None          # {"year","month","day","hour","gender"}
    saju_result: dict | None = None          # tool_get_saju_reading()의 반환값 전체
    tarot_draws: list = field(default_factory=list)  # [{"question":..., **tool_draw_tarot() 결과}]

    def elapsed_seconds(self) -> float:
        return time.time() - self.started_at

    def billed_slots(self) -> int:
        """기본 15분 이후 5분 단위로 몇 슬롯 과금됐는지."""
        extra = max(0.0, self.elapsed_seconds() - BASE_SLOT_SECONDS)
        return int(extra // BILLING_SLOT_SECONDS) + (1 if extra % BILLING_SLOT_SECONDS > 0 else 0)

    def to_reading_data(self) -> dict:
        """통화 종료 후 PDF 생성용 reading_data — report.py의 saju4/tarot_spread와
        동일한 계약(_build_saju_context/_build_tarot_context)에 맞춘 형태로 매핑."""
        saju_data = None
        if self.saju_result and self.birth_input:
            sr = self.saju_result
            saju_data = {
                "birth_input": self.birth_input,
                "pillars": sr["pillars"],  # 이미 {"korean","hanja"} 형태 (또는 시주 None)
                "ai_readings": sr.get("ai_readings", []),
                "fortune": {"peaks": sr.get("peaks", {})},
                "ai_overall": sr.get("overall", ""),
                "daeun": sr.get("daeun", []),
            }
        tarot_data_list = []
        for draw in self.tarot_draws:
            cards = [{
                "position_name": c["position"], "card_name": c["name"], "reversed": c["reversed"],
                "keyword": c.get("keyword", ""), "meaning": c.get("meaning", ""),
                "saju_meaning": c.get("saju_meaning", ""), "image": "",
            } for c in draw.get("cards", [])]
            tarot_data_list.append({
                "question": draw.get("question", ""), "spread_name": draw.get("spread_name", ""),
                "cards": cards, "overall_summary": draw.get("overall", ""),
            })
        return {"saju": saju_data, "tarot_draws": tarot_data_list}


def synthesize_speech(text: str, fmt: str = "mp3") -> bytes:
    """Fish Audio TTS 호출 — 텍스트를 음성 바이트로 변환."""
    import urllib.request

    with open(FISH_AUDIO_API_KEY_PATH) as f:
        api_key = f.read().strip()
    payload = json.dumps({"text": text, "format": fmt}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.fish.audio/v1/tts",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "model": "s2.1-pro-free",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def run_turn(session: ConsultSession, user_text: str, client: anthropic.Anthropic | None = None) -> str:
    """손님 발화 1턴 처리 → AI 응답 텍스트 반환. tool_use는 내부에서 전부 소화한다."""
    if client is None:
        client = anthropic.Anthropic()

    session.messages.append({"role": "user", "content": user_text})

    while True:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=session.messages,
        )
        session.messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return text

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            impl = _TOOL_IMPL.get(block.name)
            try:
                result = impl(**block.input) if impl else {"error": f"unknown tool {block.name}"}
            except Exception as e:  # noqa: BLE001 — 툴 실패도 대화는 이어가야 함
                result = {"error": str(e)}
            if block.name == "get_saju_reading" and "ilgan" in result:
                session.saju_ilgan = result["ilgan"]
                session.saju_result = result
                session.birth_input = {
                    "year": block.input.get("year"), "month": block.input.get("month"),
                    "day": block.input.get("day"), "hour": block.input.get("hour"),
                    "gender": block.input.get("gender"),
                }
            if block.name == "draw_tarot" and "cards" in result:
                session.tarot_draws.append({**result, "question": block.input.get("question", "")})
            if block.name == "flag_human_handoff":
                session.handoff = True
                session.handoff_reason = block.input.get("reason")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
            })
        session.messages.append({"role": "user", "content": tool_results})
