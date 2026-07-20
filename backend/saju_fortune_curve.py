# -*- coding: utf-8 -*-
"""
운세 그래프 곡선 엔진 — saju_rule_engine.py 확장 (코코 요청, 고삼타로 라이트 몰입퍼널용)
입력=원국+성별+대운수(외부 만세력 계산값) → 출력=[{age,score}] 3~83세 + 시기4종 피크
전제: 곡선값은 용신/기신 채점(명리 정설)에서만 도출 — 지어내기 금지. 데이터 없으면 미확정.
"""
from saju_rule_engine import (
    Pillars, STEMS, STEM_HANJA, STEM_OHAENG, STEM_YINYANG,
    BRANCHES, BRANCH_HANJA, BRANCH_OHAENG, JIJANGGAN,
    stem_idx, branch_idx, sipseong, SIPSEONG_GROUP,
    wangso_score, yongsin_select, ohaeng_count, daewoon_direction,
)

ORDER = ["木", "火", "土", "金", "水"]

def ke_source(target_elem):
    """target을 극하는 오행(=target의 기신 후보) 반환. 木극土이므로 ke_source(土)=木"""
    idx = ORDER.index(target_elem)
    return ORDER[(idx - 2) % 5]

def elem_of_yongsin_label(label):
    """yongsin_select()가 반환한 '木(억부-인성)' 같은 문자열에서 순오행 한 글자만 추출"""
    return label[0]

# ── 60갑자 순환 ──
def ganzi60():
    return [(STEMS[i % 10], BRANCHES[i % 12]) for i in range(60)]

GANZI60 = ganzi60()

def ganzi_index(stem, branch):
    for i, (s, b) in enumerate(GANZI60):
        if s == stem and b == branch:
            return i
    raise ValueError("잘못된 간지 조합(60갑자에 없음)")

# 앙커: 1984년 = 갑자년 (양력 기준 절기년 근사, 입춘 이전 생일은 호출측에서 이미 절기년 보정된 값을 넣을 것)
ANCHOR_YEAR = 1984

def year_ganzi(year):
    idx = (year - ANCHOR_YEAR) % 60
    return GANZI60[idx]


# ── 대운 시퀀스 ──
def daewoon_sequence(p: Pillars, gender, daewoon_su, n_periods=9):
    """
    daewoon_su: 첫 대운 시작 나이 — 정밀 절입일 계산값을 외부(기존 만세력 계산 레이어)에서 받는다.
    🔴 이 값을 이 모듈이 임의로 추정하지 않는다(정직게이트) — 없으면 대운 관련 출력 전부 '미확정'.
    """
    direction = daewoon_direction(p.year[0], gender)  # "순행"/"역행"
    step = 1 if direction == "순행" else -1
    month_idx = ganzi_index(p.month[0], p.month[1])
    seq = []
    for i in range(n_periods):
        gz_idx = (month_idx + step * (i + 1)) % 60
        stem, branch = GANZI60[gz_idx]
        age_start = daewoon_su + i * 10
        age_end = age_start + 9
        seq.append({"age_start": age_start, "age_end": age_end, "stem": stem, "branch": branch})
    return seq

def daewoon_for_age(seq, age):
    for d in seq:
        if d["age_start"] <= age <= d["age_end"]:
            return d
    return None


# ── 도화 판정 (삼합 기준, 일지/년지 기준) ──
SAMHAP_TO_DOHWA = {
    frozenset(["신","자","진"]): "유",
    frozenset(["사","유","축"]): "오",
    frozenset(["인","오","술"]): "묘",
    frozenset(["해","묘","미"]): "자",
}
def find_group(branch):
    for group, doh in SAMHAP_TO_DOHWA.items():
        if branch in group:
            return doh
    return None

def dohwa_branch(p: Pillars):
    """일지 기준 도화지지 반환"""
    return find_group(p.day[1])

YUKHAP = {frozenset(["자","축"]):1, frozenset(["인","해"]):1, frozenset(["묘","술"]):1,
          frozenset(["진","유"]):1, frozenset(["사","신"]):1, frozenset(["오","미"]):1}
CHUNG = {frozenset(["자","오"]):1, frozenset(["축","미"]):1, frozenset(["인","신"]):1,
         frozenset(["묘","유"]):1, frozenset(["진","술"]):1, frozenset(["사","해"]):1}

