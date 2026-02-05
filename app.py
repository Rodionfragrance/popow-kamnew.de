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

# --- 1. KONFIGURATION (Sidebar expanded!) ---
st.set_page_config(page_title="Rodion Chogan KI", page_icon="🧙‍♂️", layout="wide", initial_sidebar_state="expanded")
st.toast("👈 Tipp: Öffne die Sidebar (Pfeil oben links) für Datei-Uploads!", icon="💡")

# --- 2. UI DESIGN & CSS ---
st.markdown("""
<style>
    /* Chat-Container etwas enger für Lesbarkeit */
    .main .block-container { max-width: 900px; padding-top: 2rem; padding-bottom: 150px !important; }
    
    /* Elemente verstecken */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    
    /* Upload Bereich Styling */
    .stExpander { border: none; box-shadow: none; background-color: transparent; }
    
    /* Chat Input Design */
    [data-testid="stChatInput"] { padding-bottom: 15px !important; background-color: transparent !important; }
    [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 25px !important;
        padding: 12px 15px !important;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1) !important;
    }
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
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";", encoding="utf-8")
        df = df.fillna("-")
        data["csv"] = df.to_string(index=False)
    except: pass

    files = ["business_wissen.txt", "network_bible.txt", "coaching_wissen.txt", "produkt_beschreibungen.txt", "events.txt"]
    keys = ["business", "network", "coaching", "produkt", "events"]
    
    for f, k in zip(files, keys):
        try: data[k] = open(f, "r", encoding="utf-8").read()
        except: pass
            
    return data

db = load_data()

# --- 6. SIDEBAR (VERWALTUNG & DOWNLOAD) ---
with st.sidebar:
    st.header("⚙️ Verwaltung")
    
    # 1. Datenbank Reset
    if st.button("🔄 Datenbank neu laden"):
        st.cache_data.clear()
        st.success("Cache geleert!")
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    
    # 2. CHAT DOWNLOAD
    st.subheader("💾 Chat Sichern")
    if "messages" in st.session_state and len(st.session_state.messages) > 1:
        chat_text = ""
        for msg in st.session_state.messages:
            role = "RODION" if msg["role"] == "model" else "DU"
            chat_text += f"{role}:\n{msg['content']}\n\n{'-'*30}\n\n"
            
        st.download_button(
            label="📥 Verlauf herunterladen",
            data=chat_text,
            file_name=f"chat_verlauf_{datetime.now().strftime('%Y-%m-%d')}.txt",
            mime="text/plain"
        )
    else:
        st.caption("Schreibe etwas, um den Chat zu speichern.")

    st.markdown("---")
    st.subheader("🔗 Support")
    st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
    st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)

# --- 7. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "👋 Hallo! Ich bin Rodion, dein KI-Mentor.\n**Tipp:** Du kannst hier direkt Dateien anhängen.\n\nWie kann ich dir helfen?"}
    ]

# --- 8. UI HEADER & UPLOAD ---
st.title("🧙‍♂️ Rodion Chogan KI")
st.caption("Dein Business-Mentor. Frag mich alles.")

# Datei-Upload
with st.expander("📎 Datei anhängen (Bild/PDF)", expanded=False):
    uploaded_file = st.file_uploader("Datei auswählen", type=["jpg", "png", "jpeg", "pdf"], label_visibility="collapsed")

# --- 9. CHAT VERLAUF ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# --- 10. LOGIK ---
if prompt := st.chat_input("Nachricht an Rodion..."):
    
    # User Nachricht
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        if uploaded_file:
            if uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
                st.image(uploaded_file, caption="Anhang", width=200)
            else:
                st.markdown(f"📄 *Anhang: {uploaded_file.name}*")

    # KI Antwort
    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""

        coaching_content = db.get('coaching', '')
        produkt_content = db.get('produkt', '')
        events_content = db.get('events', '')

        # --- SYSTEM PROMPT (UPDATE: FORCE LISTS) ---
        system_text = f"""
        DU BIST: Rodion, ein Elite-Network-Marketing-Mentor.
        DEIN ZIEL: Präzise, taktische Antworten für dein Team (Chogan).
        
        TONFALL:
        - Direkt, autoritär ("Zeus-Modus"), aber hilfreich.
        - Bleib beim "Du".
        
        STRUKTUR-BEFEHL (STRENG EINHALTEN):
        1. Schreibe NIEMALS lange Absätze (max. 2 Zeilen Fließtext).
        2. Nutze FÜR JEDE ANTWORT Bullet-Points oder nummerierte Listen.
        3. Nutze Emojis als Aufzählungszeichen (z.B. 👉, ✅, 🚀, 💡), um den Text aufzubrechen.
        4. Starte direkt mit dem Ergebnis. KEIN "Ich habe analysiert...".
        
        Beispiel für gute Antwort:
        "Hier ist deine Strategie:
        ✅ Punkt 1: Mach das...
        ✅ Punkt 2: Achte auf...
        🚀 Fazit: Leg los."
        
        WISSEN:
        - Saison: {current_season}
        - Events 2026: {events_content}
        - Produkte: {produkt_content}
        - Datenbank: {db.get('csv', '')}
        - Bibel & Wissen: {db.get('network', '')} {db.get('business', '')} {db.get('coaching', '')}
        """

        # VERLAUF BAUEN
        api_messages = []
        api_messages.append({"role": "user", "parts": [{"text": system_text}]})
        api_messages.append({"role": "model", "parts": [{"text": "Verstanden. Ich antworte nur in Listen und kurzen Blöcken."}]})

        relevant_history = st.session_state.messages
        if len(relevant_history) > 0 and relevant_history[0]["role"] == "model":
            relevant_history = relevant_history[1:]

        for msg in relevant_history[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            api_messages.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Aktueller Input + Datei
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

        # --- API LOGIK (SCANNER) ---
        success = False
        error_log = []
        random.shuffle(api_keys)
        
        with st.spinner("Rodion analysiert... ⏳"):
            for i, key in enumerate(api_keys):
                if success: break
                
                # 1. SCAN
                valid_model = None
                try:
                    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                    list_res = requests.get(list_url, timeout=5)
                    
                    if list_res.status_code == 200:
                        models_data = list_res.json().get('models', [])
                        for m in models_data:
                            m_name = m['name'].replace('models/', '')
                            methods = m.get('supportedGenerationMethods', [])
                            if 'generateContent' in methods:
                                if 'flash' in m_name and '1.5' in m_name:
                                    valid_model = m_name
                                    break
                                elif 'pro' in m_name and '1.5' in m_name:
                                    valid_model = m_name
                                elif valid_model is None: 
                                    valid_model = m_name 
                    else:
                        error_log.append(f"Key {i} Scan-Fehler: {list_res.status_code}")
                        continue
                except Exception as e:
                    error_log.append(f"Key {i} Scan-Exception: {str(e)}")
                    continue

                if not valid_model:
                    error_log.append(f"Key {i}: Kein Modell gefunden.")
                    continue

                # 2. GENERATE
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{valid_model}:generateContent?key={key}"
                    headers = {'Content-Type': 'application/json'}
                    data = {"contents": api_messages}

                    response = requests.post(url, headers=headers, json=data, timeout=60)
                    
                    if response.status_code == 200:
                        answer = response.json()['candidates'][0]['content']['parts'][0]['text']
                        
                        for chunk in answer.split():
                            full_text += chunk + " "
                            placeholder.markdown(full_text + "▌")
                            time.sleep(0.02)
                        
                        placeholder.markdown(full_text)
                        
                        audio_bytes = None
                        if TTS_ENABLED and len(full_text) > 20:
                            try:
                                tts = gTTS(text=full_text, lang='de')
                                fp = BytesIO()
                                tts.write_to_fp(fp)
                                audio_bytes = fp.getvalue()
                                st.audio(audio_bytes, format="audio/mp3")
                            except: pass
                        
                        msg_entry = {"role": "model", "content": full_text}
                        if audio_bytes: msg_entry["audio"] = audio_bytes
                        st.session_state.messages.append(msg_entry)
                        success = True
                    else:
                        error_log.append(f"Key {i} ({valid_model}) Error: {response.status_code}")
                except Exception as e: 
                    error_log.append(f"Key {i} Request-Exception: {str(e)}")
                    continue

        if not success:
            st.error("⚠️ Verbindungsfehler.")
            st.code("\n".join(error_log), language="text")
