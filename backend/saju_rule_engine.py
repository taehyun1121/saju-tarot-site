# -*- coding: utf-8 -*-
"""
사주 명리 룰엔진 프로토타입 (GEMINI_API_KEY 불필요, 무API 순수계산)
벤치마킹 접목: 대덕이론 55점 신강신약법 / 용신 우선순위(별격>조후다급>통관>억부) / 격국 왕지생지고지 판정법
검증: 이미 사주봇이 감수·계산 완료한 실제 케이스(5편·6편·seorin) 재입력 → 결론 재현 확인
"""

STEMS = ["갑","을","병","정","무","기","경","신","임","계"]
STEM_HANJA = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEM_OHAENG = ["木","木","火","火","土","土","金","金","水","水"]
STEM_YINYANG = ["양","음","양","음","양","음","양","음","양","음"]  # 양간/음간

BRANCHES = ["자","축","인","묘","진","사","오","미","신","유","술","해"]
BRANCH_HANJA = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCH_OHAENG = ["水","土","木","木","土","火","火","土","金","金","土","水"]

# 지장간: (여기, 중기, 정기) — None 허용
JIJANGGAN = {
    "자": [("계", 10)],
    "축": [("계", 9), ("신", 3), ("기", 18)],
    "인": [("무", 7), ("병", 7), ("갑", 16)],
    "묘": [("갑", 10), ("을", 20)],
    "진": [("을", 9), ("계", 3), ("무", 18)],
    "사": [("무", 7), ("경", 7), ("병", 16)],
    "오": [("병", 10), ("기", 9), ("정", 11)],
    "미": [("정", 9), ("을", 3), ("기", 18)],
    "신": [("무", 7), ("임", 7), ("경", 16)],
    "유": [("경", 10), ("신", 20)],
    "술": [("신", 9), ("정", 3), ("무", 18)],
    "해": [("무", 7), ("갑", 7), ("임", 16)],
}

WANGJI = {"자", "오", "묘", "유"}   # 제왕지
SAENGJI = {"인", "신", "사", "해"}  # 생지
GOJI = {"진", "술", "축", "미"}     # 고지(묘지)

SAMHAP_GROUPS = {  # 방합/삼합용 참고
    frozenset(["신","자","진"]): "水",
    frozenset(["사","유","축"]): "金",
    frozenset(["인","오","술"]): "火",
    frozenset(["해","묘","미"]): "木",
}

# ══ 2026-07-21 사주봇 외부검증 완료(namu.wiki 신살문서·sajustudy.com·복수 명리칼럼
# 교차대조) 참조표 — 50페이지 확장 리포트용. 전부 확신도 "상"만 채택, 확신도 "중"
# 이하(암록/금여) 및 미확인값(己 홍염)은 지어내기 금지 원칙상 제외.

# ── 12운성(포태법) ──
TWELVE_STAGES = ["장생","목욕","관대","건록","제왕","쇠","병","사","묘","절","태","양"]
STEM_START_BRANCH = {"갑":"해","을":"오","병":"인","정":"유","무":"인","기":"유","경":"사","신":"자","임":"신","계":"묘"}
STEM_FORWARD = {"갑":True,"을":False,"병":True,"정":False,"무":True,"기":False,"경":True,"신":False,"임":True,"계":False}


def twelve_stage(stem, branch):
    s = BRANCHES.index(STEM_START_BRANCH[stem]); b = BRANCHES.index(branch)
    offset = (b - s) % 12 if STEM_FORWARD[stem] else (s - b) % 12
    return TWELVE_STAGES[offset]


# ── 12신살 ──
SAMHAP_KEY = {"인":"화국","오":"화국","술":"화국","사":"금국","유":"금국","축":"금국",
              "신":"수국","자":"수국","진":"수국","해":"목국","묘":"목국","미":"목국"}
TWELVE_SINSAL = ["겁살","재살","천살","지살","년살","월살","망신살","장성살","반안살","역마살","육해살","화개살"]
SINSAL_START = {"화국":"해","금국":"인","수국":"사","목국":"신"}


