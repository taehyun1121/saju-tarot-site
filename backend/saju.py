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
