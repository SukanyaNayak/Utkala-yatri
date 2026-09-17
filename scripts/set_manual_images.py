"""Hand-pin verified Commons photo URLs to specific places — WITH full reporting.
Every dict entry reports: applied / why-not."""
import json
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "data" / "places.json"

IMAGES = {
    "Mangalajodi Wetlands": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8e/Mangalajodi_on_the_banks_of_the_Chilika_lake.jpg/960px-Mangalajodi_on_the_banks_of_the_Chilika_lake.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Ratnagiri": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2e/Ratnagiri_%2821%29.JPG/960px-Ratnagiri_%2821%29.JPG?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Panchalingeswar Hill View" : "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b0/Pancalingeswara_Temple_Nilagiri.JPG/960px-Pancalingeswara_Temple_Nilagiri.JPG?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Deomali Peak" :"https://thumb.wikimedia.org/wikipedia/commons/thumb/2/23/Deomali_hill_top_Koraput_India.jpg/960px-Deomali_hill_top_Koraput_India.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Hirakud Dam":"https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0d/Hirakud_Dam_Panorama_%28cropped%29.jpg/960px-Hirakud_Dam_Panorama_%28cropped%29.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Tribal Museum Rourkela":"https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a7/Tribal_Museum_Chiang_Mai_DSCN5454a.jpg/960px-Tribal_Museum_Chiang_Mai_DSCN5454a.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
    "Kanika Palace":"https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a7/Rajkanika_Rajabati.jpg/960px-Rajkanika_Rajabati.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail"

}
places = json.loads(FILE.read_text(encoding="utf-8"))
print(f"{len(places)} places loaded, {len(IMAGES)} dict entries to apply\n")

applied = 0
for key, url in IMAGES.items():
    if not url.startswith("http"):
        print(f"❌ '{key}': URL doesn't start with http — paste mangled or "
              f"placeholder left? got: {url[:60]!r}")
        continue
    if "commons.wikimedia.org/wiki/File:" in url:
        print(f"❌ '{key}': that's the Commons FILE PAGE, not the image. "
              f"Fix: replace '/wiki/File:' with '/wiki/Special:FilePath/' "
              f"and add '?width=640'")
        continue
    hits = [p for p in places if key.lower() in p.get("name", "").lower()]
    if not hits:
        print(f"❌ '{key}': no place name contains this — run "
              f"list_missing_images.py and copy the exact name")
        continue
    if len(hits) > 1:
        print(f"⚠️  '{key}': matches {[p['name'] for p in hits]} — using first")
    p = hits[0]
    p["image"] = url
    p["image_source"] = "manual_commons"
    applied += 1
    print(f"✅ '{key}' → {p['name']}")

print(f"\n{applied}/{len(IMAGES)} applied. Now: python scripts/seed_catalog.py")

FILE.write_text(json.dumps(places, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")