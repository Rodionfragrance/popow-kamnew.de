import streamlit as st
import pandas as pd
import requests
import json
import random
import time
import base64
from datetime import datetime
from io import BytesIO

# Versuch, Audio-Bibliothek zu laden (Fehler-Toleranz)
try:
    from gtts import gTTS
    TTS_ENABLED = True
except ImportError:
    TTS_ENABLED = False

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- 2. UI DESIGN & CSS ---
st.markdown("""
<style>
.main .block-container { padding-bottom: 120px !important; }
[data-testid="stChatInput"] { border-radius: 20px !important; border: 1px solid #e0e0e0 !important; background-color: white !important; elevation: 5; }
.stChatMessageAvatar { background-color: #ffffff !important; }
.stMarkdown p { font-size: 16px !important; line-height: 1.8 !important; margin-bottom: 25px !important; }
.stMarkdown h3 { color: #d32f2f !important; margin-top: 40px !important; margin-bottom: 15px !important; border-bottom: 1px solid #eee; padding-bottom: 5px; font-weight: 700; }
.stMarkdown hr { margin-top: 30px !important; margin-bottom: 30px !important; border-color: #f0f0f0; }
.stMarkdown strong { color: #333; }
</style>
""", unsafe_allow_html=True)

# --- 3. HELFER: JAHRESZEIT ---
def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]: return "Winter ❄️"
    elif month in [3, 4, 5]: return "Frühling 🌷"
    elif month in [6, 7, 8]: return "Sommer ☀️"
    else: return "Herbst 🍂"

current_season = get_current_season()

# --- 4. API KEYS LADEN ---
raw_input = None
if "API_KEYS" in st.secrets: raw_input = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets: raw_input = st.secrets["GOOGLE_API_KEY"]

if not raw_input:
    st.error("⚠️ Keine Keys gefunden! Bitte in .streamlit/secrets.toml eintragen.")
    st.stop()

keys_to_use = raw_input if isinstance(raw_input, list) else [k.strip() for k in raw_input.split(",") if len(k.strip()) > 20]
api_keys = [str(k).replace("'", "").replace('"', "").strip() for k in keys_to_use]

if not api_keys:
    st.error("⚠️ Keine gültigen Keys verfügbar.")
    st.stop()

# --- 5. DATENBANK & WISSEN LADEN ---
@st.cache_data(show_spinner=False)
def load_data():
    data = {"csv": "", "business": "", "network": "", "coaching": "", "produkt": ""}
    
    # 1. CSV laden
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";", encoding="utf-8")
        df = df.fillna("-")
        data["csv"] = df.to_string(index=False)
    except Exception as e: st.error(f"Fehler CSV: {e}")

    # 2. Text-Dateien laden
    try: data["business"] = open("business_wissen.txt", "r", encoding="utf-8").read()
    except: pass
    try: data["network"] = open("network_bible.txt", "r", encoding="utf-8").read()
    except: pass
    try: data["coaching"] = open("coaching_wissen.txt", "r", encoding="utf-8").read()
    except: pass
    try: data["produkt"] = open("produkt_beschreibungen.txt", "r", encoding="utf-8").read()
    except: pass
            
    return data

# --- SIDEBAR: RESET & DATEI-UPLOAD ---
with st.sidebar:
    st.header("⚙️ Tools & Verwaltung")
    
    # DATEI UPLOAD (BILD ODER PDF!)
    st.subheader("📸 Datei-Analyse")
    uploaded_file = st.file_uploader("Lade ein Foto oder PDF hoch", type=["jpg", "png", "jpeg", "pdf"])
    
    st.markdown("---")
    
    if st.button("🔄 Datenbank neu laden"):
        st.cache_data.clear()
        st.success("Cache geleert! Neue Daten werden geladen.")
        time.sleep(1)
        st.rerun()

db = load_data()

# --- 6. HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption(f"📅 Saison: {current_season} | 🚀 Dein Mentor mit exklusivem Team-Wissen & Strategie") 
st.info("💡 **Insider-Wissen:** Anders als normale KIs kennt dieser Bot unsere Produkte & Strategien**. Nutze ihn für Pitches & Analysen!")

col1, col2 = st.columns(2)
with col1: st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
with col2: st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)
st.markdown("---")

