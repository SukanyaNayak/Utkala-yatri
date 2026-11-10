"""UtkalaYatri — landmark recognition router (drop-in replacement).
=================================================================
COPY THIS FILE OVER   backend/routers/landmark.py   (whole file).

Your main.py stays EXACTLY as it is — it already wires this router:

    app.include_router(landmark.router, prefix="/api/landmark", tags=["landmark"])

What you get
------------
POST /api/landmark  (also /api/landmark/identify and /api/landmark/scan)
    Body:  {"imageBase64": "<data URL or bare base64>", "lang": "en|hi|or"}
    (alternate key names accepted: image_base64 / image / base64 / dataUrl /
     photo — the old field names your code may have used)
    Reply: {"found": true, "name", "city", "description", "best_time"}
           {"found": false}                                  → no match
           {"found": false, "error": "landmark_bad_image"}   → not a photo
           {"found": false, "error": "landmark_unavailable"} → Pillow missing

GET  /api/landmark      → {"router": "landmark", "ready": bool, "mode": ...,
                            "pool_landmarks": N, "pool_photos": M}  (debug)

Two recognition paths, tried in order:
  1. VISION API — recognises ANY photo, any angle. Off until you set
     VISION_API_KEY; OpenAI-compatible, so these all work:
       VISION_API_KEY    your key (required to switch this on)
       VISION_BASE_URL   optional · default https://api.openai.com/v1
                         Gemini free tier:
                         https://generativelanguage.googleapis.com/v1beta/openai
       VISION_MODEL      optional · default gpt-4o-mini (Gemini: gemini-2.0-flash)
     Any vision-API failure falls through to the offline matcher.
  2. PHOTO-MATCH (offline, no key): the uploaded photo is compared against an
     embedded pool of 86 verified Odisha landmark photos (16 landmarks — every
     place in the dataset plus Mukteswar and Rajarani, and the popular Konark
     front-lions view) using pHash + dHash +
     colour/contrast layout, two framing probes per image. This reliably
     recognises (near-)copies of pool photos — the app's own gallery images
     and the popular stock shots they came from — but it cannot identify a
     different-angle snapshot of the same monument; that is what the vision
     path is for.

Setup:  pip install pillow       (in the backend environment)
This router imports NOTHING from your services/ layer, so it can never take
the rest of the API down; if Pillow is missing it registers its routes and
answers with a clear error instead.
"""

from typing import Optional

from fastapi import APIRouter, Body

router = APIRouter()

