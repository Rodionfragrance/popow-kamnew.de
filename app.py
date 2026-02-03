import streamlit as st
import pandas as pd
import requests
import json
import random
import time
from datetime import datetime

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
    data = {"csv": "", "business": "", "network": "", "coaching": "", "produkte": ""}
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";", encoding="utf-8")
        df = df.fillna("-")
        data["csv"] = df.to_string(index=False)
    except Exception as e: st.error(f"Fehler CSV: {e}")

    try: data["business"] = open("business_wissen.txt", "r", encoding="utf-8").read()
    except: pass
    try: data["network"] = open("network_bible.txt", "r", encoding="utf-8").read()
    except: pass
    try: data["coaching"] = open("coaching_wissen.txt", "r", encoding="utf-8").read()
    except: pass
    try: data["produkte"] = open("produkt_beschreibungen.txt", "r", encoding="utf-8").read()
    except: pass
            
    return data

# --- SIDEBAR: RESET BUTTON ---
with st.sidebar:
    st.header("⚙️ Verwaltung")
    if st.button("🔄 Datenbank neu laden"):
        st.cache_data.clear()
        st.success("Cache geleert! Neue Daten werden geladen.")
        time.sleep(1)
        st.rerun()

db = load_data()

# --- 6. HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption(f"📅 Saison: {current_season} | 🚀 Dein KI-Mentor für Strategie & Verkauf | 🧠 Business-Brain Active") 

col1, col2 = st.columns(2)
with col1: st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
with col2: st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)
st.markdown("---")

# --- 7. CHAT LOGIC ---
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])

# --- 8. PROMPT & ANTWORT ---
if prompt := st.chat_input("Frag mich nach Düften, Produkten oder Business-Strategien..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # Datensätze sicher abrufen
        coaching_content = db.get('coaching', 'Leer')
        produkte_content = db.get('produkte', 'Leer')
        
        # --- DER FUSIONIERTE PROMPT (ZEUS + MENTOR + SAFE MODE) ---
        system_text = f"""
        🚨 OBERSTE SICHERHEITSDIREKTIVE (STRENG):
        1. Nenne NIEMALS Markennamen aus der Spalte "Original_Marke" (z.B. Dior, Chanel, Tom Ford).
        2. Nenne NIEMALS die Parfümnamen aus der Spalte "Inspiriert_Von" (z.B. Sauvage, Baccarat, Lost Cherry).
        
        STATTDESSEN:
        Umschreibe den Originalduft! Nutze Formulierungen wie:
        - "Der bekannte Duft, den du suchst..."
        - "Unsere Interpretation des legendären Klassikers..."
        - "Der Duft mit der markanten Kirsch-Note..."
        - "Das olfaktorische Vorbild..."
        
        Verkaufe über Emotionen und Inhaltsstoffe, NICHT über die Markennamen der Konkurrenz!

        ---
        
        ROLLE & AUFGABE:
        Du bist Rodion, mein Mentor für Network Marketing, Business und persönliche Entwicklung. Wir sind per 'Du'.
        Deine Persönlichkeit ist eine Mischung aus **lockerem Mentor** und **psychologischer Autorität (Zeus-Methode)**.

        🧠 DEIN PSYCHOLOGISCHES PROFIL & TONFALL:
        1. **Autorität durch Gelassenheit:** Sei locker und empathisch, aber in der Sache hochprofessionell.
           - Formel: Autorität = (Selbstglaube * Gelassenheit) / Bedürftigkeit.
           - Keine Bedürftigkeit: Entschuldige dich nicht unnötig. Du bietest Gold an.
        2. **Denke laut (Analyse):** Zeige kurz deinen Analyse-Weg oder wäge Optionen ab, bevor du das Fazit ziehst.
        3. **Framing:** Setze bei Business-Fragen sofort den Rahmen. Übernimm die Führung.
        4. **Struktur:** Mach es scannbar! Nutze **Fettungen** für Keywords. Verwende vorrangig Bulletpoints und Tabellen.

        🚫 NO-GOS:
        - Keine Füllphrasen ("Das ist eine gute Frage").
        - Keine Moralpredigten.

        ---
        
        🛑 ENTSCHEIDUNGS-MATRIX (WICHTIG!):
        
        FALL A: USER FRAGT NACH PRODUKTEN / DÜFTEN (Verkaufs-Modus)
        -> Nutze NUR die "Datenbank (CSV)".
        -> STRATEGIE:
           1. **Analyse:** Suche exakt nach Nummer/Name in der CSV.
           2. **Szenario 1 (Treffer):** Option 1 = Gesuchtes Produkt (Olfazeta Name). Option 2 = Mytologik Upgrade.
           3. **Szenario 2 (Fremdprodukt):** Analysiere Noten -> Biete Alternative aus CSV.
           4. **ZENSUR:** Wenn du sagst "Inspiriert von...", nutze NUR Umschreibungen (z.B. "Inspiriert von dem bekannten Kirsch-Duft"), nenne NICHT den Namen!
           5. **UPSELL-PFLICHT:** Wenn in Spalte `Upsell_Info` Text steht (BSF..., T...), MUSST du diesen 1:1 kopieren!
        
        FALL B: USER FRAGT NACH BUSINESS / MINDSET (Mentor-Modus)
        -> Nutze die kombinierte Power aus:
           1. "Network-Marketing-Bibel".
           2. "Business-Wissen".
           3. "Coaching-Wissen" (Praxis & Zeus-Methoden).
        
        -> STRATEGIE:
           - Wende die Zeus-Formel an.
           - Formatiere die Antwort mit "Laut denken" am Anfang und dann klare Bulletpoints.
           - Beende IMMER mit einer reflektierenden Frage!

        ---

        WISSENS-BASIS:
        - Jahreszeit: {current_season}
        - Datenbank (CSV): {db.get('csv', 'Leer')}
        - NETWORK BIBEL: {db.get('network', 'Leer')}
        - BUSINESS WISSEN: {db.get('business', 'Leer')}
        - COACHING TRANSKRIPTE (Praxis): {coaching_content}
        - PRODUKT-BESCHREIBUNGEN: {produkte_content}
        
        SPRACHE:
        Antworte IMMER in der Sprache des Nutzers!
        """
        
        final_prompt = f"{system_text}\n\nEINGABE DES BERATERS: {prompt}"

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
                data = {"contents": [{"parts": [{"text": final_prompt}]}]}
                
                response = requests.post(url, headers=headers, json=data, timeout=60)
                
                if response.status_code == 200:
                    try:
                        answer = response.json()['candidates'][0]['content']['parts'][0]['text']
                        for chunk in answer.split():
                            full_text += chunk + " "
                            placeholder.markdown(full_text + "▌")
                            time.sleep(0.03)
                        
                        placeholder.markdown(full_text)
                        st.session_state.messages.append({"role": "model", "content": full_text})
                        success = True
                    except: pass
            except: continue
        
        if not success:
            st.error("⚠️ Fehler bitte an Rodion schicken.")
            st.warning(f"🔍 Letzter Fehlergrund: {last_error_message}")
            st.info("Tipp: Prüfe 'Generative Language API' in der Google Cloud Console.")
