"""AI Travel Chat — text & voice in, text & audio out. Grounded in app data."""
import streamlit as st

from services import chatbot_service, gemini_service
from services.stt_service import transcribe
from services.tts_service import detect_lang, synthesize

st.set_page_config(page_title="AI Travel Chat · UtkalaYatri",
                   page_icon="🤖", layout="wide")

ss = st.session_state
ss.setdefault("chat_history", [])
ss.setdefault("chat_lang", "auto")
ss.setdefault("tts_enabled", True)
ss.setdefault("tts_played", set())

SUGGESTIONS = [
    "🎪 Which festivals are happening in the next 2 months?",
    "🗺️ Plan a 3-day trip covering Puri, Konark and Bhubaneswar",
    "🏖️ Which are the best beaches in Odisha, and when should I visit?",
    "🏛️ Tell me about the Konark Sun Temple — and what's nearby?",
]

LANG_LABELS = {"auto": "🌐 Auto", "en": "English", "hi": "हिन्दी", "or": "ଓଡ଼ିଆ"}


def render_audio(text: str, key: str = "") -> None:
    """Audio player attached to the message, with an honest per-language note."""
    lang = detect_lang(text, ss["chat_lang"])
    audio = synthesize(text, lang)
    if audio:
        st.audio(audio, format="audio/mp3")
    elif lang == "or":
        st.caption("🎙️ Odia voice isn't available yet (no TTS engine currently "
                   "offers Odia) — but Odia text replies above are fully supported. "
                   "*(Planned: Bhashini / AI4Bharat Indic TTS)*")
    else:
        st.caption("🔇 Audio temporarily unavailable — try again in a moment.")

st.title("🤖 AI Travel Chat")
st.caption("Your AI guide to Odisha — type or 🎙️ speak your question; toggle 🔊 "
           "to hear the replies.")

ctl = st.columns([1, 1, 2])
ss["chat_lang"] = ctl[0].selectbox(
    "Reply language", list(LANG_LABELS),
    format_func=lambda k: LANG_LABELS[k], label_visibility="collapsed")
if ctl[1].button("🗑️ Clear chat", use_container_width=True):
    ss["chat_history"] = []
    ss["tts_played"] = set()
    st.rerun()
ss["tts_enabled"] = ctl[2].toggle("🔊 Audio replies", value=ss["tts_enabled"])

if not gemini_service.is_configured():
    st.warning(gemini_service.config_error() or "Gemini unavailable.")

# ---- voice input ----
with st.expander("🎙️ Ask by voice", expanded=False):
    mic = st.audio_input("Record your question (keep it under ~30 seconds)",
                         key="mic")
    if mic and st.button("🚀 Send voice question", type="primary",
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
            st.warning("Couldn't hear that clearly — try again or type instead.")

# ---- existing history ----
for i, msg in enumerate(ss["chat_history"]):
    with st.chat_message(msg["role"],
                         avatar="🙋" if msg["role"] == "user" else "🤖"):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg["content"]:
            if i in ss["tts_played"]:
                render_audio(msg["content"], key=f"tts_{i}")
            elif st.button("🔊 Listen", key=f"ttsbtn_{i}"):
                ss["tts_played"].add(i)
                st.rerun()

# ---- suggestion chips ----
if not ss["chat_history"]:
    st.markdown("**Try one of these:**")
    rows = [st.columns(2), st.columns(2)]
    for i, text in enumerate(SUGGESTIONS):
        if rows[i // 2][i % 2].button(text, key=f"sug_{i}",
                                      use_container_width=True):
            ss["pending"] = text
            st.rerun()

# ---- input + generation (input ALWAYS mounted every run) ----
chat_value = st.chat_input("Ask about places, festivals, trip plans…")
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
                                                  ss["chat_lang"])
            if reply:
                st.write(reply)
            else:
                reply = ("⚠️ The AI service didn't respond just now "
                         "(it may be busy) — please try again in a moment.")
                st.warning(reply)
        if reply and ss["tts_enabled"]:
            render_audio(reply, key=f"tts_new_{len(ss['chat_history'])}")

    ss["chat_history"].append({"role": "assistant", "content": reply})
    if reply and ss["tts_enabled"]:
        ss["tts_played"].add(len(ss["chat_history"]) - 1)