import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS
import time
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- CSS ---
st.markdown("""
<style>
.footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: black; text-align: center; padding: 10px; font-size: 12px;}
.stChatInput {position: fixed; bottom: 50px;}
.stChatMessage .stChatMessageAvatar { background-color: #ffffff !important; }
</style>
<div class="footer">Olfazeta Business Intelligence Tool - Powered by Gemini AI</div>
""", unsafe_allow_html=True)

# --- KEYS ---
if "API_KEYS" in st.secrets:
    api_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets:
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    st.error("⚠️ Keine API-Keys in den Secrets gefunden!")
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

# --- WEB SUCHE (Sicherheits-Variante) ---
def get_web_info(query):
    try:
        # Timeout nach 4 Sekunden, falls die Suche hängt
        with DDGS(timeout=4) as ddgs:
            results = list(ddgs.text(f"{query} Parfüm Noten", max_results=2))
            return "\n".join([r['body'] for r in results]) if results else ""
    except:
        return ""

# --- HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
col1, col2 = st.columns(2)
with col1:
    st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
with col2:
    st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Was kann ich für dich tun?"}]

for message in st.session_state.messages:
    icon = "🧙‍♂️" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # --- DER TRICK: ASYNCHRONE OPTIK ---
    # Wir zeigen den Spinner, aber begrenzen die Suche radikal
    with st.chat_message("model", avatar="🧙‍♂️"):
        message_placeholder = st.empty()
        
        with st.status("🧙‍♂️ Rodion analysiert...", expanded=False) as status:
            st.write("Prüfe interne Datenbank...")
            # Web-Suche nur ganz kurz versuchen
            web_info = get_web_info(prompt)
            status.update(label="Analyse abgeschlossen!", state="complete")

        full_response = ""
        # System-Instruction mit den verfügbaren Daten
        system_instruction = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        CSV-DATEN: {db['csv'] if db else 'Nicht verfügbar'}
        BUSINESS-WISSEN: {db['business'] if db else 'Nicht verfügbar'}
        ZUSATZ-WEB-INFO: {web_info}
        
        AUFGABE: Beantworte die Frage präzise. Nutze primär die CSV. 
        Wenn Web-Info da ist, nutze sie für den Vibe. 
        Nenne KEINE Fremdmarken. Preise **fett**.
        """

        # KEY ROTATION & GENERIERUNG
        for attempt in range(len(api_keys)):
            try:
                genai.configure(api_key=random.choice(api_keys))
                model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
                
                # Streaming für sofortiges Feedback
                response = model.generate_content(prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "model", "content": full_response})
                break
            except Exception as e:
                if attempt == len(api_keys) - 1:
                    st.error(f"Fehler: {str(e)}")
                else:
                    time.sleep(1)
                    continue
