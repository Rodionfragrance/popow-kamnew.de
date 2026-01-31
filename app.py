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

# --- KEY MANAGEMENT ---
# Wir suchen deine Keys überall
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

# Liste erzwingen
if isinstance(raw_keys, str):
    api_keys = [raw_keys]
elif isinstance(raw_keys, list):
    api_keys = raw_keys
else:
    st.error("Key-Format falsch.")
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
        sys_instr = f"Du bist Rodion, Elite-Mentor. WISSEN: {db['csv'] if db else ''} {db['business'] if db else ''}. REGELN: Keine Fremdmarken. Preise fett."

        # LISTE DER MODELLE (Die Rettungskette)
        # Wir probieren sie der Reihe nach durch
        models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
        
        success = False
        
        # Versuchsschleife: Keys UND Modelle rotieren
        for model_name in models_to_try:
            if success: break
            
            # Wir versuchen jeden Key einmal pro Modell
            current_key = random.choice(api_keys)
            
            try:
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel(model_name, system_instruction=sys_instr)
                
                # Generierung
                response = model.generate_content(prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        placeholder.markdown(full_response + "▌")
                
                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "model", "content": full_response})
                success = True # Geschafft!
                
            except Exception as e:
                # Wenn 404 kommt (Modell nicht gefunden), probieren wir sofort das nächste Modell in der Liste
                continue

        if not success:
            st.error("⚠️ Alle KI-Modelle sind gerade nicht erreichbar. Bitte lade die Seite neu (Reboot).")
