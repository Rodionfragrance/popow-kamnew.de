import streamlit as st
import google.generativeai as genai
import os

st.set_page_config(page_title="System Diagnose", page_icon="🔧")

st.title("🔧 Rodions System-Diagnose")
st.write("Wir testen jetzt jeden Key einzeln und schauen uns die Fehlermeldung an.")

# --- 1. KEYS CHECKEN ---
raw_keys = None
if "API_KEYS" in st.secrets: raw_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_keys = st.secrets["GOOGLE_API_KEY"]

if not raw_keys:
    st.error("❌ Keine Keys in Secrets gefunden.")
    st.stop()

if isinstance(raw_keys, str): api_keys = [raw_keys]
elif isinstance(raw_keys, list): api_keys = raw_keys
else: api_keys = []

st.success(f"✅ {len(api_keys)} API-Keys gefunden.")

# --- 2. VERBINDUNGSTEST ---
st.write("---")
st.header("🔍 Protokoll der Verbindungsversuche")

model_name = "gemini-1.5-flash" # Wir testen das Standard-Modell

for index, key in enumerate(api_keys):
    masked_key = key[:4] + "..." + key[-4:]
    st.write(f"**Versuch mit Key {index+1} ({masked_key}):**")
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(model_name)
        
        # Ein winziger Test-Prompt
        response = model.generate_content("Sag einfach nur 'Hallo'.")
        
        # Wenn wir hier ankommen, hat es geklappt!
        st.success(f"✅ ERFOLG! Antwort: {response.text}")
        st.balloons()
        break # Wir hören auf, sobald einer geht
        
    except Exception as e:
        # Hier sehen wir den WAHREN Grund für den Fehler
        st.error(f"❌ FEHLER: {str(e)}")

st.write("---")
st.info("Bitte mache einen Screenshot von den roten Fehlermeldungen oben und poste ihn.")
