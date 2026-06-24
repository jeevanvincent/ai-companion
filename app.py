import streamlit as st
import time
import random
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & ARTISTIC PASTEL LAYOUT
# -----------------------------------------------------------------------------
st.set_page_config(page_title="AI Companion", page_icon="🔮", layout="centered")

st.markdown("""
    <style>
    /* Global artistic background */
    .stApp {
        background: linear-gradient(135deg, #E0EAFC 0%, #CFDEF3 50%, #E8F0F8 100%) !important;
        background-attachment: fixed;
    }
    
    /* Clean, single bold header */
    .bold-header {
        text-align: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        font-size: 2.5rem;
        color: #2C3E50;
        margin-top: -30px;
        margin-bottom: 25px;
    }
    
    /* Distinct Floating Chat Canvas Area separating chat from non-chat parts */
    [data-testid="stChatMessageContainer"] {
        background: rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 20px !important;
    }

    /* Keep all text dark slate and highly visible */
    .stMarkdown p, .stMarkdown span, .stMarkdown li {
        color: #2C3E50 !important;
        font-weight: 550 !important;
    }
    
    /* USER MESSAGE: Right aligned pastel rose gold tint */
    [data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, #FFDEE9 0%, #FFB6C1 100%) !important;
        margin-left: auto !important;
        border-radius: 15px !important;
        border-bottom-right-radius: 2px !important;
        width: fit-content !important;
        max-width: 80% !important;
    }
    
    /* AI ASSISTANT MESSAGE: Left aligned pastel soft blue mint */
    [data-testid="stChatMessageAssistant"] {
        background: linear-gradient(135deg, #E0F2F1 0%, #D0E1FD 100%) !important;
        margin-right: auto !important;
        border-radius: 15px !important;
        border-bottom-left-radius: 2px !important;
        width: fit-content !important;
        max-width: 80% !important;
    }
    
    /* Clean input bar */
    .stChatInput {
        border-radius: 20px !important;
    }
    
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CLEAN HEADER
# -----------------------------------------------------------------------------
st.markdown('<div class="bold-header">AI Companion</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. INITIALIZE CLIENT & CHAT HISTORY
# -----------------------------------------------------------------------------
if "ai_client" not in st.session_state:
    # Safe for GitHub; reads your key from Streamlit Cloud's advanced settings vault
    st.session_state.ai_client = genai.Client()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

AI_PERSONA = (
    "You are a supportive, witty, and highly adaptive AI companion. "
    "Your personality is warm, helpful, charming, and intelligent. "
    "Balance empathy with candor. Always use clear Markdown formatting."
)

# -----------------------------------------------------------------------------
# 4. RENDER CHAT HISTORY USING ORIGINAL TEMPLATE STRUCTURE
# -----------------------------------------------------------------------------
for message in st.session_state.chat_history:
    avatar_logo = "🧑‍💻" if message["role"] == "user" else "🔮"
    with st.chat_message(message["role"], avatar=avatar_logo):
        st.markdown(message["content"])

# -----------------------------------------------------------------------------
# 5. CONVERSATION LOOP WITH RETRY LOGIC
# -----------------------------------------------------------------------------
if user_prompt := st.chat_input("Chit-chat with your companion here..."):
    
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_prompt)
    
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    formatted_contents = [
        types.Content(role=m["role"], parts=[types.Part.from_text(text=m["content"])])
        for m in st.session_state.chat_history
    ]

    with st.chat_message("assistant", avatar="🔮"):
        response_placeholder = st.empty()
        full_response = ""
        
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            try:
                response_stream = st.session_state.ai_client.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=formatted_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=AI_PERSONA,
                        temperature=0.7
                    )
                )
                
                for chunk in response_stream:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + " 🌸")
                    
                response_placeholder.markdown(full_response)
                st.session_state.chat_history.append({"role": "model", "content": full_response})
                success = True
                break
                
            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    wait_time = 1.5 + random.random()
                    response_placeholder.markdown(f"*Server busy, stabilizing connection (Attempt {attempt+1}/{max_retries})...*")
                    time.sleep(wait_time)
                else:
                    st.error(f"An execution error occurred: {str(e)}")
                    break

