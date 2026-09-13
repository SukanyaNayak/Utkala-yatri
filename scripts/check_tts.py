# scripts/check_tts.py
"""What TTS voices actually exist for our languages?"""
import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    print(f"edge-tts reachable — {len(voices)} voices total\n")
    for v in voices:
        loc = str(v.get("Locale", ""))
        if loc.lower().startswith(("or-", "hi-in", "en-in")):
            print(f"  {loc:<8} {v.get('ShortName')} ({v.get('Gender')})")

    odia = [v for v in voices if str(v.get("Locale", "")).lower().startswith("or-")]
    print("\n— Odia synthesis test —")
    if not odia:
        print("❌ NO Odia voice exists in edge-tts (verdict: text-first for Odia)")
        return
    for v in odia:
        name = v["ShortName"]
        try:
            stream = edge_tts.Communicate("ନମସ୍କାର! ଓଡ଼ିଶା ଆପଣଙ୍କୁ ସ୍ୱାଗତ କରୁଛି।", name)
            audio = b"".join([c["data"] async for c in stream.stream()
                              if c["type"] == "audio"])
            print(f"✅ {name}: {len(audio)} bytes of audio generated")
        except Exception as e:
            print(f"❌ {name}: {e}")

asyncio.run(main())