def twelve_sinsal(base_branch, target_branch):
    s = BRANCHES.index(SINSAL_START[SAMHAP_KEY[base_branch]])
    offset = (BRANCHES.index(target_branch) - s) % 12
    return TWELVE_SINSAL[offset]


# ── 형충회합파해 ──
# YUKHAP/CHUNG은 saju_fortune_curve.py에 이미 있는 것과 동일값(순환import 방지 위해 로컬 복제)
YUKHAP_REF = {frozenset(["자","축"]):1, frozenset(["인","해"]):1, frozenset(["묘","술"]):1,
              frozenset(["진","유"]):1, frozenset(["사","신"]):1, frozenset(["오","미"]):1}
CHUNG_REF = {frozenset(["자","오"]):1, frozenset(["축","미"]):1, frozenset(["인","신"]):1,
             frozenset(["묘","유"]):1, frozenset(["진","술"]):1, frozenset(["사","해"]):1}
SAMHAP = SAMHAP_GROUPS
BANGHAP = {frozenset(["인","묘","진"]): "木", frozenset(["사","오","미"]): "火",
           frozenset(["신","유","술"]): "金", frozenset(["해","자","축"]): "水"}
SAMHYEONG = [frozenset(["인","사","신"]), frozenset(["축","술","미"])]  # 인사신=무은지형, 축술미=지세지형
JAHYEONG_BRANCHES = {"진","오","유","해"}   # 같은 지지 2개 이상=자형
SANGHYEONG = frozenset(["자","묘"])         # 무례지형
PA = {frozenset(["자","유"]): 1, frozenset(["축","진"]): 1, frozenset(["인","해"]): 1,
      frozenset(["묘","오"]): 1, frozenset(["사","신"]): 1, frozenset(["술","미"]): 1}
HAE_REL = {frozenset(["자","미"]): 1, frozenset(["축","오"]): 1, frozenset(["인","사"]): 1,
           frozenset(["묘","진"]): 1, frozenset(["신","해"]): 1, frozenset(["유","술"]): 1}

# ── 귀인/흉신(보너스, 己 홍염 제외 — 미확인) ──
CHEONEUL_GWIIN = {"갑":["축","미"],"무":["축","미"],"경":["축","미"],"을":["자","신"],"기":["자","신"],
                  "병":["해","유"],"정":["해","유"],"신":["인","오"],"임":["묘","사"],"계":["묘","사"]}
MUNCHANG_GWIIN = {"갑":"사","을":"오","병":"신","정":"유","무":"신","기":"유","경":"해","신":"자","임":"인","계":"묘"}
YANGIN = {"갑":"묘","병":"오","무":"오","경":"유","임":"자"}   # 양간만 해당
GOEGANG_ILJU = {("무","술"),("경","진"),("경","술"),("임","진")}
BAEKHO_ILJU = {("갑","진"),("을","미"),("병","술"),("정","축"),("무","진"),("임","술"),("계","축")}
GWIMUN = {frozenset(["자","유"]): 1, frozenset(["축","오"]): 1, frozenset(["인","미"]): 1,
          frozenset(["묘","신"]): 1, frozenset(["진","해"]): 1, frozenset(["사","술"]): 1}
WONJIN = {frozenset(["자","미"]): 1, frozenset(["축","오"]): 1, frozenset(["인","유"]): 1,
          frozenset(["묘","신"]): 1, frozenset(["진","해"]): 1, frozenset(["사","술"]): 1}
HONGYEOM = {"갑":"오","을":"오","병":"인","정":"미","무":"진","경":"술","신":"유","임":"자","계":"신"}  # 기(己) 미확인, 의도적 누락


