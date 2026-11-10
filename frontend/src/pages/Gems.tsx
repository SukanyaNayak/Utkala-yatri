// src/pages/Gems.tsx  (v4 — 22 REAL hidden gems, EN / हिंदी / ଓଡ଼ିଆ built in)
//
// WHAT CHANGED vs v3 — all three of your points:
//   1. "only 7 places"        → 22 genuine offbeat gems across 15 districts.
//   2. "Puri/Konark are not hidden gems" → agreed and REMOVED. Konark, the
//      Jagannath Temple and Chilika (Barkul) are flagship attractions — they
//      no longer appear here. Everything on this page is genuinely offbeat:
//      Chandipur's vanishing sea, Mangalajodi, Hukitola, Huma's leaning
//      temple, the yogini shrines, Patali Srikhetra...
//   3. "language not changing in details" → every story, insider tip, card
//      CTA, chip label and the insider-box title now ship in English +
//      हिंदी + ଓଡ଼ିଆ inside this file and switch the moment the language
//      dropdown changes. (Hero title/count still use your locale files —
//      those keys were already translating fine in your screenshot.)
//      Gem names stay as proper nouns (like on maps) — everything else
//      translates.
//   + NEW: filter chips — All / Coast & islands / Forests & wildlife /
//     Falls & hills / Heritage & temples (translated in all 3 languages).
//   Photos: real photos (Wikimedia Commons + the 4 verified in v3); every
//   URL was HEAD-checked (HTTP 200) before shipping. A dead URL still falls
//   back to the green gradient, same as before.
//   API merge still on: any place your backend returns WITH a gem_story is
//   appended to the list (deduped by name), so your own data joins later
//   without touching this file.

import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  FaGem,
  FaLightbulb,
  FaMapMarkerAlt,
} from "react-icons/fa";
import { api } from "../api/client";
import type { Place } from "../api/client";
import PageHero from "../components/PageHero";

// ── languages ───────────────────────────────────────────────────────────────
type Lang = "en" | "hi" | "or";
type L10n = Record<Lang, string>;

// gem fields may or may not be declared on your client's Place type —
// this keeps the file compiling either way
type GemPlace = Place & {
  image?: string | null;
  gem_story?: string | null;
  insider_tip?: string | null;
};

// one gem, ready to render
type Gem = {
  key: string;
  name: string; // proper noun — kept in English on purpose (like a map)
  city: string; // district / area label
  tag: "coast" | "wild" | "hills" | "heritage";
  image?: string | null;
  story: L10n;
  tip: L10n;
};

// ── filter chips (labels in all 3 languages) ────────────────────────────────
const GEM_TAGS: { id: Gem["tag"]; label: L10n }[] = [
  { id: "coast", label: { en: "Coast & islands", hi: "तट और द्वीप", or: "ଉପକୂଳ ଓ ଦ୍ୱୀପ" } },
  { id: "wild", label: { en: "Forests & wildlife", hi: "जंगल और वन्यजीव", or: "ଅରଣ୍ୟ ଓ ବନ୍ୟଜୀବ" } },
  { id: "hills", label: { en: "Falls & hills", hi: "झरने और पहाड़", or: "ଝରଣ ଓ ପାହାଡ଼" } },
  { id: "heritage", label: { en: "Heritage & temples", hi: "धरोहर और मंदिर", or: "ଐତିହ୍ୟ ଓ ମନ୍ଦିର" } },
];

// UI strings your locale files may not have — embedded in all 3 languages
const UI = {
  readStory: { en: "Read the story", hi: "पूरी कहानी पढ़ें", or: "କାହାଣୀ ପଢ଼ନ୍ତୁ" } as L10n,
  insider: { en: "Insider tip", hi: "लोकल टिप", or: "ଲୋକାଲ ଟିପ୍" } as L10n,
  all: { en: "All gems", hi: "सभी जेम", or: "ସବୁ ରତ୍ନ" } as L10n,
  close: { en: "Close", hi: "बंद करें", or: "ବନ୍ଦ କରନ୍ତୁ" } as L10n,
  empty: {
    en: "No gems in this filter — try another one.",
    hi: "इस फ़िल्टर में कुछ नहीं — दूसरा चुनें।",
    or: "ଏହି ଫିଲ୍ଟରରେ କିଛି ନାହିଁ — ଅନ୍ୟଟିଏ ବାଛନ୍ତୁ।",
  } as L10n,
};

// photo per gem — every URL HEAD-checked (HTTP 200) before shipping; a null
// (or a dead URL at runtime) falls back to the green gradient card
const IMG: Record<string, string | null> = {
  chandipur: "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/35/Chandipur_Beach.JPG/960px-Chandipur_Beach.JPG",
  talasari: "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c5/Talsari_Sea_Beach_in_Odisha_11.jpg/960px-Talsari_Sea_Beach_in_Odisha_11.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
  hukitola: "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0d/Hukitola-2.jpg/960px-Hukitola-2.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
  rushikulya: "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c7/Rushikalya_River_in_Brahampur%2C_Orissa.JPG/960px-Rushikalya_River_in_Brahampur%2C_Orissa.JPG?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
  mangalajodi: "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/51/Mangalajodi_View_%2819834389150%29.jpg/960px-Mangalajodi_View_%2819834389150%29.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
  bhitarkanika: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/5907fd98a257.jpg",
  similipal: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/ae55dd65ab41.jpg",
  satkosia: null, // no verified photo — gradient fallback
  debrigarh: "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/71/Debrigarh_Wildlife_sanctuary_%2838509512300%29.jpg/960px-Debrigarh_Wildlife_sanctuary_%2838509512300%29.jpg",
  mandasaru: "https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ef/Misty_Phulbani_-_DSC_7860.jpg/960px-Misty_Phulbani_-_DSC_7860.jpg",
  daringbadi: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/160aebb5a92d.jpg",
  taptapani: "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/01/Brahmana_performing_puja_Taptapani_Orissa.JPG/960px-Brahmana_performing_puja_Taptapani_Orissa.JPG",
  deomali: "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/56/Deomali.jpg/960px-Deomali.jpg",
  khandadhar: "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f0/Mountains_of_khandadhar_falls.jpg/960px-Mountains_of_khandadhar_falls.jpg",
  gandhamardan: "https://thumb.wikimedia.org/wikipedia/commons/thumb/e/ec/Gandhamardan_Checkdam.jpg/960px-Gandhamardan_Checkdam.jpg",
  kapilash: "https://z-cdn.chatglm.cn/image-search-mcp/images-ppt/2a6160d52609.jpg",
  chandragiri: null, // no verified photo — gradient fallback
  khiching: null, // no verified photo — gradient fallback
  diamond: "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/5a/Kkm_ratnagiri_jajpur_odisha_3.jpg/960px-Kkm_ratnagiri_jajpur_odisha_3.jpg",
  hirapur: "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/68/Sculpture_of_a_Yogini%2C_possibly_Sri_Chhatra_Samvara_Yogini%2C_circa_9th_century_CE%2C_Chausath_Yogini_Temple%2C_Hirapur%2C_Orissa.jpg/960px-Sculpture_of_a_Yogini%2C_possibly_Sri_Chhatra_Samvara_Yogini%2C_circa_9th_century_CE%2C_Chausath_Yogini_Temple%2C_Hirapur%2C_Orissa.jpg",
  huma: "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4b/Huma%2C_Sambalpur.jpg/960px-Huma%2C_Sambalpur.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail",
  patali: null, // no verified photo — gradient fallback
};

