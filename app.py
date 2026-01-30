import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

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
        data = {}
        # 1. Produkte
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        data["csv"] = df.to_string(index=False)
        
        # 2. Business Wissen (Basis)
        with open("business_wissen.txt", "r", encoding="utf-8") as f:
            data["business"] = f.read()
            
        # 3. Network Bibel (Go Pro & 5x5) - NEU!
        try:
            with open("network_bible.txt", "r", encoding="utf-8") as f:
                data["bible"] = f.read()
        except:
            data["bible"] = "Keine Experten-Daten gefunden."
            
        return data
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
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Frag mich nach Düften, Produkten, Strategien oder Wissen."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Befehl eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Web-Check
    web_context = ""
    if not any(x in prompt.lower() for x in ["plan", "agb", "versand", "geld", "eric", "worre", "strategie"]):
        with st.status("Prüfe Duftnoten...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Check fertig.", state="complete")

    # --- SYSTEM PROMPT ---
    system_instruction = f"""
    Du bist Rodion, Elite-Mentor für Olfazeta.
    
    DEIN WISSEN:
    1. PRODUKTE: {db['csv']}
    2. REGELN & PLAN: {db['business']}
    3. EXPERTEN-STRATEGIE (Go Pro / 5x5): {db.get('bible', '')}
    4. WEB-INFOS: {web_context}

    🔴 REGEL NR. 1: MARKEN-SCHUTZ
    - Nutze "Original_Marke" nur intern. Nenne sie NIE im Chat.
    - Sag: "Wenn du diesen Vibe suchst, nimm Nr. XY."

    🔴 REGEL NR. 2: ANSPRACHE
    - Gender-neutral ("Du", keine "Bruder"-Floskeln).
    - Professionell, direkt, motivierend.

    COACHING-MODUS:
    - Wenn der User Probleme beim Recruiting hat, nutze das Wissen aus der "Network Bibel" (Eric Worre / 5x5).
    - Zitiere Strategien: "Wie Eric Worre sagt: Sei ein Farmer..." oder "Denk an die 5x5 Regel..."

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
