import streamlit as st
import pandas as pd
import google.generativeai as genai
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
        
        # --- DER HARTE MARKENSCHUTZ-PROMPT ---
        system_text = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        DATEN: {db['csv'] if db else ''} {db['business'] if db else ''}.
        
        !!! WICHTIGE REGELN !!!
        1. MARKENSCHUTZ: In der Datenbank steht oft "Inspiriert von X". Du darfst diesen Namen "X" (z.B. Dior, Chanel, YSL) NIEMALS im Chat schreiben! Das ist verboten.
        2. VERKAUF: Nenne NUR unsere Nummer (z.B. "Nr. 20"). Beschreibe den Duft emotional.
        3. PREISE: Mach Preise immer **fett**.
        4. STIL: Sei kurz, direkt und motivierend.
        """
        
        # Wir kleben die Anweisung direkt an die Frage. Das versteht auch der alte Server.
        final_prompt = f"{system_text}\n\nUSER FRAGE: {prompt}"

        # --- MODEL: gemini-pro (Das läuft immer) ---
        model_name = "gemini-pro"
        
        success = False
        
        # Keys mischen und probieren
        random.shuffle(api_keys)
        
        for key in api_keys:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name)
                
                # Generierung
                response = model.generate_content(final_prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_text += chunk.text
                        placeholder.markdown(full_text + "▌")
                
                if len(full_text) > 0:
                    placeholder.markdown(full_text)
                    st.session_state.messages.append({"role": "model", "content": full_text})
                    success = True
                    break 
                        
            except Exception:
                time.sleep(0.5)
                continue
        
        if not success:
            st.error("⚠️ Selbst 'gemini-pro' antwortet nicht. Das liegt meist am Google-Tageslimit (429). Warte bis morgen oder nutze neue Keys.")
