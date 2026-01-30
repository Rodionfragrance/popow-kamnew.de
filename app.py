import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS
import time  # WICHTIG für die Wartezeit

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- CSS ---
st.markdown("""
<style>
.footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: black; text-align: center; padding: 10px; font-size: 12px;}
.stChatInput {position: fixed; bottom: 50px;}
/* Avatar Styling: Weißer Hintergrund */
.stChatMessage .stChatMessageAvatar {
    background-color: #ffffff !important;
}
</style>
<div class="footer">Olfazeta Business Intelligence Tool - Powered by Gemini AI</div>
""", unsafe_allow_html=True)

# --- API KEY HANDLING ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ API Key fehlt! Bitte in Streamlit Secrets hinterlegen.")
    st.stop()

# --- DATEN LADEN ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        csv_text = df.to_string(index=False)
        with open("business_wissen.txt", "r", encoding="utf-8") as f:
            txt_text = f.read()
        return {"csv": csv_text, "business": txt_text}
    except Exception as e:
        return None

db = load_data()
if not db:
    st.error("Datenbank fehlt auf GitHub!")
    st.stop()

# --- WEB SUCHE ---
def get_trend_info(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} Duftnoten Beschreibung", max_results=1))
            return results[0]['body'] if results else ""
    except: return ""

# --- MAIN HEADER (Sichtbar auf Handy & PC) ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption("Dein KI-Partner für Vertrieb & Strategie.")

# BUTTONS (Breit für Handy)
col1, col2 = st.columns(2)

with col1:
    st.link_button(
        label="Mein Instagram", 
        url="https://www.instagram.com/rodionpopow", 
        icon="📸 ",
        use_container_width=True
    )

with col2:
    st.link_button(
        label="Gefällt dir? Spendier mir einen Kaffee", 
        url="https://www.paypal.com/paypalme/RodionPopow", 
        type="primary", 
        icon="☕",
        use_container_width=True
    )

st.markdown("---")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Frag mich nach Düften, Produkten, Business-Strategien oder Einwandbehandlung."}]

# Verlauf anzeigen (Mit Zauberer-Icon)
for message in st.session_state.messages:
    icon = "🧙‍♂️" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

if prompt := st.chat_input("Frage eingeben..."):
    # User Nachricht anzeigen
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Web-Check
    web_context = ""
    if not any(x in prompt.lower() for x in ["plan", "agb", "versand", "geld", "start", "einwand"]):
        with st.status("Prüfe Duftnoten...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Check fertig.", state="complete")

    # --- SYSTEM PROMPT ---
    system_instruction = f"""
    Du bist Rodion, Elite-Mentor für Olfazeta.
    
    WISSEN:
    1. PRODUKTE (CSV): {db['csv']}
    2. BUSINESS (TXT): {db['business']}
    3. EXTERNE INFOS: {web_context}

    🔴 REGEL NR. 1: DER STILLE FILTER (Markenschutz)
    - Nutze die Spalte "Original_Marke" NUR zum Verstehen der Suche.
    - Nenne NIEMALS den fremden Markennamen in der Antwort.
    - Sag stattdessen: "Wenn du diesen [Duftrichtung]-Vibe suchst, empfehle ich unsere **Nr. XY**."

    🔴 REGEL NR. 2: ANSPRACHE (GENDER NEUTRAL)
    - Gehe NICHT davon aus, dass der User männlich ist.
    - Vermeide Anreden wie "Bruder", "Kumpel", "Mein Lieber" oder "Mann".
    - Nutze ein professionelles, direktes "Du".

    UPSELLING:
    - Wenn 'Upsell_Info' in der CSV steht, biete es immer an.

    TONALITÄT:
    - Kurz, professionell, direkt. Preise **fett**.

    Antworte auf: "{prompt}"
    """

    # --- ANTI-CRASH LOGIK (3 Versuche) ---
    full_response = ""
    
    try:
        # Wir versuchen es 3 Mal
        for attempt in range(3):
            try:
                # Modell-Wahl
                model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_instruction)
                history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
                chat = model.start_chat(history=history)
                
                # Anfrage senden
                response = chat.send_message(prompt)
                full_response = response.text
                break # Wenn es klappt, brechen wir die Schleife ab (Erfolg!)
            
            except Exception as e:
                # Wenn es ein "Rate Limit" (429) Fehler ist:
                if "429" in str(e):
                    # Wartezeit anzeigen
                    wait_time = 5 * (attempt + 1)
                    with st.spinner(f"Viel los gerade... Warte kurz ({attempt+1}/3)..."):
                        time.sleep(wait_time)
                    continue # Nächster Versuch
                else:
                    # Anderer Fehler? Dann raus hier.
                    raise e
        
        # --- ANTWORT ODER NOTFALL-NACHRICHT ---
        if full_response:
            with st.chat_message("model", avatar="🧙‍♂️"):
                st.markdown(full_response)
            st.session_state.messages.append({"role": "model", "content": full_response})
        else:
            # Wenn es nach 3 Versuchen immer noch leer ist:
            st.error("⚠️ Die KI ist gerade extrem überlastet (Fehler 429). Bitte warte 1 Minute und versuche es erneut.")

    except Exception as e:
        st.error(f"Ein technischer Fehler ist aufgetreten: {e}")