# --- 7. CHAT LOGIC ---
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])
        # Audio Player anzeigen, falls vorhanden
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# --- 8. PROMPT & ANTWORT ---
if prompt := st.chat_input("Frag mich nach Düften, Produkten oder Business-Strategien..."):
    
    # User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        
        # Anzeige Logik: Nur Bilder anzeigen, keine PDFs (das würde crashen)
        if uploaded_file:
            if uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
                st.image(uploaded_file, caption="Hochgeladenes Bild", width=200)
            else:
                st.info(f"📄 PDF hochgeladen: {uploaded_file.name}")

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # Datensätze sicher abrufen
        coaching_content = db.get('coaching', 'Leer')
        produkt_content = db.get('produkt', 'Leer')
        
        # --- DER FUSIONIERTE PROMPT (ZEUS + MENTOR + SAFE MODE) ---
        system_text = f"""
        🚨 OBERSTE SICHERHEITSDIREKTIVE (STRENG):
        1. Nenne NIEMALS Markennamen aus der Spalte "Original_Marke" (z.B. Dior, Chanel, Tom Ford).
        2. Nenne NIEMALS die Parfümnamen aus der Spalte "Inspiriert_Von" (z.B. Sauvage, Baccarat, Lost Cherry).
        
        STATTDESSEN:
        Umschreibe den Originalduft! Nutze Formulierungen wie:
        - "Der bekannte Duft, den du suchst..."
        - "Unsere Interpretation des legendären Klassikers..."
        
        ---
        
        ROLLE & IDENTITÄT:
        Dein Name ist **Rodion** (KI-Mentor).
        Der User ist ein **Vertriebspartner**.
        ⚠️ WICHTIG: Sprich den User NIEMALS mit einem Namen an (auch nicht "Rodion" oder "mein Freund"). Bleibe neutral beim "Du".
        
        DEIN TONFALL (ZEUS-METHODE):
        - **Professionell & Autoritär:** Keine Kumpel-Sprache ("Kumpel", "Mein Lieber", "Bro").
        - **Sachlich & Direkt:** Keine übertriebenen Emotionen, keine Floskeln.
        - **Struktur:** Nutze "Laut denken" nur kurz zur Analyse, dann klare Bulletpoints.

        🧠 STRATEGIE:
        1. **Autorität:** Antworte bestimmt. Entschuldige dich nicht unnötig.
        2. **Wissen:** Wenn ein Produktname (z.B. "Munozent") fällt, SUCHE ZWINGEND in den "PRODUKT-BESCHREIBUNGEN"!
        3. **Datei-Analyse:** Wenn eine Datei (Bild/PDF) dabei ist, analysiere sie präzise (z.B. Inhaltsstoffe erkennen, Text auslesen).
        
        ---
        
        🛑 ENTSCHEIDUNGS-MATRIX:
        
        FALL A: PRODUKTE / DÜFTEN (Verkaufs-Modus)
        -> Nutze ZUERST die "Produkt-Beschreibungen" (Txt) für Pitches.
        -> Nutze DANN die "Datenbank (CSV)" für Preise/Codes.
        -> UPSELL-PFLICHT: Kopiere Text aus `Upsell_Info` 1:1.
        
        FALL B: BUSINESS / RECHT / MINDSET (Mentor-Modus)
        -> Nutze "Network-Marketing-Bibel", "Business-Wissen" und "Coaching-Wissen".
        -> Wenn nach Heilversprechen gefragt wird:
           1. Prüfe in "PRODUKT-BESCHREIBUNGEN", was das Produkt wirklich tut.
           2. Antworte mit einem klaren NEIN zu Heilaussagen (Compliance).
        
        -> OUTPUT FORMAT: 
           Start mit "🧠 Rodion denkt nach: ...".
           Dann die Antwort in strukturierter Form (Fettungen, Bulletpoints).
           Ende mit einer strategischen Frage.

        ---

        WISSENS-BASIS:
        - Jahreszeit: {current_season}
        - PRODUKT-BESCHREIBUNGEN: {produkt_content}
        - Datenbank (CSV): {db.get('csv', 'Leer')}
        - NETWORK BIBEL: {db.get('network', 'Leer')}
        - BUSINESS WISSEN: {db.get('business', 'Leer')}
        - COACHING TRANSKRIPTE: {coaching_content}
        
        SPRACHE:
        Antworte IMMER in der Sprache des Nutzers!
        """
        
        # --- DATEI VERARBEITUNG (BILD ODER PDF) ---
        file_part = None
        if uploaded_file:
            try:
                bytes_data = uploaded_file.getvalue()
                mime_type = uploaded_file.type
                file_part = {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(bytes_data).decode('utf-8')
                    }
                }
            except: pass

        # --- API REQUEST VORBEREITEN ---
        final_prompt_text = f"{system_text}\n\nEINGABE DES BERATERS: {prompt}"
        
        request_contents = [{"text": final_prompt_text}]
        if file_part:
            request_contents.append(file_part)

        # --- VERBINDUNG ZU GOOGLE GEMINI (AUTO-PILOT ✈️) ---
        success = False
        last_error_message = "Kein Verbindungsversuch gestartet."
        
        random.shuffle(api_keys) 
        
        for key in api_keys:
            if success: break
            
            # SCHRITT 1: SCAN (ListModels)
            valid_model = None
            try:
                list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                list_response = requests.get(list_url, timeout=5)
                
                if list_response.status_code == 200:
                    models_data = list_response.json().get('models', [])
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
                else: continue
            except: continue

            if not valid_model: continue

            # SCHRITT 2: GENERATE
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{valid_model}:generateContent?key={key}"
                headers = {'Content-Type': 'application/json'}
                data = {"contents": [{"parts": request_contents}]}
                
                response = requests.post(url, headers=headers, json=data, timeout=60)
                
                if response.status_code == 200:
                    try:
                        answer = response.json()['candidates'][0]['content']['parts'][0]['text']
                        for chunk in answer.split():
                            full_text += chunk + " "
                            placeholder.markdown(full_text + "▌")
                            time.sleep(0.03)
                        
                        placeholder.markdown(full_text)
                        
                        # --- AUDIO GENERIERUNG (TTS) ---
                        audio_bytes = None
                        if TTS_ENABLED and len(full_text) > 5:
                            try:
                                tts = gTTS(text=full_text, lang='de')
                                fp = BytesIO()
                                tts.write_to_fp(fp)
                                audio_bytes = fp.getvalue()
                                st.audio(audio_bytes, format="audio/mp3")
                            except: pass
                        
                        # Nachricht Speichern
                        msg_entry = {"role": "model", "content": full_text}
                        if audio_bytes: msg_entry["audio"] = audio_bytes
                        st.session_state.messages.append(msg_entry)
                        
                        success = True
                    except: pass
            except: continue
        
        if not success:
            st.error("⚠️ Fehler bitte an Rodion schicken.")
            st.warning(f"🔍 Letzter Fehlergrund: {last_error_message}")
            if not TTS_ENABLED:
                st.info("Hinweis: Installiere 'gTTS' für Sprachausgabe.")
