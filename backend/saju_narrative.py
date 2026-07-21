"""Gemini(AI) 없이도 동작하는 규칙기반 사주 서술 생성 — full_report()의 명리학 진단
(왕쇠/용신/격국/십성구조)을 사주봇 검증완료 로직 그대로 쓰고, 그 판정을 문장으로
매핑만 한다. 지어내는 부분(신살 등 미구현 판정) 없이, 계산된 값만 서술.

generate_ai_saju_reading()/generate_decade_reading()과 동일한 반환 형태를 맞춰서
main.py에서 Gemini 실패 시 그대로 자리 교체 가능.
"""

from saju_rule_engine import full_report, daewoon_direction, sipseong_counts, sinsal_and_stages_report, STEM_OHAENG, STEMS, ohaeng_count, sipseong
from saju_fortune_curve import score_curve, elem_of_yongsin_label, ke_source
from saju import month_pillar

MONTH_KOR = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]

# 2026-07-21 사주봇 외부리서치(데이사주·사주한눈에 등) 반영 — 오행 레이더차트 + 인생그래프(라인차트)
OHAENG_ORDER = ["木", "火", "土", "金", "水"]
OHAENG_COLOR = {"木": "#3fa76a", "火": "#c0392b", "土": "#c9a24b", "金": "#d8dde8", "水": "#2a52b5"}


def ohaeng_radar_svg(counts: dict, size=260) -> str:
    """오행 5축 레이더차트. counts: {"木":n,"火":n,...} — ohaeng_count() 결과 그대로."""
    cx = cy = size / 2
    r_max = size * 0.36
    max_count = max(3, max(counts.values()) if counts else 3)
    angles = [(-90 + i * 72) * 3.14159265 / 180 for i in range(5)]

    def pt(elem_idx, value):
        ratio = min(1.0, value / max_count)
        r = r_max * ratio
        import math
        return cx + r * math.cos(angles[elem_idx]), cy + r * math.sin(angles[elem_idx])

    import math
    grid_polys = []
    for level in (0.33, 0.66, 1.0):
        pts = " ".join(f"{cx + r_max*level*math.cos(a):.1f},{cy + r_max*level*math.sin(a):.1f}" for a in angles)
        grid_polys.append(f'<polygon points="{pts}" fill="none" stroke="rgba(212,175,55,.18)" stroke-width="1"/>')
    axis_lines = "".join(
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx+r_max*math.cos(a):.1f}" y2="{cy+r_max*math.sin(a):.1f}" stroke="rgba(212,175,55,.18)" stroke-width="1"/>'
        for a in angles
    )
    data_pts = [pt(i, counts.get(elem, 0)) for i, elem in enumerate(OHAENG_ORDER)]
    data_poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in data_pts)
    labels = "".join(
        f'<text x="{cx+r_max*1.22*math.cos(a):.1f}" y="{cy+r_max*1.22*math.sin(a):.1f}" '
        f'text-anchor="middle" dominant-baseline="middle" fill="{OHAENG_COLOR[elem]}" font-size="15" font-weight="900">{elem}({counts.get(elem,0)})</text>'
        for a, elem in zip(angles, OHAENG_ORDER)
    )
    return (
        f'<svg viewBox="0 0 {size} {size}" width="100%" height="{size}">'
        f'{"".join(grid_polys)}{axis_lines}'
        f'<polygon points="{data_poly}" fill="rgba(42,82,181,.32)" stroke="#e3c069" stroke-width="2.5"/>'
        + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#e3c069"/>' for x, y in data_pts)
        + labels + "</svg>"
    )


