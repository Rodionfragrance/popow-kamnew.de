import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS
import time

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

# --- MAIN HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption("Dein KI-Partner für Vertrieb & Strategie.")

# BUTTONS (Fehlersicher)
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
            status.update(label="Check fertig.", state="complete")

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

    # --- INTELLIGENTE FALLBACK LOGIK ---
    full_response = ""
    # Liste der Modelle, die wir nacheinander probieren (vom besten zum sparsamsten)
    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
    
    place_holder = st.empty()
    
    try:
        for model_name in models_to_try:
            try:
                # Versuch mit aktuellem Modell
                model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
                chat = model.start_chat(history=history)
                response = chat.send_message(prompt)
                full_response = response.text
                break # Erfolg! Schleife verlassen
            
            except Exception as e:
                if "429" in str(e):
                    # Wenn Limit erreicht, zeige Info und probiere nächstes Modell
                    st.toast(f"⚠️ Modell {model_name} ausgelastet. Schalte um...", icon="🔄")
                    time.sleep(2)
                    continue # Nächstes Modell in der Liste probieren
                else:
                    raise e # Anderer Fehler? Absturz.

        # --- AUSGABE ---
        if full_response:
            with st.chat_message("model", avatar="🧙‍♂️"):
                st.markdown(full_response)
            st.session_state.messages.append({"role": "model", "content": full_response})
        else:
            st.error("❌ Die KI lässt gerade keine Anfragen mehr zu. Probier es morgen wieder.")

    except Exception as e:
        st.error(f"Technischer Fehler: {e}")
