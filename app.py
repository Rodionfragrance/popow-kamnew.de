import streamlit as st
import pandas as pd
from google import genai
import time
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- DESIGN ---
st.markdown("""
<style>
.stChatInput {position: fixed; bottom: 30px;}
.stChatMessageAvatar { background-color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- KEYS & DATEN ---
if "API_KEYS" in st.secrets:
    api_keys = st.secrets["API_KEYS"]
else:
    st.error("Bitte 'API_KEYS' in den Secrets anlegen!")
    st.stop()

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        with open("business_wissen.txt", "r", encoding="utf-8") as f:
            txt = f.read()
        return {"csv": df.to_string(index=False), "info": txt}
    except: return None

data = load_data()

# --- UI ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])

# --- CORE LOGIK ---
if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # System-Anweisung als reiner String (verhindert den Listen-Fehler)
        instruction = f"Du bist Rodion, Elite-Mentor. Daten: {data['csv']} {data['info']}. Regeln: Keine Fremdmarken. Preise fett."

        try:
            client = genai.Client(api_key=random.choice(api_keys))
            
            # Streaming ohne komplexe Config-Objekte
            response = client.models.generate_content_stream(
                model='gemini-1.5-flash',
                contents=prompt,
                config={'system_instruction': instruction}
            )
            
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    placeholder.markdown(full_text + "▌")
            
            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "model", "content": full_text})
            
        except Exception as e:
            st.error(f"Technischer Fehler: {e}")
