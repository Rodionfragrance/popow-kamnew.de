import streamlit as st
import pandas as pd
import google.generativeai as genai
import random
import sys

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- DIAGNOSE-BOX (Nur für uns zur Fehlerfindung) ---
with st.expander("🛠 TECHNIK-CHECK (Hier klicken bei Fehlern)", expanded=True):
    st.write(f"**Python Version:** {sys.version.split()[0]}")
    st.write(f"**Google Library Version:** {genai.__version__}")
    
    # Keys prüfen
    raw_keys = None
    if "API_KEYS" in st.secrets: raw_keys = st.secrets["API_KEYS"]
    elif "GOOGLE_API_KEY" in st.secrets: raw_keys = st.secrets["GOOGLE_API_KEY"]
    
    if not raw_keys:
        st.error("❌ KEINE KEYS GEFUNDEN! Bitte Secrets prüfen.")
        st.stop()
    else:
        st.success(f"✅ Keys gefunden. Anzahl: {len(raw_keys) if isinstance(raw_keys, list) else 1}")

    # Formatierung der Keys sicherstellen
    if isinstance(raw_keys, str): api_keys = [raw_keys]
    elif isinstance(raw_keys, list): api_keys = raw_keys
    else: api_keys = []

# --- DATEN LADEN ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        csv_text = df.to_string(index=False)
        with open("business_wissen.txt", "r", encoding="utf-8") as f: txt = f.read()
        return {"csv": csv_text, "business": txt}
    except Exception as e:
        return None

db = load_data()

# --- HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
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
        
        sys_instr = f"Du bist Rodion. WISSEN: {db['csv'] if db else ''}. Sei direkt."
        
        # --- DIE RETTUNGSKETTE ---
        success = False
        error_log = []

        # Wir probieren erst Flash (schnell), dann Pro (stabil)
        models = ["gemini-1.5-flash", "gemini-pro"]
        
        for model_name in models:
            if success: break
            
            try:
                # Key auswählen
                chosen_key = random.choice(api_keys)
                genai.configure(api_key=chosen_key)
                
                # Modell laden
                model = genai.GenerativeModel(model_name) # Instruction im Prompt nutzen, ist sicherer bei alten Versionen
                
                # Prompt mit System-Anweisung kombinieren (Funktioniert immer)
                final_prompt = f"{sys_instr}\n\nUSER FRAGE: {prompt}"
                
                # Senden
                response = model.generate_content(final_prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_text += chunk.text
                        placeholder.markdown(full_text + "▌")
                
                placeholder.markdown(full_text)
                st.session_state.messages.append({"role": "model", "content": full_text})
                success = True
                
            except Exception as e:
                error_log.append(f"{model_name}: {str(e)}")
                continue

        if not success:
            st.error("💀 ALLE MODELLE FEHLGESCHLAGEN.")
            st.code("\n".join(error_log))
            st.info("Bitte sende Rodion einen Screenshot von diesem roten Kasten.")