def sinsal_and_stages_report(p, ilgan):
    """4주 전체에 대한 12운성·12신살·형충회합파해·귀인흉신 종합 — 전부 위 검증표 그대로 lookup만."""
    positions = [("년주", p.year), ("월주", p.month), ("일주", p.day)]
    if p.hour:
        positions.append(("시주", p.hour))
    base_branch = p.year[1]  # 12신살은 통상 년지 기준

    stages = []
    sinsals = []
    for label, (stem, branch) in positions:
        stages.append({"label": label, "stage": twelve_stage(stem, branch)})
        sinsals.append({"label": label, "sinsal": twelve_sinsal(base_branch, branch)})

    branches = [b for _, (_, b) in positions]
    relations = []
    seen = set()
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            b1, b2 = branches[i], branches[j]
            if b1 == b2 or (b1, b2) in seen or (b2, b1) in seen:
                continue
            seen.add((b1, b2))
            fs = frozenset([b1, b2])
            if fs in YUKHAP_REF:
                relations.append(f"{b1}-{b2} 육합")
            if fs in CHUNG_REF:
                relations.append(f"{b1}-{b2} 충")
            if fs in PA:
                relations.append(f"{b1}-{b2} 파")
            if fs in HAE_REL:
                relations.append(f"{b1}-{b2} 해")
    for fs, name in [(f, "삼형") for f in SAMHYEONG] + [(SANGHYEONG, "무례지형")]:
        if fs.issubset(set(branches)):
            relations.append(f"{'·'.join(sorted(fs))} {name}")
    dup = [b for b in JAHYEONG_BRANCHES if branches.count(b) >= 2]
    for b in dup:
        relations.append(f"{b}{b} 자형")

    ilju = (p.day[0], p.day[1])
    gwiin_notes = []
    if ilgan in CHEONEUL_GWIIN and any(b in CHEONEUL_GWIIN[ilgan] for b in branches):
        gwiin_notes.append("천을귀인")
    if ilgan in MUNCHANG_GWIIN and MUNCHANG_GWIIN[ilgan] in branches:
        gwiin_notes.append("문창귀인")
    if ilgan in YANGIN and YANGIN[ilgan] in branches:
        gwiin_notes.append("양인")
    if ilju in GOEGANG_ILJU:
        gwiin_notes.append("괴강일주")
    if ilju in BAEKHO_ILJU:
        gwiin_notes.append("백호일주")

    return {"stages": stages, "sinsals": sinsals, "relations": relations, "gwiin": gwiin_notes}

def sheng(a, b):
    """a가 b를 생하는가"""
    order = ["木","火","土","金","水"]
    return order[(order.index(a)+1) % 5] == b

def ke(a, b):
    """a가 b를 극하는가"""
    order = ["木","火","土","金","水"]
    return order[(order.index(a)+2) % 5] == b

def sipseong(ilgan_idx, target_idx):
    """일간(천간 index) 기준 target 천간의 십성 산출"""
    ig_o, ig_y = STEM_OHAENG[ilgan_idx], STEM_YINYANG[ilgan_idx]
    tg_o, tg_y = STEM_OHAENG[target_idx], STEM_YINYANG[target_idx]
    same_yy = (ig_y == tg_y)
    if ig_o == tg_o:
        return "비견" if same_yy else "겁재"
    if sheng(ig_o, tg_o):
        return "식신" if same_yy else "상관"
    if ke(ig_o, tg_o):
        return "편재" if same_yy else "정재"
    if sheng(tg_o, ig_o):
        return "편인" if same_yy else "정인"
    if ke(tg_o, ig_o):
        return "편관" if same_yy else "정관"
    return "?"

SIPSEONG_GROUP = {
    "비견": "비겁", "겁재": "비겁",
    "식신": "식상", "상관": "식상",
    "편재": "재성", "정재": "재성",
    "편관": "관성", "정관": "관성",
    "편인": "인성", "정인": "인성",
}


class Pillars:
    def __init__(self, year, month, day, hour=None):
        """각 인자는 ('갑','자') 같은 (천간, 지지) 튜플. hour=None이면 시주 모름."""
        self.year, self.month, self.day, self.hour = year, month, day, hour

    def all_stems(self):
        s = [self.year[0], self.month[0], self.day[0]]
        if self.hour: s.append(self.hour[0])
        return s

    def all_branches(self):
        b = [self.year[1], self.month[1], self.day[1]]
        if self.hour: b.append(self.hour[1])
        return b


def stem_idx(s): return STEMS.index(s)
def branch_idx(b): return BRANCHES.index(b)


# ── A2. 왕쇠 판정 — 대덕이론 계열 100점 환산(55점 기준) ──
# 가중치: 월지25 일지20 시지15 년지10 + 월간10 시간10 년간10 = 100
WEIGHTS = {"월지":25, "일지":20, "시지":15, "년지":10, "월간":10, "시간":10, "년간":10}

