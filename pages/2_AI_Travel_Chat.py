"""AI Travel Chat — text & voice in, text & audio out. Grounded in app data."""
import streamlit as st

from services import chatbot_service, gemini_service
from services.stt_service import transcribe
from services.tts_service import detect_lang, synthesize
from utils.i18n import t, language_picker, content_lang


ss = st.session_state
ss.setdefault("chat_history", [])
ss.setdefault("tts_enabled", True)
ss.setdefault("tts_played", set())


def render_audio(text: str) -> None:
    """Audio player attached to the message, honest per-language notes."""
    lang = detect_lang(text, content_lang())
    audio = synthesize(text, lang)
    if audio:
        st.audio(audio, format="audio/mp3")
    elif lang == "or":
        st.caption("🎙️ Odia voice isn't available yet (no TTS engine currently "
                   "offers Odia) — but Odia text replies above are fully supported. "
                   "*(Planned: Bhashini / AI4Bharat Indic TTS)*")
    else:
        st.caption("🔇 Audio temporarily unavailable — try again in a moment.")


st.title(t("chat_title"))
st.caption(t("chat_caption"))

ctl = st.columns([1, 2])
if ctl[0].button(t("clear_chat"), use_container_width=True):
    ss["chat_history"] = []
    ss["tts_played"] = set()
    st.rerun()
ss["tts_enabled"] = ctl[1].toggle(t("audio_replies"), value=ss["tts_enabled"])

if not gemini_service.is_configured():
    st.warning(gemini_service.config_error() or "Gemini unavailable.")

# ---- voice input ----
with st.expander(t("voice_expander"), expanded=False):
    mic = st.audio_input(t("record_hint"), key="mic")
    if mic and st.button(t("send_voice"), type="primary",
                         use_container_width=True):
        with st.spinner("🎧 Listening…"):
            heard = transcribe(mic.getvalue())
        if heard:
            ss["pending"] = heard
            try:
                ss["mic"] = None          # clear the recording
            except Exception:
                pass
            st.rerun()
        else:
            st.warning(t("not_heard"))

# ---- existing history ----
for i, msg in enumerate(ss["chat_history"]):
    with st.chat_message(msg["role"],
                         avatar="🙋" if msg["role"] == "user" else "🤖"):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg["content"]:
            if i in ss["tts_played"]:
                render_audio(msg["content"])
            elif st.button(t("listen"), key=f"ttsbtn_{i}"):
                ss["tts_played"].add(i)
                st.rerun()

# ---- suggestion chips (translated; the chip text IS the sent prompt) ----
if not ss["chat_history"]:
    st.markdown(f"**{t('try_these')}**")
    rows = [st.columns(2), st.columns(2)]
    for i in range(4):
        if rows[i // 2][i % 2].button(t(f"sug_{i}"), key=f"sug_{i}",
                                      use_container_width=True):
            ss["pending"] = t(f"sug_{i}")
            st.rerun()

# ---- input + generation (chat_input ALWAYS mounted every run) ----
chat_value = st.chat_input(t("chat_input_ph"))
user_msg = ss.pop("pending", None) or chat_value

if user_msg:
    ss["chat_history"].append({"role": "user", "content": user_msg})
    with st.chat_message("user", avatar="🙋"):
        st.write(user_msg)

    with st.chat_message("assistant", avatar="🤖"):
        if not gemini_service.is_configured():
            reply = ("⚠️ Gemini is not configured. Add GEMINI_API_KEY to .env, "
                     "then restart Streamlit.")
            st.error(reply)
        else:
            with st.spinner("UtkalaYatri is thinking…"):
                reply = chatbot_service.get_reply(ss["chat_history"],
                                                  content_lang())
            if reply:
                st.write(reply)
            else:
                reply = ("⚠️ The AI service didn't respond just now "
                         "(it may be busy) — please try again in a moment.")
                st.warning(reply)
        if reply and ss["tts_enabled"]:
            render_audio(reply)

    ss["chat_history"].append({"role": "assistant", "content": reply})