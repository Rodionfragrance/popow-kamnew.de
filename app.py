import streamlit as st
import pandas as pd
from google import genai
import time
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI DESIGN ---
st.markdown("""
<style>
.stChatInput {position: fixed; bottom: 30px;}
.stChatMessageAvatar { background-color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- INTELLIGENTES KEY-MANAGEMENT ---
# Wir prüfen alle möglichen Schreibweisen und Formate
raw_keys = None

if "API_KEYS" in st.secrets:
    raw_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets:
    raw_keys = st.secrets["GOOGLE_API_KEY"]
elif "api_keys" in st.secrets: # Falls kleingeschrieben
    raw_keys = st.secrets["api_keys"]

if not raw_keys:
    st.error("⚠️ Keine Keys gefunden! Bitte überprüfe die Secrets.")
    st.info("Erwartet wird: GOOGLE_API_KEY = ['key1', 'key2'] in den Secrets.")
    st.stop()

# Wir stellen sicher, dass es immer eine Liste ist (egal ob String oder Liste übergeben wurde)
if isinstance(raw_keys, str):
    api_keys = [raw_keys]
elif isinstance(raw_keys, list):
    api_keys = raw_keys
else:
    st.error("Format der Keys nicht erkannt.")
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
st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)
st.markdown("---")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    icon = "🧙‍♂️" if msg["role"] == "model" else "👤"
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_response = ""
        
        # System-Wissen
        sys_instr = f"Du bist Rodion, Elite-Mentor für Olfazeta. WISSEN: {db['csv'] if db else ''} {db['business'] if db else ''}. REGELN: Nenne NIE Fremdmarken. Preise fett. Sei direkt."

        try:
            # Zufälligen Key aus deiner Liste wählen
            chosen_key = random.choice(api_keys)
            client = genai.Client(api_key=chosen_key)
            
            response = client.models.generate_content_stream(
                model='gemini-1.5-flash',
                contents=prompt,
                config={'system_instruction': sys_instr}
            )
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "model", "content": full_response})
            
        except Exception as e:
            st.error(f"Technischer Fehler: {e}")