LM_POOL_B64 = (
    "eNqsfduSK8eR5L+c55ZZ3i/7KzQ+AAVgyJVGK9NIT/vzm+HukVl9hhqbNRuJzQbRQKFQFZEZFw/3//vj+dvv/3j8/c+Pv/7+"
    "58eP//XLL7/8+IT1//gJr4hHP75+XPUTniE90zO8w/sVf3z9Emv9ij19pRC/4hjrd/hKyf67fKW4fuegx+snp68423oc+Xis"
    "3yGv1891jLH+tt6feLw4+nqdPc7rsY4/6/q93p/WT+Df7b38vT4nr2PF9Tuu53LBe/C33NYx1mfMifOI67xiWsdd59Hr12hf"
    "dR28hC98mbJ+ZtQHJf7GAddBpv33OmBcb27rPd1OcP1ez8U4vtbb8vyq4Wt85f5V5tf6j/zV1hvX69cJRfucvL5o6Xx/XSe1"
    "vkhcJzWqnUWzK2QHKcPelNaB1rvjV01fxb7EV+9fbV0l+xLrv1O0s492bdZ1HOsbpI5nY0hfddinr8PZm9eJJzsp3IKvdeHX"
    "UdYR1hUZdnPW43Uq9lzldY6z43rFHniaOfKardNdx7PjrzNeT6570+x2rKdwAezEm71HJzML7IK2kXTspsdNn2O/A+55bLpM"
    "qfFD1iVdfyl2BuuvucJq9tnau3qjxdgn9cmbguc7H68zhBXhZ/B99rOucrQLGeavy46n7CbS/qbetD5w3ajWaRdhXczCW+jn"
    "m8uv6+3LWXpczpLe352l0Fmu9wzmLLCrQGO134EGD+dYNzdlM1izuygDXs/FDsPmewccyowZTpV44fyYdJbGGwdnGXQQczL7"
    "jDTofLDnRAeF41TZdZedD7238Kbb55vZhK+Zzb5pwOtJuxpwCn2RkHQQXXfc6cj7Zu/L9Lq4XrvOb91V84Jh5rlcb/1X/Vp3"
    "yL6VmYCZXuv0HPtAu+zrDsTlGMsGtrfYm+2QX+vgxT7ra51ZteXmaxndyF/24eaB66qu019PLJOvZgDmmAnPN7jLstflZdku"
    "mJ3bWhHWea6bDOtan93s/Vq4cJ3tK5rX2X+bGdrZ1iwPnHh1/loWbgsdXLzbxcYlWNZqBl3Xu8yz46ABTxoy7pgtX3aX192l"
    "i1R+mp2OrVRwFV/KYLJ2xFZ5DraeTTtPs4mid1f+t9mHLYiD95qP5YhYKLUI4DsOnWU0G4CrTFroutH45nZ+3Sxl4AaaryRc"
    "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"
    "cK91sxMwKcrI92tVkxzrASCGKHOw8EO22I7Kj4RXi8TUe4T68zxDmzl9OQNBKS5qTawBy6WnBrlehA3nepZeyihhuUYoV5Rr"
    "pDJbeY/5KIZN/WXPdgIENs4El1PzZhfG9sG0ceZCfZqxaBrSGR+CzD/flLxCOnKVQS6hyuFWU3USgn0u/QhDusZe6t7ZQ26K"
    "xZhzvpNTrUEa5RtqEfOZBevtBvNxabx2Zs0VykwkdK1IVbpOITicaVe0FYT7RexFk8s1U+cBiAa3C0+nBzpSA/NEbd5GDZwQ"
    "2/0iHr9wzdQ2b5rsUYVKqlOzDqy6PHWt6d4a7kkaMBptJ2c85XbEWZz/qfU905tR8U1sSAMJ3VAsrPXWKK838q14RJyzVsaq"
    "RaeOrTJfWJ4inznRwWTlx1rRkEsSjtHCQS3027CtdmHiKOAm/Uybp7HBDZUyqEOzKUPiOvA4hbg+6fbI+b12n+dafh7v+AHn"
    "dnuX9/txvdv4XPUDRynnfjliUuT5e1p5oyzzGSaN+SZnL6bbSLWRPeWZ4+aqndrOk2iZlZ8E1Qj1ijw2523h1Nucuw7OF4vR"
    "IYSN1fb50gDRGO7XqLLiwyR/gA3CZR5D5J9J9+ByWgHwf1oMa8caqRmypYbwHnlXRQjCgBKV3sjhEcT/UxokinAaM3716lkQ"
    "E6dMKJv3Z7KqgLJYPA+zSrFUrJ0Kxt26Of/PWJOL+f0xxTCYcTsd0VTrt8Fh+WouDknVwxjb7XnxPvuy6KRDxRkW08nZajjM"
    "rV4WqH5/nXJkaNkbRwvI5V+775waQr1vb84auhksfRjWh83r7Tg+rAocovlSDmdcxwlGsohHcj2Ud47qbR6DYl6O3IuPvFzl"
    "uULsT24jmDd9UnqX69Ou/kHpAN6kgqLTuGYt1N4tih7E5EOGlxS5eLIa5rl+25uUVqbg6I9dbbk91MCYBCiwGQRKPrDl0uvm"
    "e3fSaYoJsCEoDnQCwHLeZ5y0W0dR/TM8cR1zQg6c9cCZTBL6gjRYbvKTq/RU47Vh4Bp2XtEZ4UxtYNuTwAwXC26Dr5W2iej7"
    "ugbfXQwVpI1yiiY3BXxwPxyb6G5WeYfge/sYItkajPbP4yESL7Uqog6Tz8Oick+RQI3oK6OoL4fqmC6FmcNha/PJ1ap0w6vr"
    "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"
)

