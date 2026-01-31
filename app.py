import streamlit as st
import pandas as pd
import google.generativeai as genai
import random
import time

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI DESIGN ---
st.markdown("""
<style>
.stChatInput {position: fixed; bottom: 30px;}
.stChatMessageAvatar { background-color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- KEYS HOLEN ---
raw_keys = None
if "API_KEYS" in st.secrets: raw_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_keys = st.secrets["GOOGLE_API_KEY"]
elif "api_keys" in st.secrets: raw_keys = st.secrets["api_keys"]

if not raw_keys:
    st.error("⚠️ Keine Keys gefunden! Bitte Secrets prüfen.")
    st.stop()

# Formatierung sicherstellen
if isinstance(raw_keys, str): api_keys = [raw_keys]
elif isinstance(raw_keys, list): api_keys = raw_keys
else: api_keys = []

# --- DATEN LADEN ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        return {"csv": df.to_string(index=False), "business": open("business_wissen.txt", "r", encoding="utf-8").read()}
    except: return None

db = load_data()

# --- HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)

# --- AUTOMATISCHER MODELL-FINDER (Der Fix) ---
# Wir suchen einmal beim Start das beste Modell, das dein Key erlaubt
@st.cache_resource
def find_best_model():
    # Wir probieren Keys durch, bis wir eine Modell-Liste bekommen
    for key in api_keys:
        try:
            genai.configure(api_key=key)
            found_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    found_models.append(m.name)
            
            if not found_models: continue

            # Intelligente Auswahl: Wir suchen Flash, dann Pro
            best = None
            for m in found_models:
                if "flash" in m and "1.5" in m: best = m; break
            if not best:
                for m in found_models:
                    if "pro" in m and "1.5" in m: best = m; break
            if not best:
                for m in found_models:
                    if "gemini-pro" in m: best = m; break
            if not best:
                best = found_models[0] # Nimm einfach das erste
            
            return best
        except:
            continue
    return "gemini-pro" # Fallback, falls alles scheitert

# Das gefundene Modell speichern wir
active_model_name = find_best_model()

# --- DEBUG INFO (Damit wir sehen, was läuft) ---
# st.caption(f"🤖 Aktiviertes Modell: `{active_model_name}`") # Kannst du später auskommentieren

st.markdown("---")

# --- CHAT VERLAUF ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])

# --- CORE LOGIK ---
if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # SYSTEM PROMPT (Mit Markenschutz)
        sys_instr = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        DATEN: {db['csv'] if db else ''} {db['business'] if db else ''}.
        
        REGELN:
        1. Nenne NIEMALS Fremdmarken (Dior, Chanel etc.) beim Namen!
        2. Sag: "Das ist unsere Nr. XY, riecht wie..."
        3. Preise fett.
        """

        # --- GENERIERUNG ---
        success = False
        
        # Wir mischen die Keys
        random.shuffle(api_keys)
        
        for key in api_keys:
            try:
                genai.configure(api_key=key)
                
                # Wir nutzen das Modell, das wir oben gefunden haben
                model = genai.GenerativeModel(active_model_name)
                
                # Trick: System-Instruction direkt in den Prompt, falls das Modell alt ist
                final_prompt = f"{sys_instr}\n\nUSER FRAGE: {prompt}"
                
                response = model.generate_content(final_prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_text += chunk.text
                        placeholder.markdown(full_text + "▌")
                
                placeholder.markdown(full_text)
                st.session_state.messages.append({"role": "model", "content": full_text})
                success = True
                break 
                
            except Exception as e:
                time.sleep(0.5)
                continue 

        if not success:
            st.error(f"Konnte keine Verbindung herstellen. Modell: {active_model_name}")
