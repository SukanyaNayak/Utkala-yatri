"""UI label translations (en/hi/or) + sidebar language picker.

Usage in any page:
    from utils.i18n import t, language_picker
    language_picker()                     # renders sidebar selector
    st.title(t("explore_title"))
"""
import streamlit as st

T = {
    "en": {
        "lang": "Language",
        "app_tagline": "Explore Odisha Smarter with AI",
        "explore_title": "🗺️ Explore Places",
        "chat_title": "🤖 AI Travel Chat",
        "planner_title": "📅 AI Trip Planner",
        "festivals_title": "🎪 Festivals of Odisha",
        "hotels_title": "🏨 Nearby Hotels",
        "emergency_title": "🚨 Emergency Services",
        "gems_title": "💎 Hidden Gems of Odisha",
        "landmark_title": "📷 Landmark Scan",
        "search": "Search",
        "category": "Category",
        "results": "result(s)",
        "view_details": "View details",
        "back": "← Back to list",
        "ai_insights": "✨ AI Insights",
        "best_time": "Best time to visit",
        "insider_tip": "Local tip",
        "nearby": "Nearby places",
        "listen": "🔊 Listen",
        "clear_chat": "🗑️ Clear chat",
        "filter": "Filter",
        "hotels_near": "Hotels near",
        "radius": "Search radius (km)",
        "facilities_near": "Facilities near you",
        "starting_from": "🏁 Starting from",
        "destinations": "📍 Destinations (2–6 works best)",
        "trip_days": "Days",
        "travel_mode": "Travel mode",
        "trip_cost": "💰 Estimated trip cost",
        "total": "Total",
    },
    "hi": {
        "lang": "भाषा",
        "app_tagline": "एआई के साथ ओडिशा को स्मार्ट तरीके से जानें",
        "explore_title": "🗺️ स्थान खोजें",
        "chat_title": "🤖 एआई यात्रा चैट",
        "planner_title": "📅 एआई यात्रा योजनाकार",
        "festivals_title": "🎪 ओडिशा के त्योहार",
        "hotels_title": "🏨 नज़दीकी होटल",
        "emergency_title": "🚨 आपातकालीन सेवाएं",
        "gems_title": "💎 ओडिशा के छिपे हुए रत्न",
        "landmark_title": "📷 लैंडमार्क स्कैन",
        "search": "खोजें",
        "category": "श्रेणी",
        "results": "परिणाम",
        "view_details": "विवरण देखें",
        "back": "← सूची पर वापस",
        "ai_insights": "✨ एआई जानकारी",
        "best_time": "घूमने का सर्वोत्तम समय",
        "insider_tip": "स्थानीय सुझाव",
        "nearby": "नज़दीकी स्थान",
        "listen": "🔊 सुनें",
        "clear_chat": "🗑️ चैट साफ़ करें",
        "filter": "फ़िल्टर",
        "hotels_near": "इनके पास होटल",
        "radius": "खोज त्रिज्या (किमी)",
        "facilities_near": "आपके नज़दीक सुविधाएं",
        "starting_from": "🏁 यहाँ से शुरू",
        "destinations": "📍 गंतव्य (2–6 सबसे अच्छे)",
        "trip_days": "दिन",
        "travel_mode": "यात्रा का साधन",
        "trip_cost": "💰 अनुमानित यात्रा लागत",
        "total": "कुल",
    },
    "or": {
        "lang": "ଭାଷା",
        "app_tagline": "କୃତ୍ରିମ ବୁଦ୍ଧି ସହ ଓଡ଼ିଶାକୁ ଅଧିକ ଚତୁରତାର ସହିତ ଅନ୍ୱେଷଣ କରନ୍ତୁ",
        "explore_title": "🗺️ ସ୍ଥାନ ଅନ୍ୱେଷଣ",
        "chat_title": "🤖 ଏଆଇ ଯାତ୍ରା ଚାଟ୍",
        "planner_title": "📅 ଏଆଇ ଯାତ୍ରା ଯୋଜନା",
        "festivals_title": "🎪 ଓଡ଼ିଶାର ପର୍ବପର୍ବାଣି",
        "hotels_title": "🏨 ନିକଟତମ ହୋଟଲ",
        "emergency_title": "🚨 ଆପାତକାଳୀନ ସେବା",
        "gems_title": "💎 ଓଡ଼ିଶାର ଲୁଚା ରତ୍ନ",
        "landmark_title": "📷 ଲ୍ୟାଣ୍ଡମାର୍କ ସ୍କାନ୍",
        "search": "ଖୋଜନ୍ତୁ",
        "category": "ଶ୍ରେଣୀ",
        "results": "ଫଳାଫଳ",
        "view_details": "ବିବରଣୀ ଦେଖନ୍ତୁ",
        "back": "← ତାଲିକାକୁ ଫେରନ୍ତୁ",
        "ai_insights": "✨ ଏଆଇ ସୂଚନା",
        "best_time": "ପରିଦର୍ଶନ ପାଇଁ ସର୍ବୋତ୍ତମ ସମୟ",
        "insider_tip": "ସ୍ଥାନୀୟ ସୂଚନା",
        "nearby": "ନିକଟବର୍ତ୍ତୀ ସ୍ଥାନ",
        "listen": "🔊 ଶୁଣନ୍ତୁ",
        "clear_chat": "🗑️ ଚାଟ୍ ସଫା କରନ୍ତୁ",
        "filter": "ଫିଲଟର",
        "hotels_near": "ଏହି ସ୍ଥାନ ପାଖରେ ହୋଟଲ",
        "radius": "ଖୋଜା ବ୍ୟାସାର୍ଦ୍ଧ (କିମି)",
        "facilities_near": "ଆପଣଙ୍କ ପାଖରେ ସୁବିଧା",
        "starting_from": "🏁 ଏହି ସ୍ଥାନରୁ ଆରମ୍ଭ",
        "destinations": "📍 ଗନ୍ତବ୍ୟ (୨–୬ ସର୍ବୋତ୍ତମ)",
        "trip_days": "ଦିନ",
        "travel_mode": "ଯାତ୍ରା ମାଧ୍ୟମ",
        "trip_cost": "💰 ଆନ୍ଦାଜିତ ଯାତ୍ରା ଖର୍ଚ୍ଚ",
        "total": "ମୋଟ",
    },
}


def t(key: str) -> str:
    """Translate a UI label for the chosen language (en fallback → key)."""
    lang = st.session_state.get("lang", "en")
    return T.get(lang, T["en"]).get(key) or T["en"].get(key, key)


def language_picker() -> None:
    """Sidebar selector — call once at the top of every page."""
    ss = st.session_state
    ss.setdefault("lang", "en")
    label = {"en": "Language", "hi": "भाषा", "or": "ଭାଷା"}
    choice = st.sidebar.selectbox(
        label[ss["lang"]], ["en", "hi", "or"],
        format_func=lambda k: {"en": "English", "hi": "हिन्दी",
                               "or": "ଓଡ଼ିଆ"}[k],
        key="lang_picker")
    ss["lang"] = choice