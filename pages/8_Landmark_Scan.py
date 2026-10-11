"""Landmark Scan — upload or shoot a photo, UtkalaYatri recognizes the place."""
import streamlit as st

from services import gemini_service, landmark_service, place_service
from utils.i18n import content_lang, t
from services.translate_service import localized_text
ss = st.session_state
ss.setdefault("landmark_result", None)

st.title(t("landmark_title"))
st.caption(t("landmark_caption"))

if not gemini_service.is_configured():
    st.warning(gemini_service.config_error() or "Gemini unavailable.")

up = st.file_uploader(t("upload_photo"), type=["jpg", "jpeg", "png"])
cam = st.camera_input(t("or_camera"))
img = up or cam

# new photo uploaded -> invalidate the previous result
if img is None and ss["landmark_result"] is not None:
    ss["landmark_result"] = None

if img and st.button(t("identify_btn"), type="primary"):
    with st.spinner(t("analyzing")):
        ss["landmark_result"] = landmark_service.identify(
            img.getvalue(), img.type or "image/jpeg")

res = ss["landmark_result"]
if img and res:
    st.image(img, width=420)
    st.caption(f"👁️ {res.get('seen', '')}")
    pid = res.get("matched_place_id")
    place = place_service.get_place(pid) if pid else None
    if place:
        conf = res.get("confidence", "?")
        badge = {"high": "🟢", "medium": "🟡", "low": "🟠"}.get(conf, "⚪")
        st.success(f"{badge} **{place['name']}** — {conf} {t('confidence')}")
       
        if place.get("description"):
            text, was_translated = localized_text(place["description"],
                                                content_lang())
            st.write(text)
            if was_translated:
                st.caption("🌐")
        if place.get("insider_tip"):
            st.info(f"🗝️ {place['insider_tip']}")
        if place.get("best_time"):
            st.info(f"🗓️ {t('best_time')}: **{place['best_time']}**")
        ss["selected_place_id"] = place["place_id"]
        # OUTSIDE any other button's conditional — clickable on every rerun
        if st.button(t("open_details"), type="primary"):
            ss["landmark_result"] = None
            st.switch_page("pages/1_Explore_Places.py")
    else:
        st.warning(f"{t('no_match')} **{res.get('best_guess') or '?'}**")
elif not img:
    st.info(t("demo_tip"))