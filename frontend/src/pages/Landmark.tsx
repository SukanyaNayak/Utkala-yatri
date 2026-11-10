// src/pages/Landmark.tsx  (v3 — drop-in for frontend/src/pages/Landmark.tsx)
//
// v3 CHANGES (page renders fine, "Identify landmark" failed):
//   • The photo is downscaled to max 1024 px (JPEG 85%) in the browser
//     before it is sent — phone photos are 3-8 MB of base64 and made the
//     request slow; the backend only needs a small image.
//   • The error box now says WHAT failed instead of a generic "service busy":
//       - "network"      → the backend isn't running / the /api proxy is down
//       - landmark_unavailable → backend up but Pillow missing (pip install pillow)
//       - landmark_bad_image   → the chosen file isn't a photo
//   • The "not recognised" box explains the two recognition paths honestly:
//     photo-match (offline, works with the app's own gallery / popular stock
//     photos of the 16 pool landmarks) and the optional vision API (any
//     photo — set VISION_API_KEY on the backend, see README section 8).
//
// i18n v2 behaviour kept: imports the SAME PageHero your Gems page uses,
// every t() call carries an English defaultValue so a missing key never
// prints raw key text. Logic: POST /api/landmark with { imageBase64, lang }.

import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import PageHero from "../components/PageHero";

interface LandmarkResult {
  found?: boolean;
  name?: string;
  city?: string;
  description?: string;
  best_time?: string;
  error?: string;
}

async function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onloadend = () => resolve(String(r.result));
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

/** Downscale to max 1024 px JPEG (~150 KB instead of 3-8 MB base64). */
async function shrinkDataUrl(dataUrl: string): Promise<string> {
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = reject;
      el.src = dataUrl;
    });
    const max = 1024;
    const scale = Math.min(1, max / Math.max(img.width, img.height));
    if (scale === 1) return dataUrl;
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(img.width * scale));
    canvas.height = Math.max(1, Math.round(img.height * scale));
    canvas.getContext("2d")?.drawImage(img, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.85);
  } catch {
    return dataUrl; // canvas unavailable (very old browser) — send as-is
  }
}

