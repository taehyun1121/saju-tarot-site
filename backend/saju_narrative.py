"""Gemini(AI) 없이도 동작하는 규칙기반 사주 서술 생성 — full_report()의 명리학 진단
(왕쇠/용신/격국/십성구조)을 사주봇 검증완료 로직 그대로 쓰고, 그 판정을 문장으로
매핑만 한다. 지어내는 부분(신살 등 미구현 판정) 없이, 계산된 값만 서술.

generate_ai_saju_reading()/generate_decade_reading()과 동일한 반환 형태를 맞춰서
main.py에서 Gemini 실패 시 그대로 자리 교체 가능.
"""

from datetime import date

from saju_rule_engine import (full_report, daewoon_direction, sipseong_counts, sinsal_and_stages_report,
                               STEM_OHAENG, STEMS, ohaeng_count, sipseong, CHEONEUL_GWIIN)
from saju_fortune_curve import score_curve, elem_of_yongsin_label, ke_source, dohwa_branch, is_yukhap
from saju import month_pillar

MONTH_KOR = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]

# 일간합(천간합 5종) — 2026-07-21 사주봇 외부검증(이성궁합 좋은 특징 근거)
CHEONGAN_HAP = {"갑":"기","을":"경","병":"신","정":"임","무":"계","기":"갑","경":"을","신":"병","임":"정","계":"무"}

# 2026-07-21 디자인봇 정식 컴포넌트(saju_sections.html/render_sections.py) 데이터계약 그대로 포팅.
# 구조화 dict를 돌려주고, 실제 <svg> 마크업은 Jinja2 템플릿(saju_sections.html)이 그림.
OHAENG_KEY = {"木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water"}
OHAENG_LABEL = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}


def ohaeng_legend(counts: dict) -> list:
    """레이더차트 옆 범례용 — {key,label,count} 5개. counts: ohaeng_count() 결과."""
    return [{"key": OHAENG_KEY[e], "label": OHAENG_LABEL[e], "count": counts.get(e, 0)} for e in ["木", "火", "土", "金", "水"]]


def radar_svg(ohaeng_items: list, size=300) -> dict:
    """오행 레이더 기하 계산(디자인봇 render_sections.py radar_svg 포팅). ohaeng_items=ohaeng_legend() 결과."""
    import math
    cx = cy = size / 2
    R = size * 0.36
    maxv = max([i["count"] for i in ohaeng_items] + [1])
    n = len(ohaeng_items)
    grid = []
    for ring in (0.25, 0.5, 0.75, 1.0):
        rp = [f"{cx+math.cos(-math.pi/2+2*math.pi*k/n)*R*ring:.1f},{cy+math.sin(-math.pi/2+2*math.pi*k/n)*R*ring:.1f}" for k in range(n)]
        grid.append(" ".join(rp))
    pts, labels = [], []
    for k, it in enumerate(ohaeng_items):
        a = -math.pi/2 + 2*math.pi*k/n
        r = R * (it["count"]/maxv if maxv else 0)
        pts.append(f"{cx+math.cos(a)*r:.1f},{cy+math.sin(a)*r:.1f}")
        labels.append({"x": f"{cx+math.cos(a)*(R+22):.1f}", "y": f"{cy+math.sin(a)*(R+22):.1f}",
                        "label": it["label"], "count": it["count"], "key": it["key"]})
    axes = []
    for k in range(n):
        a = -math.pi/2 + 2*math.pi*k/n
        axes.append((f"{cx:.1f}", f"{cy:.1f}", f"{cx+math.cos(a)*R:.1f}", f"{cy+math.sin(a)*R:.1f}"))
    return {"size": size, "cx": f"{cx:.1f}", "cy": f"{cy:.1f}", "grid": grid, "poly": " ".join(pts), "labels": labels, "axes": axes}