def wangso_score(p: Pillars):
    ig = stem_idx(p.day[0])
    ig_o = STEM_OHAENG[ig]
    score = 0.0
    detail = []

    def add(label, o_elem, weight):
        nonlocal score
        # 비겁(같은오행) or 인성(나를 생하는 오행) → 생조 → 가산
        if o_elem == ig_o or sheng(o_elem, ig_o):
            score += weight
            detail.append(f"{label}={o_elem}(생조) +{weight}")
        else:
            detail.append(f"{label}={o_elem}(설/극) +0")

    add("년간", STEM_OHAENG[stem_idx(p.year[0])], WEIGHTS["년간"])
    add("월간", STEM_OHAENG[stem_idx(p.month[0])], WEIGHTS["월간"])
    add("년지", BRANCH_OHAENG[branch_idx(p.year[1])], WEIGHTS["년지"])
    add("월지", BRANCH_OHAENG[branch_idx(p.month[1])], WEIGHTS["월지"])
    if p.hour:
        add("시간", STEM_OHAENG[stem_idx(p.hour[0])], WEIGHTS["시간"])
        add("시지", BRANCH_OHAENG[branch_idx(p.hour[1])], WEIGHTS["시지"])
    else:
        # 시주 모름 → 그 25점(시간10+시지15)은 판정 불능 구간으로 분리, 나머지 75점 기준 환산
        pass

    total_weight = sum(WEIGHTS.values()) if p.hour else (WEIGHTS["년간"]+WEIGHTS["월간"]+WEIGHTS["년지"]+WEIGHTS["월지"])
    # 일지도 포함해야 함 — 별도 처리(일지는 항상 확정값)
    add("일지", BRANCH_OHAENG[branch_idx(p.day[1])], WEIGHTS["일지"])
    total_weight += WEIGHTS["일지"]

    norm_score = round(score / total_weight * 100, 1)
    verdict = "신강" if norm_score >= 55 else "신약"
    override_note = None

    # ── 록겁/양인 오버라이드 ──
    # 명리 정설: 월지가 일간과 같은 오행이면서 왕지(자오묘유=제왕지)인 경우
    # = 록겁격/양인격 성립, 다른 조건이 약해도 '득령 최강'으로 최우선 신강 판정.
    # (단순 가중합산의 사각지대 — 검증 케이스 6편남에서 실제 발견된 오분류를 교정)
    month_o = BRANCH_OHAENG[branch_idx(p.month[1])]
    if month_o == ig_o and p.month[1] in WANGJI and verdict == "신약":
        verdict = "신강"
        override_note = f"록겁/양인 오버라이드: 월지({p.month[1]})가 일간과 동일오행의 왕지(제왕지) → 원점수({norm_score})와 무관하게 신강 확정"

    confidence = "상" if p.hour else "중(시주미확정, 최대75/88점 기준 잠정)"
    return {"score": norm_score, "verdict": verdict, "confidence": confidence, "detail": detail, "override": override_note}


# ── A3. 용신 선정 — 별격 > 조후(다급) > 통관(상극팽팽) > 억부(기본) ──
def ohaeng_count(p: Pillars):
    cnt = {"木":0,"火":0,"土":0,"金":0,"水":0}
    for s in p.all_stems():
        cnt[STEM_OHAENG[stem_idx(s)]] += 1
    for b in p.all_branches():
        cnt[BRANCH_OHAENG[branch_idx(b)]] += 1
    return cnt

