import streamlit as st
import pandas as pd
import requests
import json
import random
import time
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI DESIGN (CSS für schöne Optik) ---
st.markdown("""
<style>
.stChatInput {position: fixed; bottom: 30px;}
.stChatMessageAvatar { background-color: #ffffff !important; }
/* Vergrößert den Text und macht Abstände angenehmer */
.stMarkdown p { font-size: 16px; line-height: 1.6; margin-bottom: 15px; }
.stMarkdown h3 { color: #d32f2f; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- JAHRESZEIT ERMITTELN (AUTOMATISCH) ---
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

# Keys vorbereiten
keys_to_use = []
if isinstance(raw_input, str):
    if "," in raw_input: keys_to_use = [k.strip() for k in raw_input.split(",")]
    else: keys_to_use = [raw_input.strip()]
elif isinstance(raw_input, list):
    keys_to_use = raw_input

# Aggressive Reinigung
api_keys = []
for k in keys_to_use:
    clean = str(k).replace("'", "").replace('"', "").strip()
    if len(clean) > 20: api_keys.append(clean)

if not api_keys:
    st.error("⚠️ Keine gültigen Keys nach der Reinigung.")
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
st.caption(f"📅 Modus: {current_season} | 🚀 Status: Online") 
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
        
        # --- DER INTELLIGENTE PROMPT ---
        system_text = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        
        SITUATION:
        - Aktuelle Jahreszeit: {current_season} (WICHTIG! Beachte das bei der Duftwahl!)
        - Datenbank: {db['csv'] if db else ''} {db['business'] if db else ''}
        
        DEINE AUFGABE:
        Empfiehl passende Produkte. Achte darauf, dass sie zur Jahreszeit passen (z.B. im Sommer nichts zu Schweres, im Winter nichts zu Leichtes, außer der Kunde wünscht es explizit).
        
        REGELN FÜR DAS DESIGN (STRIKT EINHALTEN):
        1. Nutze KEINE langen Textblöcke. Mach viele Absätze.
        2. Nutze Emojis.
        3. MARKENSCHUTZ: Nenne NIEMALS Fremdmarken (Dior, Chanel etc.)! Sag "Unsere Nr. XY".
        4. PREISE: Immer **fett** markieren.
        
        STRUKTUR VORLAGE (Nutze exakt dieses Format):
        
        "Hier ist meine Empfehlung für dich [Anrede]:
        
        ### 🏆 Top-Favorit: Nr. [Nummer]
        * **Vibe:** [Beschreibung]
        * **Warum es passt:** [Begründung mit Bezug zur Jahreszeit {current_season}]
        * **Preis:** **[Preis] €**
        
        ### ✨ Alternative: Nr. [Nummer]
        * **Vibe:** [Beschreibung]
        * **Preis:** **[Preis] €**
        
        💡 **Pro-Tipp:** [Kurzer Tipp zur Anwendung]"
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
                        except: answer = "Sicherheitsfilter-Blockade."

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
