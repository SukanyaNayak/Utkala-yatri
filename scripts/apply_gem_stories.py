"""Merge hand-written gem stories into data/places.json (matched by name).
Review with git diff, then:  python scripts/seed_catalog.py
⚠️ Numbers/facts below are from general knowledge — verify each before demo."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "places.json"

STORIES = {
    "mangalajodi": {
        "description": "A wetland village on Chilika's northern edge where former bird "
                       "poachers now work as protectors and boat guides — one of India's "
                       "best community-conservation stories. Winter dawns bring thousands "
                       "of migratory waders within a canoe's length.",
        "insider_tip": "Book the dawn boat through the village ecotourism counter; "
                       "Nov–Feb is peak birding season.",
    },
    "daringbadi": {
        "description": "Odisha's hill-station oddity at around 3,000 ft: pine groves, "
                       "coffee gardens and some of the state's coolest winter nights. "
                       "The surrounding Kandhamal hills double as a scenic drive.",
        "insider_tip": "Dec–Jan is frost season; small local homestays beat the big resorts.",
    },
    "deomali": {
        "description": "At roughly 1,672 m, Deomali is Odisha's highest peak — a roll of "
                       "green hills and tribal villages in Koraput. The drive up is as "
                       "much the attraction as the summit panorama.",
        "insider_tip": "Time it for sunset; combine with Koraput's Parab festival (Nov–Dec).",
    },
    "hirakud": {
        "description": "One of the world's longest earthen dams (about 26 km) holding "
                       "back the Mahanadi near Sambalpur. The dyke-top drive and the "
                       "Gandhi Minar tower views are quintessentially Odia.",
        "insider_tip": "Sunset from Gandhi Minar; monsoon-season water releases are dramatic.",
    },
    "panchalingeswar": {
        "description": "Five lingas lie bathed by a mountain stream on this forested hill "
                       "near Nilagiri — pilgrims wade upstream to reach them. A shrine "
                       "that doubles as a creek-side mini-trek.",
        "insider_tip": "Carry footwear you can take off — the path is in shallow water "
                       "most of the year.",
    },
    "chandrabhaga": {
        "description": "The beach where the sun rises for Konark: a wide, open shoreline "
                       "that hosts the Magha Saptami sea-bathing festival. At dawn you'll "
                       "share the sand with fishermen rather than crowds.",
        "insider_tip": "Pair with the Sun Temple; February's Magha Saptami is the big day.",
    },
    "ratnagiri": {
        "description": "Part of Jajpur's 'Buddhist Diamond Triangle', Ratnagiri's hilltop "
                       "mahavihara holds sprawling stupa fields and monastery ruins — "
                       "Buddhist Odisha at its most atmospheric.",
        "insider_tip": "Do the Udayagiri–Lalitgiri–Ratnagiri loop in one day; "
                       "start at Ratnagiri's museum.",
    },
    "taptapani": {
        "description": "A steaming sulfur spring beside a forest road in Gajapati, where "
                       "a natural tank draws pilgrims and picnickers alike. The drive "
                       "through tribal market country is half the experience.",
        "insider_tip": "The OTDC rooms overlook the spring; winter mornings are the magic hour.",
    },
}


def main() -> None:
    places = json.loads(FILE.read_text(encoding="utf-8"))
    hit, missed = 0, dict(STORIES)
    for p in places:
        for key in list(STORIES):
            if key in p.get("name", "").lower():
                p["description"] = STORIES[key]["description"]
                p["insider_tip"] = STORIES[key]["insider_tip"]
                p["description_source"] = "hand_curated"
                hit += 1
                missed.pop(key)
                break
    FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(f"✅ {hit} stories applied. Unmatched keys: {list(missed) or 'none'}")


if __name__ == "__main__":
    main()