def curve_line_graph_svg(curve: list, width=720, height=200) -> str:
    """세운 81개(3~83세) '인생그래프' — 라인+영역 차트. curve: score_curve()의 curve 리스트."""
    pad_l, pad_r, pad_t, pad_b = 36, 12, 14, 22
    w = width - pad_l - pad_r
    h = height - pad_t - pad_b
    n = len(curve)
    if n < 2:
        return ""

    def xy(i, score):
        x = pad_l + (i / (n - 1)) * w
        y = pad_t + (1 - score / 100) * h
        return x, y

    pts = [xy(i, c["score"]) for i, c in enumerate(curve)]
    path_d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area_d = path_d + f" L{pts[-1][0]:.1f},{pad_t+h:.1f} L{pts[0][0]:.1f},{pad_t+h:.1f} Z"
    baseline_y = pad_t + (1 - 50/100) * h
    tick_idx = [i for i, c in enumerate(curve) if c["age"] % 10 == 0]
    ticks = "".join(
        f'<text x="{pts[i][0]:.1f}" y="{height-4}" text-anchor="middle" fill="#7f8aa8" font-size="8.5">{curve[i]["age"]}세</text>'
        for i in tick_idx
    )
    peak_i = max(range(n), key=lambda i: curve[i]["score"])
    worst_i = min(range(n), key=lambda i: curve[i]["score"])
    markers = "".join(
        f'<circle cx="{pts[i][0]:.1f}" cy="{pts[i][1]:.1f}" r="4" fill="{color}"/>'
        f'<text x="{pts[i][0]:.1f}" y="{pts[i][1]-8:.1f}" text-anchor="middle" fill="{color}" font-size="8.5" font-weight="700">{curve[i]["age"]}세</text>'
        for i, color in [(peak_i, "#3fa76a"), (worst_i, "#c0392b")]
    )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}">'
        f'<defs><linearGradient id="areafill" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#2a52b5" stop-opacity=".38"/><stop offset="1" stop-color="#2a52b5" stop-opacity="0"/></linearGradient></defs>'
        f'<line x1="{pad_l}" y1="{baseline_y:.1f}" x2="{width-pad_r}" y2="{baseline_y:.1f}" stroke="rgba(255,255,255,.12)" stroke-dasharray="3 4"/>'
        f'<path d="{area_d}" fill="url(#areafill)"/>'
        f'<path d="{path_d}" fill="none" stroke="#e3c069" stroke-width="2"/>'
        f'{markers}{ticks}</svg>'
    )

# 2026-07-21 사주봇 외부검증 참조표 기반(namu.wiki·sajustudy.com 등 교차대조) — 표준 의미만, 지어내기 없음.
STAGE_MEANING = {
    "장생": "새로운 시작 — 태동하는 기운", "목욕": "변화·불안정 — 형태를 갖춰가는 과도기",
    "관대": "성장·독립 준비 — 틀을 갖추는 시기", "건록": "전성기 시작 — 자립하는 힘",
    "제왕": "최고조 — 힘이 가장 강한 정점", "쇠": "하강 시작 — 원숙하지만 기세는 꺾임",
    "병": "쇠약 — 휴식이 필요한 시기", "사": "정지 — 흐름이 멈추는 전환점",
    "묘": "침잠 — 안으로 갈무리하는 시기", "절": "단절 — 옛 흐름이 끊기는 지점",
    "태": "잉태 — 다음 순환의 씨앗", "양": "양육 — 다음 도약을 준비하는 기간",
}
SINSAL_MEANING = {
    "겁살": "상실·강제적 변화에 노출되기 쉬움", "재살": "관재·구설에 얽히기 쉬움",
    "천살": "천재지변 등 불가항력적 변수", "지살": "이동·새로운 시작의 기운",
    "년살": "인기·매력이 드러나는 기운(도화)", "월살": "기운이 고갈되고 정체되기 쉬움",
    "망신살": "체면·평판이 흔들리기 쉬움", "장성살": "권위·리더십이 강해지는 기운",
    "반안살": "안정·명예가 따르는 기운", "역마살": "이동·타지·해외와 인연",
    "육해살": "관재·건강 문제에 주의 필요", "화개살": "예술·종교성, 홀로 깊어지는 기운",
}

SIPSEONG_MEANING = {
    "비견": "형제·동료·독립심 — 스스로 서려는 힘, 협력과 경쟁이 공존",
    "겁재": "재물·기회를 두고 겨루는 힘 — 승부욕, 형제자매·동업 관계의 변수",
    "식신": "표현력·재능·의식주의 여유 — 느긋하게 풀어내는 재주",
    "상관": "비판·재기·자기표현 — 규칙을 넘어서려는 기질, 예리한 언변",
    "편재": "유동적 재물·사업수완 — 활동적으로 벌어들이는 돈",
    "정재": "고정적 재물·성실함 — 차곡차곡 쌓이는 안정적 수입",
    "편관": "권력·통제·도전(칠살) — 강한 승부욕과 위기대응력",
    "정관": "명예·직위·책임감 — 원칙과 질서를 따르는 힘",
    "편인": "특수학문·직관·의존성 — 변칙적이고 독창적인 사고",
    "정인": "학문·문서·인덕 — 보호받고 배우는 힘",
}


