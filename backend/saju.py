CHEONGAN = ["갑","을","병","정","무","기","경","신","임","계"]
JIJI     = ["자","축","인","묘","진","사","오","미","신","유","술","해"]
HANJA_CG = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
HANJA_JJ = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# 절기별 월지 (양력 월 → 절기 고려 간략 버전)
# 실제 절기 날짜 하드코딩 (주요 기준일)
JEOLGI = {
    1:  (6,  "축"),  2:  (4,  "인"),  3:  (6,  "묘"),
    4:  (5,  "진"),  5:  (6,  "사"),  6:  (6,  "오"),
    7:  (7,  "미"),  8:  (7,  "신"),  9:  (8,  "유"),
    10: (8,  "술"),  11: (7,  "해"),  12: (7,  "자"),
}

def get_month_ji(month, day):
    jeolgi_day, ji = JEOLGI[month]
    if day < jeolgi_day:
        prev_month = 12 if month == 1 else month - 1
        _, ji = JEOLGI[prev_month]
    return ji

def year_pillar(year):
    cg = CHEONGAN[(year-4)%10]
    jj = JIJI[(year-4)%12]
    return cg, jj, HANJA_CG[(year-4)%10] + HANJA_JJ[(year-4)%12]

def month_pillar(year, month, day):
    ji = get_month_ji(month, day)
    ji_idx = JIJI.index(ji)
    yg = CHEONGAN[(year-4)%10]
    base = {"갑":2,"을":4,"병":6,"정":8,"무":0,"기":2,"경":4,"신":6,"임":8,"계":0}
    gan_idx = (base[yg] + (ji_idx - 2) % 12) % 10
    cg = CHEONGAN[gan_idx]
    return cg, ji, HANJA_CG[gan_idx] + HANJA_JJ[ji_idx]

def day_pillar(year, month, day):
    y, m = year, month
    if m <= 2:
        y -= 1; m += 12
    A = y // 100
    B = 2 - A + A // 4
    jd = int(365.25*(y+4716)) + int(30.6001*(m+1)) + day + B - 1524
    cg = CHEONGAN[(jd+6)%10]
    jj = JIJI[(jd+8)%12]
    return cg, jj, HANJA_CG[(jd+6)%10] + HANJA_JJ[(jd+8)%12]

HOUR_JI = [
    (23,1,"자"),(1,3,"축"),(3,5,"인"),(5,7,"묘"),
    (7,9,"진"),(9,11,"사"),(11,13,"오"),(13,15,"미"),
    (15,17,"신"),(17,19,"유"),(19,21,"술"),(21,23,"해"),
]

def get_hour_ji(hour):
    if hour >= 23 or hour < 1: return "자"
    for s, e, ji in HOUR_JI:
        if s <= hour < e: return ji
    return "자"

def hour_pillar(day_gan, hour):
    ji = get_hour_ji(hour)
    ji_idx = JIJI.index(ji)
    base = {"갑":0,"을":2,"병":4,"정":6,"무":8,"기":0,"경":2,"신":4,"임":6,"계":8}
    gan_idx = (base[day_gan] + ji_idx) % 10
    cg = CHEONGAN[gan_idx]
    return cg, ji, HANJA_CG[gan_idx] + HANJA_JJ[ji_idx]

def calc_pillars(year, month, day, hour=None):
    yp = year_pillar(year)
    mp = month_pillar(year, month, day)
    dp = day_pillar(year, month, day)
    hp = hour_pillar(dp[0], hour) if hour is not None else None
    return yp, mp, dp, hp

def calc_daeun(year, month, day, gender):
    """대운 계산 (간략 버전)"""
    yang_year = ((year - 4) % 10) % 2 == 0
    forward = (yang_year and gender == "남") or (not yang_year and gender == "여")
    _, _, month_hanja = month_pillar(year, month, day)
    mp_gan_idx = CHEONGAN.index(month_pillar(year, month, day)[0])
    mp_ji_idx  = JIJI.index(month_pillar(year, month, day)[1])
    daeun = []
    for i in range(1, 9):
        if forward:
            gi = (mp_gan_idx + i) % 10
            ji = (mp_ji_idx  + i) % 12
        else:
            gi = (mp_gan_idx - i) % 10
            ji = (mp_ji_idx  - i) % 12
        start_age = i * 10 - 7
        daeun.append({
            "hanja": HANJA_CG[gi] + HANJA_JJ[ji],
            "korean": CHEONGAN[gi] + JIJI[ji],
            "start": start_age,
            "end": start_age + 10,
        })
    return daeun

# ── 궁합 ───────────────────────────────────────────────────

