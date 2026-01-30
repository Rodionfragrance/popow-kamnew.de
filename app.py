import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS
import time
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- CSS (Optik) ---
st.markdown("""
<style>
.footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: black; text-align: center; padding: 10px; font-size: 12px;}
.stChatInput {position: fixed; bottom: 50px;}
.stChatMessage .stChatMessageAvatar {
    background-color: #ffffff !important;
}
</style>
<div class="footer">Olfazeta Business Intelligence Tool - Powered by Gemini AI</div>
""", unsafe_allow_html=True)

# --- KEYS HOLEN ---
if "API_KEYS" in st.secrets:
    api_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets:
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    st.error("⚠️ Keine Keys gefunden!")
    st.stop()

def get_random_key():
    return random.choice(api_keys)

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
if not db:
    st.error("Datenbank fehlt!")
    st.stop()

# --- WEB SUCHE (Robust) ---
def get_trend_info(query):
    try:
        # Nur suchen, wenn die Anfrage lang genug ist (vermeidet unnötige Wartezeit bei "Hallo")
        if len(query.split()) < 2: 
            return ""
            
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} Duftnoten Parfüm Beschreibung", max_results=1))
            if results:
                return results[0]['body']
            return ""
    except:
        return ""

# --- HEADER & BUTTONS ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption("Dein KI-Partner für Vertrieb & Strategie.")

col1, col2 = st.columns(2)
with col1:
    st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
with col2:
    st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)

st.markdown("---")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit."}]

for message in st.session_state.messages:
    icon = "🧙‍♂️" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # --- ANTWORT GENERIEREN ---
    # Hier zeigen wir den Lade-Text an, während im Hintergrund gearbeitet wird
    with st.spinner("Rodion sucht das Passende für dich... 🧙‍♂️"):
        
        # 1. Web Context holen (dauert 1-2 Sek)
        web_context = get_trend_info(prompt)

        # 2. Prompt bauen
        system_instruction = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        
        DEIN WISSEN:
        1. PRODUKT-DATENBANK (CSV): {db['csv']}
        2. BUSINESS-GUIDE (TXT): {db['business']}
        3. ZUSATZ-INFOS (WEB): {web_context}

        DEINE AUFGABE:
        - Finde in der CSV das passende Parfüm.
        - Nutze Web-Infos nur für Kontext (z.B. was ist ein "Candle Light Konzert").
        
        REGELN:
        - Nenne NIE Fremdmarken (Dior, Chanel etc.) im Text. Sag "Riecht wie..." oder "Alternative zu...".
        - Sei gender-neutral ("Du").
        - Mach Preise **fett**.

        Antworte auf: "{prompt}"
        """

        # 3. KI Abfragen (Load Balancing)
        full_response = ""
        success = False
        
        for attempt in range(5):
            try:
                genai.configure(api_key=get_random_key())
                # Modell: 1.5 Flash ist das schnellste
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
                
                history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
                chat = model.start_chat(history=history)
                
                # Streaming starten (Hier endet der Spinner, sobald das erste Wort da ist)
                response_stream = chat.send_message(prompt, stream=True)
                
                # Wir verlassen den Spinner-Block und zeigen die Nachricht an
                with st.chat_message("model", avatar="🧙‍♂️"):
                    message_placeholder = st.empty()
                    for chunk in response_stream:
                        if chunk.text:
                            full_response += chunk.text
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                
                success = True
                break 
            
            except Exception as e:
                time.sleep(1)
                continue

    if success:
        st.session_state.messages.append({"role": "model", "content": full_response})
    else:
        st.error("⚠️ Der Server ist gerade überlastet. Bitte warte einen Moment und klicke nochmal auf Senden.")