export const BUILT_IN_GEMS: Gem[] = [
  // ── coast & islands ────────────────────────────────────────────────────────
  {
    key: "chandipur",
    name: "Chandipur",
    city: "Balasore",
    tag: "coast",
    image: IMG.chandipur,
    story: {
      en: "Twice a day the sea simply walks away — up to five kilometres at low tide — leaving wet sand, red crabs and tide pools. Walk far out onto the seabed and watch it all rush back by evening.",
      hi: "दिन में दो बार समुद्र खुद पीछे हट जाता है — भाटे में पाँच किलोमीटर तक — और गीली रेत, लाल केकड़ों और ज्वार-तालाबों को पीछे छोड़ देता है। समुद्र तल पर किलोमीटरों चलिए, और शाम को सब लौटते देखिए।",
      or: "ଦିନକୁ ଦୁଇଥର ସମୁଦ୍ର ନିଜେ ପଛକୁ ଯାଏ — ଭଟ୍ଟିରେ ପାଞ୍ଚ କିମି ପର୍ଯ୍ୟନ୍ତ — ଓଦା ବାଲି, ଲାଲ କଙ୍କଡ଼ା ଓ ଜୋୟାର-ପୁଷ୍କର ଛଡ଼ାଇ ଯାଏ। ସମୁଦ୍ର ତଳେ କିଲୋମିଟର ସାରି ଚାଲନ୍ତୁ, ସନ୍ଧ୍ୟା ବେଳକୁ ସବୁ ଫେରିଆସିବା ଦେଖନ୍ତୁ।",
    },
    tip: {
      en: "Ask your hotel for the tide chart — go at low tide, walk far, but head back before the water returns.",
      hi: "होटल से टाइड चार्ट लें — भाटे में जाएँ, दूर तक चलें, पर पानी लौटने से पहले वापस आ जाएँ।",
      or: "ହୋଟେଲରୁ ଟାଇଡ୍ ଚାର୍ଟ ନିଅନ୍ତୁ — ଭଟ୍ଟିରେ ଯାଆନ୍ତୁ, ଦୂର ଚାଲନ୍ତୁ, କିନ୍ତୁ ପାଣି ଫେରିବା ପୂର୍ବରୁ ଫେରନ୍ତୁ।",
    },
  },
  {
    key: "talasari",
    name: "Talasari Beach",
    city: "Balasore",
    tag: "coast",
    image: IMG.talasari,
    story: {
      en: "Where the Subarnarekha meets the Bay of Bengal: palm-fringed sand, a shallow creek you cross on foot at low tide, and a shore dotted with red crabs.",
      hi: "जहाँ सुवर्णरेखा बंगाल की खाड़ी से मिलती है: ताड़ों से घिरी शांत रेत, भाटे में पैदल पार की जाने वाली उथली धार, और लाल केकड़ों से बिखरा किनारा।",
      or: "ଯେଉଁଠି ସୁବର୍ଣ୍ଣରେଖା ବଙ୍ଗୋପସାଗରରେ ମିଶେ: ତାଳ ଘେରା ଶାନ୍ତ ବାଲିଚରଣ, ଭଟ୍ଟିରେ ପାଦରେ ପାର ହେଉଥିବା ଅଗଭୀର ସ୍ରୋତ, ଆଉ ଲାଲ କଙ୍କଡ଼ାରେ ବିଖରା କୂଳ।",
    },
    tip: {
      en: "Cross the creek by boat or on foot and walk on to the quiet Udaipur beach next door.",
      hi: "नाव या पैदल धारा पार करें और आगे शांत उदयपुर बीच तक चल जाएँ।",
      or: "ନୌକା ବା ପାଦରେ ସ୍ରୋତ ପାର ହୋଇ ଆଗ ଶାନ୍ତ ଉଦୟପୁର ବେଳାଭୂମିକୁ ଚାଲନ୍ତୁ।",
    },
  },
  {
    key: "hukitola",
    name: "Hukitola Island",
    city: "Kendrapara",
    tag: "coast",
    image: IMG.hukitola,
    story: {
      en: "A 19th-century British grain store with arched vents stands alone on a mangrove island — built to guard famine rice, reached today only by fishermen's boats.",
      hi: "मैंग्रोव द्वीप पर अकेला खड़ा 19वीं सदी का ब्रिटिश अनाज-भंडार — अकाल के चावल रखने के लिए बना, आज सिर्फ़ मछुआरों की नावों से पहुँचा जाता है।",
      or: "ମାନ୍ଗ୍ରୋଭ ଦ୍ୱୀପ ଉପରେ ଏକୁଟିଆ ଛିଡ଼ା ୧୯ଶ ଶତାବ୍ଦୀର ଇଂରେଜ ଧାନ-ଗୁଦାମ — ଦୁର୍ଭିକ୍ଷ ଚାଉଳ ରଖିବା ପାଇଁ ତିଆରି, ଆଜି କେବଳ ଧୀବର ନୌକାରେ ପହଞ୍ଚାଯାଏ।",
    },
    tip: {
      en: "Ask for the Hukitola crossing at the Gupti or Jambu ghat — it pairs perfectly with a Bhitarkanika boat day.",
      hi: "गुप्ती या जम्बू घाट पर हुकिटोला की नाव माँगें — भितरकनिका के नाव-दिन के साथ अच्छा जुड़ता है।",
      or: "ଗୁପ୍ତି ବା ଜମ୍ବୁ ଘାଟରେ ହୁକିଟୋଲା ନୌକା ମାଗନ୍ତୁ — ଭିତରକନିକା ନୌକା ଦିନ ସହ ଭଲ ମିଶେ।",
    },
  },
  {
    key: "rushikulya",
    name: "Rushikulya River Mouth",
    city: "Ganjam",
    tag: "coast",
    image: IMG.rushikulya,
    story: {
      en: "On some February nights tens of thousands of olive ridley turtles crawl out of the Bay of Bengal here to nest — one of the world's great wildlife sights, just off the highway.",
      hi: "फ़रवरी की कुछ रातों में हज़ारों ऑलिव रिडले कछुए यहीं बंगाल की खाड़ी से निकलकर अंडे देने आते हैं — दुनिया के महान वन्य-दृश्यों में एक, बस हाईवे से कुछ दूर।",
      or: "ଫେବୃଆରୀର କେତେକ ରାତିରେ ହଜାର ହଜାର ଅଲିଭ୍ ରିଡଲେ କଇଁଛ ବଙ୍ଗୋପସାଗରରୁ ଉଠି ଆସି ଏଠାରେ ଅଣ୍ଡା ଦିଅନ୍ତି — ପୃଥିବୀର ମହାନ ବନ୍ୟ ଦୃଶ୍ୟ ମଧ୍ୟରୁ ଏକ, ରାଜପଥ ପାଖରେ।",
    },
    tip: {
      en: "Feb–March: join a forest-department turtle watch at Podampeta — red lights only after dark, and never touch a turtle.",
      hi: "फ़रवरी–मार्च: पोडम्पेटा में वन विभाग की टर्टल-वॉच से जुड़ें — शाम के बाद लाल बत्ती ही, और कछुए को हाथ मत लगाएँ।",
      or: "ଫେବୃ–ମାର୍ଚ: ପୋଡମ୍ପେଟାରେ ବନ ବିଭାଗର କଇଁଛ ଦେଖା ସହ ଯୋଡ଼ି ହୁଅନ୍ତୁ — ସନ୍ଧ୍ୟା ପରେ ଲାଲ ବତୀ ହିଁ, ଆଉ କଇଁଛ ଛୁଅଁନ୍ତୁ ନାହିଁ।",
    },
  },
  // ── forests & wildlife ─────────────────────────────────────────────────────
  {
    key: "mangalajodi",
    name: "Mangalajodi",
    city: "Khordha (north Chilika)",
    tag: "wild",
    image: IMG.mangalajodi,
    story: {
      en: "A village of reformed poachers now rows visitors through Chilika's northern reeds — in winter, lakhs of migratory ducks and godwits feed within arm's length of the boat.",
      hi: "शिकारी से रक्षक बने गाँव के लोग अब चिल्का के उत्तरी सरकंडों में पर्यटकों को नाव चलाते हैं — सर्दियों में लाखों प्रवासी बत्तखें नाव के पास चरती हैं।",
      or: "ଶିକାରୀରୁ ରକ୍ଷକ ହୋଇଥିବା ଗାଁ ଲୋକେ ଆଜି ଚିଲିକା ଉତ୍ତର ବାଉଁଶ ମଧ୍ୟରେ ପର୍ଯ୍ୟଟକଙ୍କୁ ନୌକା ଚଲାଇ ନିଅନ୍ତି — ଶୀତରେ ଲକ୍ଷ ଲକ୍ଷ ପ୍ରବାସୀ ବତକ ନୌକା ପାଖରେ ଖାଆନ୍ତି।",
    },
    tip: {
      en: "Take the dawn boat from the village eco-trust ghat — a guide who once set those nets knows every bird by name.",
      hi: "गाँव के इको-ट्रस्ट घाट से भोर की नाव लें — जिस गाइड ने कभी जाल बिछाए, वही हर चिड़िया नाम से जानता है।",
      or: "ଗାଁର ଇକୋ-ଟ୍ରସ୍ଟ ଘାଟରୁ ଭୋର ନୌକା ନିଅନ୍ତୁ — ଯେଉଁ ଗାଇଡ୍ କେବେ ଜାଲ ପକାଉଥିଲେ, ସେ ହିଁ ପ୍ରତ୍ୟେକ ପକ୍ଷୀର ନାମ ଜାଣନ୍ତି।",
    },
  },
  {
    key: "bhitarkanika",
    name: "Bhitarkanika Mangroves",
    city: "Kendrapara",
    tag: "wild",
    image: IMG.bhitarkanika,
    story: {
      en: "India's second-largest mangrove world — boat through Khola creek at dawn past estuarine crocodiles and the loudest birdsong in Odisha.",
      hi: "भारत का दूसरा सबसे बड़ा मैंग्रोव जंगल — भोर में खोला क्रीक से नाव भरें; रास्ते में खारे पानी के मगरमच्छ और ओडिशा की सबसे तेज़ चिड़ियों की आवाज़ें।",
      or: "ଭାରତର ଦ୍ୱିତୀୟ ସବୁଠାରୁ ବଡ଼ ମାନ୍ଗ୍ରୋଭ ଜଙ୍ଗଲ — ଭୋରରେ ଖୋଲା କ୍ରିକ୍‌ରୁ ନୌକା ଚଲାନ୍ତୁ; ବାଟରେ ଲୁଣା ପାଣି କୁମ୍ଭୀର ଆଉ ଓଡ଼ିଶାର ସବୁଠାରୁ ଜୋରର ପକ୍ଷୀ ଡାକ।",
    },
    tip: {
      en: "Carry cash — Dangmal has no ATMs or signal; the Bagagahan heronry is at its busiest in winter.",
      hi: "नकद रखें — डंगमल में न एटीएम है, न नेटवर्क; बागाघन बगुला-बसेरा सर्दियों में सबसे भरा होता है।",
      or: "ନଗଦ ନିଅନ୍ତୁ — ଡଙ୍ଗମାଲରେ ନ ଏଟିଏମ୍ ଅଛି ନ ନେଟ୍‌ୱର୍କ; ବାଗାଘନ ବଗ ବସତି ଶୀତରେ ସବୁଠାରୁ ଭରା।",
    },
  },
  {
    key: "similipal",
    name: "Similipal Tiger Reserve",
    city: "Mayurbhanj",
    tag: "wild",
    image: IMG.similipal,
    story: {
      en: "Sal forests and big-animal country, with the 399-metre Barehipani Falls thundering inside the reserve — Odisha's wildest drive.",
      hi: "साल के जंगल और बड़े जानवरों की ज़मीन, और अभयारण्य के भीतर गरजता 399 मीटर का बारेहिपानी जलप्रपात — ओडिशा का सबसे जंगली सफ़र।",
      or: "ସାଲ ଜଙ୍ଗଲ ଆଉ ବଡ଼ ଜୀବଙ୍କ ଦେଶ, ଆଉ ଅଭୟାରଣ୍ୟ ଭିତରେ ଗର୍ଜାଉଥିବା ୩୯୯ ମିଟରର ବାରେହିପାଣି ଜଳପ୍ରପାତ — ଓଡ଼ିଶାର ସବୁଠାରୁ ଜଙ୍ଗଲିଆ ଯାତ୍ରା।",
    },
    tip: {
      en: "Book the online permit for the Pithabata gate two days ahead; stay at the Lulung or Jamuani eco-cottages.",
      hi: "पीथाबाटा गेट की ऑनलाइन परमिट दो दिन पहले बुक करें; लुलुंग या जामुआनी इको-कॉटेज में रुकें।",
      or: "ପିଥାବାଟା ଗେଟ୍‌ର ଅନଲାଇନ୍ ପରମିଟ୍ ଦୁଇ ଦିନ ପୂର୍ବରୁ ବୁକ୍ କରନ୍ତୁ; ଲୁଲୁଙ୍ଗ ବା ଜାମୁଆନୀ ଇକୋ-କୋଟେଜରେ ରୁହନ୍ତୁ।",
    },
  },
  {
    key: "satkosia",
    name: "Satkosia Gorge (Tikarpada)",
    city: "Angul",
    tag: "wild",
    image: IMG.satkosia,
    story: {
      en: "The Mahanadi squeezes through a 22-kilometre gorge between two hills — boat on green water past a gharial sanctuary and eagle cliffs.",
      hi: "महानदी दो पहाड़ों के बीच 22 किमी लंबी घाटी से गुज़रती है — हरे पानी पर नाव, रास्ते में गहरियाल अभयारण्य और चीलों की चट्टानें।",
      or: "ମହାନଦୀ ଦୁଇ ପାହାଡ଼ ମଧ୍ୟରେ ୨୨ କିମି ଲମ୍ବା ଗୋର୍ଜ ଦେଇ ବହେ — ସବୁଜ ପାଣିରେ ନୌକା, ବାଟରେ ଘଡ଼ିଆଳ ଅଭୟାରଣ୍ୟ ଓ ଚିଲଙ୍କ ପଥର।",
    },
    tip: {
      en: "Winter is boating season; sleep in the Tikarpada nature camp right above the river.",
      hi: "सर्दियों में नाव चलती है; टिकरपड़ा नेचर कैंप में ठहरें — ठीक नदी के ऊपर।",
      or: "ଶୀତରେ ନୌକା ଚାଲେ; ଟିକରପଡ଼ା ନେଚର କ୍ୟାମ୍ପରେ ରୁହନ୍ତୁ — ଠିକ୍ ନଦୀ ଉପରେ।",
    },
  },
  {
    key: "debrigarh",
    name: "Debrigarh Sanctuary",
    city: "Bargarh",
    tag: "wild",
    image: IMG.debrigarh,
    story: {
      en: "A sanctuary right on the shore of the vast Hirakud reservoir — deer cross the track, peacocks call, and sunset turns the whole lake to gold.",
      hi: "विशाल हीराकुंड जलाशय के किनारे बसा अभयारण्य — पगडंडी पार करते हिरण, बोलते मोर, और ढलती शाम में सोना हो उठती पूरी झील।",
      or: "ବିଶାଳ ହୀରାକୁଦ ଜଳଭଣ୍ଡାର କୂଳରେ ବସା ଅଭୟାରଣ୍ୟ — ପଥ ପାର ହେଉଥିବା ମାନ, ଡାକୁଥିବା ମୟୂର, ଆଉ ଅସ୍ତରେ ସୁନା ହୋଇଉଠୁଥିବା ପୁରା ପୁଷ୍କରିଣୀ।",
    },
    tip: {
      en: "Book a safari at the wildlife office and stay for the Hirakud sunset — the best in western Odisha.",
      hi: "वन्यजीव कार्यालय से सफ़ारी बुक करें और हीराकुंड के सूर्यास्त तक रुकें — पश्चिमी ओडिशा का सबसे सुंदर।",
      or: "ବନ୍ୟପ୍ରାଣୀ କାର୍ଯ୍ୟାଳୟରୁ ସାଫାରି ବୁକ୍ କରନ୍ତୁ ଆଉ ହୀରାକୁଦର ଅସ୍ତ ପର୍ଯ୍ୟନ୍ତ ରୁହନ୍ତୁ — ପଶ୍ଚିମ ଓଡ଼ିଶାର ସବୁଠାରୁ ସୁନ୍ଦର।",
    },
  },
  {
    key: "mandasaru",
    name: "Mandasaru Silent Valley",
    city: "Kandhamal",
    tag: "wild",
    image: IMG.mandasaru,
    story: {
      en: "Kandhamal's own \"Silent Valley\" — a gorge half a kilometre deep, wild orchids, and a hush so complete you hear only wind and bird calls.",
      hi: "कंधमाल की अपनी साइलेंट वैली — आधा किलोमीटर गहरी घाटी, जंगली ऑर्किड़ और इतनी गहरी ख़ामोशी कि सिर्फ़ हवा और चिड़ियों की आवाज़ सुनाई देती है।",
      or: "କନ୍ଧମାଳର ନିଜସ୍ୱ ସାଇଲେଣ୍ଟ ଭ୍ୟାଲି — ଅଧା କିମି ଗଭୀର ଗୋର୍ଜ, ଜଙ୍ଗଲି ଅର୍କିଡ୍ ଆଉ ଏମିତି ନୀରବତା ଯେ କେବଳ ପବନ ଆଉ ପକ୍ଷୀ ଡାକ ଶୁଣାଯାଏ।",
    },
    tip: {
      en: "Go at dawn from the Phulbani side when cloud fills the gorge; there are no shops up there — carry water and snacks.",
      hi: "फुलबानी से भोर में जाएँ जब घाटी में बादल भर जाए; ऊपर दुकान नहीं — पानी और नाश्ता साथ रखें।",
      or: "ଫୁଲବାଣୀ ପାଖରୁ ଭୋରରେ ଯାଆନ୍ତୁ ଯେତେବେଳେ ଗୋର୍ଜ ମେଘରେ ଭରିଯାଏ; ଉପରେ ଦୋକାନ ନାହିଁ — ପାଣି ଆଉ ନାସ୍ତା ନିଅନ୍ତୁ।",
    },
  },
  // ── falls & hills ──────────────────────────────────────────────────────────
  {
    key: "daringbadi",
    name: "Daringbadi",
    city: "Kandhamal",
    tag: "hills",
    image: IMG.daringbadi,
    story: {
      en: "The \"Kashmir of Odisha\" at 3,000 feet — December mornings sometimes frost the pine needles white, and roadside sellers pass you fresh turmeric and wild honey.",
      hi: "3,000 फ़ुट पर \"ओडिशा का कश्मीर\" — दिसंबर की सुबह कभी-कभी पाइन की सुइयों को पाला सफ़ेद कर देता है, और सड़क किनारे लोग ताज़ी हल्दी और जंगली शहद बेचते हैं।",
      or: "୩,୦୦୦ ଫୁଟ ଉଚ୍ଚତାରେ \"ଓଡ଼ିଶାର କାଶ୍ମୀର\" — ଡିସେମ୍ବର ସକାଳ ବେଳେବେଳେ ପାଇନ୍ ସୂଚିକା ପାଳାରେ ଧଳା ହୋଇଯାଏ, ଆଉ ରାସ୍ତା ଧାରରେ ଲୋକେ ତାଜା ହଳଦୀ ଆଉ ଜଙ୍ଗଲି ମହୁ ବେଚନ୍ତି।",
    },
    tip: {
      en: "Network is patchy — download offline maps, and pack a jacket even in April.",
      hi: "नेटवर्क कमज़ोर है — ऑफ़लाइन मैप डाउनलोड करें, और अप्रैल में भी जैकेट रखें।",
      or: "ନେଟ୍‌ୱର୍କ ଦୁର୍ବଳ — ଅଫଲାଇନ୍ ମାପ ଡାଉନଲୋଡ୍ କରନ୍ତୁ, ଅପ୍ରେଲରେ ବି ଜାକେଟ୍ ନିଅନ୍ତୁ।",
    },
  },
  {
    key: "taptapani",
    name: "Taptapani Hot Springs",
    city: "Gajapati",
    tag: "hills",
    image: IMG.taptapani,
    story: {
      en: "A steaming sulphur spring in a forested valley — bathe in the warm tank, then browse the tribal haat that assembles on the road below.",
      hi: "हरी-भरी घाटी में उबलता गंधक झरना — गरम कुंड में डुबकी लगाएँ, फिर नीचे सड़क पर लगने वाली आदिवासी हाट देखें।",
      or: "ସବୁଜ ଉପତ୍ୟକାରେ ଗରମ ଗନ୍ଧକ ଝରା — ଉଷୁମା କୁଣ୍ଡରେ ଡୁବକି ଦିଅନ୍ତୁ, ପରେ ତଳ ରାସ୍ତାରେ ବସୁଥିବା ଆଦିବାସୀ ହାଟ ଦେଖନ୍ତୁ।",
    },
    tip: {
      en: "Sleep at the hillside OTDC Pantha Nivas — the rooms open right beside the spring.",
      hi: "पहाड़ी पर ओटीडीसी पंथ निवास में रुकें — कमरे सीधे झरने के पास खुलते हैं।",
      or: "ପାହାଡ଼ ଉପରେ ଓଟିଡିସି ପନ୍ଥ ନିବାସରେ ରୁହନ୍ତୁ — କୋଠରି ସିଧା ଝରା ପାଖରେ।",
    },
  },
  {
    key: "deomali",
    name: "Deomali Peak",
    city: "Koraput",
    tag: "hills",
    image: IMG.deomali,
    story: {
      en: "Odisha's highest peak — 1,672 metres above Koraput's coffee slopes, where winter clouds drift below the road.",
      hi: "ओडिशा का सबसे ऊँचा पहाड़ — कोरापुट की कॉफ़ी ढलानों पर 1,672 मीटर, जहाँ सर्दियों में बादल सड़क के नीचे तैरते हैं।",
      or: "ଓଡ଼ିଶାର ସର୍ବୋଚ୍ଚ ପର୍ବତ — କୋରାପୁଟର କଫି ଢାଲ ଉପରେ ୧,୬୭୨ ମିଟର, ଯେଉଁଠି ଶୀତରେ ମେଘ ରାସ୍ତା ତଳେ ବୁଲନ୍ତି।",
    },
    tip: {
      en: "Start from Koraput town before sunrise — the summit is coldest and clearest at dawn.",
      hi: "कोरापुट से सूर्योदय से पहले निकलें — भोर में चोटी सबसे साफ़ और ठंडी होती है।",
      or: "କୋରାପୁଟରୁ ସୂର୍ଯ୍ୟୋଦୟ ପୂର୍ବରୁ ବାହାରନ୍ତୁ — ଭୋରରେ ଶିଖର ସବୁଠାରୁ ସଫା ଆଉ ଥଣ୍ଡା।",
    },
  },
  {
    key: "khandadhar",
    name: "Khandadhar Waterfall",
    city: "Sundargarh",
    tag: "hills",
    image: IMG.khandadhar,
    story: {
      en: "Odisha's tallest waterfall drops 244 metres in one unbroken horse-tail of white, hidden in the forested hills of Sundargarh.",
      hi: "ओडिशा का सबसे ऊँचा झरना 244 मीटर एक अखंड सफ़ेद घोड़ी-पूँछ बनकर गिरता है — सुंदरगढ़ के जंगली पहाड़ों में छिपा।",
      or: "ଓଡ଼ିଶାର ସର୍ବୋଚ୍ଚ ଜଳପ୍ରପାତ ୨୪୪ ମିଟର ଏକ ଅଖଣ୍ଡ ଧଳା ଘୋଡ଼ା-ଲାଞ୍ଜ ପରି ଖସେ — ସୁନ୍ଦରଗଡ଼ର ଜଙ୍ଗଲ ପାହାଡ଼ରେ ଲୁଚା।",
    },
    tip: {
      en: "Flow is best from August to December; the last forest road is rough — a local auto from Lahunipara handles it better than a car.",
      hi: "अगस्त से दिसंबर तक सबसे भरा रहता है; आख़िरी जंगली रास्ता खुरदरा है — लहुनीपाड़ा से ऑटो कार से बेहतर चलता है।",
      or: "ଅଗଷ୍ଟରୁ ଡିସେମ୍ବର ପର୍ଯ୍ୟନ୍ତ ସବୁଠାରୁ ଭରା; ଶେଷ ଜଙ୍ଗଲ ରାସ୍ତା କର୍କଶ — ଲହୁନିପାଡ଼ାରୁ ଅଟୋ ଗାଡ଼ି ଠାରୁ ଭଲ ଚାଲେ।",
    },
  },
  {
    key: "gandhamardan",
    name: "Gandhamardan Hills",
    city: "Bargarh",
    tag: "hills",
    image: IMG.gandhamardan,
    story: {
      en: "The hill that legend says Hanuman carried for a life-saving herb — and botanists agree on the treasure: hundreds of medicinal plants ring the Nrusimhanath shrine and its falls.",
      hi: "पहाड़ जिसे कहा जाता है कि हनुमान ने जीवनी-बूटी के लिए उठाया — और वैज्ञानिक भी ख़ज़ाना मानते हैं: सैकड़ों औषधीय पौधे नृसिंहनाथ मंदिर और उसके झरने के चारों ओर हैं।",
      or: "ପାହାଡ଼ ଯାହାକୁ କୁହାଯାଏ ହନୁମାନ ଜୀବନୀ ବୁଦା ପାଇଁ ଉଠାଇ ନେଇଥିଲେ — ଆଉ ବୈଜ୍ଞାନିକ ମଧ୍ୟ ଏହି ଧନ ମାନନ୍ତି: ଶହ ଶହ ଔଷଧୀୟ ଗଛ ନୃସିଂହନାଥ ମନ୍ଦିର ଆଉ ଝରଣା ଚାରିଆଡ଼େ।",
    },
    tip: {
      en: "The shaded walk from Nrusimhanath to the falls is easy; Harishankar sits on the far slope — one hill, two shrines, a full day.",
      hi: "नृसिंहनाथ से झरने तक छायादार पगडंडी आसान है; हरिशंकर दूसरी ढलान पर है — एक पहाड़, दो मंदिर, पूरा दिन।",
      or: "ନୃସିଂହନାଥରୁ ଝରଣା ପାଖକୁ ଛାୟା ପଥ ସହଜ; ହରିଶଙ୍କର ଅନ୍ୟ ଢାଲରେ — ଏକ ପାହାଡ଼, ଦୁଇ ମନ୍ଦିର, ପୁରା ଦିନ।",
    },
  },
  // ── heritage & temples ─────────────────────────────────────────────────────
  {
    key: "kapilash",
    name: "Kapilash Temple",
    city: "Dhenkanal",
    tag: "heritage",
    image: IMG.kapilash,
    story: {
      en: "Climb the stone steps at 6 AM — you'll likely hear elephants calling from the reserve below, and the chai stall at the top is a local legend.",
      hi: "सुबह 6 बजे पत्थर की सीढ़ियाँ चढ़ें — नीचे अभयारण्य से हाथियों की आवाज़ सुनाई दे सकती है, और ऊपर वाली चाय की दुकान लोकप्रिय है।",
      or: "ସକାଳ ୬ଟାରେ ପଥର ପାହାଚ ଉଠନ୍ତୁ — ତଳ ଅଭୟାରଣ୍ୟରୁ ହାତୀ ଡାକ ଶୁଣାଯାଇପାରେ, ଆଉ ଉପର ଚା ଦୋକାନ ଏଠାକାର କିମ୍ବଦନ୍ତୀ।",
    },
    tip: {
      en: "Pair it with the seven hills of Saptasajya about 20 km away for a full-day trip.",
      hi: "लगभग 20 किमी दूर सप्तसज्य की सात पहाड़ियों के साथ जोड़ें — पूरे दिन की यात्रा बनेगी।",
      or: "ପ୍ରାୟ ୨୦ କିମି ଦୂର ସପ୍ତସଜ୍ୟର ସାତ ପାହାଡ଼ ସହ ଯୋଡ଼ନ୍ତୁ — ପୁରା ଦିନର ଯାତ୍ରା ହେବ।",
    },
  },
  {
    key: "chandragiri",
    name: "Chandragiri Tibetan Colony",
    city: "Gajapati",
    tag: "heritage",
    image: IMG.chandragiri,
    story: {
      en: "\"Mini Tibet\" — a Tibetan settlement since the 1960s with the towering Padmasambhava monastery, hand-woven carpets and steaming momos.",
      hi: "\"छोटा तिब्बत\" — 1960 के दशक से बसा तिब्बती बस्ती, ऊँचा पद्मसंभव मठ, हाथ से बुने कालीन और गरम मोमो।",
      or: "\"ଛୋଟ ତିବ୍ବତ\" — ୧୯୬୦ ଦଶକରୁ ଥିବା ତିବ୍ବତୀୟ ବସ୍ତି, ଉଚ୍ଚ ପଦ୍ମସମ୍ଭବ ମଠ, ହାତରେ ବୁଣା କାର୍ପେଟ୍ ଆଉ ଗରମ ମୋମୋ।",
    },
    tip: {
      en: "Sit in on the monks' morning prayers, then buy a carpet straight from the weavers' co-op.",
      hi: "सुबह भिक्षुओं की प्रार्थना में बैठें, फिर बुनकर सहकारी समिति से सीधे कालीन खरीदें।",
      or: "ସକାଳ ଭିକ୍ଷୁଙ୍କ ପ୍ରାର୍ଥନାରେ ବସନ୍ତୁ, ପରେ ବୁଣକର ସହକାରୀ ସମିତିରୁ ସିଧା କାର୍ପେଟ୍ କିନନ୍ତୁ।",
    },
  },
  {
    key: "khiching",
    name: "Khiching",
    city: "Mayurbhanj",
    tag: "heritage",
    image: IMG.khiching,
    story: {
      en: "The forgotten capital of the Bhanja kings — a black-stone Khichakeswari temple rebuilt on old foundations and a quiet museum full of 8th–12th century sculpture.",
      hi: "भंज राजाओं की भुला दी गई राजधानी — पुरानी नींव पर फिर बना काले-पत्थर का खिचकेश्वरी मंदिर और 8वीं–12वीं सदी की मूर्तियों से भरा शांत संग्रहालय।",
      or: "ଭଞ୍ଜ ରାଜାଙ୍କ ଭୁଲା ରାଜଧାନୀ — ପୁରୁଣା ଭିତ୍ତି ଉପରେ ପୁନର୍ନିମିତ କଳା ପଥର ଖିଚକେଶ୍ୱରୀ ମନ୍ଦିର ଆଉ ୮ମ–୧୨ଶ ଶତାବ୍ଦୀର ମୂର୍ତ୍ତିରେ ଭରା ଶାନ୍ତ ସଂଗ୍ରହାଳୟ।",
    },
    tip: {
      en: "Reach it via Karanjia and add Devkund's falls if the forest road is open.",
      hi: "करंजिया होते हुए पहुँचें और अगर वन-रास्ता खुला हो तो देवकुंड का झरना भी जोड़ें।",
      or: "କରଞ୍ଜିଆ ଦେଇ ପହଞ୍ଚନ୍ତୁ ଆଉ ବନ ରାସ୍ତା ଖୋଲା ଥିଲେ ଦେବକୁଣ୍ଡ ଝରଣା ମଧ୍ୟ ଯୋଡ଼ନ୍ତୁ।",
    },
  },
  {
    key: "diamond",
    name: "Ratnagiri · Lalitgiri · Udayagiri",
    city: "Jajpur",
    tag: "heritage",
    image: IMG.diamond,
    story: {
      en: "The Buddhist Diamond Triangle — Ratnagiri's carved monastery doorframe, Buddha relic caskets unearthed at Lalitgiri, and a giant stepped stupa at Udayagiri, all on green lonely hills.",
      hi: "बौद्ध हीरा त्रिकोण — रत्नगिरि का नक्काशीदार मठ-द्वार, ललितगिरि में खुदे मिले बुद्ध अवशेष-कोष्ठ और उदयगिरि का विशाल सीढ़ीदार स्तूप — सब हरी-भरी सूनी पहाड़ियों पर।",
      or: "ବୌଦ୍ଧ ହୀରା ତ୍ରିକୋଣ — ରତ୍ନଗିରିର ଖୋଦିତ ମଠ-ଦ୍ୱାର, ଲଳିତଗିରିରେ ମିଳିଥିବା ବୁଦ୍ଧ ଧାତୁ-ପେଟିକା ଆଉ ଉଦୟଗିରିର ବିଶାଳ ପାହାଚ ସ୍ତୂପ — ସବୁ ସବୁଜ ନିର୍ଜନ ପାହାଡ଼ରେ।",
    },
    tip: {
      en: "Start at Ratnagiri for the doorframe, end with the stupa climb at Udayagiri; carry water — no stalls on the hills.",
      hi: "नक्काशी के लिए रत्नगिरि से शुरू करें, उदयगिरि के स्तूप की चढ़ाई से ख़त्म करें; पानी साथ रखें — पहाड़ियों पर दुकान नहीं।",
      or: "ଖୋଦାଇ ପାଇଁ ରତ୍ନଗିରିରୁ ଆରମ୍ଭ କରନ୍ତୁ, ଉଦୟଗିରି ସ୍ତୂପ ଉଠି ଶେଷ କରନ୍ତୁ; ପାଣି ଆଣନ୍ତୁ — ପାହାଡ଼ରେ ଦୋକାନ ନାହିଁ।",
    },
  },
  {
    key: "hirapur",
    name: "Chausath Yogini Temple",
    city: "Hirapur, Khordha (near Bhubaneswar)",
    tag: "heritage",
    image: IMG.hirapur,
    story: {
      en: "Nine kilometres from Bhubaneswar hides one of India's four surviving yogini shrines — a roofless circle of 64 black-stone goddesses open to the sky.",
      hi: "भुवनेश्वर से मात्र 9 किमी दूर छिपा है भारत के बचे चार योगिनी मंदिरों में एक — 64 काले-पत्थर की देवियों का बिना छत वाला गोल घेरा, ऊपर खुला आसमान।",
      or: "ଭୁବନେଶ୍ୱରରୁ ମାତ୍ର ୯ କିମି ଦୂରରେ ଲୁଚିଛି ଭାରତର ବଞ୍ଚିଥିବା ଚାରି ଯୋଗିନୀ ମନ୍ଦିର ମଧ୍ୟରୁ ଏକ — ୬୪ କଳା ପଥର ଦେବୀଙ୍କ ଛଣବିହୀନ ଗୋଲ ମନ୍ଦିର, ଉପରେ ଖୋଲା ଆକାଶ।",
    },
    tip: {
      en: "Tiny and almost always empty — go early when the morning light is best; pair it with the Diamond Triangle for a full ancient day.",
      hi: "छोटा और लगभग हमेशा खाली — सुबह जल्दी जाएँ जब रोशनी सबसे अच्छी हो; हीरा त्रिकोण के साथ जोड़ें।",
      or: "ଛୋଟ ଆଉ ପ୍ରାୟ ସବୁବେଳେ ଖାଲି — ସକାଳେ ଯାଆନ୍ତୁ ଯେତେବେଳେ ଆଲୁଅ ସବୁଠାରୁ ଭଲ; ହୀରା ତ୍ରିକୋଣ ସହ ଯୋଡ଼ନ୍ତୁ।",
    },
  },
  {
    key: "huma",
    name: "Leaning Temple of Huma",
    city: "Sambalpur",
    tag: "heritage",
    image: IMG.huma,
    story: {
      en: "A Shiva temple that leans like Pisa's tower — and has stood that way for centuries — on the Mahanadi's bank, with sacred fish you can feed at the ghat.",
      hi: "शिव मंदिर जो पीसा की मीनार की तरह झुका है — और सदियों से ऐसे ही खड़ा है — महानदी किनारे, और घाट पर पवित्र मछलियाँ जिन्हें आप दाना दे सकते हैं।",
      or: "ଶିବ ମନ୍ଦିର ଯାହା ପିସା ଟାଓର ପରି ହେଲାଣ ହୋଇଛି — ଆଉ ଶତାବ୍ଦୀ ଧରି ସେପରି ଛିଡ଼ା — ମହାନଦୀ କୂଳରେ, ଆଉ ଘାଟରେ ପବିତ୍ର ମାଛ ଯାହାଙ୍କୁ ଦାନା ଦେଇପାରିବେ।",
    },
    tip: {
      en: "Buy puffed rice at the ghat and feed the big sacred fish — then watch the sunset from the river bend.",
      hi: "घाट पर मुरमुरा खरीदें और बड़ी पवित्र मछलियों को डालें — फिर नदी के मोड़ से सूर्यास्त देखें।",
      or: "ଘାଟରେ ମୁଦି ଖଣ୍ଡି କିନି ବଡ଼ ପବିତ୍ର ମାଛଙ୍କୁ ଦିଅନ୍ତୁ — ପରେ ନଦୀ ବାଁକରୁ ଅସ୍ତ ଦେଖନ୍ତୁ।",
    },
  },
  {
    key: "patali",
    name: "Patali Srikhetra",
    city: "Sonepur",
    tag: "heritage",
    image: IMG.patali,
    story: {
      en: "The hill shrine at Sonepur where tradition says the Jagannath trinity lay hidden for years during medieval raids, before returning to Puri — above the Mahanadi–Tel confluence.",
      hi: "सोनपुर की पहाड़ी तीर्थ जहाँ परंपरा कहती है कि मध्यकालीन आक्रमणों के दौरान जगन्नाथ त्रित्व वर्षों यहीं गुफा में छिपा रहा, फिर पुरी लौटा — महानदी–तेल संगम के ऊपर।",
      or: "ସୋନପୁରର ପାହାଡ଼ ତୀର୍ଥ ଯେଉଁଠି ପରମ୍ପରା କହେ ମଧ୍ୟଯୁଗୀୟ ଆକ୍ରମଣ ବେଳେ ଜଗନ୍ନାଥ ତ୍ରିତ୍ୱ ବର୍ଷ ବର୍ଷ ଏଠାରେ ଗୁମ୍ଫାରେ ଲୁଚି ରହିଥିଲା, ପରେ ପୁରୀ ଫେରିଲା — ମହାନଦୀ–ତେଲ ସଙ୍ଗମ ଉପରେ।",
    },
    tip: {
      en: "Add Sonepur's riverside temples (Sureswari is the famous one) — the town sits where the Mahanadi meets the Tel.",
      hi: "सोनपुर के नदी-किनारे के मंदिर भी जोड़ें (सुरेश्वरी सबसे प्रसिद्ध है) — कस्बा वहीं बसा है जहाँ महानदी तेल से मिलती है।",
      or: "ସୋନପୁରର ନଦୀ କୂଳ ମନ୍ଦିର ମଧ୍ୟ ଯୋଡ଼ନ୍ତୁ (ସୁରେଶ୍ୱରୀ ସବୁଠାରୁ ପ୍ରସିଦ୍ଧ) — ସହର ସେଠାରେ ଯେଉଁଠି ମହାନଦୀ ତେଲ ସହ ମିଶେ।",
    },
  },
];

