import streamlit as st
import requests

st.set_page_config(page_title="Key Diagnose", layout="wide")
st.title("🕵️‍♂️ Der API-Detektiv")

# 1. KEYS LESEN
raw_input = None
if "API_KEYS" in st.secrets: raw_input = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_input = st.secrets["GOOGLE_API_KEY"]

if not raw_input:
    st.error("❌ Keine Keys in den Secrets gefunden.")
    st.stop()

# Wir wandeln alles in eine Liste um, egal wie es eingegeben wurde
keys_to_test = []
if isinstance(raw_input, str):
    # Falls es ein langer String mit Kommas ist
    if "," in raw_input:
        keys_to_test = [k.strip() for k in raw_input.split(",")]
    else:
        keys_to_test = [raw_input.strip()]
elif isinstance(raw_input, list):
    keys_to_test = raw_input

st.write(f"Gefundene Einträge: {len(keys_to_test)}")

# 2. TESTEN
st.write("---")
st.subheader("Wir fragen Google: 'Welche Modelle darf ich sehen?'")
st.info("Wenn hier 404 kommt, ist die API in deinem Google-Account deaktiviert.")

for i, key in enumerate(keys_to_test):
    # Key säubern (Anführungszeichen weg, Leerzeichen weg)
    clean_key = str(key).replace("'", "").replace('"', "").strip()
    
    # Maskierten Key anzeigen
    masked = f"{clean_key[:5]}...{clean_key[-4:]}" if len(clean_key) > 10 else "UNGÜLTIG"
    
    st.write(f"**Test Key #{i+1}:** `{masked}` (Länge: {len(clean_key)})")
    
    # Der einfachste Test: Liste die Modelle auf
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            st.success("✅ TREFFER! Dieser Key funktioniert perfekt.")
            st.json(response.json()) # Zeigt, was Google antwortet
            st.stop() # Wir haben einen Gewinner!
            
        elif response.status_code == 400:
            st.error("❌ FEHLER 400: Der Key ist falsch formatiert (Ungültige Zeichen).")
            
        elif response.status_code == 404:
            st.error("❌ FEHLER 404: Key gültig, aber API deaktiviert.")
            st.warning("👉 LÖSUNG: Geh in die Google Cloud Console, such nach 'Generative Language API' und klicke auf 'ENABLE'.")
            
        else:
            st.error(f"❌ FEHLER {response.status_code}: {response.text}")
            
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")

st.write("---")
