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

# --- API KEY HANDLING (Secrets) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ API Key fehlt! Bitte in Streamlit Secrets hinterlegen.")
    st.stop()

# --- DATEN LADEN ---
@st.cache_data
def load_data():
    data = {}
    try:
        # CSV laden (Semikolon-getrennt)
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        data["csv"] = df.to_string(index=False)
        
        # Business Wissen laden
        with open("business_wissen.txt", "r", encoding="utf-8") as f:
            data["business"] = f.read()
    except Exception as e:
        return None
    return data

db = load_data()

if not db:
    st.error("FEHLER: Datenbank-Dateien nicht gefunden!")
    st.stop()

# --- LIVE WEB SUCHE ---
def get_trend_info(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} Parfum Trend Erfahrung 2025", max_results=2))
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results]) if results else ""
    except: return ""

# --- CHAT ---
st.title("🦁 Rodions Command Center")
st.caption("Dein KI-Partner für Vertrieb & Strategie.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Frag mich nach Düften, Upsells oder Business-Regeln."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Befehl eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Web-Check nur bei Produktfragen
    web_context = ""
    if not any(x in prompt.lower() for x in ["plan", "agb", "versand", "geld"]):
        with st.status("Analysiere Live-Trends...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Check fertig.", state="complete")

    # --- GEMINI PROMPT ---
    system_instruction = f"""
    Du bist Rodion, ein Elite-Mentor für Olfazeta.
    
    WISSEN:
    1. PRODUKTE (CSV): {db['csv']}
    2. BUSINESS (TXT): {db['business']}
    3. LIVE-WEB: {web_context}

    REGELN:
    - KUNDEN: Wenn jemand einen Duft sucht, sei ein Sommelier. Biete 1-2 Optionen (Klassiker & Geheimtipp).
    - UPSELL: Wenn in der CSV 'Upsell_Info' steht, MUSST du es anbieten ("Dazu passt perfekt...").
    - BUSINESS: Bei Fragen zu Regeln/Geld zitiere nur das Business-Wissen.
    - RECHT: Sag NIE "Inspiriert von". Sag "Geht in die Richtung von".
    - PREISE: Immer **fett**.

    Antworte auf: "{prompt}"
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
        chat = model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"])
        response = chat.send_message(prompt)
        
        with st.chat_message("model"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "model", "content": response.text})
        
    except Exception as e:
        st.error(f"Fehler: {e}")
