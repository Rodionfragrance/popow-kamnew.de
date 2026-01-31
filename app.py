import streamlit as st
import pandas as pd
import google.generativeai as genai
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

# --- KEY MANAGEMENT (Findet jeden Key) ---
raw_keys = None
if "API_KEYS" in st.secrets:
    raw_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets:
    raw_keys = st.secrets["GOOGLE_API_KEY"]
elif "api_keys" in st.secrets:
    raw_keys = st.secrets["api_keys"]

if not raw_keys:
    st.error("⚠️ Keine API-Keys gefunden! Bitte in Secrets prüfen.")
    st.stop()

# Sicherstellen, dass es eine Liste ist
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

# --- CHAT VERLAUF ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    icon = "🧙‍♂️" if msg["role"] == "model" else "👤"
    with st.chat_message(msg["role"], avatar=icon):
        st.markdown(msg["content"])

# --- CORE LOGIK ---
if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_response = ""
        
        # WICHTIG: System Instruction als einfacher String (verhindert den 'strip' Fehler der alten Lib)
        sys_instr = f"Du bist Rodion, Elite-Mentor. WISSEN: {db['csv'] if db else ''} {db['business'] if db else ''}. REGELN: Keine Fremdmarken. Preise fett."

        try:
            # Key setzen
            genai.configure(api_key=random.choice(api_keys))
            
            # Modell initialisieren (Alte Lib Syntax - Robust)
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=sys_instr)
            
            # Generierung (Ohne History-Objekt, direkt Prompt senden -> Maximale Stabilität)
            response = model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "model", "content": full_response})
            
        except Exception as e:
            # Fehler abfangen, falls Modell 404 wirft (Fallback auf Standard)
            if "404" in str(e):
                st.error("Modell nicht erreichbar. Versuche Neustart.")
            else:
                st.error(f"Technischer Fehler: {e}")
