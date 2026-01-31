import streamlit as st
import pandas as pd
import requests
import json
import random
import time

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI DESIGN ---
st.markdown("""
<style>
.stChatInput {position: fixed; bottom: 30px;}
.stChatMessageAvatar { background-color: #ffffff !important; }
/* Macht die Ausgabe lesbarer */
.stMarkdown { font-size: 16px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

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
        
        # --- DER NEUE DESIGN-PROMPT ---
        system_text = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        DATEN: {db['csv'] if db else ''} {db['business'] if db else ''}.
        
        DEINE AUFGABE:
        Berate den Kunden kurz, knackig und visuell ansprechend.
        
        VISUELLE REGELN (WICHTIG):
        1. Nutze NIEMALS Blocktext. Mach Absätze!
        2. Nutze Listenpunkte ( - ) für Produkte.
        3. Nutze Überschriften mit ### für Struktur.
        4. Mache Preise und Nummern immer **fett**.
        
        INHALTLICHE REGELN:
        1. MARKENSCHUTZ: Nenne NIEMALS die Namen aus der Spalte 'Original_Marke' oder 'Inspiriert von' (kein Dior, Chanel, etc.)!
        2. VERKAUF: Sag "Das ist unsere **Nr. XY**".
        
        Beispiel-Format:
        ### 🌟 Meine Top-Empfehlung
        - **Nr. XY**: Ein warmer Duft...
        - **Vibe**: Männlich, stark...
        - **Preis**: **30,00 €**
        
        ### 💡 Alternative
        - **Nr. AB**: ...
        """
        final_prompt = f"{system_text}\n\nUSER FRAGE: {prompt}"

        # --- VERBINDUNG ---
        success = False
        
        models_to_try = [
            "gemini-2.0-flash", 
            "gemini-flash-latest", 
            "gemini-pro-latest"
        ]

        random.shuffle(api_keys)
        
        for model_name in models_to_try:
            if success: break
            
            for key in api_keys:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    headers = {'Content-Type': 'application/json'}
                    data = {
                        "contents": [{"parts": [{"text": final_prompt}]}]
                    }
                    
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        try:
                            answer = result['candidates'][0]['content']['parts'][0]['text']
                        except: 
                            answer = "Sicherheitsfilter hat die Antwort blockiert."

                        # Streaming
                        for chunk in answer.split():
                            full_text += chunk + " "
                            placeholder.markdown(full_text + "▌")
                            time.sleep(0.03)
                        
                        placeholder.markdown(full_text)
                        st.session_state.messages.append({"role": "model", "content": full_text})
                        success = True
                        break 
                    
                except Exception:
                    continue
            
        if not success:
            st.error("⚠️ Verbindung fehlgeschlagen.")
