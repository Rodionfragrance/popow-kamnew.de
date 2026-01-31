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
elif "api_keys" in st.secrets: raw_keys = st.secrets["api_keys"]

if not raw_keys:
    st.error("⚠️ Keine Keys gefunden! Bitte Secrets prüfen.")
    st.stop()

# Sicherstellen, dass wir eine Liste haben
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

# --- CHAT VERLAUF ---
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
        
        # SYSTEM PROMPT (Mit Markenschutz & Verkaufsturbo)
        sys_instr = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        
        DATENBANK:
        1. PRODUKTE: {db['csv'] if db else ''}
        2. BUSINESS: {db['business'] if db else ''}

        🔴 REGEL 1 (MARKENSCHUTZ):
        Du kennst die Original-Marken aus der CSV, aber du darfst sie NIEMALS nennen.
        Sag statt "Riecht wie Dior Sauvage": "Das ist unsere **Nr. XY**. Ein frischer, wilder Duft..."
        
        🔴 REGEL 2 (VERKAUF):
        Sei überzeugt. Preise immer **fett**. Nutze Emojis.
        """

        # --- DIE ROTATION (Der Trick gegen 429 Fehler) ---
        success = False
        last_error = ""
        
        # Wir mischen die Keys, damit nicht immer Key 1 belastet wird
        random.shuffle(api_keys)
        
        # Wir probieren JEDEN Key in deiner Liste durch, bis einer geht
        for key in api_keys:
            try:
                genai.configure(api_key=key)
                
                # HIER IST DER FIX: Wir zwingen ihn auf das Modell 'gemini-1.5-flash'
                # Dieses Modell hat 1.500 Anfragen pro Tag (statt 20)
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=sys_instr)
                
                response = model.generate_content(prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_text += chunk.text
                        placeholder.markdown(full_text + "▌")
                
                placeholder.markdown(full_text)
                st.session_state.messages.append({"role": "model", "content": full_text})
                success = True
                break # Wenn es geklappt hat, hören wir auf zu suchen
                
            except Exception as e:
                # Wenn Key leer ist (429), merken wir uns das und probieren SOFORT den nächsten
                last_error = str(e)
                time.sleep(0.5) # Kurze Atempause für den Server
                continue 

        if not success:
            st.error(f"Alle 5 Keys sind gerade ausgelastet oder das Modell spinnt. Fehler: {last_error}")
            st.info("Tipp: Warte 1 Minute. Wenn das öfter passiert, brauchen wir mehr Keys.")
