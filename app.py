import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Business-Hub", page_icon="🦁", layout="wide")

# --- CSS ---
st.markdown("""
<style>
.footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: black; text-align: center; padding: 10px; font-size: 12px;}
.stChatInput {position: fixed; bottom: 50px;}
</style>
<div class="footer">Olfazeta Business Intelligence Tool - Powered by Gemini AI</div>
""", unsafe_allow_html=True)

# --- API KEY HANDLING ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ API Key fehlt! Bitte in Streamlit Secrets hinterlegen.")
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
if not db:
    st.error("Datenbank fehlt auf GitHub!")
    st.stop()

# --- CHAT ---
st.title("🦁 Rodions Command Center")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Befehl eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Web-Suche
    web_context = ""
    try:
        with DDGS() as ddgs:
            r = list(ddgs.text(f"{prompt} Parfum Trend 2025", max_results=1))
            if r: web_context = r[0]['body']
    except: pass

    system_instruction = f"""
    Du bist Rodion, Mentor für Olfazeta.
    DATEN: {db['csv']}
    WISSEN: {db['business']}
    WEB: {web_context}
    Antworte kurz, direkt und fettgedruckte Preise.
    """

    # --- DIAGNOSE MODUS ---
    try:
        # Versuch 1: Standard Flash
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
        chat = model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"])
        response = chat.send_message(prompt)
        
        with st.chat_message("model"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "model", "content": response.text})

    except Exception as e:
        st.error(f"Fehler beim Zugriff auf Gemini: {e}")
        
        # DIAGNOSE: Was kann der Key überhaupt sehen?
        st.warning("🔍 Diagnose-Modus: Ich prüfe deinen API Key...")
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            st.code(f"Verfügbare Modelle für deinen Key:\n{available_models}")
            
            if not available_models:
                st.error("DEIN KEY HAT KEINEN ZUGRIFF AUF MODELLE. Erstelle einen neuen Key in einem neuen Google-Projekt.")
            else:
                st.info("Tipp: Kopiere einen der Namen oben (z.B. 'models/gemini-pro') und wir passen den Code an.")
                
        except Exception as debug_e:
            st.error(f"Kritischer Fehler: Dein Key scheint komplett ungültig zu sein. ({debug_e})")
