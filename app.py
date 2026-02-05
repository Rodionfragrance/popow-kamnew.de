import streamlit as st
import pandas as pd
import requests
import json
import random
import time
import base64
from datetime import datetime
from io import BytesIO

# Versuch, Audio-Bibliothek zu laden
try:
    from gtts import gTTS
    TTS_ENABLED = True
except ImportError:
    TTS_ENABLED = False

# --- 1. KONFIGURATION (ChatGPT Style: Zentriert, aber Sidebar verfügbar) ---
st.set_page_config(page_title="Rodion Mastermind", page_icon="🧙‍♂️", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CSS & DESIGN ---
st.markdown("""
<style>
    /* Chat-Container enger und fokussierter */
    .main .block-container { max-width: 800px; padding-top: 2rem; padding-bottom: 10rem; }
    
    /* Verstecke Header für cleanen Look */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Upload Bereich Styling */
    .stExpander { border: none; box-shadow: none; background-color: transparent; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELFER ---
def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]: return "Winter ❄️"
    elif month in [3, 4, 5]: return "Frühling 🌷"
    elif month in [6, 7, 8]: return "Sommer ☀️"
    else: return "Herbst 🍂"

current_season = get_current_season()

# --- 4. API KEYS ---
raw_input = None
if "API_KEYS" in st.secrets: raw_input = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_input = st.secrets["GOOGLE_API_KEY"]

if not raw_input:
    st.error("⚠️ Keine Keys gefunden! Bitte in .streamlit/secrets.toml eintragen.")
    st.stop()

keys_to_use = raw_input if isinstance(raw_input, list) else [k.strip() for k in raw_input.split(",") if len(k.strip()) > 20]
api_keys = [str(k).replace("'", "").replace('"', "").strip() for k in keys_to_use]

# --- 5. DATENBANK LADEN ---
@st.cache_data(show_spinner=False)
def load_data():
    data = {"csv": "", "business": "", "network": "", "coaching": "", "produkt": "", "events": ""}
    # CSV laden
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";", encoding="utf-8")
        df = df.fillna("-")
        data["csv"] = df.to_string(index=False)
    except: pass

    # Text-Dateien laden
    files = ["business_wissen.txt", "network_bible.txt", "coaching_wissen.txt", "produkt_beschreibungen.txt", "events.txt"]
    keys = ["business", "network", "coaching", "produkt", "events"]
    
    for f, k in zip(files, keys):
        try: data[k] = open(f, "r", encoding="utf-8").read()
        except: pass
            
    return data

db = load_data()

# --- 6. SIDEBAR (VERWALTUNG & SUPPORT) ---
with st.sidebar:
    st.header("⚙️ Verwaltung")
    if st.button("🔄 Datenbank neu laden"):
        st.cache_data.clear()
        st.success("Cache geleert!")
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    st.subheader("🔗 Support")
    st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
    st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)

# --- 7. SESSION STATE (GEDÄCHTNIS) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 8. UI: HEADER & UPLOADER ---
st.title("🧙‍♂️ Rodion Mastermind")
st.caption("Dein Business-Mentor. Frag mich alles.")

# Datei-Upload direkt im Hauptbereich (Aufklappbar)
with st.expander("📎 Datei anhängen (Bild/PDF)", expanded=False):
    uploaded_file = st.file_uploader("Datei auswählen", type=["jpg", "png", "jpeg", "pdf"], label_visibility="collapsed")

# --- 9. CHAT VERLAUF ANZEIGEN ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# --- 10. LOGIK: PROMPT & HISTORY ---
if prompt := st.chat_input("Nachricht an Rodion..."):
    
    # 1. User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        if uploaded_file:
            if uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
                st.image(uploaded_file, caption="Anhang", width=200)
            else:
                st.markdown(f"📄 *Anhang: {uploaded_file.name}*")

    # 2. KI Antwort generieren
    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""

        # SYSTEM PROMPT (OHNE DENKPROZESS!)
        coaching_content = db.get('coaching', '')
        produkt_content = db.get('produkt', '')
        events_content = db.get('events', '')

        system_text = f"""
        DU BIST: Rodion, ein Elite-Network-Marketing-Mentor.
        DEIN ZIEL: Präzise, taktische und gewinnbringende Antworten für dein Team (Chogan).
        
        TONFALL:
        - Kein Geschwafel. Direkt, autoritär, lösungsorientiert ("Zeus-Modus").
        - Sprich den User niemals mit Namen an. Bleib beim "Du".
        
        WICHTIG - FORMATIERUNG:
        - KEIN "Laut denken" oder "Ich analysiere...". Das passiert intern.
        - Starte die Antwort IMMER direkt mit dem Ergebnis oder: "Rodion empfiehlt:"
        - Nutze Fettungen für Key-Facts.
        
        SICHERHEIT:
        - Keine Markennamen (Dior, Chanel etc.) nennen -> Umschreiben!
        - Keine Heilversprechen -> Rechtssicher bleiben.
        
        WISSEN (KONTEXT):
        - Saison: {current_season}
        - Events 2026: {events_content}
        - Produkte & Storys: {produkt_content}
        - Datenbank: {db.get('csv', '')}
        - Bibel & Wissen: {db.get('network', '')} {db.get('business', '')} {db.get('coaching', '')}
        """

        # --- CONTEXT BUILDER (DAS GEDÄCHTNIS) ---
        api_messages = []
        api_messages.append({"role": "user", "parts": [{"text": system_text}]})
        api_messages.append({"role": "model", "parts": [{"text": "Verstanden. Ich bin bereit."}]})

        # Letzte 6 Nachrichten (Kurzzeitgedächtnis)
        for msg in st.session_state.messages[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            api_messages.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Aktueller Prompt + Anhang
        current_parts = [{"text": f"EINGABE: {prompt}"}]
        
        if uploaded_file:
            try:
                bytes_data = uploaded_file.getvalue()
                mime_type = uploaded_file.type
                current_parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(bytes_data).decode('utf-8')
                    }
                })
            except: pass
            
        api_messages.append({"role": "user", "parts": current_parts})

        # --- API CALL (MIT ROBUSTER SUCHE GEGEN FEHLER) ---
        success = False
        last_error = ""
        random.shuffle(api_keys)
        
        for key in api_keys:
            if success: break
            
            # 1. SCAN: Welches Modell ist da? (Verhindert 404 Fehler)
            valid_model = None
            try:
                list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                list_res = requests.get(list_url, timeout=5)
                if list_res.status_code == 200:
                    for m in list_res.json().get('models', []):
                        if 'generateContent' in m.get('supportedGenerationMethods', []):
                            m_name = m['name'].replace('models/', '')
                            if 'flash' in m_name and '1.5' in m_name:
                                valid_model = m_name
                                break
                            if 'pro' in m_name and '1.5' in m_name:
                                valid_model = m_name
            except: continue

            if not valid_model: continue

            # 2. GENERATE: Anfrage senden
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{valid_model}:generateContent?key={key}"
                headers = {'Content-Type': 'application/json'}
                data = {"contents": api_messages} # Sende gesamten Verlauf

                response = requests.post(url, headers=headers, json=data, timeout=60)
                
                if response.status_code == 200:
                    answer = response.json()['candidates'][0]['content']['parts'][0]['text']
                    
                    # Streaming
                    for chunk in answer.split():
                        full_text += chunk + " "
                        placeholder.markdown(full_text + "▌")
                        time.sleep(0.02)
                    
                    placeholder.markdown(full_text)
                    
                    # Audio
                    audio_bytes = None
                    if TTS_ENABLED and len(full_text) > 20:
                        try:
                            tts = gTTS(text=full_text, lang='de')
                            fp = BytesIO()
                            tts.write_to_fp(fp)
                            audio_bytes = fp.getvalue()
                            st.audio(audio_bytes, format="audio/mp3")
                        except: pass
                    
                    # Speichern
                    msg_entry = {"role": "model", "content": full_text}
                    if audio_bytes: msg_entry["audio"] = audio_bytes
                    st.session_state.messages.append(msg_entry)
                    success = True
                else:
                    last_error = f"Status: {response.status_code} - {response.text}"
            except Exception as e: 
                last_error = str(e)
                continue

        if not success:
            st.error("⚠️ Verbindungsfehler. Bitte Fehler an Rodion schicken.")
            if last_error: st.caption(f"Details: {last_error}")
