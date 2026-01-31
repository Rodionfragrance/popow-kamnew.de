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
</style>
""", unsafe_allow_html=True)

# --- KEYS HOLEN ---
raw_keys = None
if "API_KEYS" in st.secrets: raw_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_keys = st.secrets["GOOGLE_API_KEY"]

if not raw_keys:
    st.error("⚠️ Keine Keys gefunden! Bitte Secrets prüfen.")
    st.stop()

if isinstance(raw_keys, str): api_keys = [raw_keys]
elif isinstance(raw_keys, list): api_keys = raw_keys
else: api_keys = []

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
        
        # --- PROMPT ---
        system_text = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        DATEN: {db['csv'] if db else ''} {db['business'] if db else ''}.
        
        REGELN:
        1. Nenne NIEMALS Fremdmarken (Dior, Chanel etc.)! Die Spalte "Original_Marke" ist geheim.
        2. Sag: "Das ist unsere Nr. XY, eine tolle Alternative..."
        3. Preise fett.
        """
        
        final_prompt = f"{system_text}\n\nUSER FRAGE: {prompt}"

        # --- DIE DIREKTE API ANBINDUNG (REST) ---
        success = False
        error_details = []
        
        # Wir probieren erst Flash (schnell), dann Pro (altes Modell als Backup)
        # Manchmal ist Flash leer, aber Pro hat noch Quote!
        models_to_test = ["gemini-1.5-flash", "gemini-pro"]
        
        # Keys mischen
        random.shuffle(api_keys)
        
        for model_name in models_to_test:
            if success: break
            
            for key in api_keys:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    headers = {'Content-Type': 'application/json'}
                    data = {"contents": [{"parts": [{"text": final_prompt}]}]}
                    
                    response = requests.post(url, headers=headers, json=data)
                    
                    if response.status_code == 200:
                        # Erfolg!
                        result_json = response.json()
                        try:
                            answer = result_json['candidates'][0]['content']['parts'][0]['text']
                        except:
                            # Manchmal blockiert der Sicherheitsfilter die Antwort
                            answer = "Entschuldigung, meine Antwort wurde vom Sicherheitsfilter blockiert. Bitte formuliere die Frage etwas anders."

                        # Streaming Effekt
                        for word in answer.split():
                            full_text += word + " "
                            placeholder.markdown(full_text + "▌")
                            time.sleep(0.05)
                        
                        placeholder.markdown(full_text)
                        st.session_state.messages.append({"role": "model", "content": full_text})
                        success = True
                        break
                    else:
                        # Fehler protokollieren (aber weitermachen)
                        error_details.append(f"Modell {model_name} mit Key ...{key[-4:]}: Code {response.status_code}")
                        continue
                        
                except Exception as e:
                    error_details.append(str(e))
                    continue

        if not success:
            st.error("⚠️ Limit erreicht.")
            with st.expander("Details für Rodion (Hier klicken)"):
                st.write(error_details)
                st.info("LÖSUNG: Erstelle ein 'Neues Projekt' in Google AI Studio und generiere dort einen frischen Key.")