def lifegraph_svg(seun: list, W=820, H=220) -> dict:
    """인생그래프 기하 계산(디자인봇 포팅). seun=[{age,year,score},...].
    🔴 2026-07-21 디자인봇 리뷰 캐치: 단순 argmax는 8세 같은 유아기 피크를 뽑을 수 있어
    어색함 — 19세(성년) 이후 구간에서 우선 최댓값을 찾고, 그마저 없을 때만 전체 최댓값으로 폴백."""
    pad_l, pad_r, pad_t, pad_b = 38, 16, 16, 26
    pw, ph = W - pad_l - pad_r, H - pad_t - pad_b
    n = len(seun)

    def X(i): return pad_l + pw * i / (n - 1)
    def Y(s): return pad_t + ph * (1 - s / 100)

    line = " ".join((("M" if i == 0 else "L") + f"{X(i):.1f} {Y(p['score']):.1f}") for i, p in enumerate(seun))
    area = f"M{X(0):.1f} {Y(0):.1f} " + " ".join(f"L{X(i):.1f} {Y(p['score']):.1f}" for i, p in enumerate(seun)) \
        + f" L{X(n-1):.1f} {pad_t+ph:.1f} L{X(0):.1f} {pad_t+ph:.1f} Z"

    adult_idx = [i for i, p in enumerate(seun) if p["age"] >= 19]
    peak_pool = adult_idx if adult_idx else list(range(n))
    smax = max(peak_pool, key=lambda i: seun[i]["score"])
    smin = min(range(n), key=lambda i: seun[i]["score"])
    peak = {"x": f"{X(smax):.1f}", "y": f"{Y(seun[smax]['score']):.1f}", "age": seun[smax]["age"], "score": seun[smax]["score"]}
    trough = {"x": f"{X(smin):.1f}", "y": f"{Y(seun[smin]['score']):.1f}", "age": seun[smin]["age"], "score": seun[smin]["score"]}

    ticks = [{"x": f"{X(i):.1f}", "age": p["age"]} for i, p in enumerate(seun) if p["age"] % 10 == 0]
    warn_x = None
    for i, p in enumerate(seun):
        if p["age"] >= 45:
            warn_x = f"{X(i):.1f}"
            break
    return {"W": W, "H": H, "line": line, "area": area, "peak": peak, "trough": trough, "ticks": ticks,
            "warn_x": warn_x, "right_x": f"{X(n-1):.1f}", "base_y": f"{pad_t+ph:.1f}", "top_y": f"{pad_t:.1f}", "padL": pad_l}


