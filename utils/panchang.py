"""Minimal tithi calculator for Odia lunar festivals.

Rule implemented (standard panchang): a festival falls on the day whose
SUNRISE tithi (Bhubaneswar) equals the target tithi of the named amanta month.

Accuracy: usually exact; can slip ±1 day on kshaya/vriddhi tithi days.
ALWAYS verify against drikpanchang.com before flipping approximate:false.
"""
from datetime import date, datetime, timedelta

import ephem

OBS_LAT, OBS_LON = "20.2961", "85.8245"  # Bhubaneswar

# sidereal rashi of the Sun at the month's opening new moon -> amanta month
_RASHI_TO_MONTH = {0: "vaishakha", 1: "jyeshtha", 2: "ashadha", 3: "shravana",
                   4: "bhadrapada", 5: "ashwin", 6: "kartika", 7: "margashira",
                   8: "pausha", 9: "magha", 10: "phalguna", 11: "chaitra"}

# festival_id -> (lunar_month, paksha, tithi)
LUNAR_RULES = {
    "rath_yatra":         ("ashadha",    "shukla", 2),   # Ashadha Shukla Dwitiya
    "durga_puja_cuttack": ("ashwin",     "shukla", 6),   # Shashthi (pandals open)
    "bali_jatra":         ("kartika",    "shukla", 15),  # Kartika Purnima
    "kumar_purnima":      ("ashwin",     "shukla", 15),  # Sharad Purnima
    "nuakhai":            ("bhadrapada", "shukla", 5),   # Bhadrapada Shukla Panchami
    "magha_saptami":      ("magha",      "shukla", 7),   # Chandrabhaga Mela
    "sital_sasthi":       ("jyeshtha",   "shukla", 6),
    "joranda_mela":       ("magha",      "shukla", 15),  # Magha Purnima
}


def _ayanamsa(d: date) -> float:
    """Lahiri ayanamsa (~0.05° error 1990–2060). Only used for month naming."""
    return 23.85 + (d.year - 2000) * 50.29 / 3600.0


def _sunrise(d: date) -> datetime:
    obs = ephem.Observer()
    obs.lat, obs.lon, obs.horizon = OBS_LAT, OBS_LON, "0"
    obs.date = datetime(d.year, d.month, d.day) - timedelta(hours=7)  # prev evening UTC
    return obs.next_rising(ephem.Sun()).datetime()                    # morning of d


def _elongation_deg(when: datetime) -> float:
    e = ephem.Date(when)
    raw = ephem.Ecliptic(ephem.Moon(e)).lon - ephem.Ecliptic(ephem.Sun(e)).lon
    return (raw % (2 * ephem.pi)) * 180.0 / ephem.pi   # ayanamsa-free by construction


def _tithi(d: date, sample: str) -> int:               # 1..30
    t = _sunrise(d) if sample == "sunrise" else datetime(d.year, d.month, d.day, 5, 30)
    return int(_elongation_deg(t) // 12) + 1


def lunar_month(d: date) -> str:
    """Amanta month name: named by sidereal solar rashi at the last new moon."""
    nm = ephem.previous_new_moon(datetime(d.year, d.month, d.day)).datetime()
    sun = ephem.Ecliptic(ephem.Sun(ephem.Date(nm))).lon * 180.0 / ephem.pi
    return _RASHI_TO_MONTH[int(((sun - _ayanamsa(nm.date())) % 360.0) // 30)]


def compute_dates(festival_id: str, year: int) -> list[dict]:
    """All occurrences of the festival whose START falls in Gregorian `year`."""
    month, paksha, tithi = LUNAR_RULES[festival_id]
    target = tithi if paksha == "shukla" else 15 + tithi
    days = [date(year, 1, 1) + timedelta(n) for n in range(365 + (year % 4 == 0))]

    for sample in ("sunrise", "noon"):                 # noon = kshaya-tithi fallback
        hits = [d for d in days if lunar_month(d) == month and _tithi(d, sample) == target]
        if hits:
            break
    if not hits:
        return []
    if len(hits) > 1:                                  # Adhika (leap) month:
        hits = [hits[-1]]                              # festivals fall in the 2nd (nija)
    return [{"date": hits[0], "rule": f"{month} {paksha} tithi {tithi}"}]