def yongsin_select(p: Pillars, wangso):
    ig_o = STEM_OHAENG[stem_idx(p.day[0])]
    cnt = ohaeng_count(p)
    month_b = p.month[1]

    # 1) 조후(다급) 체크 — 겨울(해자축) 태생인데 火 전무 / 여름(사오미) 태생인데 水 전무
    if month_b in ["해","자","축"] and cnt["火"] == 0:
        return {"용신": "火(丙)", "근거": "조후(다급)", "설명": "겨울생 원국에 火 전무 — 조후가 억부보다 우선, 궁통보감 기준"}
    if month_b in ["사","오","미"] and cnt["水"] == 0:
        return {"용신": "水(壬)", "근거": "조후(다급)", "설명": "여름생 원국에 水 전무 — 조후가 억부보다 우선"}

    # 2) 통관 체크 — 상극 두 오행이 둘 다 count>=2이고 중간(통관) 오행이 count 0 or 1
    order = ["木","火","土","金","水"]
    for i, a in enumerate(order):
        b = order[(i+2) % 5]  # a가 극하는 오행
        mediator = order[(i+1) % 5]  # a→mediator→b (a生mediator生b, mediator가 a와 b 사이 통관)
        if cnt[a] >= 2 and cnt[b] >= 2 and cnt[mediator] <= 1:
            return {"용신": f"{mediator}(통관)", "근거": "통관",
                    "설명": f"{a}↔{b} 상극 팽팽({a}={cnt[a]},{b}={cnt[b]}) → 중간오행 {mediator}로 소통"}

    # 3) 억부(기본)
    if wangso["verdict"] == "신강":
        # 설/극 오행 중 최다인 것을 용신으로 (식상>재>관 순 우선탐색, 카운트 기준)
        candidates = [o for o in order if o != ig_o and not sheng(o, ig_o) and o != ig_o]
        # 설극 오행 = 일간이 생하거나 일간을 극하거나 일간이 극하는 것들(즉 비겁/인성 제외)
        seolgeuk = [o for o in order if not (o == ig_o or sheng(o, ig_o))]
        best = max(seolgeuk, key=lambda o: cnt[o])
        return {"용신": f"{best}(억부-설/극)", "근거": "억부(신강)", "설명": f"신강하므로 설기/극하는 오행 중 최다({best}={cnt[best]})를 용신"}
    else:
        saengjo = [o for o in order if o == ig_o or sheng(o, ig_o)]
        # 인성(나를 생) 우선
        inseong = [o for o in saengjo if o != ig_o]
        if inseong and cnt[inseong[0]] >= 0:
            best = inseong[0]
            return {"용신": f"{best}(억부-인성)", "근거": "억부(신약)", "설명": f"신약하므로 나를 생하는 인성({best})을 용신으로 우선"}
        return {"용신": f"{ig_o}(억부-비겁)", "근거": "억부(신약)", "설명": "인성 부재, 비겁으로 부조"}


# ── A4. 격국 판정 — 왕지/생지/고지 규칙 ──
def gyeokguk_select(p: Pillars):
    ig = stem_idx(p.day[0])
    mb = p.month[1]
    jjg = JIJANGGAN[mb]  # [(간, 일수), ...] 여기~정기 순

    if mb in WANGJI:
        # 왕지: 정기(마지막 원소)가 투출여부 무관하게 격
        jeonggi = jjg[-1][0]
        chosen = jeonggi
        rule = "왕지(자오묘유) — 정기 무조건 격"
    elif mb in SAENGJI:
        # 생지: 천간에 투출한 지장간 중 세력 큰 것 (투출 없으면 정기)
        stems_present = set(p.all_stems())
        toechul = [g for g,_ in jjg if g in stems_present]
        if toechul:
            # 세력(일수) 큰 순
            chosen = max(toechul, key=lambda g: dict(jjg)[g])
            rule = "생지(인신사해) — 천간투출 중 세력최대"
        else:
            chosen = jjg[-1][0]
            rule = "생지 — 투출없어 정기로"
    else:  # GOJI 진술축미
        # 고지: 삼합 여부로 중기/정기 결정(단순화: 삼합 미확인 시 정기)
        chosen = jjg[-1][0]  # 정기 (여기/중기 투출 있으면 우선하도록 아래서 보정)
        stems_present = set(p.all_stems())
        toechul = [g for g,_ in jjg if g in stems_present]
        if toechul:
            chosen = max(toechul, key=lambda g: dict(jjg)[g])
            rule = "고지(진술축미) — 천간투출 있어 그걸로(단순화, 삼합판정 생략)"
        else:
            rule = "고지 — 투출없어 정기로(단순화)"

    ss = sipseong(ig, stem_idx(chosen))
    geok_name = f"{ss}격"
    # 양인 병기: 월지가 일간과 동일오행의 왕지 + 일간이 양간이면 격국 팔격체계와 별개로 양인 성립
    month_o = BRANCH_OHAENG[branch_idx(mb)]
    ig_o = STEM_OHAENG[ig]
    if month_o == ig_o and mb in WANGJI and STEM_YINYANG[ig] == "양":
        geok_name += "(=양인격 겸함)"
    return {"격": geok_name, "격지지": mb, "격간": chosen, "판정근거": rule}


