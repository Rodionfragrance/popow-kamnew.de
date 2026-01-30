import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS
import time
import random  # WICHTIG für das Zufalls-Roulette

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

# --- MULTI-KEY HANDLING (Das Load-Balancing) ---
# Wir holen die Liste aus den Secrets
if "API_KEYS" in st.secrets:
    api_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets:
    # Fallback, falls nur ein Key da ist
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    st.error("⚠️ Keine API Keys gefunden! Bitte in Secrets hinterlegen.")
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
    st.error("Datenbank fehlt auf GitHub!")
    st.stop()

# --- WEB SUCHE ---
def get_trend_info(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} Duftnoten Beschreibung", max_results=1))
            return results[0]['body'] if results else ""
    except: return ""

# --- MAIN HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption("Dein KI-Partner für Vertrieb & Strategie.")

# BUTTONS
col1, col2 = st.columns(2)
with col1:
    st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
with col2:
    st.link_button("☕ Spendier mir einen Kaffee", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)

st.markdown("---")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Frag mich nach Düften, Produkten oder Business-Strategien."}]

for message in st.session_state.messages:
    icon = "🧙‍♂️" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Web-Check
    web_context = ""
    if not any(x in prompt.lower() for x in ["plan", "agb", "versand", "geld", "start", "einwand"]):
        with st.status("Prüfe Duftnoten...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Denke nach. Bitte warten.", state="complete")

    # System-Prompt
    system_instruction = f"""
    Du bist Rodion, Elite-Mentor für Olfazeta.
    WISSEN:
    1. PRODUKTE (CSV): {db['csv']}
    2. BUSINESS (TXT): {db['business']}
    3. EXTERNE INFOS: {web_context}

    REGELN:
    - Markenschutz: Nutze "Original_Marke" nur intern. Nenne NIE Fremdmarken im Text.
    - Ansprache: "Du", direkt, professionell, gender-neutral.
    - Upsell: Immer anbieten.
    - Preise: **Fett**.

    Antworte auf: "{prompt}"
    """

    # --- INTELLIGENTE LOAD-BALANCING LOGIK ---
    full_response = ""
    # Echte, existierende Modelle
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]
    
    try:
        # Wir versuchen es bis zu 5 Mal mit verschiedenen Keys und Modellen
        for attempt in range(5):
            try:
                # 1. Zufälligen Key ziehen (Das ist der Trick!)
                current_key = get_random_key()
                genai.configure(api_key=current_key)
                
                # 2. Modell auswählen (Beim ersten Versuch das Beste, dann Fallback)
                model_name = models_to_try[0] if attempt == 0 else models_to_try[1]
                
                model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
                chat = model.start_chat(history=history)
                
                # 3. Feuer frei
                response = chat.send_message(prompt)
                full_response = response.text
                break # Erfolg!
            
            except Exception as e:
                error_msg = str(e)
                # Nur bei Überlastung oder 404 weitermachen
                if "429" in error_msg or "404" in error_msg or "Quota" in error_msg:
                    time.sleep(1)
                    continue # Nächster Versuch mit neuem Key!
                else:
                    raise e # Echter Fehler? Anzeigen.

        # --- AUSGABE ---
        if full_response:
            with st.chat_message("model", avatar="🧙‍♂️"):
                st.markdown(full_response)
            st.session_state.messages.append({"role": "model", "content": full_response})
        else:
            st.error("❌ Maximale Auslastung...Bitte warten.")

    except Exception as e:
        st.error(f"Technischer Fehler: {e}")
