import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- SIDEBAR (SOCIALS & SUPPORT) ---
with st.sidebar:
    st.title("Connect")
    st.markdown("---")
    
    # 1. Instagram
    st.write("**Folge mir:**")
    st.link_button(
        label="📸 Mein Instagram", 
        url="https://www.instagram.com/rodionpopow", # <--- HIER DEINEN NAMEN EINTRAGEN
        icon="📱" 
    )
    
    st.markdown("---")
    
    # 2. PayPal / Support
    st.write("**Gefällt dir das Tool?**")
    st.caption("Unterstütze die Weiterentwicklung:")
    st.link_button(
        label="☕ Spendier mir einen Kaffee", 
        url="https://www.paypal.com/paypalme/RodionPopow", # <--- HIER DEINEN PAYPAL LINK EINTRAGEN
        type="primary" # Macht den Button rot/auffällig
    )
    st.markdown("---")
    st.caption("© 2026 Rodion Popow")

# --- CSS ---
st.markdown("""
<style>
.footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: black; text-align: center; padding: 10px; font-size: 12px;}
.stChatInput {position: fixed; bottom: 50px;}
</style>
<div class="footer">Olfazeta Business Intelligence Tool - Powered by Gemini 2.5 AI</div>
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
        # CSV laden (mit Marken für interne Suche)
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

# --- CHAT ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.caption("Dein KI-Partner für Vertrieb & Strategie. (Hinweis: Fehler 429 = Zu viele Anfragen, bitte warten)")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Frag mich nach Düften, Produkten, Business-Strategien oder Einwandbehandlung."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Befehl eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Web-Check
    web_context = ""
    if not any(x in prompt.lower() for x in ["plan", "agb", "versand", "geld", "start", "einwand"]):
        with st.status("Prüfe Duftnoten...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Check fertig.", state="complete")

    # --- SYSTEM PROMPT (NEUTRAL & SICHER) ---
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
    - Beispiel Falsch: "Das ist genau dein Ding, Bruder."
    - Beispiel Richtig: "Das ist genau das Richtige für dich."

    UPSELLING:
    - Wenn 'Upsell_Info' in der CSV steht, biete es immer an.

    TONALITÄT:
    - Kurz, professionell, direkt. Preise **fett**.

    Antworte auf: "{prompt}"
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_instruction)
        history = [{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"]
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)
        
        with st.chat_message("model"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "model", "content": response.text})

    except Exception as e:
        st.error(f"Fehler: {e}")