def jonggyeok_check(p: Pillars, wangso, cnt):
    """종격 후보 판별 — 극단치 + 뿌리 유무"""
    ig_o = STEM_OHAENG[stem_idx(p.day[0])]
    root_branches = []
    for b in p.all_branches():
        for g, _ in JIJANGGAN[b]:
            if STEM_OHAENG[stem_idx(g)] == ig_o:
                root_branches.append(b)
                break
    has_root = len(root_branches) > 0
    if wangso["score"] <= 15 and not has_root:
        return {"종격후보": True, "종류": "종격(뿌리없음, 순수)", "뿌리": root_branches}
    if wangso["score"] <= 25 and has_root:
        return {"종격후보": True, "종류": "假從(가종, 미약한 뿌리 있음 — 정격/종격 양론 병기 필요)", "뿌리": root_branches}
    if wangso["score"] >= 90:
        dominant = max(cnt, key=lambda o: cnt[o] if o != ig_o else -1)
        return {"종격후보": True, "종류": f"종왕/종강격 방향(비겁·인성 태왕)", "뿌리": root_branches}
    return {"종격후보": False, "종류": "정격", "뿌리": root_branches}


# ── A5. 구조패턴 카탈로그 ──
def sipseong_counts(p: Pillars):
    ig = stem_idx(p.day[0])
    counts = {}
    for s in p.all_stems():
        if s == p.day[0]: continue
        ss = sipseong(ig, stem_idx(s))
        counts[ss] = counts.get(ss, 0) + 1
    # 지지는 정기 기준 간이 십성 산출(정밀화 여지 있음, 프로토타입 한계로 명시)
    for b in p.all_branches():
        jeonggi = JIJANGGAN[b][-1][0]
        ss = sipseong(ig, stem_idx(jeonggi))
        counts[ss] = counts.get(ss, 0) + 1
    return counts

def gujo_pattern(p: Pillars, wangso):
    ss = sipseong_counts(p)
    grp = {"비겁":0,"식상":0,"재성":0,"관성":0,"인성":0}
    for k,v in ss.items():
        grp[SIPSEONG_GROUP[k]] += v

    patterns = []
    if grp["재성"] >= 2 and wangso["verdict"] == "신약":
        patterns.append("재다신약 — 재성 과다+일간약, 현실·이성 부담 감당력 초과")
    if grp["비겁"] >= 3 and grp["재성"] <= 1:
        patterns.append("군겁쟁재(群劫爭財) — 비겁多가 재를 극탈, 재물·배우자 인연 붙었다끊김")
    if grp["식상"] >= 2 and grp["재성"] >= 1:
        patterns.append("식상생재(食傷生財) — 재능·표현으로 돈 버는 구조")
    if grp["관성"] >= 2 and any(k in ss for k in ["정관"]) and any(k in ss for k in ["편관"]):
        patterns.append("관살혼잡 — 정관+편관 혼재, 갈피 어려움(여명 남자운 다양)")
    if grp["인성"] >= 3 and wangso["verdict"] == "신약":
        patterns.append("인다신약(모자멸자) — 인성과다가 일간 매몰, 의존↑실행↓")
    return patterns, grp


# ── A9. 대운 순역 ──
def daewoon_direction(year_stem, gender):
    yy = STEM_YINYANG[stem_idx(year_stem)]
    if gender == "남":
        return "순행" if yy == "양" else "역행"
    else:
        return "역행" if yy == "양" else "순행"


