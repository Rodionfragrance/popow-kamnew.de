import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Business-Hub", page_icon="🧙‍♂️", layout="wide")

# --- CSS ---
st.markdown("""
<style>
.footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: black; text-align: center; padding: 10px; font-size: 12px;}
.stChatInput {position: fixed; bottom: 50px;}
</style>
<div class="footer">Olfazeta Business Intelligence Tool - Powered by Gemini 2.5 AI</div>
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
    except Exception as e:
        return None

db = load_data()
if not db:
    st.error("Datenbank fehlt auf GitHub!")
    st.stop()

# --- WEB SUCHE ---
def get_trend_info(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} Duftnoten Beschreibung", max_results=1))
            return results[0]['body'] if results else ""
    except: return ""

# --- CHAT ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption("Dein KI-Partner für Vertrieb & Strategie.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Frag mich nach Düften (Olfazeta Nummern), Upsells oder Business-Regeln."}]

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
        with st.status("Prüfe Duftnoten...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Check fertig.", state="complete")

    # --- INTELLIGENTER PROMPT (NO-BRAND MODE) ---
    system_instruction = f"""
    Du bist Rodion, Elite-Mentor für Olfazeta.
    
    WISSEN:
    1. PRODUKTE (CSV): {db['csv']}
    2. BUSINESS (TXT): {db['business']}
    3. EXTERNE INFOS: {web_context}

    DIE WICHTIGSTE REGEL (MARKENRECHT):
    - Wenn der User nach einer Fremdmarke fragt (z.B. "Baccarat Rouge", "Dior"), darfst du diesen Namen in deiner Antwort **NICHT** als Produktnamen verwenden.
    - Du sagst STATTDESSEN: "Ich habe da unsere **Nr. 118**. Die trifft genau diese orientalisch-blumige Duftrichtung."
    - Benutze NIEMALS Formulierungen wie "Inspiriert von..." oder "Das ist der Zwilling von...". 
    - Sag immer: "Geht in die Richtung von..." oder "Hat denselben Vibe wie...".

    UPSELLING:
    - Wenn in der CSV bei 'Upsell_Info' etwas steht (z.B. Duschgel), biete es IMMER an!
    - Beispiel: "Dazu passt perfekt unser Luxus-Duschgel für 18,90 €."

    FORMAT:
    - Sei kurz und knackig.
    - Preise immer **fett**.

    Antworte auf: "{prompt}"
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_instruction)
        history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        
        with st.chat_message("model"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "model", "content": response.text})

    except Exception as e:
        st.error(f"Fehler: {e}")
