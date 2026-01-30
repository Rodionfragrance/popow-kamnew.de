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
.stChatMessage .stChatMessageAvatar {
    background-color: #ffffff !important;
}
</style>
<div class="footer">Olfazeta Business Intelligence Tool - Powered by Gemini AI</div>
""", unsafe_allow_html=True)

# --- MULTI-KEY HANDLING ---
if "API_KEYS" in st.secrets:
    api_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets:
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    st.error("⚠️ Keine API Keys gefunden!")
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
    except Exception as e:
        return None

db = load_data()
if not db:
    st.error("Datenbank fehlt!")
    st.stop()

# --- WEB SUCHE (TURBO: Nur bei Bedarf) ---
def get_trend_info(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} Duftnoten Beschreibung", max_results=1))
            return results[0]['body'] if results else ""
    except: return ""

# --- HEADER & BUTTONS ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption("Dein KI-Partner für Vertrieb & Strategie.")

col1, col2 = st.columns(2)
with col1:
    st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", icon="📱", use_container_width=True)
with col2:
    st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", icon="☕", use_container_width=True)

st.markdown("---")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Frag mich nach Düften oder Business."}]

for message in st.session_state.messages:
    icon = "🧙‍♂️" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # --- TURBO-MODUS ---
    # Wir suchen NUR im Web, wenn explizit danach gefragt wird, sonst nutzen wir nur die CSV (viel schneller!)
    web_context = ""
    if any(keyword in prompt.lower() for keyword in ["suche", "google", "info zu", "trend", "aktuell"]):
        with st.status("🔍 Recherche läuft...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Recherche beendet.", state="complete")

    # System-Prompt
    system_instruction = f"""
    Du bist Rodion, Elite-Mentor für Olfazeta.
    WISSEN:
    1. PRODUKTE (CSV): {db['csv']}
    2. BUSINESS (TXT): {db['business']}
    3. EXTERNE INFOS: {web_context}

    REGELN:
    - Markenschutz: Nenne NIE Fremdmarken im Text.
    - Ansprache: "Du", direkt, professionell.
    - Upsell: Immer anbieten.
    - Preise: **Fett**.

    Antworte auf: "{prompt}"
    """

    # --- ANTWORT GENERIEREN ---
    full_response = ""
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]
    
    # Lade-Animation anzeigen
    with st.spinner("Der Zauberer denkt nach... 🧙‍♂️"):
        try:
            for attempt in range(5): # 5 Versuche (Keys + Modelle)
                try:
                    current_key = get_random_key()
                    genai.configure(api_key=current_key)
                    
                    # Modellwahl: Beim 1. Versuch das Beste, dann Fallback
                    model_name = models_to_try[0] if attempt == 0 else models_to_try[1]
                    
                    model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                    history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
                    chat = model.start_chat(history=history)
                    
                    response = chat.send_message(prompt)
                    full_response = response.text
                    break 
                
                except Exception as e:
                    if "429" in str(e) or "404" in str(e) or "Quota" in str(e):
                        time.sleep(1) # Nur 1 Sekunde warten, dann Key wechseln
                        continue
                    else:
                        raise e

            if full_response:
                with st.chat_message("model", avatar="🧙‍♂️"):
                    st.markdown(full_response)
                st.session_state.messages.append({"role": "model", "content": full_response})
            else:
                st.error("⚠️ Hohe Auslastung. Bitte warten.")

        except Exception as e:
            st.error(f"Technischer Fehler: {e}")
