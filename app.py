import streamlit as st
import pandas as pd
import google.generativeai as genai
import random
import time

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- UI ---
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
st.markdown("---")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # SYSTEM PROMPT (Wir kleben das direkt an die Nachricht, das ist sicherer)
        system_text = f"""
        Du bist Rodion, Elite-Mentor für Olfazeta.
        DATEN: {db['csv'] if db else ''} {db['business'] if db else ''}.
        
        REGELN:
        1. Nenne NIEMALS Fremdmarken (Dior, Chanel etc.)!
        2. Sag: "Das ist unsere Nr. XY, riecht wie..."
        3. Preise fett.
        """
        
        # Kombinierter Prompt (Funktioniert mit jedem Modell)
        final_prompt = f"{system_text}\n\nUSER FRAGE: {prompt}"

        # --- DIE RETTUNGSKETTE (PRIORITÄTSLISTE) ---
        # Wir definieren harte Namen, die wir nacheinander testen
        models_to_try = [
            "gemini-1.5-flash",       # Der Schnelle (Prio 1)
            "gemini-1.5-flash-latest", # Der Neue Schnelle
            "gemini-1.5-pro",         # Der Schlaue
            "gemini-1.5-pro-latest",
            "gemini-pro"              # Der Alte Stabil (Prio Letzte)
        ]
        
        success = False
        used_model = ""

        # Wir probieren JEDES Modell mit JEDEM Key, bis eines klappt
        # Das ist die "Brechstangen"-Methode
        
        for model_name in models_to_try:
            if success: break # Wenn wir eine Antwort haben, hören wir auf
            
            # Keys mischen für Load Balancing
            random.shuffle(api_keys)
            
            for key in api_keys:
                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel(model_name)
                    
                    # Generierung starten
                    response = model.generate_content(final_prompt, stream=True)
                    
                    # Wenn wir hier sind, hat die Verbindung geklappt. Jetzt streamen.
                    for chunk in response:
                        if chunk.text:
                            full_text += chunk.text
                            placeholder.markdown(full_text + "▌")
                    
                    # Wenn Text da ist, war es erfolgreich
                    if len(full_text) > 5:
                        placeholder.markdown(full_text)
                        st.session_state.messages.append({"role": "model", "content": full_text})
                        success = True
                        used_model = model_name
                        break # Raus aus der Key-Schleife
                        
                except Exception:
                    # Wenn Key oder Modell nicht geht, einfach stillschweigend weitermachen
                    continue
        
        if not success:
            st.error("❌ Kritischer Fehler: Kein einziges Modell und kein Key hat funktioniert.")
            st.info("Bitte prüfe, ob deine API-Keys im Google AI Studio noch aktiv sind.")
        # else:
            # st.caption(f"Genutzt: {used_model}") # Nur zur Info, kann später weg
