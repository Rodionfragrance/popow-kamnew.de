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
if prompt := st.chat_input("Frag mich nach Düften oder Business-Tipps..."):
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

        # --- VERBINDUNG ZU GOOGLE GEMINI (ROBUST & DEBUGGING) ---
        success = False
        random.shuffle(api_keys) 
        
        for key in api_keys:
            if success: break
            
            # Auto-Discovery des Modells
            available_model = None
            try:
                list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                list_resp = requests.get(list_url, timeout=5)
                if list_resp.status_code == 200:
                    for m in list_resp.json().get('models', []):
                        if 'generateContent' in m.get('supportedGenerationMethods', []):
                            m_name = m['name'].replace('models/', '')
                            if 'flash' in m_name and '1.5' in m_name: available_model = m_name; break
                            if 'pro' in m_name and '1.5' in m_name: available_model = m_name
                    if not available_model: available_model = "gemini-1.5-flash-latest" # Fallback 1
            except: available_model = "gemini-1.5-flash" # Fallback 2

            if not available_model: available_model = "gemini-pro" # Notfall-Fallback

            # Anfrage
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{available_model}:generateContent?key={key}"
                headers = {'Content-Type': 'application/json'}
                data = {"contents": [{"parts": [{"text": final_prompt}]}]}
                
                response = requests.post(url, headers=headers, json=data, timeout=60)
                
                if response.status_code == 200:
                    try:
                        answer = response.json()['candidates'][0]['content']['parts'][0]['text']
                    except: answer = "Format-Fehler."

                    for chunk in answer.split():
                        full_text += chunk + " "
                        placeholder.markdown(full_text + "▌")
                        time.sleep(0.03)
                    
                    placeholder.markdown(full_text)
                    st.session_state.messages.append({"role": "model", "content": full_text})
                    success = True
                    break 
                elif response.status_code == 429:
                    continue # Rate Limit -> Nächster Key
                else:
                    # HIER IST DER DEBUGGER: ZEIGE DEN FEHLER AN!
                    st.error(f"❌ API Fehler mit Modell {available_model}: {response.status_code}")
                    st.code(response.text)
                    continue 

            except Exception as e:
                st.error(f"❌ System-Fehler: {e}")
                continue
        
        if not success:
            st.error("⚠️ Wenn du oben rote Fehlermeldungen siehst, schicke diese an Rodion!")