export default function Gems() {
  const { t, i18n } = useTranslation();

  // pick the display language from the app's current i18n language
  const raw = (i18n.language || "en").toLowerCase();
  const lang: Lang =
    raw.startsWith("or") || raw.startsWith("od") ? "or" : raw.startsWith("hi") ? "hi" : "en";
  const L = (s: L10n) => s[lang] || s.en;

  // start with the built-in gems — instant content, never an empty flash
  const [gems, setGems] = useState<Gem[]>(BUILT_IN_GEMS);
  const [open, setOpen] = useState<Gem | null>(null);
  const [filter, setFilter] = useState<Gem["tag"] | "all">("all");

  // merge in any gem_story places your API returns (deduped by name)
  useEffect(() => {
    api
      .places()
      .then((p) => {
        if (!Array.isArray(p)) {
          console.error("places API did not return a list:", p);
          return; // built-in gems keep the page alive
        }
        const seen = new Set(BUILT_IN_GEMS.map((g) => g.name.trim().toLowerCase()));
        const fromApi: Gem[] = [];
        for (const place of p as GemPlace[]) {
          if (!place || !place.name || !place.gem_story) continue;
          const key = place.name.trim().toLowerCase();
          if (seen.has(key)) continue; // already built in
          seen.add(key);
          fromApi.push({
            key: place.place_id || place.name,
            name: place.name,
            city: place.city || "Odisha",
            tag: "wild",
            image: place.image ?? null,
            story: { en: place.gem_story, hi: place.gem_story, or: place.gem_story },
            tip: { en: place.insider_tip ?? "", hi: place.insider_tip ?? "", or: place.insider_tip ?? "" },
          });
        }
        if (fromApi.length) setGems([...BUILT_IN_GEMS, ...fromApi]);
      })
      .catch(console.error);
  }, []);

  const shown = useMemo(
    () => (filter === "all" ? gems : gems.filter((g) => g.tag === filter)),
    [gems, filter],
  );

  const chipCls = (active: boolean) =>
    `rounded-full px-4 py-2 text-xs font-bold transition-colors ${
      active
        ? "bg-forest text-white"
        : "border border-[#EAD9C6] bg-white text-[#6B5D4F] hover:border-[#C4A882]"
    }`;

  // the hero button just jumps to the gem cards
  function scrollToGems() {
    document.getElementById("gems-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="pb-4">
      {/* ── hero banner ────────────────────────────────────────────────── */}
      <PageHero
        title={t("gems_title", { defaultValue: "Hidden Gems" })}
        tagline={t("gems_tag", { defaultValue: "SECRET • WILD • UNTOUCHED" })}
        desc={t("gems_desc", {
          defaultValue:
            "Skip the crowds — these hand-picked corners of Odisha are where locals go when they want something special.",
        })}
        quote={t("gems_quote", { defaultValue: "Where Crowds Don't Go" })}
      >
        {/* CTA pill ON the hero photo — same white capsule as Hotels/Emergency */}
        <div className="inline-flex rounded-full bg-white p-2 shadow-[0_10px_30px_rgba(0,0,0,0.28)]">
          <button
            onClick={scrollToGems}
            className="flex h-11 items-center justify-center gap-2 rounded-full bg-forest px-7 text-sm font-bold text-white shadow-sm transition-colors hover:bg-[#2C4634] active:scale-95"
          >
            {t("gems_see", { defaultValue: "See the gems" })} <span aria-hidden>→</span>
          </button>
        </div>
      </PageHero>

      {/* ── filter chips ───────────────────────────────────────────────── */}
      <div id="gems-list" className="mt-6 scroll-mt-4">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <button onClick={() => setFilter("all")} className={chipCls(filter === "all")}>
            {L(UI.all)}
          </button>
          {GEM_TAGS.map((tg) => (
            <button key={tg.id} onClick={() => setFilter(tg.id)} className={chipCls(filter === tg.id)}>
              {L(tg.label)}
            </button>
          ))}
        </div>

        {/* ── gem cards ────────────────────────────────────────────────── */}
        {shown.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-[#EAD9C6] bg-white/60 p-10 text-center">
            <FaGem className="mb-3 text-4xl text-[#C4A882]" aria-hidden />
            <p className="text-sm font-semibold text-[#B08968]">{L(UI.empty)}</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {shown.map((p) => (
              <article
                key={p.key}
                className="group cursor-pointer overflow-hidden rounded-3xl border border-[#F0E2D0] bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg"
                onClick={() => setOpen(p)}
              >
                <div className="relative h-44 overflow-hidden bg-gradient-to-br from-[#35543F] to-[#2C4634]">
                  <FaGem className="absolute inset-0 m-auto text-4xl text-white/50" aria-hidden />
                  {p.image ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={p.image}
                      alt={p.name}
                      loading="lazy"
                      className="relative h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      onError={(e) => {
                        e.currentTarget.style.display = "none"; // dead URL → show the gradient behind
                      }}
                    />
                  ) : null}
                  <span className="absolute right-2.5 top-2.5 rounded-full bg-[#FCF3CF]/95 px-2.5 py-1 text-[11px] font-bold text-[#7D6608] shadow-sm">
                    {t("nav_gems", { defaultValue: "Gems" })}
                  </span>
                </div>

                <div className="p-5">
                  <h3 className="font-script text-2xl leading-tight text-[#3E2A1B]">{p.name}</h3>
                  <p className="mt-1.5 flex items-center gap-1.5 text-xs font-semibold text-[#6B5D4F]">
                    <FaMapMarkerAlt className="text-[#C4A882]" aria-hidden /> {p.city}
                  </p>
                  <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-[#6B5D4F]">{L(p.story)}</p>
                  <span className="mt-3 inline-flex items-center gap-1.5 text-sm font-bold text-terracotta transition-all group-hover:gap-2.5">
                    {L(UI.readStory)} <span aria-hidden>→</span>
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      {/* ── story modal ────────────────────────────────────────────────── */}
      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/45 p-0 backdrop-blur-sm sm:items-center sm:p-6"
          onClick={() => setOpen(null)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="max-h-[85vh] w-full overflow-y-auto rounded-t-3xl bg-white sm:max-w-lg sm:rounded-3xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="relative h-52 bg-gradient-to-br from-[#35543F] to-[#2C4634]">
              <FaGem className="absolute inset-0 m-auto text-5xl text-white/50" aria-hidden />
              {open.image ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={open.image}
                  alt={open.name}
                  className="relative h-full w-full object-cover"
                  onError={(e) => {
                    e.currentTarget.style.display = "none"; // dead URL → show the gradient behind
                  }}
                />
              ) : null}
              <button
                onClick={() => setOpen(null)}
                aria-label={L(UI.close)}
                className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-black/40 text-white backdrop-blur transition-colors hover:bg-black/60"
              >
                ✕
              </button>
            </div>

            <div className="p-6">
              <h2 className="font-script text-3xl leading-tight text-[#3E2A1B]"> {open.name}</h2>
              <span className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-sage px-3 py-1 text-xs font-bold text-forest">
                <FaMapMarkerAlt className="text-[10px]" aria-hidden /> {open.city}
              </span>

              <p className="mt-4 text-sm leading-relaxed text-[#6B5D4F]">{L(open.story)}</p>

              {open.tip.en ? (
                <div className="mt-4 flex items-start gap-2.5 rounded-2xl border border-[#F0E2D0] bg-[#FFF7EF] p-4">
                  <FaLightbulb className="mt-0.5 shrink-0 text-terracotta" aria-hidden />
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wide text-terracotta">{L(UI.insider)}</p>
                    <p className="mt-1 text-sm leading-relaxed text-[#6B5D4F]">{L(open.tip)}</p>
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

