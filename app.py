import streamlit as st
import pandas as pd
import requests
import random
import time

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI DESIGN ---
st.markdown("""
<style>
.stChatInput {position: fixed; bottom: 30px;}
.stChatMessageAvatar { background-color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- KEYS HOLEN & REINIGEN (WICHTIG!) ---
raw_keys = None
if "API_KEYS" in st.secrets: raw_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_keys = st.secrets["GOOGLE_API_KEY"]

if not raw_keys:
    st.error("⚠️ Keine Keys gefunden! Bitte Secrets prüfen.")
    st.stop()

if isinstance(raw_keys, str): raw_keys = [raw_keys]
elif not isinstance(raw_keys, list): raw_keys = []

# --- DIE WASCHMASCHINE FÜR KEYS ---
api_keys = []
for k in raw_keys:
    if isinstance(k, str):
        # Entfernt Leerzeichen, Zeilenumbrüche und versehentliche Anführungszeichen
        clean_key = k.strip().replace('"', '').replace("'", "").replace("\n", "")
        if len(clean_key) > 10: # Nur echte Keys behalten
            api_keys.append(clean_key)

if not api_keys:
    st.error("⚠️ Keine gültigen Keys nach der Reinigung übrig.")
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
        
        # PROMPT
        system_text = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        DATEN: {db['csv'] if db else ''} {db['business'] if db else ''}.
        REGELN: 1. KEINE Fremdmarken nennen! 2. Preise fett. 3. Sei direkt.
        """
        final_prompt = f"{system_text}\n\nUSER FRAGE: {prompt}"

        # --- INTELLIGENTE VERBINDUNG ---
        success = False
        debug_log = []
        
        # Wir testen verschiedene Adressen (Endpoints), falls eine 404 ist
        endpoints = [
            ("gemini-1.5-flash", "v1beta"), # Standard Neu
            ("gemini-1.5-flash", "v1"),     # Alternative Adresse
            ("gemini-pro", "v1beta"),       # Alt Stabil
            ("gemini-pro", "v1")            # Alt Alternative
        ]

        random.shuffle(api_keys)

        # Wir probieren erst alle Keys am besten Modell, dann alle Keys am zweitbesten...
        for model_name, version in endpoints:
            if success: break
            
            for key in api_keys:
                try:
                    url = f"https://generativelanguage.googleapis.com/{version}/models/{model_name}:generateContent?key={key}"
                    headers = {'Content-Type': 'application/json'}
                    data = {"contents": [{"parts": [{"text": final_prompt}]}]}
                    
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                    
                    if response.status_code == 200:
                        # TREFFER!
                        result = response.json()
                        try:
                            answer = result['candidates'][0]['content']['parts'][0]['text']
                        except: answer = "Ich habe eine Antwort, aber der Sicherheitsfilter hat sie blockiert."
                        
                        # Stream Output
                        for chunk in answer.split():
                            full_text += chunk + " "
                            placeholder.markdown(full_text + "▌")
                            time.sleep(0.04)
                        
                        placeholder.markdown(full_text)
                        st.session_state.messages.append({"role": "model", "content": full_text})
                        success = True
                        break
                    else:
                        debug_log.append(f"{model_name} ({version}): Code {response.status_code}")
                except Exception as e:
                    debug_log.append(f"Error: {str(e)}")
                    continue

        if not success:
            st.error("⚠️ Verbindung fehlgeschlagen.")
            with st.expander("Fehleranalyse anzeigen"):
                st.write(debug_log)
                st.write("Mögliche Ursachen: 404 = Key/Modell passt nicht zusammen. 429 = Limit.")
