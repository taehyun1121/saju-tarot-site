"""test_saju_pillars.py — 사주 사주(四柱) 계산 회귀테스트.

실행: python3 test_saju_pillars.py     (백엔드 디렉토리에서)
필요: pip install sxtwl korean_lunar_calendar   ※개발 전용, requirements.txt에는 안 넣는다
      (배포는 `jeolgi_table.py` 정적표만 쓴다 — C확장 의존성을 프로덕션에 늘리지 않으려고)

🔴 왜 만들었나 (2026-08-11, 사주팔자봇 제보 → 코코 수정)
  `day_pillar()`가 **모든 날짜에서** 오답이었다. 특정 날짜 문제가 아니라 상수가 틀려
  정답보다 간+3·지+5(60갑자로 -7) 어긋났다. 지금까지 나간 리포트·답글 전부가 영향권이다.
  같은 종류의 사고를 두 번 내지 않으려면 **검증이 코드로 남아야** 한다.

🔴 검증 기준의 함정 — 라이브러리마다 보는 게 다르다
  · **일주**: sxtwl · korean_lunar_calendar 둘 다 동일. 기준으로 써도 된다.
  · **월주**: korean_lunar_calendar의 `getGapJaString()` 월주는 **음력 초하루에 바뀐다**
    (실측: 2001-02-23=음2/1에서 경인→신묘). 즉 **음력월 간지이지 명리 월주(절기 기준)가 아니다.**
    → **월주 검증에 klc를 쓰면 안 된다.** sxtwl만 쓴다.
  · **시간대**: sxtwl은 중국시(UTC+8), 우리 표는 KST(UTC+9). 절기가 중국시 23시대면
    날짜가 하루 갈린다(실측 73건). 한국 서비스이므로 우리는 KST를 유지하고,
    이 차이는 아래 3번 항목으로 분리해 보고한다(실패가 아니라 **기준 차이**).
"""
import importlib.util
import random
import datetime
import sys

spec = importlib.util.spec_from_file_location("saju", "saju.py")
saju = importlib.util.module_from_spec(spec)
spec.loader.exec_module(saju)
from jeolgi_table import JEOLGI_TABLE

try:
    import sxtwl
except ImportError:
    print("sxtwl 미설치 — pip install sxtwl 후 다시 실행"); sys.exit(2)

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"


def truth(y, m, d):
    x = sxtwl.fromSolar(y, m, d)
    return (GAN[x.getYearGZ().tg] + ZHI[x.getYearGZ().dz],
            GAN[x.getMonthGZ().tg] + ZHI[x.getMonthGZ().dz],
            GAN[x.getDayGZ().tg] + ZHI[x.getDayGZ().dz])


def is_jie_day(y, m, d):
    return any((jm, jd) == (m, d) for jm, jd, _ in JEOLGI_TABLE.get(y, []))


def main():
    random.seed(7)
    dates = []
    start, end = datetime.date(1930, 1, 1), datetime.date(2030, 12, 31)
    span = (end - start).days
    for _ in range(3000):
        dt = start + datetime.timedelta(days=random.randint(0, span))
        dates.append((dt.year, dt.month, dt.day))
    # 입춘 경계 집중 — 년주 버그가 나던 구간
    for y in range(1930, 2031):
        for d in range(1, 9):
            dates.append((y, 2, d))
        dates += [(y, 1, 1), (y, 1, 15), (y, 12, 31)]

    day_fail, ym_fail, jie_after_fail, tz_diff = [], [], [], []

    for y, m, d in dates:
        ty, tm, td = truth(y, m, d)

        # ① 일주 — 시각과 무관하다. 여기서 한 건이라도 틀리면 그게 이번 버그의 재발이다.
        _, _, dp, _ = saju.calc_pillars(y, m, d)
        if dp[2] != td:
            day_fail.append((y, m, d, dp[2], td))

        if is_jie_day(y, m, d):
            # ② 절기 당일 — 절입 시각 이후(23:59)면 sxtwl과 같아야 한다
            yp, mp, _, _ = saju.calc_pillars(y, m, d, 23, 59)
            if yp[2] != ty or mp[2] != tm:
                jie_after_fail.append((y, m, d, yp[2], ty, mp[2], tm))
        else:
            yp, mp, _, _ = saju.calc_pillars(y, m, d)
            if yp[2] != ty or mp[2] != tm:
                # ③ 시간대(KST vs 중국시) 차이인지 분리한다 — 실패가 아니라 기준 차이일 수 있다
                y2, m2, d2 = (datetime.date(y, m, d) + datetime.timedelta(days=1)).timetuple()[:3]
                if is_jie_day(y, m, d) or is_jie_day(y2, m2, d2) or is_jie_day(*(datetime.date(y, m, d) - datetime.timedelta(days=1)).timetuple()[:3]):
                    tz_diff.append((y, m, d, mp[2], tm))
                else:
                    ym_fail.append((y, m, d, yp[2], ty, mp[2], tm))

    n = len(dates)
    print(f"검증 {n}건 (무작위 3000 + 입춘 경계 집중)")
    print(f"① 일주 불일치            : {len(day_fail)}건   {'✅' if not day_fail else '🔴 이번 버그 재발'}")
    print(f"② 절기당일+시각지정 불일치: {len(jie_after_fail)}건   {'✅' if not jie_after_fail else '🔴'}")
    print(f"③ 절기 인접일 기준차(KST) : {len(tz_diff)}건   (sxtwl=중국시라 하루 갈리는 구간. 실패 아님)")
    print(f"④ 그 외 년/월주 불일치    : {len(ym_fail)}건   {'✅' if not ym_fail else '🔴 진짜 버그'}")

    for label, arr in (("일주", day_fail), ("절기당일", jie_after_fail), ("년/월주", ym_fail)):
        for f in arr[:5]:
            print(f"   [{label}] {f}")

    bad = len(day_fail) + len(jie_after_fail) + len(ym_fail)
    print("\n" + ("통과 — ①②④ 모두 0건" if bad == 0 else f"🔴 실패 {bad}건"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
