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
    st.error("⚠️ Keine Keys gefunden! Bitte API Keys in den Secrets hinterlegen.")
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
    st.error("Fehler: Datenbank fehlt auf GitHub!")
    st.stop()

# --- WEB SUCHE (Mit Sicherheits-Check) ---
def get_trend_info(query):
    try:
        # Wir suchen gezielt nach Kontext
        with DDGS() as ddgs:
            # max_results=2 reicht für Kontext, spart Zeit
            results = list(ddgs.text(f"{query} Parfüm Duftnoten Beschreibung Anlass", max_results=2))
            if results:
                # Wir geben die Zusammenfassung der ersten 2 Ergebnisse zurück
                return "\n".join([r['body'] for r in results])
            return ""
    except Exception as e:
        # Wenn die Suche fehlschlägt (Timeout/Block), geben wir leer zurück, damit der Chat nicht abstürzt
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

# --- CHAT VERLAUF ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Ich suche für dich auch im Web nach aktuellen Trends."}]

for message in st.session_state.messages:
    icon = "🧙‍♂️" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

# --- EINGABE ---
if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # --- 1. WEB RECHERCHE (Sichtbar) ---
    web_context = ""
    # Wir zeigen dem User, dass wir arbeiten
    with st.status("Rodion sucht das Passende für dich... 🧙‍♂️", expanded=False) as status:
        start_time = time.time()
        web_context = get_trend_info(prompt)
        duration = time.time() - start_time
        
        if web_context:
            status.update(label=f"Recherche abgeschlossen ({duration:.1f}s).", state="complete")
        else:
            status.update(label="Keine Web-Ergebnisse (nutze internes Wissen).", state="complete")

    # --- 2. KI ANTWORT ---
    system_instruction = f"""
    Du bist Rodion, Elite-Mentor für Olfazeta.
    
    QUELLEN:
    1. PRODUKTE (CSV): {db['csv']}
    2. WISSEN (TXT): {db['business']}
    3. WEB-RECHERCHE: {web_context}
    
    AUFGABE:
    - Kombiniere das Wissen aus der CSV mit den Infos aus der Web-Recherche.
    - Wenn die Web-Recherche Infos zu einem Anlass (z.B. "Candle Light") liefert, nutze diese, um das passende Parfüm in der CSV zu finden.
    - Priorität hat IMMER die CSV (verkaufe unsere Produkte!).
    
    REGELN:
    - Nenne NIE Fremdmarken (Dior, Chanel etc.) im Text. Sag "Riecht wie..." oder "Alternative zu...".
    - Sei gender-neutral ("Du").
    - Mach Preise **fett**.

    Antworte auf: "{prompt}"
    """

    with st.chat_message("model", avatar="🧙‍♂️"):
        message_placeholder = st.empty()
        full_response = ""
        success = False
        
        # Key Rotation (Load Balancing)
        for attempt in range(5):
            try:
                genai.configure(api_key=get_random_key())
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
                
                history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
                chat = model.start_chat(history=history)
                
                response_stream = chat.send_message(prompt, stream=True)
                
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
        st.error("⚠️ Server überlastet.")
