import streamlit as st
import requests
import uuid
import os

# Get the meraki-llm service host from environment variable or default
MERAKI_LLM_HOST = os.environ.get("MERAKI_LLM_HOST", "meraki-llm")
AGENT_APP_NAME = "agent" # Use the correct agent app name
AGENT_RUN_URL = f"http://{MERAKI_LLM_HOST}/run"
AGENT_SESSION_URL_TEMPLATE = f"http://{MERAKI_LLM_HOST}/apps/{AGENT_APP_NAME}/users/{{user_id}}/sessions/{{session_id}}"

# Function to initialize the agent session
def initialize_session(user_id, session_id):
    session_url = AGENT_SESSION_URL_TEMPLATE.format(user_id=user_id, session_id=session_id)
    headers = {"Content-Type": "application/json"}
    # Provide an empty initial state, adjust if your agent needs specific initial state
    payload = {"state": {}} 
    try:
        response = requests.post(session_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status() # Check for HTTP errors
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to initialize agent session: {e}")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during session initialization: {e}")
        return False

# Function to call the agent's /run endpoint
def call_agent_run(user_id, session_id, prompt_text):
    headers = {"Content-Type": "application/json"}
    payload = {
        "app_name": AGENT_APP_NAME,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": prompt_text}]
        }
    }
    try:
        response = requests.post(AGENT_RUN_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status() # Raise an exception for bad status codes
        
        # The /run endpoint returns a list of event objects
        events = response.json()
        
        # Extract the final text response from the last event
        final_text_response = ""
        if events and isinstance(events, list):
            for event in reversed(events):
                if (event.get("content") and 
                    event["content"].get("role") == "model" and 
                    event["content"].get("parts") and 
                    isinstance(event["content"]["parts"], list) and
                    len(event["content"]["parts"]) > 0 and
                    event["content"]["parts"][0].get("text")):
                    final_text_response = event["content"]["parts"][0]["text"]
                    break # Found the text response
        
        if not final_text_response:
             final_text_response = f"Received response, but couldn't extract text content"

        return final_text_response

    except requests.exceptions.RequestException as e:
        st.error(f"Error contacting agent: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

st.title(f"Chat with {AGENT_APP_NAME} (HTTP)")

# Initialize chat history and session ID
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_initialized" not in st.session_state:
    st.session_state.session_initialized = False
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.user_id = "streamlit_user" # Keep user ID consistent

# Initialize session only if not already done
if not st.session_state.session_initialized:
    if initialize_session(st.session_state.user_id, st.session_state.session_id):
         st.session_state.session_initialized = True
    else:
        # Stop execution if session initialization fails
        st.error("Critical Error: Could not initialize agent session. Chat functionality disabled.")
        st.stop()

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What is up?"):
    # Add user message to display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the agent and display response
    with st.spinner("Waiting for agent..."):
        agent_response = call_agent_run(
            st.session_state.user_id,
            st.session_state.session_id,
            prompt
        )
    
    if agent_response:
        st.session_state.messages.append({"role": "assistant", "content": agent_response})
        with st.chat_message("assistant"):
            st.markdown(agent_response)
    else:
        # Error message already shown by call_agent_run
        pass 