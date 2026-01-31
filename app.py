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
        
        # --- PROMPT MIT MARKENSCHUTZ ---
        system_text = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        DATEN: {db['csv'] if db else ''} {db['business'] if db else ''}.
        
        REGELN:
        1. Nenne NIEMALS Fremdmarken (Dior, Chanel etc.)! Die Spalte "Original_Marke" ist geheim.
        2. Sag: "Das ist unsere Nr. XY, eine tolle Alternative..."
        3. Preise fett.
        """
        
        final_prompt = f"{system_text}\n\nUSER FRAGE: {prompt}"

        # --- DIE DIREKTE API ANBINDUNG (Ohne Bibliothek) ---
        success = False
        
        # Wir nutzen 'gemini-1.5-flash', weil es schnell ist und hohe Limits hat
        model_name = "gemini-1.5-flash"
        
        # Keys mischen
        random.shuffle(api_keys)
        
        for key in api_keys:
            try:
                # Das ist der direkte Link zu Google (funktioniert immer)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                
                headers = {'Content-Type': 'application/json'}
                data = {
                    "contents": [{
                        "parts": [{"text": final_prompt}]
                    }]
                }
                
                # Wir senden die Post per Internet (requests)
                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    # Erfolg! Daten auspacken
                    result_json = response.json()
                    answer = result_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # Streaming simulieren (für den Effekt)
                    for word in answer.split():
                        full_text += word + " "
                        placeholder.markdown(full_text + "▌")
                        time.sleep(0.05)
                    
                    placeholder.markdown(full_text)
                    st.session_state.messages.append({"role": "model", "content": full_text})
                    success = True
                    break
                else:
                    # Wenn Google Fehler meldet (z.B. 429 Limit), probieren wir den nächsten Key
                    # st.write(f"Key Error: {response.status_code}") # Debug
                    continue
                    
            except Exception as e:
                continue

        if not success:
            st.error("⚠️ Alle Keys sind aufgebraucht (Limit erreicht) oder gesperrt. Bitte erstelle morgen neue Keys oder nutze ein anderes Google Konto.")
            st.info("Hinweis: Der Server ist okay, aber Google lässt deine Keys gerade nicht durch.")
