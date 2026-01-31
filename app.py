import streamlit as st
import pandas as pd
import google.generativeai as genai
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI ---
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
elif "api_keys" in st.secrets: raw_keys = st.secrets["api_keys"]

if not raw_keys:
    st.error("⚠️ Keine Keys gefunden! Bitte Secrets prüfen.")
    st.stop()

# Formatierung sicherstellen
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
        
        # System-Wissen
        sys_instr = f"Du bist Rodion. WISSEN: {db['csv'] if db else ''} {db['business'] if db else ''}. Sei direkt."

        try:
            # 1. Key setzen
            genai.configure(api_key=random.choice(api_keys))
            
            # 2. AUTO-PILOT: Wir fragen Google, welche Modelle da sind
            available_models = []
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
            except Exception as e:
                st.error(f"Fehler beim Listen der Modelle: {e}")
                st.stop()
            
            # 3. Das beste verfügbare Modell auswählen
            # Wir bevorzugen Flash, dann Pro, dann irgendeins mit 'gemini'
            chosen_model = None
            if not available_models:
                st.error("❌ Keine Modelle verfügbar für diesen API Key.")
                st.stop()
                
            # Intelligente Auswahl
            for m in available_models:
                if "flash" in m and "1.5" in m: chosen_model = m; break
            if not chosen_model:
                for m in available_models:
                    if "pro" in m and "1.5" in m: chosen_model = m; break
            if not chosen_model:
                for m in available_models:
                    if "gemini" in m: chosen_model = m; break
            if not chosen_model:
                chosen_model = available_models[0] # Nimm einfach das Erste
            
            # Debug-Info (Kannst du später löschen)
            # st.caption(f"Nutze Modell: {chosen_model}") 

            # 4. Generieren mit dem gefundenen Modell
            model = genai.GenerativeModel(chosen_model) # Alte Syntax (stabil)
            
            # Trick: Instruction in den Prompt packen, das verstehen alle Modelle
            final_prompt = f"{sys_instr}\n\nUSER FRAGE: {prompt}"
            
            response = model.generate_content(final_prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_text += chunk.text
                    placeholder.markdown(full_text + "▌")
            
            placeholder.markdown(full_text)
            st.session_state.messages.append({"role": "model", "content": full_text})
            
        except Exception as e:
            st.error(f"Kritischer Fehler: {e}")
            if "404" in str(e):
                st.info("Tipp: API Key könnte ungültig sein oder keinen Zugriff auf Modelle haben.")