OHAENG = {
    "갑":"木","을":"木","병":"火","정":"火","무":"土",
    "기":"土","경":"金","신":"金","임":"水","계":"水",
}
OHAENG_HAP = {  # 오행 상생 방향 (a가 b를 생함)
    ("木","火"):True,("火","土"):True,("土","金"):True,("金","水"):True,("水","木"):True,
}
OHAENG_GEUK = {  # 오행 상극 방향 (a가 b를 극함)
    ("木","土"):True,("土","水"):True,("水","火"):True,("火","金"):True,("金","木"):True,
}
CHEONGAN_HAP_MAP = {  # 천간합
    frozenset(["갑","기"]): ("甲己合", "토(土) 합", "현실적이고 안정적인 관계 — 서로의 부족한 면을 채워줌"),
    frozenset(["을","경"]): ("乙庚合", "금(金) 합", "의리와 신뢰 중심 — 한번 맺으면 끊기 어려운 관계"),
    frozenset(["병","신"]): ("丙辛合", "수(水) 합", "서로 강하게 끌리는 관계 — 에너지가 잘 맞음"),
    frozenset(["정","임"]): ("丁壬合", "목(木) 합", "감성적·로맨틱 — 정서적 교감이 깊음"),
    frozenset(["무","계"]): ("戊癸合", "화(火) 합", "열정과 헌신 — 서로에게 강한 인상을 줌"),
}
CHEONGAN_CHUNG_MAP = {  # 천간충
    frozenset(["갑","경"]): "甲庚冲 — 서로 부딪히는 에너지, 주도권 갈등 주의",
    frozenset(["을","신"]): "乙辛冲 — 섬세함과 예리함의 충돌, 상처 주고받기 쉬움",
    frozenset(["병","임"]): "丙壬冲 — 열정과 이성의 충돌, 방향성 불일치",
    frozenset(["정","계"]): "丁癸冲 — 감성 대 논리의 충돌, 서로 이해 못 할 수 있음",
}
EUMYANG = {"갑":"양","병":"양","무":"양","경":"양","임":"양",
           "을":"음","정":"음","기":"음","신":"음","계":"음"}

def ohaeng_relation(g1, g2):
    o1, o2 = OHAENG.get(g1,""), OHAENG.get(g2,"")
    if o1 == o2:
        return "비화(比和)", f"같은 오행({o1}) — 동질감이 강하고 경쟁심도 생길 수 있음"
    if OHAENG_HAP.get((o1,o2)):
        return "상생(相生)", f"{o1}이 {o2}를 생함 — 나(대상1)가 상대를 키워주는 관계"
    if OHAENG_HAP.get((o2,o1)):
        return "상생(相生)", f"{o2}이 {o1}를 생함 — 상대가 나(대상1)를 키워주는 관계"
    if OHAENG_GEUK.get((o1,o2)):
        return "상극(相克)", f"{o1}이 {o2}를 극함 — 나(대상1)가 상대에게 압박이 될 수 있음"
    if OHAENG_GEUK.get((o2,o1)):
        return "상극(相克)", f"{o2}이 {o1}를 극함 — 상대가 나(대상1)에게 압박이 될 수 있음"
    return "중립", "특별한 상생·상극 없음"