def group_seun_by_decade(seun_table: list) -> list:
    """세운 81개를 10년 단위 그룹으로(디자인봇 밀도표 컴포넌트). seun_table=[{age,year,ganji,score,one_line},...]."""
    groups = []
    cur = None
    for p in seun_table:
        g = (p["age"] // 10) * 10
        if cur is None or cur["g"] != g:
            cur = {"g": g, "title": f"{g if g > 0 else 3}~{g+9}세", "rows": []}
            groups.append(cur)
        row = dict(p)
        row["cls"] = "good" if p["score"] >= 75 else ("warn" if p["score"] <= 35 else "mid")
        cur["rows"].append(row)
    return groups

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

    # 세운(3~83세, 81개) 전체 — 대운 구간별 평균점수 계산에도 필요해서 먼저 계산.
    curve = score_curve(engine_pillars, gender, birth_year,
                         daewoon_su=(daeun[0]["start"] if daeun else None), age_range=(3, 83))["curve"]

    # ① 대운 전체 구간(보통 8~9개) — 구간 평균점수 + 테마 한줄(디자인봇 필드계약: age_range/ganji/score/theme)
    full_daeun = []
    for d in daeun:
        rng_scores = [c["score"] for c in curve if d["start"] <= c["age"] <= d["end"]]
        avg_score = round(sum(rng_scores) / len(rng_scores)) if rng_scores else 50
        full_daeun.append({
            "age_range": f"{d['start']}~{d['end']}세", "ganji": f"{d['hanja']}({d['korean']})", "score": avg_score,
            "theme": f"용신({yongsin['용신']})과의 관계로 본 이 10년의 흐름",
        })

    # ② 십성 10개 전체 분포 — 디자인봇 필드명(short_meaning) 그대로
    counts = sipseong_counts(engine_pillars)
    sipseong_full = [
        {"name": name, "count": counts.get(name, 0), "short_meaning": SIPSEONG_MEANING[name]}
        for name in SIPSEONG_MEANING
    ]

    # ②-보조 오행 레이더차트 — 디자인봇 정식 컴포넌트(구조화 dict, 템플릿이 SVG 그림)
    ohaeng_items = ohaeng_legend(ohaeng_count(engine_pillars))
    radar = radar_svg(ohaeng_items)

    # ③ 세운 연도별 전체(3~83세, 81개) — 숫자만 나열하면 의미 없어서(2026-07-21 주인 지적)
    # 점수 미니바(시각화) + 한줄해설 + 10년단위 그룹(디자인봇 밀도표 컴포넌트).
    def _seun_tier(score):
        if score >= 75: return "기회가 크게 열리는 해"
        if score >= 55: return "안정적으로 흘러가는 해"
        if score >= 35: return "평이한 흐름의 해"
        return "신중함이 필요한 해"

    seun_table = [{"age": c["age"], "year": c["year"], "ganji": c["sewoon"], "score": round(c["score"]),
                   "one_line": _seun_tier(c["score"])} for c in curve]
    seun_groups = group_seun_by_decade(seun_table)
    life = lifegraph_svg([{"age": c["age"], "score": round(c["score"])} for c in curve])   # '인생그래프'

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
    gyeok_dict = {"name": gyeok["격"], "body": gyeok_detail}

    # ⑤ 12운성·12신살·형충회합파해·귀인흉신 — 사주봇 외부검증 참조표(2026-07-21) 기반.
    # 디자인봇 필드계약: pillar/value(="값(의미)" 합성문자열), tags는 relations+gwiin 통합.
    sinsal_rep = sinsal_and_stages_report(engine_pillars, engine_pillars.day[0])
    stages_full = [{"pillar": s["label"], "value": f"{s['stage']}({STAGE_MEANING.get(s['stage'], '')})"}
                   for s in sinsal_rep["stages"]]
    sinsal_full = [{"pillar": s["label"], "value": f"{s['sinsal']}({SINSAL_MEANING.get(s['sinsal'], '')})"}
                   for s in sinsal_rep["sinsals"]]
    GIL_SET = {"천을귀인", "문창귀인"}
    tags = [{"type": "형충회합파해", "pair_or_name": r, "note": ""} for r in sinsal_rep["relations"]]
    tags += [{"type": "길신" if g in GIL_SET else "흉신", "pair_or_name": g, "note": ""} for g in sinsal_rep["gwiin"]]

    # ⑥ 월운(月建) — 현재년도(2026) 기준. 절기 근사치 오차 disclaimer 포함(사주봇 캐치).
    # 디자인봇 템플릿은 month를 순수 정수로 기대(템플릿이 "월" 접미어 붙임).
    wolun_raw = monthly_fortune(2026, yongsin["용신"])
    wolun = [{"month": i + 1, "ganji": m["ganji"], "one_line": m["one_line"]}
             for i, m in enumerate(wolun_raw["months"])]
    wolun_disclaimer = wolun_raw["disclaimer"]

    # ⑦ 연애 인연 — 좋은 인연(정관/정재) vs 주의 인연(편관/편재), 2026-07-21 사주봇 외부검증
    # (여명=관성, 남명=재성 기준. sipseong() 재사용만, 새 계산 없음).
    # 2026-07-21 디자인봇 리뷰 반영: 색상만으로 좋음/나쁨을 구분하면 WCAG 1.4.1 위반(색맹 접근성 X)
    # + 16장 카드나열은 세운 천간이 10개뿐이라 같은 십성이 정확히 10년마다 찍히는 당연현상이라
    # 정보 중복 → 아이콘+라벨+근거를 주정보로, 10년주기는 칩으로 압축(saju_sections.html ⑪ 개정판).
    love_matches = []
    good_key, care_key = ("정관", "편관") if gender == "여" else ("정재", "편재")
    for c in curve:
        se_stem_idx = STEMS.index(c["sewoon"][0])
        ss = sipseong(STEMS.index(engine_pillars.day[0]), se_stem_idx)
        if ss == good_key:
            love_matches.append({"age": c["age"], "year": c["year"], "kind": "good", "sipseong": ss})
        elif ss == care_key:
            love_matches.append({"age": c["age"], "year": c["year"], "kind": "care", "sipseong": ss})
    good_ages = sorted(m["age"] for m in love_matches if m["kind"] == "good")
    warn_ages = sorted(m["age"] for m in love_matches if m["kind"] == "care")

    CUR_YEAR = date.today().year
    CUR_AGE = CUR_YEAR - birth_year + 1   # 한국나이(출생해=1세), curve의 year=birth_year+age-1 과 동일 공식

    def _next(ages):
        fut = [a for a in ages if a >= CUR_AGE]
        a = fut[0] if fut else (ages[-1] if ages else CUR_AGE)
        return {"age": a, "year": CUR_YEAR + (a - CUR_AGE), "is_now": a == CUR_AGE}

    def _chips(ages):
        return [{"age": a, "year": CUR_YEAR + (a - CUR_AGE), "cur": a == CUR_AGE} for a in ages]

    LOVE_REASON = {"정관": "원칙 있고 성실한 결 — 안정적이고 오래가는 인연입니다.",
                   "정재": "성실하고 차곡차곡 쌓는 결 — 안정적이고 오래가는 인연입니다.",
                   "편관": "강렬하게 끌리지만 굴곡이 큰 결 — 서두르면 흔들리는 인연입니다.",
                   "편재": "자유롭고 변화 많은 결 — 강렬하지만 굴곡이 큰 인연입니다."}
    yeonae = {
        "good": {"icon": "✓", "label": "좋은 인연", "sipseong": good_key, "count": counts.get(good_key, 0),
                  "reason": LOVE_REASON[good_key], "chips": _chips(good_ages), "next": _next(good_ages), "tone": "ok"},
        "warn": {"icon": "⚠", "label": "주의할 인연", "sipseong": care_key, "count": counts.get(care_key, 0),
                  "reason": LOVE_REASON[care_key], "chips": _chips(warn_ages), "next": _next(warn_ages), "tone": "warn"},
        "cur_age": CUR_AGE,
    }

    # ⑧ 자녀운(정성적만) — 2026-07-21 사주봇: 숫자(명수) 지어내기 금지, 강약·관계성향만.
    # 여명=식상(식신+상관), 남명=관성(정관+편관) — 자녀성 카운트.
    child_ss = ("식신", "상관") if gender == "여" else ("정관", "편관")
    child_count = counts.get(child_ss[0], 0) + counts.get(child_ss[1], 0)
    child_strength = "강하게" if child_count >= 3 else ("보통으로" if child_count >= 1 else "약하게")
    has_hour = engine_pillars.hour is not None
    if has_hour:
        hour_ss = sipseong(STEMS.index(engine_pillars.day[0]), STEMS.index(engine_pillars.hour[0]))
        child_bond = ("효도형·순종적 관계에 가깝습니다" if hour_ss in ("정관","정재","정인")
                      else "독립적이고 자기 주도적인 관계에 가깝습니다" if hour_ss in ("편관","편재","편인")
                      else "친구처럼 편안한 관계에 가깝습니다")
        child_text = (f"자녀성({'/'.join(child_ss)})이 원국에 {child_count}개로, 자녀 인연이 {child_strength} 나타납니다. "
                      f"시주 십성({hour_ss}) 기준으로 보면 자녀와의 관계는 {child_bond} "
                      f"※ 자녀 수는 명리학 내에서도 논쟁적인 영역이라(민간 통설은 있으나 검증된 정설 아님) 이 리포트에서는 다루지 않습니다.")
    else:
        child_text = ("시주(태어난 시간)가 확정되지 않아 자녀궁 판정은 제한적입니다. "
                      f"참고로 자녀성({'/'.join(child_ss)})은 원국에 {child_count}개로 자녀 인연이 {child_strength} 나타납니다.")

    # ⑨ 이성궁합 특징(일반 서술, 상대방 데이터 없이 본인 사주 기준) — 2026-07-21 사주봇 외부검증
    hap_stem = CHEONGAN_HAP.get(engine_pillars.day[0], "")
    ilji_dohwa = dohwa_branch(engine_pillars)
    compat_love = (
        f"일간이 {engine_pillars.day[0]}이라 {hap_stem}일간(일간합)을 가진 상대와는 첫 만남부터 자연스러운 케미가 흐르기 쉽습니다. "
        f"용신({yongsin['용신']}) 기운을 가진 상대 — 즉 나에게 부족한 부분을 채워주는 사람과는 서로 보완적인 좋은 궁합입니다. "
        f"반대로 서로의 기신(용신과 반대 기운)을 자극하는 조합이거나, 배우자궁(일지)끼리 충(沖)이 겹치는 상대는 마찰이 잦을 수 있어 주의가 필요합니다."
    )

    # ⑩ 동료/직장 궁합 특징 — 2026-07-21 사주봇: 이성궁합과 다른 축(비겁/관성·인성/식상)
    bigyeop_count = counts.get("비견", 0) + counts.get("겁재", 0)
    compat_work = (
        ("비겁(협력·경쟁) 기운이 원국에 강해서, 동료와는 급속도로 가까워지거나 반대로 경쟁구도가 뚜렷해지는 양극단이 나타나기 쉽습니다. "
         "같은 목표를 향할 땐 든든한 동료가 되지만, 이해관계가 갈리면 신경전으로 번질 수 있습니다."
         if bigyeop_count >= 3 else
         "비겁 기운이 과하지 않아, 동료·상사와 무난하게 협력하는 편입니다.")
        + f" 상사와의 관계는 관성·인성 축으로 보는데, 원국의 용신({yongsin['용신']}) 방향과 맞는 조직문화일수록 인정받기 수월합니다. "
        f"사업 파트너로는 재성·식상 조합(능력이 결과로 이어지는 구조)이 맞는 사람이 좋은 궁합입니다."
    )

    # ⑪ 결혼시기 강화 — 조건 카운트(일지합/천을귀인/도화)로 등급, 2026-07-21 사주봇 근거
    marriage_tier_notes = []
    for c in curve:
        se_branch = c["sewoon"][1]
        cond = 0
        if is_yukhap(se_branch, engine_pillars.day[1]): cond += 1
        if se_branch in CHEONEUL_GWIIN.get(engine_pillars.day[0], []): cond += 1
        if se_branch == ilji_dohwa: cond += 1
        if cond >= 2:
            marriage_tier_notes.append({"age": c["age"], "year": c["year"], "conditions": cond})
    marriage_tier_notes.sort(key=lambda x: -x["conditions"])
    marriage_candidates = marriage_tier_notes[:3]

    return {
        # 디자인봇 saju_sections.html 정식 컴포넌트 데이터계약(그대로 슬롯)
        "ohaeng": ohaeng_items, "radar": radar, "life": life,
        "sipseong": sipseong_full, "daeun": full_daeun, "seun_groups": seun_groups,
        "stages": stages_full, "sinsal": sinsal_full, "tags": tags,
        "gyeok": gyeok_dict, "wolun": wolun, "wolun_disclaimer": wolun_disclaimer, "yeonae": yeonae,
        # 보조(기존 report_saju.html 섹션에서 계속 사용)
        "seun_table": seun_table, "gyeok_detail": gyeok_detail,
        "child_text": child_text, "compat_love": compat_love, "compat_work": compat_work,
        "marriage_candidates": marriage_candidates,
    }


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
