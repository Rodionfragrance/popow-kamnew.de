import streamlit as st
import pandas as pd
import requests
import json
import random
import time
from datetime import datetime

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- 2. UI DESIGN & CSS FIXES ---
st.markdown("""
<style>
/* 1. HAUPTBEREICH: PLATZ UNTEN RESERVIEREN */
/* Verhindert, dass der letzte Text hinter dem Eingabefeld verschwindet */
.main .block-container {
    padding-bottom: 120px !important; 
}

/* 2. EINGABEFELD STYLEN (ChatGPT Style) */
/* Wir lassen Streamlit die Breite regeln, machen es aber hübsch */
[data-testid="stChatInput"] {
    border-radius: 20px !important;
    border: 1px solid #e0e0e0 !important;
    background-color: white !important;
    elevation: 5;
}

/* 3. AVATARE */
.stChatMessageAvatar { background-color: #ffffff !important; }

/* 4. TEXT-FORMATIERUNG (Lesbarkeit & Business-Look) */
.stMarkdown p {
    font-size: 16px !important;
    line-height: 1.8 !important;
    margin-bottom: 25px !important;
}
.stMarkdown h3 {
    color: #d32f2f !important; /* Chogan Rot-Ton */
    margin-top: 40px !important;
    margin-bottom: 15px !important;
    border-bottom: 1px solid #eee; 
    padding-bottom: 5px;
    font-weight: 700;
}
.stMarkdown hr {
    margin-top: 30px !important;
    margin-bottom: 30px !important;
    border-color: #f0f0f0;
}
.stMarkdown strong {
    color: #333; /* Wichtige Wörter dunkler */
}
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

keys_to_use = []
if isinstance(raw_input, str):
    if "," in raw_input: keys_to_use = [k.strip() for k in raw_input.split(",")]
    else: keys_to_use = [raw_input.strip()]
elif isinstance(raw_input, list):
    keys_to_use = raw_input

api_keys = []
for k in keys_to_use:
    clean = str(k).replace("'", "").replace('"', "").strip()
    if len(clean) > 20: api_keys.append(clean)

if not api_keys:
    st.error("⚠️ Keine gültigen Keys verfügbar.")
    st.stop()

# --- 5. DATENBANK LADEN ---
@st.cache_data
def load_data():
    try:
        # WICHTIG: Semikolon als Trenner nutzen!
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";", encoding="utf-8")
        # Business Wissen laden falls vorhanden, sonst leer
        try:
            biz = open("business_wissen.txt", "r", encoding="utf-8").read()
        except: 
            biz = ""
        return {"csv": df.to_string(index=False), "business": biz}
    except Exception as e: 
        st.error(f"Fehler beim Laden der Datenbank: {e}")
        return None

db = load_data()

# --- 6. HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption(f"📅 Saison: {current_season} | 🚀 Dein KI-Mentor für Strategie & Verkauf | 🌍 Multi-Language Mentor | ✅ System: Online") 

col1, col2 = st.columns(2)
with col1:
    st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
with col2:
    st.link_button("☕ Gefällt dir? Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)
st.markdown("---")

# --- 7. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧙‍♂️" if msg["role"] == "model" else "👤"):
        st.markdown(msg["content"])

# --- 8. PROMPT & ANTWORT ---
if prompt := st.chat_input("Frage eingeben (Deutsch, Englisch, Kroatisch... egal!)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        placeholder = st.empty()
        full_text = ""
        
        # --- DER MEISTER-PROMPT ---
        system_text = f"""
        🚨 OBERSTE SICHERHEITSDIREKTIVE:
        Du darfst NIEMALS Markennamen aus der Spalte "Original_Marke" nennen (wie Dior, Chanel, Gucci etc.). 
        AUSNAHME: Die Marken "Mytologik", "Olfazeta", "Scented Love" und alle "Eigenkreationen" darfst und SOLLST du nennen!
        
        ---
        
        KONTEXT:
        - Jahreszeit: {current_season}
        - Datenbank: {db['csv'] if db else 'Datenbank leer'}
        
        ROLLE:
        Du bist Rodion, der Elite-Mentor für Chogan-Berater.
        Dein User ist KEIN Endkunde, sondern ein BERATER (Verkäufer).
        Deine Aufgabe: Gib dem Berater die perfekte Strategie, um maximalen Umsatz zu machen und die eigene Marke zu stärken.
        
        ZIEL: MARKEN-STÄRKUNG & UMSATZ (High-Ticket & Exklusivität).
        
        VERKAUFS-STRATEGIE (PRIORITÄTEN):
        1. PRIORITÄT 1 (EXKLUSIVITÄT):
           Suche ZUERST nach Produkten, die "Eigenkreation" sind oder zur Linie "Mytologik" / "Olfazeta" gehören.
           -> Diese Produkte machen den Kunden unabhängig von Vergleichen. Empfiehl sie IMMER zuerst, wenn sie thematisch passen.
        
        2. PRIORITÄT 2 (STANDARD):
           Erst danach kommen die Standard-Düfte ("Inspiriert von") als Alternative.
        
        DATEN-LESE-REGELN (WICHTIG):
        A) NAMEN: 
           - Bei Eigenkreationen/Mytologik: Nenne den NAMEN aus der Spalte 'Marke_Olfazeta' (z.B. "Ares", "ASTRAL24", "Baby Boy"). Sag NICHT "Nr. Ares". Sag: "Ich empfehle dir Ares".
           - Bei Standard-Düften: Nenne "Nr. [ID]" (z.B. "Nr. 68").
        
        B) PREISE:
           - Nimm exakt den Preis aus der CSV (meist Spalte 9 'Preis_50ml' oder Spalte 10 'Preis_100ml'). Erfinde keine Preise.
           
        C) UPSELLING:
           - Lies die Spalte 'Upsell_Info'. Empfiehl genau das, was da steht.
        
        SPRACHE:
        Erkenne die Sprache der Eingabe. Antworte IMMER in der exakt gleichen Sprache wie der Nutzer!
        
        LAYOUT-PFLICHT:
        - Nutze `---` als Trennlinie.
        - Mach DOPPELTE ABSÄTZE nach jedem Punkt für Lesbarkeit.
        
        STRUKTUR-VORGABE (Nutze diese Vorlage dynamisch für bis zu 5 Empfehlungen):
        
        "Hier sind die Top-Empfehlungen(Exklusiv-Linien zuerst):
        
        ---
        
        ### 🏆 Option 1 (Exklusiv/Premium): [Name oder Nummer]
        **Das Argument für den Kunden:**
        "[Schreibe hier einen Pitch, den der Berater sagen soll. Fokus auf Einzigartigkeit/Luxus.]"
        💰 **Preis:** **[Preis aus CSV]**
        
        ---
        
        ### ✨ Option 2: [Name oder Nummer]
        **Das Argument für den Kunden:**
        "[Pitch für den Kunden]"
        💰 **Preis:** **[Preis aus CSV]**
        
        [Füge weitere Optionen 3, 4, 5 an, falls passend...]
        
        ---
        
        ### 🛍️ Cross-Selling (Umsatz-Booster):
        [Infos aus Spalte 'Upsell_Info'. Wenn leer, empfiehl allgemein passendes Duschgel.]
        
        ---
        
        ### ❓ Deine Abschlussfrage an den Kunden:
        [Gib dem Berater eine offene Frage an die Hand, z.B. Wahl zwischen Exklusiv oder Standard.]"
        """
        
        final_prompt = f"{system_text}\n\nEINGABE DES BERATERS: {prompt}"

        # --- VERBINDUNG ZU GOOGLE GEMINI ---
        success = False
        models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro"]
        random.shuffle(api_keys) # Load Balancing
        
        for model_name in models_to_try:
            if success: break
            for key in api_keys:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                    headers = {'Content-Type': 'application/json'}
                    data = {"contents": [{"parts": [{"text": final_prompt}]}]}
                    
                    response = requests.post(url, headers=headers, json=data, timeout=10)
                    
                    if response.status_code == 200:
                        result = response.json()
                        try:
                            answer = result['candidates'][0]['content']['parts'][0]['text']
                        except: 
                            answer = "⚠️ Die KI hat geantwortet, aber das Format war unerwartet."

                        # Streaming Effekt
                        for chunk in answer.split():
                            full_text += chunk + " "
                            placeholder.markdown(full_text + "▌")
                            time.sleep(0.03)
                        
                        placeholder.markdown(full_text)
                        st.session_state.messages.append({"role": "model", "content": full_text})
                        success = True
                        break 
                except Exception as e:
                    # HIER ZEIGEN WIR DEN FEHLER ANSTATT IHN ZU VERSTECKEN
                    st.error(f"Technischer Fehler bei Key ...{key[-5:]}: {e}")
                    if 'response' in locals():
                        st.error(f"Status Code: {response.status_code}")
                        st.error(f"Details: {response.text}")
                    continue
            
        if not success:
            st.error("⚠️ Verbindung fehlgeschlagen. Siehe Fehlermeldungen oben. Bitte den Fehler an Rodion schicken")
