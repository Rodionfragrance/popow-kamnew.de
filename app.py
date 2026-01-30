import streamlit as st
import pandas as pd
from google import genai
from google.genai import types # WICHTIG für das neue Format
import time
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Rodions Chogan KI", page_icon="🧙‍♂️", layout="wide")

# --- CSS ---
st.markdown("""
<style>
.footer {position: fixed; left: 0; bottom: 0; width: 100%; background-color: #f1f1f1; color: black; text-align: center; padding: 10px; font-size: 12px; z-index: 100;}
.stChatInput {position: fixed; bottom: 50px;}
.stChatMessage .stChatMessageAvatar { background-color: #ffffff !important; }
</style>
<div class="footer">Olfazeta Business Intelligence Tool - Powered by Gemini AI</div>
""", unsafe_allow_html=True)

# --- API KEYS ---
if "API_KEYS" in st.secrets:
    api_keys = st.secrets["API_KEYS"]
elif "GOOGLE_API_KEY" in st.secrets:
    api_keys = [st.secrets["GOOGLE_API_KEY"]]
else:
    st.error("⚠️ Keine API-Keys gefunden!")
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
    except: return None

db = load_data()

# --- HEADER ---
st.title("🧙‍♂️ Rodions Chogan KI")
st.link_button("📸 Mein Instagram", "https://www.instagram.com/rodionpopow", use_container_width=True)
st.link_button("☕ Kaffee spendieren", "https://www.paypal.com/paypalme/RodionPopow", type="primary", use_container_width=True)
st.markdown("---")

# --- CHAT LOGIK ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    icon = "🧙‍♂️" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=icon):
        st.markdown(message["content"])

if prompt := st.chat_input("Frage eingeben..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🧙‍♂️"):
        message_placeholder = st.empty()
        full_response = ""
        
        # DER FIX: System Instruction als korrektes Objekt-Format
        sys_instr = types.Content(
            parts=[types.Part(text=f"Du bist Rodion, Elite-Mentor für Olfazeta. WISSEN: {db['csv'] if db else ''} {db['business'] if db else ''}. REGELN: Nenne NIE Fremdmarken. Preise fett. Sei direkt.")]
        )

        success = False
        for attempt in range(len(api_keys)):
            try:
                client = genai.Client(api_key=random.choice(api_keys))
                
                # Streaming Starten
                response = client.models.generate_content_stream(
                    model='gemini-1.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=sys_instr,
                        temperature=0.7
                    )
                )
                
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "model", "content": full_response})
                success = True
                break
            except Exception as e:
                if attempt == len(api_keys) - 1:
                    st.error(f"Fehler: {str(e)}")
                else:
                    time.sleep(1)
                    continue