LM_POOL: dict = {}
LM_READY = False
try:
    import base64 as _b64
    import io as _io
    import json as _json
    import math as _math
    import os as _os
    import re as _re
    import threading as _threading
    import urllib.request as _urlreq
    import zlib as _zlib

    from PIL import Image as _Image
    from PIL import ImageOps as _ImageOps

    LM_POOL = _json.loads(_zlib.decompress(_b64.b64decode(LM_POOL_B64)))
    for _pid in list(LM_POOL):
        LM_POOL[_pid] = [
            [(int(p[0], 16), int(p[1], 16), tuple(p[2]), tuple(p[3])) for p in img]
            for img in LM_POOL[_pid]
        ]

    # card data for every pool landmark — multilingual names from the dataset
    LM_INFO = {
        "konark-sun-temple": {
                "name": "Konark Sun Temple",
                "name_hi": "कोणार्क सूर्य मंदिर",
                "name_or": "କୋଣାର୍କ ସୂର୍ଯ୍ୟ ମନ୍ଦିର",
                "city": "Konark, Puri district",
                "description": "UNESCO World Heritage 13th-century sun chariot of King Narasimhadeva I — 24 carved wheels, 7 stone horses, and the famous magnetic lore. Sunrise light on the wheels is unreal.",
                "best_time": "Oct – Feb, early morning"
        },
        "jagannath-temple-puri": {
                "name": "Shree Jagannath Temple",
                "name_hi": "श्री जगन्नाथ मंदिर",
                "name_or": "ଶ୍ରୀ ଜଗନ୍ନାଥ ମନ୍ଦିର",
                "city": "Puri",
                "description": "One of the Char Dham and home to Lord Jagannath, Balabhadra and Subhadra. The 214 ft Neelachakra on the shikhara and the annual Rath Yatra draw millions.",
                "best_time": "Early morning aarti"
        },
        "lingaraj-temple": {
                "name": "Lingaraj Temple",
                "name_hi": "लिंगराज मंदिर",
                "name_or": "ଲିଙ୍ଗରାଜ ମନ୍ଦିର",
                "city": "Bhubaneswar",
                "description": "The crown of Bhubaneswar's 'Temple City' — an 11th-century Kalinga masterpiece with a 180 ft vimana, surrounded by 50+ shrines around Bindu Sagar lake.",
                "best_time": "Feb – Mar (Shivaratri)"
        },
        "chilika-barkul": {
                "name": "Chilika Lake (Barkul)",
                "name_hi": "चिल्का झील (बरकुल)",
                "name_or": "ଚିଲିକା ହ୍ରଦ (ବରକୁଲ)",
                "city": "Khordha",
                "description": "Asia's largest brackish lagoon — 1,100 sq km of islands, Irrawaddy dolphins at Satapada, and a million wintering birds at Nalabana bird sanctuary.",
                "best_time": "Nov – Feb (migratory birds + dolphins)"
        },
        "udayagiri-caves": {
                "name": "Udayagiri & Khandagiri Caves",
                "name_hi": "उदयगिरि और खंडगिरि गुफाएँ",
                "name_or": "ଉଦୟଗିରି ଓ ଖଣ୍ଡଗିରି ଗୁମ୍ଫା",
                "city": "Bhubaneswar",
                "description": "2nd-century BCE Jain rock-cut retreats of King Kharavela — 33 caves with carved friezes of dancing girls, elephants and the famous Hathi Gumpha inscription.",
                "best_time": "Nov – Feb"
        },
        "dhauli-shanti-stupa": {
                "name": "Dhauli Shanti Stupa",
                "name_hi": "धौली शांति स्तूप",
                "name_or": "ଧୌଳି ଶାନ୍ତି ସ୍ତୂପ",
                "city": "Bhubaneswar",
                "description": "White peace pagoda on the banks of the Daya where Emperor Ashoka embraced Buddhism after the Kalinga war. Rock edicts still bear his message of dharma.",
                "best_time": "Sunset"
        },
        "puri-beach": {
                "name": "Puri Beach",
                "name_hi": "पुरी बीच",
                "name_or": "ପୁରୀ ବେଳାଭୂମି",
                "city": "Puri",
                "description": "Golden sands where pilgrims take a holy dip before darshan. Watch fishermen haul in the morning catch, sand-art sculptures, and a famous sunrise horizon.",
                "best_time": "Sunrise; Nov – Feb"
        },
        "chandrabhaga-beach": {
                "name": "Chandrabhaga Beach",
                "name_hi": "चंद्रभागा बीच",
                "name_or": "ଚନ୍ଦ୍ରଭାଗା ବେଳାଭୂମି",
                "city": "Konark",
                "description": "Blue-flag certified beach 3 km from Konark temple — clean sands, casuarina groves and the most reliable sunrise point on the Odisha coast.",
                "best_time": "Sunrise (Magha Saptami)"
        },
        "nandankanan": {
                "name": "Nandankanan Zoological Park",
                "name_hi": "नंदनकानन चिड़ियाघर",
                "name_or": "ନନ୍ଦନକାନନ ଜୀବ ଉଦ୍ୟାନ",
                "city": "Bhubaneswar",
                "description": "Zoo + botanical garden inside a forest — white tigers (born here first in the world), lion and bear safaris, and a lake-side boating loop.",
                "best_time": "Oct – Mar, weekdays"
        },
        "similipal": {
                "name": "Similipal National Park",
                "name_hi": "सिमिलिपाल राष्ट्रीय उद्यान",
                "name_or": "ସିମିଲିପାଲ ଜାତୀୟ ଉଦ୍ୟାନ",
                "city": "Mayurbhanj",
                "description": "2,750 sq km tiger reserve of sal forests, waterfalls (Barehipani, Joranda) and 55+ tribal villages. Melanistic tigers roam these hills.",
                "best_time": "Nov – Jun (core closed monsoon)"
        },
        "hirakud-dam": {
                "name": "Hirakud Dam",
                "name_hi": "हीराकुंड बांध",
                "name_or": "ହୀରାକୁଦ ବାନ୍ଧ",
                "city": "Sambalpur",
                "description": "One of the world's longest earthen dams (25.8 km) across the Mahanadi — sunrise from Gandhi Minar and sunset from Nehru Minar frame the vast reservoir.",
                "best_time": "Aug – Feb"
        },
        "daringbadi": {
                "name": "Daringbadi — Kashmir of Odisha",
                "name_hi": "दारिंगबाड़ी — ओडिशा का कश्मीर",
                "name_or": "ଦାରିଙ୍ଗବାଡ଼ି — ଓଡ଼ିଶାର କାଶ୍ମୀର",
                "city": "Kandhamal",
                "description": "Hill station at 3,000 ft with pine forests, coffee gardens, and Odisha's occasional sub-zero winter nights. Doluri river and Hill View Park are short hops.",
                "best_time": "Dec – Jan (record frosts), monsoon"
        },
        "bhitarkanika": {
                "name": "Bhitarkanika Mangroves",
                "name_hi": "भितरकनिका मैंग्रोव",
                "name_or": "ଭିତରକନିକା ମାନ୍ଗ୍ରୋଭ",
                "city": "Kendrapara",
                "description": "India's second-largest mangrove ecosystem — giant saltwater crocodiles (some 20+ ft), kingfishers, and a heronry of tens of thousands of birds.",
                "best_time": "Dec – Feb"
        },
        "kapilash": {
                "name": "Kapilash Temple",
                "name_hi": "कपिलाश मंदिर",
                "name_or": "କପିଳାଶ ମନ୍ଦିର",
                "city": "Dhenkanal",
                "description": "Shiva temple perched at 2,239 ft on a elephant-corridor hill — 1,352 steps or a winding ghat road, with panoramic views over Dhenkanal.",
                "best_time": "Oct – Feb"
        },
        "mukteswar-temple": {
                "name": "Mukteswar Temple",
                "name_hi": "मुक्तेश्वर मंदिर",
                "name_or": "ମୁକ୍ତେଶ୍ୱର ମନ୍ଦିର",
                "city": "Bhubaneswar",
                "description": "A 10th-century gem of Kalinga architecture, famous for its exquisitely carved torana archway — often called a miniature Lingaraj.",
                "best_time": "Oct – Feb"
        },
        "rajarani-temple": {
                "name": "Rajarani Temple",
                "name_hi": "राजरानी मंदिर",
                "name_or": "ରାଜାରାଣୀ ମନ୍ଦିର",
                "city": "Bhubaneswar",
                "description": "An 11th-century sandstone temple known for its graceful sculpted figures around the jagamohana — no presiding deity, hence the name.",
                "best_time": "Oct – Feb"
        }
}

    def _lm_dhash(img) -> int:
        small = img.resize((9, 8)).convert("L")
        px = list(small.getdata())
        bits = 0
        for row in range(8):
            for col in range(8):
                bits <<= 1
                if px[row * 9 + col] > px[row * 9 + col + 1]:
                    bits |= 1
        return bits

    def _lm_phash(img) -> int:
        small = img.convert("L").resize((32, 32))
        px = list(small.getdata())
        N = 32

        def dct1d(vec):
            out = []
            for k in range(N):
                s = 0.0
                for n, v in enumerate(vec):
                    s += v * _math.cos(_math.pi * (2 * n + 1) * k / (2 * N))
                out.append(s * (_math.sqrt(1 / N) if k == 0 else _math.sqrt(2 / N)))
            return out

        rows = [dct1d(px[r * N:(r + 1) * N]) for r in range(N)]
        cols = [dct1d([rows[r][c] for r in range(N)]) for c in range(N)]
        block = [cols[c][r] for r in range(8) for c in range(8)]
        avg = (sum(block) - block[0]) / 63.0
        bits = 0
        for v in block:
            bits <<= 1
            if v > avg:
                bits |= 1
        return bits

    def _lm_colours(img):
        return tuple(ch for px in img.resize((8, 8)).convert("RGB").getdata() for ch in px)

    def _lm_gray(img):
        return tuple(img.resize((4, 4)).convert("L").getdata())

    def _lm_center(img):
        w, h = img.size
        dw, dh = int(w * 0.85), int(h * 0.85)
        return img.crop(((w - dw) // 2, (h - dh) // 2, (w + dw) // 2, (h + dh) // 2))

    def _lm_feats(img):
        return [
            (_lm_dhash(im), _lm_phash(im), _lm_colours(im), _lm_gray(im))
            for im in (img, _lm_center(img))
        ]

    def _lm_hamming(a: int, b: int) -> int:
        return bin(a ^ b).count("1")

    # weights measured against all pool pairs — no feature mix can separate
    # "same monument, different photo" from "different monument", so the
    # threshold only trusts close matches (see README section 9)
    _LM_W = (0.45, 0.25, 0.15, 0.15)

    def _lm_score(fa, fb) -> float:
        return (
            _LM_W[0] * _lm_hamming(fa[0], fb[0]) / 64
            + _LM_W[1] * _lm_hamming(fa[1], fb[1]) / 64
            + _LM_W[2] * (sum((x - y) ** 2 for x, y in zip(fa[2], fb[2])) / len(fa[2])) ** 0.5 / 255
            + _LM_W[3] * (sum((x - y) ** 2 for x, y in zip(fa[3], fb[3])) / len(fa[3])) ** 0.5 / 255
        )

    def _lm_match(feats_list):
        best_id, best = None, 1.0
        for pid, imgs in LM_POOL.items():
            for img in imgs:
                sc = min(_lm_score(u, r) for u in feats_list for r in img)
                if sc < best:
                    best_id, best = pid, sc
        return best_id, best

    def _lm_vision(data_url: str, lang: str):
        """Optional vision-API path — returns parsed JSON or None (not set)."""
        api_key = _os.environ.get("VISION_API_KEY", "").strip()
        if not api_key:
            return None
        base = _os.environ.get(
            "VISION_BASE_URL", "https://api.openai.com/v1"
        ).strip().rstrip("/")
        model = _os.environ.get("VISION_MODEL", "gpt-4o-mini").strip()
        lang_note = (
            "Write EVERY value (name, city, description, best_time) in the Odia "
            "language, using Odia script. Do not leave any value in English."
            if lang.startswith("or")
            else
            "Write EVERY value (name, city, description, best_time) in the Hindi "
            "language, using Devanagari script. Do not leave any value in English."
            if lang.startswith("hi")
            else
            "Write every value in English."
        )
        body = _json.dumps({
            "model": model,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text":
                    "Identify this landmark. If it is in Odisha, India, name it "
                    "confidently. Respond ONLY with compact JSON: "
                    '{"found": true/false, "name": "...", "city": "...", '
                    '"description": "2-3 sentence tourist description", '
                    '"best_time": "..."} . ' + lang_note},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]}],
        }).encode()
        req = _urlreq.Request(
            base + "/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        )
        with _urlreq.urlopen(req, timeout=60) as resp:
            reply = _json.loads(resp.read().decode())
        raw = (reply.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        m = _re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return None
        parsed = _json.loads(m.group(0))
        return parsed if isinstance(parsed, dict) else None

    LM_READY = True
    print(
        f"[landmark] ready — photo-match pool: {len(LM_POOL)} landmarks, "
        f"{sum(len(i) for i in LM_POOL.values())} photos; "
        f"vision API: {'on' if _os.environ.get('VISION_API_KEY') else 'off (set VISION_API_KEY to enable)'}"
    )
except Exception as _lm_exc:  # noqa: BLE001 — report, don't crash
    print(
        f"[landmark] disabled: {_lm_exc}\n"
        "       (enable it with:  pip install pillow)"
    )

# measured: pool cross-place scores top out at 0.383 — 0.20 is a safe
# confident-match threshold (exact/re-encoded pool photos score far below it)
LM_MATCH = 0.20

_IMG_KEYS = ("imageBase64", "image_base64", "image", "base64", "dataUrl", "data_url", "photo")


def _lm_pick(payload: dict, *keys: str) -> str:
    for k in keys:
        v = payload.get(k)
        if v:
            return str(v)
    return ""


@router.get("")
@router.get("/")
def landmark_info():
    return {
        "router": "landmark",
        "ready": LM_READY,
        "mode": (
            ("vision+photo-match" if _os.environ.get("VISION_API_KEY") else "photo-match")
            if LM_READY
            else "disabled"
        ),
        "pool_landmarks": len(LM_POOL),
        "pool_photos": sum(len(i) for i in LM_POOL.values()),
    }


@router.post("")
@router.post("/")
@router.post("/identify")
@router.post("/scan")
def identify_landmark(payload: Optional[dict] = Body(default=None)):
    if not LM_READY:
        return {"found": False, "error": "landmark_unavailable"}

    body = payload or {}
    data_url = _lm_pick(body, *_IMG_KEYS)
    if not data_url:
        return {"found": False, "error": "landmark_bad_image"}
    lang = _lm_pick(body, "lang", "language") or "en"

    # 1) vision API — full recognition when a key is configured
    try:
        vlm = _lm_vision(data_url, lang)
    except Exception:
        vlm = None
    if vlm is not None:
        out = {"found": bool(vlm.get("found"))}
        for k in ("name", "city", "description", "best_time"):
            if vlm.get(k):
                out[k] = str(vlm[k])
        return out

    # 2) offline photo-match against the embedded pool
    b64part = data_url.split(",", 1)[1] if "," in data_url[:64] else data_url
    try:
        img = _ImageOps.exif_transpose(
            _Image.open(_io.BytesIO(_b64.b64decode(b64part)))
        ).convert("RGB")
    except Exception:
        return {"found": False, "error": "landmark_bad_image"}

    pid, score = _lm_match(_lm_feats(img))
    if pid is None or score > LM_MATCH:
        return {"found": False}
    info = LM_INFO.get(pid) or {}
    name_key = (
        "name_hi" if lang.startswith("hi")
        else "name_or" if lang.startswith("or")
        else "name"
    )
    return {
        "found": True,
        "name": info.get(name_key) or info.get("name", pid.replace("-", " ").title()),
        "city": info.get("city", ""),
        "description": info.get("description", ""),
        "best_time": info.get("best_time", ""),
    }