def _wangso_line(wangso):
    verdict = wangso["verdict"]
    tone = "스스로 힘이 강해 자기 주도로 밀고 나가는 구조" if verdict == "신강" else "주변 기운의 도움을 받아야 힘을 쓰는 구조"
    override = f" {wangso['override']}." if wangso.get("override") else ""
    return f"일간이 {verdict}(득세 점수 {wangso['score']}점, 판정 확신도 {wangso['confidence']})으로 나옵니다. {tone}입니다.{override}"


def rule_based_ai_reading(pillars: dict, ilgan: str, ilgan_trait: dict, daeun: list, seun: str,
                            gender: str, engine_pillars, has_hour: bool) -> dict:
    rep = full_report("api", engine_pillars, gender)
    wangso, yongsin, gyeok, jong, patterns = rep["wangso"], rep["yongsin"], rep["gyeok"], rep["jong"], rep["patterns"]
    dw_dir = daewoon_direction(engine_pillars.year[0], gender)
    cur_daeun = daeun[2] if len(daeun) > 2 else (daeun[0] if daeun else None)
    ohaeng = ilgan_trait.get("오행", ilgan)
    seong = ilgan_trait.get("성격", "고유한 기질")
    dan = ilgan_trait.get("단점", "균형 조절")

    sections = []

    sections.append(("1. 사주 기본 구성 분석 — 일간",
        f"{ohaeng} 일간이시고, {seong} 기질을 타고나셨습니다. {_wangso_line(wangso)} "
        f"이 구조를 기준으로 아래 풀이가 이어집니다."))

    sections.append(("2. 오행 분포 — 장점 5가지",
        f"타고난 장점은 {seong}으로 요약됩니다. 명식에서 도움이 되는 기운(용신)은 {yongsin['용신']}이며, "
        f"근거는 {yongsin['근거']} — {yongsin['설명']}입니다. 이 기운과 맞닿는 환경·관계·선택을 늘릴수록 "
        f"본래 장점이 자연스럽게 발휘됩니다."))

    pattern_text = " ".join(f"{p}." for p in patterns) if patterns else "원국 자체의 극단적인 편중 구조는 확인되지 않았습니다."
    sections.append(("3. 오행 분포 — 단점과 실제 삶의 예시",
        f"주의할 부분은 {dan}입니다. 구조적으로는 {pattern_text} "
        f"이런 흐름이 강하게 나타나는 시기엔 위 단점이 더 도드라질 수 있어 미리 인지해두는 것이 도움이 됩니다."))

    sections.append(("4. 월지 — 사회생활과 직업운",
        f"격국은 {gyeok['격']}으로 판정됩니다({gyeok['판정근거']}). "
        f"용신({yongsin['용신']}) 방향과 맞는 분야·역할일수록 사회생활에서 힘을 덜 들이고도 성과가 따라옵니다."))

    if has_hour:
        sections.append(("5. 시주 — 말년운과 자녀·결실",
            f"시주까지 포함해 판정한 결과라 말년·자녀 관련 해석의 신뢰도가 상 등급입니다. "
            f"{dw_dir}(대운 순역) 흐름을 기준으로, 앞으로의 대운이 용신({yongsin['용신']}) 방향과 맞아떨어지는 "
            f"시기에 결실이 두드러집니다."))
    else:
        sections.append(("5. 시주 — 말년운과 자녀·결실",
            "시주(태어난 시간) 정보가 없어 말년·자녀운은 확정 판정 대신 참고용으로만 안내드립니다. "
            "정확한 시간을 아신다면 다시 입력해 주시면 더 정밀한 풀이가 가능합니다."))

    if cur_daeun:
        sections.append(("6. 대운 흐름 — 현재 대운 분석",
            f"현재 대운은 {cur_daeun['hanja']}({cur_daeun['korean']}) {cur_daeun['start']}~{cur_daeun['end']}세 구간입니다. "
            f"대운은 {dw_dir}으로 흐르며, 이 시기가 용신({yongsin['용신']})과 가까운지 먼지에 따라 체감 난이도가 달라집니다."))
    else:
        sections.append(("6. 대운 흐름 — 현재 대운 분석", f"대운은 {dw_dir}으로 흐르는 구조입니다."))

    sections.append(("7. 2026년 세운 분석",
        f"2026년 세운은 {seun}입니다. 이 해의 기운이 용신({yongsin['용신']})을 돕는 방향인지, "
        f"기신(용신과 반대)에 가까운지에 따라 한 해의 체감이 갈립니다 — 용신에 가까울수록 수월하고, "
        f"반대일수록 평소보다 신중함이 필요한 해입니다."))

    grp = rep.get("gyeok", {})  # placeholder to keep structure explicit
    sections.append(("8. 십성 구조 — 내 성격의 핵심",
        (f"성격의 핵심 구조로 {'; '.join(patterns)}가 확인됩니다. " if patterns else "십성 분포상 특별히 튀는 과다·과소 구조는 없어, 비교적 균형 잡힌 성격 구조로 보입니다. ")
        + f"기본 기질({seong})과 결합해서 보면, 이 구조가 대인관계·의사결정 방식에 직접 영향을 줍니다."))

    jong_text = (f"종격 후보로 분류됩니다({jong['종류']}) — 일반적인 억부 판단과 다른 특수 구조라 해석에 참고가 필요합니다."
                 if jong["종격후보"] else "일반적인 정격 구조로, 별도의 특수 판정 사항은 없습니다.")
    sections.append(("9. 신살 — 특수한 기운",
        f"{jong_text} (이 리포트는 검증된 왕쇠/용신/격국 판정만 다루며, 도화·역마 등 개별 신살 판정은 별도 항목이라 포함하지 않았습니다.)"))

    sections.append(("10. 종합 조언",
        f"정리하면 {ohaeng} 일간의 {wangso['verdict']} 구조이고, {yongsin['용신']}을 용신으로 삼는 사주입니다. "
        f"이 방향에 맞는 선택을 늘리고, {dan}을 스스로 인지하고 다듬어 나가시면 원국이 가진 흐름을 "
        f"무리 없이 타고 갈 수 있습니다."))

    return {
        "ai_readings": [{"title": t, "content": c} for t, c in sections],
        "overall": (f"지금 이 사주는 {ohaeng} 일간의 {wangso['verdict']} 구조로, {yongsin['용신']}이 용신입니다. "
                    f"격국은 {gyeok['격']}이며 대운은 {dw_dir}으로 흐릅니다. 용신 방향에 맞는 환경·관계를 "
                    f"의식적으로 선택하시고, {dan} 부분만 스스로 다듬으면 지금 흐름을 안정적으로 이어가실 수 있습니다."),
    }