def is_yukhap(b1, b2): return frozenset([b1,b2]) in YUKHAP
def is_chung(b1, b2): return frozenset([b1,b2]) in CHUNG


# ── 채점 코어 ──
def score_curve(p: Pillars, gender, birth_year, daewoon_su=None, age_range=(3, 83)):
    """
    반환: {
      "curve": [{"age":n, "year":YYYY, "daewoon":"간지", "sewoon":"간지", "score":0~100}, ...],
      "peaks": {"대박운":..., "조심시기":..., "연애운":..., "결혼운":...},
      "flags": [정직게이트 메시지들]
    }
    """
    flags = []
    wangso = wangso_score(p)
    yongsin = yongsin_select(p, wangso)
    yongsin_elem = elem_of_yongsin_label(yongsin["용신"])
    gisin_elem = ke_source(yongsin_elem)

    if not p.hour:
        flags.append("시주 미확정 — 시지 의존도가 큰 세부판단(자녀운 등)은 이 곡선에서 제외됨. 왕쇠확신도 '중'.")

    if daewoon_su is None:
        flags.append("🔴 대운수(첫 대운 시작나이) 미입력 — 대운 기반 전체 곡선/피크4종 산출 불가. 만세력 계산레이어에서 정밀 절입일 기준 대운수를 받아야 함(임의추정 금지). daewoon_su 없이는 '세운만 반영한 약식곡선'만 제공.")
        dw_seq = None
    else:
        dw_seq = daewoon_sequence(p, gender, daewoon_su)

    doh = dohwa_branch(p)
    ilji = p.day[1]

    curve = []
    a0, a1 = age_range
    for age in range(a0, a1 + 1):
        year = birth_year + age - 1  # 한국나이 기준(출생해=1세) — 만나이 환산은 호출측 책임
        se_stem, se_branch = year_ganzi(year)
        se_elem_stem = STEM_OHAENG[stem_idx(se_stem)]
        se_elem_branch = BRANCH_OHAENG[branch_idx(se_branch)]

        score = 50.0  # 중립 기준선
        # 세운 천간 오행
        if se_elem_stem == yongsin_elem: score += 15
        elif se_elem_stem == gisin_elem: score -= 15
        # 세운 지지 오행
        if se_elem_branch == yongsin_elem: score += 15
        elif se_elem_branch == gisin_elem: score -= 15

        dw_stem = dw_branch = None
        if dw_seq is not None:
            dw = daewoon_for_age(dw_seq, age)
            if dw:
                dw_stem, dw_branch = dw["stem"], dw["branch"]
                dw_elem_s = STEM_OHAENG[stem_idx(dw_stem)]
                dw_elem_b = BRANCH_OHAENG[branch_idx(dw_branch)]
                if dw_elem_s == yongsin_elem: score += 20
                elif dw_elem_s == gisin_elem: score -= 20
                if dw_elem_b == yongsin_elem: score += 20
                elif dw_elem_b == gisin_elem: score -= 20

        # 일지 합충 보정(생활/배우자궁 동요)
        if is_yukhap(se_branch, ilji): score += 5
        if is_chung(se_branch, ilji): score -= 8

        score = max(0, min(100, round(score, 1)))
        curve.append({
            "age": age, "year": year,
            "daewoon": f"{dw_stem}{dw_branch}" if dw_stem else "미확정",
            "sewoon": f"{se_stem}{se_branch}",
            "score": score,
        })

    # ── 피크 4종 ──
    ig = stem_idx(p.day[0])
    def sipseong_of_elem(elem):
        """해당 오행에 대응하는 대표 천간의 십성(같은 음양 기준 1개 대표로 간이 판정)"""
        for s_idx, s in enumerate(STEMS):
            if STEM_OHAENG[s_idx] == elem and STEM_YINYANG[s_idx] == STEM_YINYANG[ig]:
                return sipseong(ig, s_idx)
        return "?"

    yongsin_ss = sipseong_of_elem(yongsin_elem)
    yongsin_grp = SIPSEONG_GROUP.get(yongsin_ss, "?")

    peaks = {}

    # ① 대박운: 용신오행이 재성/식상 계열일 때만 유의미, 곡선 최고점
    if yongsin_grp in ("재성", "식상"):
        best = max(curve, key=lambda r: r["score"])
        peaks["대박운"] = {"age": best["age"], "year": best["year"], "score": best["score"],
                          "근거": f"용신={yongsin_elem}({yongsin_grp}) 峰, 대운{best['daewoon']}+세운{best['sewoon']}"}
    else:
        peaks["대박운"] = {"미확정": f"이 원국 용신({yongsin_elem}={yongsin_grp})이 재성/식상 계열이 아니라 '재물피크'로 직결 안 됨 — 대신 '{yongsin_grp} 강화 시기'로 해석 필요"}

    # ② 조심시기: 곡선 최저점
    worst = min(curve, key=lambda r: r["score"])
    peaks["조심시기"] = {"age": worst["age"], "year": worst["year"], "score": worst["score"],
                       "근거": f"기신={gisin_elem} 골, 대운{worst['daewoon']}+세운{worst['sewoon']}"}

    # 🔴 나이 하한(2026-07-19 실사용 검증 중 발견·수정): 도화/일지합 조건만으로는 미성년 나이도
    #    후보에 들어가 "7세 연애운 피크" 같은 비현실적 결과가 나옴. 연애=현실적 이성교제 최저선,
    #    결혼=법적 성인 기준으로 하한을 걸어 필터링. (요청 age_range의 하한과 무관하게 항상 적용)
    LOVE_MIN_AGE = 15
    MARRIAGE_MIN_AGE = 19

    # ③ 연애운: 도화 발동 + 재성(남명)/관성(여명) 활성 세운 겹치는 해 중 최고점
    love_candidates = []
    if doh:
        for r in curve:
            if r["age"] < LOVE_MIN_AGE:
                continue
            se_branch = r["sewoon"][1]
            if se_branch == doh:
                love_candidates.append(r)
    if love_candidates:
        best_love = max(love_candidates, key=lambda r: r["score"])
        peaks["연애운"] = {"age": best_love["age"], "year": best_love["year"], "score": best_love["score"],
                         "근거": f"도화({doh}) 세운 발동 + 원국점수, 세운{best_love['sewoon']}"}
    else:
        peaks["연애운"] = {"미확정": f"도화 발동 세운이 {LOVE_MIN_AGE}~83세 범위에 없거나 일지 기준 도화 산출 불가"}

    # ④ 결혼운: 일지와 세운 합 + 그 시기 재관 대운(용신군) 겹치는 해
    marriage_candidates = []
    for r in curve:
        if r["age"] < MARRIAGE_MIN_AGE:
            continue
        se_branch = r["sewoon"][1]
        if is_yukhap(se_branch, ilji) and yongsin_grp in ("재성", "관성"):
            marriage_candidates.append(r)
    if marriage_candidates:
        best_m = max(marriage_candidates, key=lambda r: r["score"])
        peaks["결혼운"] = {"age": best_m["age"], "year": best_m["year"], "score": best_m["score"],
                         "근거": f"일지합+용신({yongsin_grp}) 겹침, 세운{best_m['sewoon']}"}
    else:
        peaks["결혼운"] = {"미확정": f"일지합 세운({MARRIAGE_MIN_AGE}세 이상)과 용신군({yongsin_grp}) 재관 겹치는 해 없음 — 조건 완화 필요 시 별도 재산출"}

    return {"curve": curve, "peaks": peaks, "flags": flags,
            "meta": {"왕쇠": wangso, "용신": yongsin, "용신그룹": yongsin_grp, "기신오행": gisin_elem, "도화": doh}}


if __name__ == "__main__":
    # 검증: 6편-남(주창환) 1990.03.30, 시주모름, 대운수=2(앞서 대화에서 산출)
    p = Pillars(("경","오"),("기","묘"),("갑","오"))
    result = score_curve(p, "남", 1990, daewoon_su=2, age_range=(3, 83))

    print("### 6편-남(주창환) 운세곡선 검증 ###")
    print("meta:", result["meta"]["왕쇠"]["verdict"], "| 용신:", result["meta"]["용신"]["용신"], "| 용신그룹:", result["meta"]["용신그룹"])
    if result["flags"]:
        for f in result["flags"]: print("⚠️", f)
    print("\n5년 간격 샘플:")
    for r in result["curve"]:
        if r["age"] % 5 == 0:
            print(f"  {r['age']}세({r['year']}) 대운{r['daewoon']} 세운{r['sewoon']} → {r['score']}점")
    print("\n피크4종:")
    for k, v in result["peaks"].items():
        print(f"  [{k}] {v}")
