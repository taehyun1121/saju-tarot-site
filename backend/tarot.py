import random

MAJOR = [
    "바보(0)","마법사(1)","여사제(2)","황후(3)","황제(4)",
    "교황(5)","연인(6)","전차(7)","힘(8)","은둔자(9)",
    "운명의바퀴(10)","정의(11)","매달린사람(12)","죽음(13)","절제(14)",
    "악마(15)","탑(16)","별(17)","달(18)","태양(19)","심판(20)","세계(21)",
]
SUITS  = ["완드","컵","소드","펜타클"]
PIPS   = ["에이스","2","3","4","5","6","7","8","9","10"]
COURTS = ["페이지","나이트","퀸","킹"]
DECK   = list(MAJOR)
for s in SUITS:
    for p in PIPS:   DECK.append(f"{p}/{s}")
    for c in COURTS: DECK.append(f"{c}/{s}")

MAJOR_FILES = {
    "바보(0)":"0. 바보 카드.jpg","마법사(1)":"1. 마법사 카드.jpg",
    "여사제(2)":"2. 여사제 카드.jpg","황후(3)":"3. 여황제 카드.jpg",
    "황제(4)":"4. 황제 카드.jpg","교황(5)":"5. 교황 카드.jpg",
    "연인(6)":"6. 연인 카드.jpg","전차(7)":"7. 전차 카드.jpg",
    "힘(8)":"8. 힘 카드.jpg","은둔자(9)":"9. 은둔자 카드.jpg",
    "운명의바퀴(10)":"10. 운명의 수레바퀴.jpg","정의(11)":"11. 정의 카드.jpg",
    "매달린사람(12)":"12. 행맨 카드.jpg","죽음(13)":"13. 죽음 카드.jpg",
    "절제(14)":"14. 절제 카드.jpg","악마(15)":"15. 악마 카드.jpg",
    "탑(16)":"16. 타워 카드.jpg","별(17)":"17. 별 카드.jpg",
    "달(18)":"18. 달 카드.jpg","태양(19)":"19. 태양 카드.jpg",
    "심판(20)":"20. 심판 카드.jpg","세계(21)":"21. 세계 카드.jpg",
}

def card_image_url(name: str) -> str:
    if name in MAJOR_FILES:
        return f"/static/cards/메이저카드/{MAJOR_FILES[name]}"
    pip, suit = name.split("/")
    if pip in COURTS:
        fname = f"{suit} {pip}.jpg"
    elif pip == "에이스":
        fname = f"{suit} 에이스.jpg"
    else:
        fname = f"{suit}{pip}.jpg"
    return f"/static/cards/{suit}/{fname}"

KEYWORDS = {
    "바보(0)":      ("새출발·모험·가능성",   "무모함·준비 부족"),
    "마법사(1)":    ("의지·실행력·창조",     "자신감 과잉·사기"),
    "여사제(2)":    ("직관·비밀·내면 지혜",  "억압된 감정·집착"),
    "황후(3)":      ("풍요·모성·창조력",     "의존·과보호"),
    "황제(4)":      ("권위·안정·구조",       "독재·경직"),
    "교황(5)":      ("전통·조언·믿음",       "형식주의·맹목적 복종"),
    "연인(6)":      ("선택·조화·사랑",       "우유부단·관계 갈등"),
    "전차(7)":      ("의지·승리·통제",       "공격성·방향 상실"),
    "힘(8)":        ("내면의 힘·용기·인내",  "자기의심·억압"),
    "은둔자(9)":    ("성찰·지혜·고독",       "고립·회피"),
    "운명의바퀴(10)":("전환점·기회·흐름",    "불운·저항"),
    "정의(11)":     ("공정·균형·진실",       "불공정·편향"),
    "매달린사람(12)":("희생·관조·대기",      "지연·희생 거부"),
    "죽음(13)":     ("변화·종결·재탄생",     "변화 거부·정체"),
    "절제(14)":     ("균형·조화·인내",       "과잉·불균형"),
    "악마(15)":     ("집착·욕망·속박",       "해방·각성"),
    "탑(16)":       ("급변·해체·혼란",       "재난 회피·위기 지속"),
    "별(17)":       ("희망·치유·영감",       "희망 상실·낙담"),
    "달(18)":       ("환상·불안·무의식",     "혼란 해소·명확함"),
    "태양(19)":     ("성공·활력·기쁨",       "과도한 낙관·자기중심"),
    "심판(20)":     ("각성·부활·부름",       "자기비판·과거 집착"),
    "세계(21)":     ("완성·통합·성취",       "미완성·지연"),
}
SUIT_KW = {
    "완드":   ("열정·행동·의욕",  "과욕·소진"),
    "컵":     ("감정·직관·관계",  "감정 억압·상실"),
    "소드":   ("사고·갈등·진실",  "혼란·분쟁"),
    "펜타클": ("물질·현실·안정",  "탐욕·손실"),
}