def extended_report_sections(engine_pillars, daeun: list, gender: str, birth_year: int) -> dict:
    """50페이지 확장 리포트(결제완료 PDF 전용) 섹션 — 전부 이미 검증된 계산값을
    더 촘촘히 노출하는 것뿐, 새 판정 로직(신살·12운성·형충회합파)은 사주봇 참조표
    확보 전까지 포함하지 않음(지어내기 금지)."""
    rep = full_report("extended", engine_pillars, gender)
    wangso, yongsin, gyeok, jong = rep["wangso"], rep["yongsin"], rep["gyeok"], rep["jong"]
    dw_dir = daewoon_direction(engine_pillars.year[0], gender)

    # ① 대운 전체 구간(보통 8~9개) — 용신과의 근접도로 한 줄씩
    full_daeun = []
    for d in daeun:
        full_daeun.append({
            "range": f"{d['start']}~{d['end']}세", "ganji": f"{d['hanja']}({d['korean']})",
            "note": f"대운 {dw_dir} {d['start']}번째 구간. 용신({yongsin['용신']})과의 관계에 따라 이 10년의 체감 난이도가 갈립니다.",
        })

    # ② 십성 10개 전체 분포
    counts = sipseong_counts(engine_pillars)
    sipseong_full = [
        {"name": name, "count": counts.get(name, 0), "meaning": SIPSEONG_MEANING[name]}
        for name in SIPSEONG_MEANING
    ]

    # ②-보조 오행 레이더차트(사주봇 외부리서치: 업계표준 시각화 패턴)
    oheng_svg = ohaeng_radar_svg(ohaeng_count(engine_pillars))

    # ③ 세운 연도별 전체(3~83세, 81개) — 숫자만 나열하면 의미 없어서(2026-07-21 주인 지적)
    # 점수 미니바(시각화) + 한줄해설 붙임. 디자인봇이 정식 밀도표 컴포넌트로 착수하면 교체 예정.
    curve = score_curve(engine_pillars, gender, birth_year,
                         daewoon_su=(daeun[0]["start"] if daeun else None), age_range=(3, 83))["curve"]

    def _seun_tier(score):
        if score >= 75: return "기회가 크게 열리는 해"
        if score >= 55: return "안정적으로 흘러가는 해"
        if score >= 35: return "평이한 흐름의 해"
        return "신중함이 필요한 해"

    seun_table = [{"age": c["age"], "year": c["year"], "ganji": c["sewoon"], "score": round(c["score"]),
                   "one_line": _seun_tier(c["score"])} for c in curve]
    curve_svg = curve_line_graph_svg(curve)   # '인생그래프'(사주봇 리서치: 업계 통용 라인차트 패턴)

    # ④ 격국 성립/파격 근거 — 이미 계산된 gyeok/jong을 서술로 풀어냄(새 판정 없음)
    gyeok_detail = (
        f"이 사주의 격국은 {gyeok['격']}입니다. 판정 근거는 '{gyeok['판정근거']}' — "
        f"월지({gyeok['격지지']})에서 격을 정하는 천간({gyeok['격간']})을 뽑아 일간과의 관계로 격명을 확정했습니다. "
    )
    if jong["종격후보"]:
        gyeok_detail += (
            f"다만 왕쇠 점수가 극단({wangso['score']}점)에 가까워 종격 후보({jong['종류']})로도 검토됩니다 — "
            f"뿌리 유무: {'있음(' + ', '.join(jong['뿌리']) + ')' if jong['뿌리'] else '없음'}. "
            f"일반 격국과 종격은 해석 방향이 반대라 두 가능성을 함께 참고하시는 게 정확합니다."
        )
    else:
        gyeok_detail += "왕쇠가 극단적이지 않아 종격(특수격) 가능성 없이, 이 격국 판정을 그대로 따르면 됩니다."

    # ⑤ 12운성·12신살·형충회합파해·귀인흉신 — 사주봇 외부검증 참조표(2026-07-21) 기반
    sinsal_rep = sinsal_and_stages_report(engine_pillars, engine_pillars.day[0])
    stages_full = [{"label": s["label"], "stage": s["stage"], "meaning": STAGE_MEANING.get(s["stage"], "")}
                   for s in sinsal_rep["stages"]]
    sinsal_full = [{"label": s["label"], "sinsal": s["sinsal"], "meaning": SINSAL_MEANING.get(s["sinsal"], "")}
                   for s in sinsal_rep["sinsals"]]

    # ⑥ 월운(月建) — 현재년도(2026) 기준. 절기 근사치 오차 disclaimer 포함(사주봇 캐치).
    wolun = monthly_fortune(2026, yongsin["용신"])

    # ⑦ 연애 인연 — 좋은 인연(정관/정재) vs 주의 인연(편관/편재), 2026-07-21 사주봇 외부검증
    # (여명=관성, 남명=재성 기준. sipseong() 재사용만, 새 계산 없음).
    love_matches = []
    good_key, care_key = ("정관", "편관") if gender == "여" else ("정재", "편재")
    for c in curve:
        se_stem_idx = STEMS.index(c["sewoon"][0])
        ss = full_report.__globals__["sipseong"](STEMS.index(engine_pillars.day[0]), se_stem_idx)
        if ss == good_key:
            love_matches.append({"age": c["age"], "year": c["year"], "kind": "good", "sipseong": ss})
        elif ss == care_key:
            love_matches.append({"age": c["age"], "year": c["year"], "kind": "care", "sipseong": ss})
    # 우호적 흐름 연속 구간 길이(개월수 지어내기 아님 — 연속 "해" 카운트만, 사주봇 권장 프레이밍)
    def _consecutive_runs(items):
        runs, cur = [], []
        for it in items:
            if cur and it["age"] == cur[-1]["age"] + 1:
                cur.append(it)
            else:
                if cur: runs.append(cur)
                cur = [it]
        if cur: runs.append(cur)
        return [{"start_age": r[0]["age"], "end_age": r[-1]["age"], "start_year": r[0]["year"],
                 "end_year": r[-1]["year"], "years": len(r)} for r in runs if len(r) >= 1]
    good_runs = _consecutive_runs([m for m in love_matches if m["kind"] == "good"])
    care_runs = _consecutive_runs([m for m in love_matches if m["kind"] == "care"])

    return {"full_daeun": full_daeun, "sipseong_full": sipseong_full, "oheng_svg": oheng_svg,
            "seun_table": seun_table, "gyeok_detail": gyeok_detail, "curve_svg": curve_svg,
            "stages_full": stages_full, "sinsal_full": sinsal_full,
            "relations": sinsal_rep["relations"], "gwiin": sinsal_rep["gwiin"],
            "wolun": wolun, "good_love_runs": good_runs, "care_love_runs": care_runs}