export default function Landmark() {
  const { t, i18n } = useTranslation();
  const [preview, setPreview] = useState<string | null>(null);
  const [base64, setBase64] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<LandmarkResult | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function pick(file: File | undefined) {
    if (!file) return;
    setResult(null);
    const dataUrl = await fileToDataUrl(file);
    const small = await shrinkDataUrl(dataUrl);
    setPreview(small);
    setBase64(small);
  }

  async function scan() {
    if (!base64 || busy) return;
    setBusy(true);
    try {
      const res = await fetch("/api/landmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imageBase64: base64, lang: i18n.language }),
      });
      // a non-JSON reply (proxy returning HTML, 502 page …) must not throw
      const data = (await res.json().catch(() => null)) as LandmarkResult | null;
      setResult(data ?? { found: false, error: "network" });
    } catch {
      setResult({ found: false, error: "network" });
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setPreview(null);
    setBase64(null);
    setResult(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  function errorMessage(error: string): string {
    if (error === "network") {
      return t("lm_err_backend", {
        defaultValue:
          "Can't reach the backend. Start it (start-dev.ps1, or uvicorn on port 8000) and try again.",
      });
    }
    if (error === "landmark_unavailable") {
      return t("lm_err_pillow", {
        defaultValue:
          "Recognition isn't enabled on the backend yet — run  pip install pillow  in the backend folder and restart it.",
      });
    }
    if (error === "landmark_bad_image") {
      return t("lm_err_photo", {
        defaultValue: "That file doesn't look like a photo — try a JPG or PNG.",
      });
    }
    return t("recognize_failed", {
      defaultValue: "Recognition failed — try again.",
    });
  }

  return (
    <div>
      {/* ── hero banner — same component + props as Gems/Festivals/Hotels ── */}
      <PageHero
        title={t("landmark_title", { defaultValue: "📷 Landmark Scan" })}
        tagline={t("hero_tag_snap", { defaultValue: "SNAP • SCAN • EXPLORE" })}
        desc={t("landmark_caption", {
          defaultValue:
            "Snap or upload a photo of any monument — recognition is constrained to our verified Odisha place database.",
        })}
        quote={t("hero_story", { defaultValue: "Every Monument Has a Story" })}
      >
        <div className="flex flex-col gap-2 rounded-[2rem] bg-white p-2 pl-5 shadow-[0_10px_30px_rgba(0,0,0,0.28)] sm:flex-row sm:items-center sm:rounded-full">
          <div className="flex h-11 min-w-0 flex-1 items-center gap-2.5">
            <span aria-hidden>📷</span>
            <span className="truncate text-sm font-semibold text-[#3E2A1B]">
              {t("upload_photo", { defaultValue: "Upload a photo" })}
            </span>
          </div>
          <button
            onClick={() => fileRef.current?.click()}
            className="flex h-11 shrink-0 items-center justify-center gap-2 rounded-full bg-forest px-7 text-sm font-bold text-white shadow-sm transition-colors hover:bg-[#2C4634] active:scale-95"
          >
            {t("hero_scan_cta", { defaultValue: "Scan a landmark" })} <span aria-hidden>→</span>
          </button>
        </div>
      </PageHero>

      <div className="mt-6 grid gap-5 lg:grid-cols-2 items-start">
        {/* upload zone */}
        <div
          className="bg-white border-2 border-dashed border-[#EAD9C6] rounded-2xl p-6 text-center cursor-pointer hover:border-[#D35400]/50 transition-colors"
          onClick={() => fileRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && fileRef.current?.click()}
        >
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => pick(e.target.files?.[0])}
          />
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt={t("lm_preview_alt", { defaultValue: "Selected photo preview" })} className="mx-auto max-h-72 rounded-xl shadow" />
          ) : (
            <div className="py-10">
              <span className="text-5xl" aria-hidden>
                📸
              </span>
              <p className="mt-3 text-sm font-semibold text-[#7A5C42]">{t("lm_upload", { defaultValue: "Snap or upload a photo" })}</p>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="flex gap-3">
            <button
              onClick={scan}
              disabled={!base64 || busy}
              className="flex-1 h-12 rounded-full bg-[#D35400] text-white font-bold shadow-sm hover:bg-[#BF4E00] disabled:opacity-40 transition-colors active:scale-[0.98]"
            >
              {busy ? t("analyzing", { defaultValue: "Analyzing photo…" }) : t("identify_btn", { defaultValue: "🔍 Identify landmark" })}
            </button>
            {preview ? (
              <button
                onClick={reset}
                className="h-12 px-5 rounded-full bg-white border border-[#EAD9C6] font-bold text-[#7A5C42] hover:bg-[#FFF7EF] transition-colors"
              >
                {t("landmark_reset", { defaultValue: "Scan another" })}
              </button>
            ) : null}
          </div>

          {result ? (
            result.error ? (
              <div className="bg-[#FDEBD0] border border-[#E9C46A]/60 rounded-2xl p-4 text-sm text-[#7A4A10]">
                {errorMessage(result.error)}
              </div>
            ) : result.found ? (
              <div className="bg-white border border-[#F0E2D0] rounded-2xl p-5 shadow-sm">
                <h3 className="text-xl font-bold text-[#4A2A12]">🏛️ {result.name}</h3>
                <p className="mt-0.5 text-sm text-[#B08968]">📍 {result.city}</p>
                <p className="mt-3 text-sm text-[#6B4B30] leading-relaxed">{result.description}</p>
                {result.best_time ? (
                  <p className="mt-3 rounded-xl bg-[#FFF7EF] border border-[#F0E2D0] p-3 text-sm text-[#7A5C42]">
                    ⏰ <span className="font-bold">{t("best_time", { defaultValue: "Best time to visit" })}:</span> {result.best_time}
                  </p>
                ) : null}
              </div>
            ) : (
              <div className="bg-[#FDEBD0] border border-[#E9C46A]/60 rounded-2xl p-4 text-sm text-[#7A4A10]">
                <p className="font-bold">
                  {t("no_match", {
                    defaultValue:
                      "Couldn't recognise this photo — it isn't a close match to our verified Odisha landmark photos.",
                  })}
                </p>
                <p className="mt-1 leading-relaxed">
                  {t("no_match_hint", {
                    defaultValue:
                      "Photo-match works with the app's own gallery photos and the popular stock shots they came from. To recognise ANY photo of any monument, set VISION_API_KEY on the backend (README section 8).",
                  })}
                </p>
              </div>
            )
          ) : null}

          {!result ? (
            <p className="text-xs text-[#B08968] leading-relaxed">ℹ️ {t("demo_tip", { defaultValue: "Add a photo to begin — recognition runs against our verified Odisha place database." })}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
