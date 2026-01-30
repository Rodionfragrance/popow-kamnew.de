import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS
import time

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
    data = {}
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        data["csv"] = df.to_string(index=False)
        with open("business_wissen.txt", "r", encoding="utf-8") as f:
            data["business"] = f.read()
    except Exception as e:
        return None
    return data

db = load_data()

if not db:
    st.error("FEHLER: Datenbank-Dateien (CSV/TXT) fehlen auf GitHub!")
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

    # Web-Check
    web_context = ""
    if not any(x in prompt.lower() for x in ["plan", "agb", "versand", "geld"]):
        with st.status("Analysiere Live-Trends...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Check fertig.", state="complete")

    # --- INTELLIGENTER PROMPT ---
    system_instruction = f"""
    Du bist Rodion, ein Elite-Mentor für Olfazeta.
    
    WISSEN:
    1. PRODUKTE (CSV): {db['csv']}
    2. BUSINESS (TXT): {db['business']}
    3. LIVE-WEB: {web_context}

    REGELN:
    - KUNDEN: Sei Sommelier. Empfiehl Klassiker & Geheimtipps (Mytologik/Event).
    - UPSELL: Wenn 'Upsell_Info' existiert, biete es an!
    - BUSINESS: Zitiere Regeln/Karriereplan exakt aus dem Text.
    - RECHT: Sag "Geht in die Richtung von" (NIE "Inspiriert von").
    - PREISE: Immer **fett**.

    Antworte auf: "{prompt}"
    """

    # --- ROBUSTE MODELL-AUSWAHL (Self-Healing) ---
    response_text = ""
    # Wir probieren diese Modelle nacheinander durch:
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    success = False
    error_log = []

    with st.spinner("Denke nach..."):
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                # Verlauf aufbauen
                history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
                chat = model.start_chat(history=history)
                response = chat.send_message(prompt)
                response_text = response.text
                success = True
                break # Wenn es klappt, brechen wir die Schleife ab
            except Exception as e:
                error_log.append(f"{model_name}: {str(e)}")
                continue # Nächstes Modell probieren

    if success:
        with st.chat_message("model"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "model", "content": response_text})
    else:
        st.error(f"Alle KI-Modelle sind gerade ausgelastet oder nicht erreichbar. Details: {error_log}")
