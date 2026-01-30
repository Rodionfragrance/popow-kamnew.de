import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS
import time
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- KEYS HOLEN ---
if "API_KEYS" in st.secrets:
    api_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets:
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    st.error("⚠️ Keine API-Keys gefunden! Bitte in Streamlit Secrets prüfen.")
    st.stop()

# --- DATEN LADEN ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        csv_text = df.to_string(index=False)
        with open("business_wissen.txt", "r", encoding="utf-8") as f:
            txt_text = f.read()
        return {"csv": csv_text, "business": txt_text}
    except: return None

db = load_data()

# --- HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
col1, col2 = st.columns(2)
with col1:
    st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
with col2:
    st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Was kann ich für dich tun?"}]

for message in st.session_state.messages:
    icon = "🧙‍♂️" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        message_placeholder = st.empty()
        full_response = ""
        web_info = ""

        # --- RADIKALER WEB-TIMEOUT (2 Sekunden) ---
        try:
            with DDGS(timeout=2) as ddgs:
                results = list(ddgs.text(f"{prompt} Parfüm Noten", max_results=1))
                if results:
                    web_info = results[0]['body']
        except:
            web_info = "" # Wenn es hakt, einfach ignorieren und weitermachen

        # SYSTEM PROMPT
        system_instruction = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        CSV-DATEN: {db['csv'] if db else 'Nicht verfügbar'}
        BUSINESS-WISSEN: {db['business'] if db else 'Nicht verfügbar'}
        WEB-INFO: {web_info}
        
        AUFGABE: Beantworte die Frage präzise. Nutze primär die CSV. 
        Nenne KEINE Fremdmarken. Preise fett.
        """

        # GENERIERUNG
        success = False
        for attempt in range(len(api_keys)):
            try:
                genai.configure(api_key=random.choice(api_keys))
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
                
                # Streaming starten
                response = model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "model", "content": full_response})
                success = True
                break
            except:
                time.sleep(1)
                continue
        
        if not success:
            st.error("⚠️ Aktuell keine Verbindung möglich. Bitte kurz warten.")
            
