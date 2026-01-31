import streamlit as st
import pandas as pd
import requests
import json
import random
import time
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI DESIGN (CSS für maximalen Abstand) ---
st.markdown("""
<style>
/* Eingabefeld fixieren */
.stChatInput {position: fixed; bottom: 30px;}
.stChatMessageAvatar { background-color: #ffffff !important; }

/* TEXT-FORMATIERUNG */
.stMarkdown p {
    font-size: 16px !important;
    line-height: 1.8 !important; /* Viel Luft zwischen Zeilen */
    margin-bottom: 25px !important; /* Großer Abstand nach jedem Absatz */
}
.stMarkdown h3 {
    color: #d32f2f !important; 
    margin-top: 40px !important; /* Abstand vor Überschriften */
    margin-bottom: 15px !important;
    border-bottom: 1px solid #eee; 
    padding-bottom: 5px;
}
.stMarkdown hr {
    margin-top: 30px !important;
    margin-bottom: 30px !important;
    border-color: #f0f0f0;
}
.stMarkdown li {
    margin-bottom: 10px !important;
    line-height: 1.7 !important;
}
</style>
""", unsafe_allow_html=True)

# --- JAHRESZEIT ERMITTELN ---
def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]: return "Winter ❄️"
    elif month in [3, 4, 5]: return "Frühling 🌷"
    elif month in [6, 7, 8]: return "Sommer ☀️"
    else: return "Herbst 🍂"

current_season = get_current_season()

# --- KEYS HOLEN & REINIGEN ---
raw_input = None
if "API_KEYS" in st.secrets: raw_input = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_input = st.secrets["GOOGLE_API_KEY"]

if not raw_input:
    st.error("⚠️ Keine Keys gefunden! Bitte Secrets prüfen.")
    st.stop()

# Keys vorbereiten & reinigen
keys_to_use = []
if isinstance(raw_input, str):
    if "," in raw_input: keys_to_use = [k.strip() for k in raw_input.split(",")]
    else: keys_to_use = [raw_input.strip()]
elif isinstance(raw_input, list):
    keys_to_use = raw_input

api_keys = []
for k in keys_to_use:
    clean = str(k).replace("'", "").replace('"', "").strip()
    if len(clean) > 20: api_keys.append(clean)

if not api_keys:
    st.error("⚠️ Keine gültigen Keys verfügbar.")
    st.stop()

# --- DATEN LADEN ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        return {"csv": df.to_string(index=False), "business": open("business_wissen.txt", "r", encoding="utf-8").read()}
    except: return None

db = load_data()

# --- HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption(f"📅 Saison: {current_season} | 💎 Elite-Modus") 
st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)
st.markdown("---")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # --- DER NEUE "DU & CLEAN" PROMPT ---
        system_text = f"""
        Du bist Rodion, der KI-Mentor für Olfazeta.
        
        KONTEXT:
        - Jahreszeit: {current_season}
        - Daten: {db['csv'] if db else ''} {db['business'] if db else ''}
        
        TONALITY (STRIKT):
        1. ANSPRACHE: Nutze immer das **"Du"**. Sei locker, direkt, aber professionell.
        2. KEINE FLOSKELN: **Lass die Vorstellung weg.** Sag nicht "Hier ist Rodion" oder "Hallo Partner". Starte direkt mit der Antwort.
        3. MARKENSCHUTZ: Nenne NIEMALS Fremdmarken (Dior, Chanel etc.)!
        
        LAYOUT-REGELN (STRIKT):
        1. Nutze `---` als Trennlinie zwischen den Optionen.
        2. Mach nach JEDER Info (Vibe, Preis, Warum) einen **doppelten Absatz** (Leerzeile).
        3. Kein Fließtext! Nutze die Struktur unten.
        
        ANTWORT-SCHABLONE (Nutze genau diese):
        
        "Hier sind die passenden Empfehlungen für dich:
        
        ---
        
        ### 🏆 1. Der Favorit: Nr. [Nummer]
        
        **Vibe:**
        [Beschreibung]
        
        **Warum er passt:**
        [Erklärung passend zur Jahreszeit {current_season}]
        
        💰 **Preis:** **[Preis] €**
        
        ---
        
        ### ✨ 2. Die Alternative: Nr. [Nummer]
        
        **Vibe:**
        [Beschreibung]
        
        💰 **Preis:** **[Preis] €**
        
        ---
        
        💡 **Pro-Tipp:**
        [Kurzer Tipp]"
        """
        
        final_prompt = f"{system_text}\n\nUSER FRAGE: {prompt}"

        # --- VERBINDUNG ---
        success = False
        models_to_try = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-pro-latest"]
        random.shuffle(api_keys)
        
        for model_name in models_to_try:
            if success: break
            for key in api_keys:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    headers = {'Content-Type': 'application/json'}
                    data = {"contents": [{"parts": [{"text": final_prompt}]}]}
                    
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        try:
                            answer = result['candidates'][0]['content']['parts'][0]['text']
                        except: answer = "Antwort blockiert."

                        # Streaming
                        for chunk in answer.split():
                            full_text += chunk + " "
                            placeholder.markdown(full_text + "▌")
                            time.sleep(0.03)
                        
                        placeholder.markdown(full_text)
                        st.session_state.messages.append({"role": "model", "content": full_text})
                        success = True
                        break 
                except: continue
            
        if not success:
            st.error("⚠️ Verbindung fehlgeschlagen.")
