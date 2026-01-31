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
@st.cache_data
def load_data():
    data = {"csv": "", "business": "", "network": ""}
    try:
        # 1. CSV laden
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";", encoding="utf-8")
        data["csv"] = df.to_string(index=False)
    except Exception as e: st.error(f"Fehler CSV: {e}")

    # 2. Business Wissen laden
    try:
        data["business"] = open("business_wissen.txt", "r", encoding="utf-8").read()
    except: pass

    # 3. NETWORK BIBEL LADEN
    try:
        data["network"] = open("network_bible.txt", "r", encoding="utf-8").read()
    except: pass
            
    return data

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
if prompt := st.chat_input("Frag mich nach Düften oder Business-Tipps...(Multi-Language)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # --- DER INTELLIGENTE "SWITCH"-PROMPT ---
        system_text = f"""
        🚨 OBERSTE SICHERHEITSDIREKTIVE:
        Nenne NIEMALS Markennamen aus "Original_Marke" (Dior, Chanel etc.). Ausnahme: "Mytologik", "Olfazeta", "Eigenkreation".

        ---
        
        ROLLE & AUFGABE:
        Du bist Rodion, ein harter, direkter und erfolgreicher Network-Marketing Mentor & Chogan-Experte.
        Analysiere ZUERST die Eingabe des Users. Entscheide dann, welchen Modus du nutzt:
        
        ---
        
        🛑 ENTSCHEIDUNGS-MATRIX (WICHTIG!):
        
        FALL A: USER FRAGT NACH PRODUKTEN / DÜFTEN / EMPFEHLUNGEN
        -> Nutze NUR die "Datenbank (CSV)".
        -> Ignoriere Business-Tipps.
        -> STRATEGIE: Exklusivität vor Standard. 
           1. Suche ZUERST nach "Mytologik"/"Eigenkreation". 
           2. Sortiere STRIKT nach Preis (teuerste zuerst).
        -> OUTPUT FORMAT (Zwingend!):
           "Hier ist die Umsatz-Strategie:
           ### 🏆 Option 1 (Premium): [Name] - [Preis]
           [Pitch]
           ### ✨ Option 2: [Name] - [Preis]
           [Pitch]
           ### 🛍️ Cross-Selling: [Upsell]"
        
        FALL B: USER FRAGT NACH BUSINESS / DOWNLINE / REKRUTIERUNG / MINDSET
        -> Nutze NUR "Network-Marketing-Bibel" und "Business-Wissen".
        -> VERBOT: Empfiehl KEINE konkreten Parfüms, wenn es um Mindset oder Downline-Probleme geht! Konzentriere dich auf Führung und Strategie.
        -> Ignoriere die CSV-Datenbank und Preise.
        -> STRATEGIE: Sei ein gnadenloser Mentor. Gib klare, harte Handlungsempfehlungen. Kein "Blabla", sondern Strategie.
        -> OUTPUT FORMAT: 
           Freier Text. Nutze Fettgedrucktes für Key-Learnings. Erstelle eine Schritt-für-Schritt Liste. Sprich Klartext.

        ---

        WISSENS-BASIS:
        - Jahreszeit: {current_season}
        - Datenbank (CSV): {db['csv'] if db and db['csv'] else 'Leer'}
        - NETWORK BIBEL & BUSINESS WISSEN: {db['network']} \n {db['business']}
        
        SPRACHE:
        Antworte IMMER in der Sprache des Nutzers!
        """
        
        final_prompt = f"{system_text}\n\nEINGABE DES BERATERS: {prompt}"

        # --- VERBINDUNG ZU GOOGLE GEMINI (AUTO-PILOT MODE ✈️) ---
        success = False
        last_error_message = "Kein Verbindungsversuch gestartet."
        used_model_name = "Unbekannt"
        
        random.shuffle(api_keys) 
        
        for key in api_keys:
            if success: break
            
            # SCHRITT 1: FRAGEN WIR GOOGLE, WELCHE MODELLE DA SIND (LISTMODELS)
            # Damit verhindern wir den 404 Fehler, weil wir nur existierende Namen nutzen.
            valid_model = None
            try:
                list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                list_response = requests.get(list_url, timeout=5)
                
                if list_response.status_code == 200:
                    models_data = list_response.json().get('models', [])
                    # Wir suchen das beste Modell, das 'generateContent' kann
                    for m in models_data:
                        m_name = m['name'].replace('models/', '')
                        methods = m.get('supportedGenerationMethods', [])
                        
                        if 'generateContent' in methods:
                            # Priorität: Flash -> Pro -> Irgendeins
                            if 'flash' in m_name and '1.5' in m_name:
                                valid_model = m_name
                                break
                            elif 'pro' in m_name and '1.5' in m_name:
                                valid_model = m_name
                            elif valid_model is None: # Nimm das erste verfügbare als Fallback
                                valid_model = m_name
                else:
                    last_error_message = f"Konnte Modell-Liste nicht laden: {list_response.status_code}"
                    continue
            except Exception as e:
                last_error_message = f"Fehler beim Auto-Scan der Modelle: {str(e)}"
                continue

            # Wenn wir kein Modell gefunden haben, ist der Key nutzlos
            if not valid_model:
                last_error_message = "Kein passendes 'generateContent' Modell für diesen Key gefunden."
                continue

            # SCHRITT 2: ANFRAGE SENDEN (MIT DEM GEFUNDENEN NAMEN)
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
                        used_model_name = valid_model # Für Debugging
                    except Exception as parse_err:
                        last_error_message = f"Antwort ungültig: {parse_err}"
                else:
                    error_json = response.json()
                    error_msg = error_json.get('error', {}).get('message', response.text)
                    last_error_message = f"Fehler {response.status_code} bei {valid_model}: {error_msg}"

            except Exception as e:
                last_error_message = f"Technischer Absturz bei Anfrage: {str(e)}"
                continue
        
        if not success:
            st.error("⚠️ Fehler bitte an Rodion schicken.")
            st.warning(f"🔍 Letzter Fehlergrund: {last_error_message}")
            st.info("Tipp: Wenn 'ListModels' fehlschlägt, ist die 'Generative Language API' in der Google Cloud Console für dieses Projekt vielleicht nicht aktiviert.")