def build_compatibility_reading(g1, g2, ilgan1, ilgan2):
    o1, o2 = OHAENG.get(ilgan1, ""), OHAENG.get(ilgan2, "")
    ey1, ey2 = EUMYANG.get(ilgan1, ""), EUMYANG.get(ilgan2, "")
    oe_type, oe_desc = ohaeng_relation(ilgan1, ilgan2)
    hap   = CHEONGAN_HAP_MAP.get(frozenset([ilgan1, ilgan2]))
    chung = CHEONGAN_CHUNG_MAP.get(frozenset([ilgan1, ilgan2]))
    t1 = ILGAN_TRAITS.get(ilgan1, {"성격": "강한 에너지", "단점": "균형 필요", "오행": ""})
    t2 = ILGAN_TRAITS.get(ilgan2, {"성격": "강한 에너지", "단점": "균형 필요", "오행": ""})

    eumyang_desc = (
        "음양이 다름 — 서로 끌리고 보완되는 조화로운 에너지 구성"
        if ey1 != ey2 else
        "음양이 같음 — 동질감이 강하나 새로운 자극은 적을 수 있음"
    )

    if hap:
        hap_title = "천간합 ✓ (" + hap[0] + ")"
        hap_desc  = hap[2]
    elif chung:
        hap_title = "천간충 ⚠"
        hap_desc  = chung
    else:
        hap_title = "천간 중립"
        hap_desc  = "특별한 합충 없음 — 자연스러운 관계, 노력에 따라 깊어질 수 있음"

    if "상생" in oe_type:
        love_oe = "에너지를 서로 보완해주는 이상적인 구조예요."
    elif "비화" in oe_type:
        love_oe = "같은 에너지라 동질감이 크지만 자극이 필요해요."
    else:
        love_oe = "부딪힘이 있을 수 있어 서로 배려가 필요해요."

    if hap:
        love_hap = "천간합이 있어 자연스럽게 끌리는 구조예요. 처음 만남부터 묘하게 편안한 느낌을 받을 수 있어요."
    elif chung:
        love_hap = "천간충이 있어 처음엔 긴장감이 있지만, 그 긴장이 오히려 매력이 되기도 해요."
    else:
        love_hap = "자연스러운 발전형 관계예요. 시간이 쌓일수록 서로에게 익숙해지고 깊어지는 스타일이에요."

    if hap:
        marriage_hap = "합이 있어 결혼 후 서로 안정적으로 정착하는 구조예요. 장기적으로 함께할수록 더 잘 맞아요."
    else:
        marriage_hap = "결혼은 노력과 이해가 핵심이에요. 서로의 생활 방식을 존중하는 게 무엇보다 중요해요."

    marriage_oe = (
        "상생 관계라 함께 성장하며 가정을 꾸려나가는 힘이 있어요."
        if "상생" in oe_type else
        "서로의 차이를 강점으로 바꾸는 훈련이 필요해요."
    )

    if hap:
        biz_hap = "합이 있어 함께 일할 때 시너지가 나요. 목표가 같을 때 특히 강력한 팀이 돼요."
    elif chung:
        biz_hap = "충이 있어 사업에서 의견 충돌이 잦을 수 있어요. 역할을 명확히 나누는 게 중요해요."
    else:
        biz_hap = "협력 자체는 가능한 구조예요. 각자의 역할과 책임을 명확히 하면 좋은 결과를 낼 수 있어요."

    p1_trait = t1["성격"].split("·")[0]
    p2_trait = t2["성격"].split("·")[0]

    if hap:
        advice_hap = "합이 있다는 건 인연의 끈이 단단하다는 의미예요. 서로에 대한 믿음을 유지하세요."
    elif chung:
        advice_hap = "충이 있어도 극복하면 더 단단해져요. 충돌 자체보다 그 후 서로를 대하는 방식이 더 중요해요."
    else:
        advice_hap = "서로에 대한 이해를 쌓아가는 게 관계의 핵심이에요."

    if "상생" in oe_type:
        advice_oe = "서로 성장시켜주는 방향으로 에너지를 쓰세요."
    elif "비화" in oe_type:
        advice_oe = "비슷한 에너지끼리 의식적으로 새로운 자극을 만들어주세요."
    else:
        advice_oe = "극하는 에너지를 자극으로 전환하는 연습을 해보세요."

    items = [
        ("오행 상성",
         "대상1은 " + o1 + "(" + ilgan1 + "), 대상2는 " + o2 + "(" + ilgan2 + ")예요. "
         + oe_type + " 관계입니다. " + oe_desc + "."),
        ("천간 관계",
         hap_title + ". " + hap_desc + "."),
        ("음양 조화",
         eumyang_desc + ". 대상1(" + ilgan1 + ")은 " + ey1 + ", 대상2(" + ilgan2 + ")는 " + ey2 + "의 기운."),
        ("두 사람의 성격 조합",
         "대상1은 " + t1["성격"] + " 스타일이고, 대상2는 " + t2["성격"] + " 스타일이에요. "
         "서로의 강점이 만나면 에너지가 배가되지만, 부딪힐 때는 양쪽 단점이 동시에 튀어나올 수 있어요."),
        ("갈등 요소",
         "대상1의 단점(" + t1["단점"] + ")과 대상2의 단점(" + t2["단점"] + ")이 만날 때 주로 마찰이 생겨요. "
         "서로 다른 방식을 강요하지 않는 게 핵심이에요."),
        ("연애 궁합",
         love_hap + " " + oe_type + "이라 " + love_oe),
        ("결혼 궁합",
         marriage_hap + " " + marriage_oe),
        ("사업·협력 궁합",
         biz_hap + " 대상1의 " + p1_trait + " 기질과 대상2의 " + p2_trait + " 기질이 역할 분담에 도움이 돼요."),
        ("현재 두 사람의 에너지",
         "지금 이 시기는 서로를 더 깊이 이해하는 단계에 있어요. "
         "한쪽이 지칠 때 다른 한쪽이 받쳐주는 역할을 자연스럽게 하게 되는 시기예요. "
         "억지로 맞추려 하기보다 있는 그대로를 보여주는 게 더 좋은 흐름을 만들어요."),
        ("조언",
         advice_hap + " " + advice_oe),
    ]
    return items