def monthly_fortune(target_year: int, yongsin_label: str) -> dict:
    """월운(月建) 세부 — 2026-07-21 사주봇 외부검증 오호둔가 공식(saju.py month_pillar()가
    이미 동일 공식 사용 중). 각 월 15일(절기 경계에서 가장 먼 안전지점)을 대표일로 계산.
    🔴 사주봇 캐치: saju.py의 절기 판정(JEOLGI)이 근사 하드코딩이라, 절기 경계 ±1~2일에
    걸친 실제 생일은 월이 하나 밀릴 수 있음 — 월운은 세운보다 이 오차에 더 자주 부딪힘.
    리포트에 명시적으로 안내(disclaimer=True)."""
    yongsin_elem = elem_of_yongsin_label(yongsin_label)
    gisin_elem = ke_source(yongsin_elem)
    months = []
    for m in range(1, 13):
        stem, branch, hanja = month_pillar(target_year, m, 15)
        stem_elem = STEM_OHAENG[STEMS.index(stem)]
        if stem_elem == yongsin_elem:
            one_line = "용신과 같은 기운 — 비교적 수월하게 흘러가는 달"
        elif stem_elem == gisin_elem:
            one_line = "기신과 같은 기운 — 평소보다 신중함이 필요한 달"
        else:
            one_line = "무난하게 지나가는 달"
        months.append({"month": MONTH_KOR[m-1], "ganji": f"{hanja}({stem}{branch})", "one_line": one_line})
    return {"year": target_year, "months": months,
            "disclaimer": "월운은 절기(입춘 등) 경계를 기준으로 나뉘는데, 이 계산은 근사치를 씁니다. "
                           "생일이나 조회일이 절기 경계 ±1~2일 근처라면 실제 월과 하나 어긋날 수 있습니다."}


def rule_based_decade_reading(decades: list, ilgan_trait: dict, engine_pillars, gender: str) -> list:
    rep = full_report("decade", engine_pillars, gender)
    yongsin_label = rep["yongsin"]["용신"]
    tone_by_status = {
        "과거": "이 시기는 {daeun} 기운이 흘렀던 구간입니다. 지나온 시기로, 이 대운 기운이 지금의 바탕을 만들었습니다.",
        "현재": "지금 이 시기는 {daeun} 기운 위에 있습니다. 용신({yongsin})과의 관계에 따라 체감이 갈리는 구간입니다.",
        "미래": "앞으로 올 이 시기는 {daeun} 기운입니다. 용신({yongsin})과 가까운 흐름이면 수월하고, 멀면 신중함이 필요합니다.",
    }
    out = []
    for d in decades:
        tmpl = tone_by_status.get(d["status"], tone_by_status["미래"])
        content = tmpl.format(daeun=d["daeun"], yongsin=yongsin_label)
        out.append({"label": d["label"], "status": d["status"], "content": content})
    return out
