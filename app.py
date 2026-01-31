import streamlit as st
import pandas as pd
import requests
import json
import random
import time
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI DESIGN ---
st.markdown("""
<style>
/* 1. PLATZ HALTER UNTEN */
.main .block-container {
    padding-bottom: 120px !important; 
}

/* 2. EINGABEFELD STYLEN */
[data-testid="stChatInput"] {
    border-radius: 20px !important;
    border: 1px solid #e0e0e0 !important;
}

/* 3. AVATARE */
.stChatMessageAvatar { background-color: #ffffff !important; }

/* 4. TEXT-FORMATIERUNG */
.stMarkdown p {
    font-size: 16px !important;
    line-height: 1.8 !important;
    margin-bottom: 25px !important;
}
.stMarkdown h3 {
    color: #d32f2f !important; 
    margin-top: 40px !important;
    margin-bottom: 15px !important;
    border-bottom: 1px solid #eee; 
    padding-bottom: 5px;
}
.stMarkdown hr {
    margin-top: 30px !important;
    margin-bottom: 30px !important;
    border-color: #f0f0f0;
}
</style>
""", unsafe_allow_html=True)

# --- JAHRESZEIT ---
def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]: return "Winter ❄️"
    elif month in [3, 4, 5]: return "Frühling 🌷"
    elif month in [6, 7, 8]: return "Sommer ☀️"
    else: return "Herbst 🍂"

current_season = get_current_season()

# --- KEYS ---
raw_input = None
if "API_KEYS" in st.secrets: raw_input = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_input = st.secrets["GOOGLE_API_KEY"]

if not raw_input:
    st.error("⚠️ Keine Keys gefunden! Bitte Secrets prüfen.")
    st.stop()

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

# --- DATEN ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        return {"csv": df.to_string(index=False), "business": open("business_wissen.txt", "r", encoding="utf-8").read()}
    except: return None

db = load_data()

# --- HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption(f"📅 Saison: {current_season} | 🚀 Dein KI-Mentor für Strategie & Verkauf | 🌍 Multi-Language Mentor") 

st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)
st.markdown("---")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Frage eingeben (Beratung, Business, egal)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # --- DER "MAX 5 OPTIONEN" PROMPT ---
        system_text = f"""
        🚨 OBERSTE SICHERHEITSDIREKTIVE:
        Du darfst NIEMALS Markennamen aus der Spalte "Original_Marke" oder "Inspiriert_Von" (wie Creed, Armani, Tom Ford) nennen. 
        Ausnahme: Die Eigenmarke "Mytologik" darfst und sollst du nennen!
        Nenne sonst NUR die Chogan-Nummer (z.B. "Nr. 68").
        
        ---
        
        ZIEL: MAXIMALER WARENKORBWERT (High-Ticket-First) & AUSWAHL BIETEN.
        
        VERKAUFS-LOGIK:
        1. Identifiziere ALLE Produkte, die *perfekt* zur Anfrage passen.
        2. Sortiere diese Liste nach PREIS (Teuerste/Mytologik zuerst).
        3. Präsentiere alle TOP-Treffer (bis zu 5 Stück). Wenn nur 2 passen, zeig 2. Wenn 5 passen, zeig 5.
        
        SPRACHE:
        Antworte IMMER in der exakt gleichen Sprache wie der Nutzer!
        
        LAYOUT-PFLICHT:
        - Nutze `---` als Trennlinie zwischen JEDEM Produkt.
        - Mach DOPPELTE ABSÄTZE nach jedem Punkt für Lesbarkeit.
        
        STRUKTUR-VORGABE (Wiederhole diesen Block für jedes passende Produkt, max. 5x):
        
        "Hier sind alle Top-Optionen (sortiert nach Umsatz-Potenzial):
        
        ---
        
        ### 🏆 Option 1 (Premium): [Name/Nummer]
        **Argument:** "[Satz über Luxus & Exklusivität]"
        💰 **Preis:** **[Preis] €**
        
        ---
        
        ### ✨ Option 2: [Name/Nummer]
        **Argument:** "[Satz über den Vibe]"
        💰 **Preis:** **[Preis] €**
        
        ---
        
        [Füge hier weitere Optionen (3, 4, 5) ein, falls sie PERFEKT passen]
        
        ---
        
        ### 🛍️ Cross-Selling (Pflicht):
        [Lies die Spalte 'Upsell_Info' für den gewählten Duft. Wenn dort z.B. 'Passendes Duschgel' steht, empfiehl GENAU DAS.]
        
        ---
        
        ### ❓ Abschlussfrage:
        [Frage den Kunden, welche Richtung ihm am meisten zusagt.]"
        """
        
        final_prompt = f"{system_text}\n\nEINGABE DES BERATERS: {prompt}"

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
