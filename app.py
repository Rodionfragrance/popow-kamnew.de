import streamlit as st
import pandas as pd
import google.generativeai as genai
from duckduckgo_search import DDGS

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Business-Hub", page_icon="🦁", layout="wide")

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
        df = pd.read_csv("master_duft_datenbank_ULTIMATE.csv", sep=";")
        csv_text = df.to_string(index=False)
        with open("business_wissen.txt", "r", encoding="utf-8") as f:
            txt_text = f.read()
        return {"csv": csv_text, "business": txt_text}
    except Exception as e:
        return None

db = load_data()

if not db:
    st.error("FEHLER: Datenbank-Dateien (CSV/TXT) fehlen auf GitHub!")
    st.stop()

# --- LIVE WEB SUCHE ---
def get_trend_info(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{query} Parfum Trend Erfahrung 2026", max_results=2))
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results]) if results else ""
    except: return ""

# --- CHAT ---
st.title("🦁 Rodions Chogan Chat KI")
st.caption("Dein KI-Partner für Vertrieb & Strategie.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Servus. Ich bin bereit. Frag mich nach Düften (Olfazeta Nummern), Upsells oder Business-Regeln."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Befehl eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Web-Check
    web_context = ""
    if not any(x in prompt.lower() for x in ["plan", "agb", "versand", "geld"]):
        with st.status("Analysiere Live-Trends...", expanded=False) as status:
            web_context = get_trend_info(prompt)
            status.update(label="Check fertig.", state="complete")

    # --- INTELLIGENTER PROMPT (SAFE MODE) ---
    system_instruction = f"""
    Du bist Rodion, ein Elite-Mentor für Olfazeta.
    
    WISSEN:
    1. PRODUKTE (CSV): {db['csv']}
    2. BUSINESS (TXT): {db['business']}
    3. LIVE-WEB: {web_context}

    STRENGE REGELN FÜR DEN VERKAUF:
    
    1. MARKEN-SCHUTZ (WICHTIG!):
       - Du verkaufst **AUSSCHLIESSLICH** Produkte von "Olfazeta", "Aurodhea", "SuppleFit" oder "Mytologik".
       - Wenn der Kunde nach einer Fremdmarke fragt (z.B. "Hast du Dior Sauvage?"), darfst du **NIEMALS** sagen: "Ja, hier ist es."
       - Du musst sagen: "Wir führen keine Fremdmarken. Aber ich empfehle dir unsere **Olfazeta Nr. 94**. Die geht genau in diese würzig-frische Duftrichtung."
       - Benutze Markennamen NUR als Referenz für die Duftfamilie ("Riecht wie...", "Duftzwilling zu..."), nie als Produktnamen.

    2. UPSELLING:
       - Prüfe die CSV-Spalte 'Upsell_Info'. Wenn dort etwas steht, biete es aktiv an.

    3. BUSINESS-COACH:
       - Bei Fragen zu Geld/Karriere: Zitiere den Marketingplan 2026 exakt. Fantasiere keine Zahlen.

    4. TONALITÄT:
       - Direkt, maskulin, professionell. Preise immer **fett**.

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