# 14항목 풀이
ILGAN_TRAITS = {
    "갑": {"성격":"리더십·추진력·직선적","단점":"고집·융통성 부족","자존심":"85%","오행":"甲木"},
    "을": {"성격":"유연함·섬세함·예술적","단점":"우유부단·의존성","자존심":"70%","오행":"乙木"},
    "병": {"성격":"밝음·열정·카리스마","단점":"충동적·지속력 부족","자존심":"90%","오행":"丙火"},
    "정": {"성격":"따뜻함·직관·헌신","단점":"감정 기복·번아웃","자존심":"75%","오행":"丁火"},
    "무": {"성격":"안정·포용력·신뢰","단점":"변화 거부·답답함","자존심":"80%","오행":"戊土"},
    "기": {"성격":"섬세·현실적·분석적","단점":"걱정 많음·소심","자존심":"72%","오행":"己土"},
    "경": {"성격":"결단력·원칙·강함","단점":"냉정·타협 어려움","자존심":"88%","오행":"庚金"},
    "신": {"성격":"세련·완벽주의·예리함","단점":"예민·자존심 상처 잘 받음","자존심":"85%","오행":"辛金"},
    "임": {"성격":"지혜·유연·포용","단점":"방향성 부재·우유부단","자존심":"78%","오행":"壬水"},
    "계": {"성격":"직관·감수성·깊이","단점":"걱정·비밀스러움","자존심":"73%","오행":"癸水"},
}

def build_reading(year, month, day, hour, gender, yp, mp, dp, hp):
    ilgan = dp[0]
    t = ILGAN_TRAITS.get(ilgan, {"성격":"강한 에너지","단점":"균형 필요","자존심":"80%","오행":""})
    gender_str = "남성" if gender == "남" else "여성"
    hour_str = f"{hour}시" if hour is not None else "모름"

    items = [
        ("전체 인생", f"{t['오행']} 일간이세요. {t['성격']} 에너지를 타고나셨어요. 자기 색깔이 뚜렷하고 한번 마음먹으면 끝까지 가는 스타일이에요. 인생 전체 흐름이 천천히 단단하게 쌓여가는 구조예요."),
        ("살아왔던 방식", f"내 기준대로, 내 방식대로 살아오셨어요. 남한테 쉽게 기대거나 의지하기보다 스스로 해결하려는 경향이 강해요. 타협보다 직진이 익숙한 분이에요."),
        ("자존심", f"{t['자존심']}예요. 속으로 상처를 많이 받아도 겉으론 티 안 내는 편이에요. 무너져 보이기 싫어서 혼자 삭히는 경향이 있어요."),
        ("장점", f"{t['성격']}. 한번 믿으면 끝까지 가는 신뢰감도 큰 장점이에요. 리더십이 자연스럽게 나오고 정직함이 강점이에요."),
        ("단점", f"{t['단점']}. 이 부분만 조금 다듬으면 훨씬 더 잘 풀려요. 가까운 사람과의 관계에서 특히 이 부분이 마찰을 만들 수 있어요."),
        ("현재 상태", "변화의 시기에 서 있어요. 뭔가 정리가 필요하거나 새로운 국면으로 넘어가는 과도기예요. 지금까지 해온 것들을 점검하는 시기예요."),
        ("앞으로 키워야 할 것", "유연성이에요. 내 방식도 좋지만 상대방 입장도 받아들이는 능력을 키우면 훨씬 더 크게 열려요. 감정 표현도 조금 더 열어두는 게 도움이 돼요."),
        ("앞으로 조심해야 할 것", f"{t['단점']} 쪽이에요. 특히 가까운 사람일수록 이 부분이 관계에 균열을 만들 수 있어요. 말을 다듬는 연습이 필요해요."),
        ("연애방식", "감정 표현보다는 행동으로 보여주는 스타일이에요. 좋아해도 먼저 다가가기가 어렵고, 상대가 먼저 다가와 주길 기다리는 편이에요."),
        ("연애 상태", "지금은 인연이 들어올 타이밍을 준비하는 시기예요. 급하게 찾기보다 자연스럽게 만나지는 흐름이 맞아요."),
        ("결혼운", "결혼 자체는 있는 사주예요. 다만 시기가 중요한데, 본인이 안정되는 시점 이후에 훨씬 잘 맞는 인연이 와요."),
        ("현재 심리 상태", "겉으로는 괜찮아 보이지만 속으로는 꽤 지쳐 있는 상태예요. 혼자 너무 많이 안고 있지는 않은지 돌아봐야 할 때예요."),
        ("금전운", "크게 잃지는 않지만 모이는 속도가 더딘 시기예요. 지출 관리가 핵심이고 큰 투자나 보증은 지금은 피하세요."),
        ("직업운", "지금 하고 있는 일에서 성과가 나올 시기가 가까워지고 있어요. 조급해하지 말고 지금 자리에서 실력을 더 쌓아가세요."),
    ]
    return items
