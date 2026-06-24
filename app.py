import streamlit as st
from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# 1. PAGE SETUP & CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="AI Companion Sandbox", page_icon="🤖", layout="centered")
st.title("🤖 My Custom AI Companion")
st.caption("A stateful AI companion featuring a custom persona and persistent chat memory.")

# -----------------------------------------------------------------------------
# 2. THE PERSONA ENGINE (SYSTEM INSTRUCTIONS)
# -----------------------------------------------------------------------------
# Modify this text to entirely change your AI's personality, behavior, or goals!
AI_PERSONA = (
    "You are a supportive, highly adaptive AI collaborator with a touch of wit. "
    "Your goal is to address the user's true intent with clear, concise, and insightful responses. "
    "Balance empathy with candor: validate the user's feelings authentically while correcting "
    "significant misinformation gently yet directly—like a helpful peer. "
    "Subtly adapt your tone, energy, and humor to match the user's style. "
    "Always use clear Markdown formatting (bullet points, bold text) to avoid dense blocks of text."
)

# -----------------------------------------------------------------------------
# 3. INITIALIZE STATE & INITIAL CHAT ENGINE
# -----------------------------------------------------------------------------
# Initialize your API client. It automatically looks for the GEMINI_API_KEY env variable,
# or you can paste your string directly inside: genai.Client(api_key="AIzaSy...")
if "ai_client" not in st.session_state:
    try:
        st.session_state.ai_client = genai.Client()
    except Exception as e:
        st.error("API Client initialization failed. Ensure your GEMINI_API_KEY environment variable is set.")
        st.stop()

# Initialize conversational session history if it doesn't exist
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------------------------------------------------------
# 4. RENDER PREVIOUS MESSAGES (To keep UI consistent across script reruns)
# -----------------------------------------------------------------------------
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------------------------------------------------------
# 5. CONVERSATION LOOP
# -----------------------------------------------------------------------------
# Wait for user input at the bottom of the screen
if user_prompt := st.chat_input("Say something to your companion..."):
    
    # Immediately render user message to the UI
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    # Commit the user's message to the session memory tracking array
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    # Prepare payload back to the Model API. 
    # We map our flat history list into the structural types expected by the SDK.
    formatted_contents = [
        types.Content(role=m["role"], parts=[types.Part.from_text(text=m["content"])])
        for m in st.session_state.chat_history
    ]

    # Generate streaming response container from assistant
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # Call the Google Gen AI API using the lightweight streaming protocol
            response_stream = st.session_state.ai_client.models.generate_content_stream(
                model="gemini-2.5-flash",  # High-speed conversational baseline
                contents=formatted_contents,
                config=types.GenerateContentConfig(
                    system_instruction=AI_PERSONA,
                    temperature=0.7 # Slight randomness for conversational flair
                )
            )
            
            # Unpack chunks as they fly back in real time
            for chunk in response_stream:
                full_response += chunk.text
                # Dynamically update UI text block
                response_placeholder.markdown(full_response + "▌")
                
            # Clean up the trailing cursor typing visual once generation completes
            response_placeholder.markdown(full_response)
            
            # Commit the AI's final answer to persistent session state memory
            st.session_state.chat_history.append({"role": "model", "content": full_response})
            
        except Exception as e:
            st.error(f"An execution error occurred: {str(e)}")