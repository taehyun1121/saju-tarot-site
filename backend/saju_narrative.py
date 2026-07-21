"""Gemini(AI) 없이도 동작하는 규칙기반 사주 서술 생성 — full_report()의 명리학 진단
(왕쇠/용신/격국/십성구조)을 사주봇 검증완료 로직 그대로 쓰고, 그 판정을 문장으로
매핑만 한다. 지어내는 부분(신살 등 미구현 판정) 없이, 계산된 값만 서술.

generate_ai_saju_reading()/generate_decade_reading()과 동일한 반환 형태를 맞춰서
main.py에서 Gemini 실패 시 그대로 자리 교체 가능.
"""

from saju_rule_engine import full_report, daewoon_direction


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