def full_report(name, p: Pillars, gender):
    print(f"\n{'='*60}\n[{name}] {gender}명 — 년{p.year[0]}{p.year[1]} 월{p.month[0]}{p.month[1]} 일{p.day[0]}{p.day[1]}" + (f" 시{p.hour[0]}{p.hour[1]}" if p.hour else " 시주모름"))
    wangso = wangso_score(p)
    print(f"  왕쇠: {wangso['verdict']} (점수 {wangso['score']}/100, 확신도 {wangso['confidence']})")
    if wangso.get("override"):
        print(f"  ⚙️ {wangso['override']}")
    yongsin = yongsin_select(p, wangso)
    print(f"  용신: {yongsin['용신']} — 근거={yongsin['근거']} ({yongsin['설명']})")
    gyeok = gyeokguk_select(p)
    print(f"  격국: {gyeok['격']} (격지지={gyeok['격지지']}, 격간={gyeok['격간']}, {gyeok['판정근거']})")
    cnt = ohaeng_count(p)
    jong = jonggyeok_check(p, wangso, cnt)
    if jong["종격후보"]:
        print(f"  🔴 종격검토: {jong['종류']} / 뿌리={jong['뿌리']}")
    patterns, grp = gujo_pattern(p, wangso)
    print(f"  십성그룹: {grp}")
    for pat in patterns:
        print(f"  ▶ 구조진단: {pat}")
    dw = daewoon_direction(p.year[0], gender)
    print(f"  대운방향: {dw} ({STEM_YINYANG[stem_idx(p.year[0])]}년생 {gender}명)")
    return {"wangso": wangso, "yongsin": yongsin, "gyeok": gyeok, "jong": jong, "patterns": patterns}


if __name__ == "__main__":
    print("### 검증 테스트 — 이미 사주봇이 수기계산·감수 완료한 실제 케이스 재입력 ###")

    # 5편 감자11 (여) — 년庚辰 월己丑 일丙申, 시주 戌/酉 두 버전
    r1a = full_report("5편-감자11(戌시=戊戌 버전)", Pillars(("경","진"),("기","축"),("병","신"),("무","술")), "여")
    r1b = full_report("5편-감자11(酉시=丁酉 버전)", Pillars(("경","진"),("기","축"),("병","신"),("정","유")), "여")
    r1c = full_report("5편-감자11(시주모름 버전, 참고)", Pillars(("경","진"),("기","축"),("병","신")), "여")

    # 6편 여 (1995.07.25 새벽1시) — 년乙亥 월癸未 일丁巳, 시주 辛丑/庚子
    r2a = full_report("6편-여(자시=辛丑 무보정)", Pillars(("을","해"),("계","미"),("정","사"),("신","축")), "여")
    r2b = full_report("6편-여(진태양시=庚子)", Pillars(("을","해"),("계","미"),("정","사"),("경","자")), "여")

    # 6편 남 (1990.03.30) — 년庚午 월己卯 일甲午, 시주모름
    r3 = full_report("6편-남(주창환, 시주모름)", Pillars(("경","오"),("기","묘"),("갑","오")), "남")

    # seorin 케이스 (여, 1995.07.18 未시) — 년乙亥 월癸未 일庚戌 시癸未
    r4 = full_report("seorin(여, 1995.07.18 未시)", Pillars(("을","해"),("계","미"),("경","술"),("계","미")), "여")

    print(f"\n{'='*60}\n### 재현성 대조 (엔진출력 vs 사주봇 기존 수기판정) ###")
    checks = [
        ("5편 신약여부", r1a["wangso"]["verdict"], "신약(수기판정)"),
        ("5편 酉시 도화 관련 용신방향", r1b["yongsin"]["용신"], "참고용(수기는 신살 별도로직)"),
        ("6편여 신약여부", r2a["wangso"]["verdict"], "신약(수기판정)"),
        ("6편여 용신", r2a["yongsin"]["용신"], "木/火(수기: 용신木 희신火)"),
        ("6편남 신강여부", r3["wangso"]["verdict"], "신강/양인(수기판정)"),
        ("6편남 격국", r3["gyeok"]["격"], "양인격 계열(수기: 卯=甲의 양인)"),
        ("6편남 구조", r3["patterns"], "水0 인성부재(수기판정)"),
        ("seorin 신약여부", r4["wangso"]["verdict"], "신약(케이스파일 기록)"),
    ]
    for label, engine_out, manual in checks:
        print(f"  [{label}] 엔진={engine_out} | 기존수기={manual}")