def get_keyword(name: str, reversed_: bool) -> str:
    if name in KEYWORDS:
        return KEYWORDS[name][1 if reversed_ else 0]
    for s, (p, n) in SUIT_KW.items():
        if s in name:
            return n if reversed_ else p
    return "변화·흐름"

def draw_cards(n: int) -> list:
    drawn = random.sample(DECK, n)
    return [{"name": c, "reversed": random.random() < 0.35,
             "image": card_image_url(c),
             "keyword": ""} for c in drawn]

def finalize_cards(cards: list) -> list:
    for c in cards:
        c["keyword"] = get_keyword(c["name"], c["reversed"])
    return cards

# ── 스프레드 정의 ───────────────────────────────────────────
SPREADS = {
    "sangdae": {
        "name": "상대방 마음 알고 싶을 때",
        "cards": 3,
        "description": "상대방이 나에 대해 어떻게 느끼는지 알고 싶을 때 사용",
        "positions": [
            {"num":1,"name":"심리 상태","desc":"상대방이 보는 질문자의 모습"},
            {"num":2,"name":"외부가 보는 나","desc":"상대방이 질문자에게 가지는 감정"},
            {"num":3,"name":"미래 상황","desc":"두 사람의 관계"},
        ],
        "layout": [
            {"pos":1,"col":0,"row":0},
            {"pos":2,"col":1,"row":0},
            {"pos":3,"col":2,"row":0},
        ],
        "gridCols": 3, "gridRows": 1,
    },
    "selection": {
        "name": "선택의 기로에 섰을 때",
        "cards": 3,
        "description": "두 가지 선택지 사이에서 결정이 필요할 때",
        "positions": [
            {"num":1,"name":"현재 문제","desc":"현재 직면한 문제점"},
            {"num":2,"name":"우선 방법","desc":"가장 먼저 선택할 수 있는 방법"},
            {"num":3,"name":"차후 선택","desc":"두 번째로 선택할 수 있는 방법"},
        ],
        "layout": [
            {"pos":2,"col":0,"row":0},
            {"pos":1,"col":1,"row":0},
            {"pos":3,"col":2,"row":0},
        ],
        "gridCols": 3, "gridRows": 1,
    },
    "success": {
        "name": "일의 성패 가늠하기 힘들 때",
        "cards": 3,
        "description": "일이 잘 될지 가늠하기 어려울 때",
        "positions": [
            {"num":1,"name":"나의 희망","desc":"질문에 대한 희망"},
            {"num":2,"name":"현재 고민","desc":"질문에 대한 걱정"},
            {"num":3,"name":"주변 상황","desc":"주변 환경이 좋은지 나쁜지"},
        ],
        "layout": [
            {"pos":3,"col":0,"row":0},
            {"pos":2,"col":1,"row":0},
            {"pos":1,"col":2,"row":0},
        ],
        "gridCols": 3, "gridRows": 1,
    },
    "relation3": {
        "name": "관계의 이해가 필요할 때",
        "cards": 3,
        "description": "관계의 원인과 미래를 파악하고 싶을 때",
        "positions": [
            {"num":1,"name":"질문의 원인","desc":"질문의 원인과 이유"},
            {"num":2,"name":"질문자 마음","desc":"질문자의 마음"},
            {"num":3,"name":"미래 상황","desc":"앞으로 전개될 상황"},
        ],
        "layout": [
            {"pos":2,"col":0,"row":0},
            {"pos":1,"col":1,"row":0},
            {"pos":3,"col":2,"row":0},
        ],
        "gridCols": 3, "gridRows": 1,
    },
    "four": {
        "name": "4장 배열 (Four Card)",
        "cards": 4,
        "description": "문제의 답을 빠르게 찾아야 할 때",
        "positions": [
            {"num":1,"name":"현재 상황","desc":"현재 상황을 비롯한 전체적인 문제"},
            {"num":2,"name":"영향을 미치는 환경","desc":"질문자에게 영향을 미치는 사람·생각·일"},
            {"num":3,"name":"영향을 미치는 영향","desc":"질문자에게 영향을 미치는 문제"},
            {"num":4,"name":"극복 방법","desc":"문제를 극복할 수 있는 해결 방법"},
        ],
        "layout": [
            {"pos":1,"col":0,"row":0},
            {"pos":2,"col":1,"row":0},
            {"pos":3,"col":2,"row":0},
            {"pos":4,"col":3,"row":0},
        ],
        "gridCols": 4, "gridRows": 1,
    },
    "five": {
        "name": "5장 배열 (Five Card)",
        "cards": 5,
        "description": "시간의 흐름에 따라 세밀하게 파악하고 싶을 때",
        "positions": [
            {"num":1,"name":"가장 먼 과거","desc":"가장 먼 과거"},
            {"num":2,"name":"가까운 과거","desc":"최근에 있었던 가까운 상황"},
            {"num":3,"name":"현재","desc":"현재의 문제점·상황"},
            {"num":4,"name":"가까운 미래","desc":"앞으로 다가올 가까운 미래"},
            {"num":5,"name":"먼 미래","desc":"가장 먼 미래"},
        ],
        "layout": [
            {"pos":1,"col":0,"row":0},
            {"pos":2,"col":1,"row":0},
            {"pos":3,"col":2,"row":0},
            {"pos":4,"col":3,"row":0},
            {"pos":5,"col":4,"row":0},
        ],
        "gridCols": 5, "gridRows": 1,
    },
    "horseshoe": {
        "name": "말편자 배열법",
        "cards": 5,
        "description": "광범위한 질문, 인간관계 외 특정 문제에 적용",
        "positions": [
            {"num":1,"name":"현재 상황","desc":"내담자 문제의 현재 상태·마음"},
            {"num":2,"name":"문제의 쟁점","desc":"미래에 떠오르는 쟁점·중요 요소"},
            {"num":3,"name":"문제의 핵심","desc":"현재 가장 고민하는 핵심 문제"},
            {"num":4,"name":"가까운 미래","desc":"앞으로 6개월 동안의 모습"},
            {"num":5,"name":"먼 미래","desc":"최종 결과"},
        ],
        "layout": [
            {"pos":1,"col":0,"row":2},
            {"pos":2,"col":1,"row":1},
            {"pos":3,"col":2,"row":0},
            {"pos":4,"col":3,"row":1},
            {"pos":5,"col":4,"row":2},
        ],
        "gridCols": 5, "gridRows": 3,
    },
    "relation7": {
        "name": "관계 배열법",
        "cards": 7,
        "description": "사랑·연애·인간관계 문제에 적용",
        "positions": [
            {"num":1,"name":"질문자","desc":"질문자가 이 관계에 대해 느끼는 감정·상태"},
            {"num":2,"name":"상대방","desc":"상대방이 이 관계·질문자에 대해 느끼는 것"},
            {"num":3,"name":"현재 상황","desc":"관계의 현재 성질·분위기"},
            {"num":4,"name":"떠오르는 문제","desc":"관계가 향하는 가까운 미래의 쟁점"},
            {"num":5,"name":"문제의 핵심","desc":"해석의 핵심 카드"},
            {"num":6,"name":"가까운 미래","desc":"6~12개월 사이의 미래"},
            {"num":7,"name":"먼 미래","desc":"내년까지의 미래"},
        ],
        "layout": [
            {"pos":1,"col":1,"row":2},
            {"pos":2,"col":2,"row":2},
            {"pos":3,"col":0,"row":1},
            {"pos":4,"col":1,"row":1},
            {"pos":5,"col":2,"row":0},
            {"pos":6,"col":3,"row":0},
            {"pos":7,"col":3,"row":1},
        ],
        "gridCols": 4, "gridRows": 3,
    },
    "magic7": {
        "name": "매직 세븐 (Magic Seven)",
        "cards": 7,
        "description": "목적을 이루기 위한 조언에 특화. 원하는 것이 명확할 때 사용",
        "positions": [
            {"num":1,"name":"과거의 사건","desc":"현재 문제를 있게 한 과거"},
            {"num":2,"name":"현재 상태","desc":"현재 내담자의 상태"},
            {"num":3,"name":"가까운 미래","desc":"내담자의 가까운 미래"},
            {"num":4,"name":"문제 해결 방법","desc":"문제를 해결할 수 있는 방법"},
            {"num":5,"name":"주변 환경","desc":"내담자의 주변 환경"},
            {"num":6,"name":"장애물","desc":"현재 가지고 있는 문제·장애물"},
            {"num":7,"name":"결과","desc":"앞으로의 결과"},
        ],
        "layout": [
            {"pos":1,"col":1,"row":0},
            {"pos":2,"col":2,"row":2},
            {"pos":3,"col":0,"row":2},
            {"pos":4,"col":1,"row":2},
            {"pos":5,"col":0,"row":1},
            {"pos":6,"col":2,"row":1},
            {"pos":7,"col":1,"row":1},
        ],
        "gridCols": 3, "gridRows": 3,
    },
    "celtic": {
        "name": "켈틱 크로스",
        "cards": 10,
        "description": "가장 널리 쓰이는 배열. 현재~미래 전반을 종합적으로 파악",
        "positions": [
            {"num":1,"name":"현재 위치","desc":"내담자의 현재 상황과 문제"},
            {"num":2,"name":"현재 방해물","desc":"현재 상황을 가로막는 장애물 또는 도움"},
            {"num":3,"name":"가까운 미래","desc":"한 달 앞의 가까운 미래"},
            {"num":4,"name":"오래된 과거","desc":"1년 이상 된 오래된 과거"},
            {"num":5,"name":"가까운 과거","desc":"6개월 이내의 가까운 과거"},
            {"num":6,"name":"미래","desc":"앞으로 2개월 정도의 미래"},
            {"num":7,"name":"내가 보는 나","desc":"내담자의 감정 상태"},
            {"num":8,"name":"타인들의 평가","desc":"주위 환경·주변 상황"},
            {"num":9,"name":"심리 상태","desc":"내담자의 심리·가장 원하는 것·걱정"},
            {"num":10,"name":"결과","desc":"미래의 최종 결과와 문제의 해답"},
        ],
        "layout": [
            {"pos":1,"col":1,"row":1},
            {"pos":2,"col":1,"row":1,"cross":True},
            {"pos":3,"col":1,"row":0},
            {"pos":4,"col":1,"row":2},
            {"pos":5,"col":2,"row":1},
            {"pos":6,"col":0,"row":1},
            {"pos":7,"col":3,"row":3},
            {"pos":8,"col":3,"row":2},
            {"pos":9,"col":3,"row":1},
            {"pos":10,"col":3,"row":0},
        ],
        "gridCols": 4, "gridRows": 4,
    },
}
