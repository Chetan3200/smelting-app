from openai import OpenAI
import os
import json
import streamlit as st
from streamlit_js_eval import streamlit_js_eval


OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']
assistantID = st.secrets['assistantID']
messageID = st.secrets['messageID']

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

model_name = "gpt-4-0125-preview"

client = OpenAI()

st.set_page_config(page_title="Realtime Assistant pipeline", page_icon=":memo:")
st.title("Smelting Manual Assistant 🤖")

def create_new_thread():
    new_thread = client.beta.threads.create()
    new_thread_id = new_thread.id
    with open("/home/crimsondawn/streamlit_app/smelting_app/thread_ids.json", "r") as file:
        thread_ids = json.load(file)
    thread_ids.append(new_thread_id)
    with open("/home/crimsondawn/streamlit_app/smelting_app/thread_ids.json", "w") as file:
        json.dump(thread_ids, file)


# function to delete the selected thread from the thread_ids.json file
def delete_selected_thread(thread_id):
    with open("/home/crimsondawn/streamlit_app/smelting_app/thread_ids.json", "r") as file:
        thread_ids = json.load(file)
    thread_ids.remove(thread_id)
    with open("/home/crimsondawn/streamlit_app/smelting_app/thread_ids.json", "w") as file:
        json.dump(thread_ids, file)


# Allow the user to upload a JSON file
uploaded_file = st.sidebar.file_uploader("Upload JSON file", type=["json"])

# If a file was uploaded
if uploaded_file is not None:
    content = uploaded_file.getvalue()
    try:
        thread_ids = json.loads(content)
        with open("/home/crimsondawn/streamlit_app/smelting_app/thread_ids.json", "w") as file:
            json.dump(thread_ids, file)

    except json.JSONDecodeError:
        st.write("Error: Invalid JSON file.")
else:
    with open("/home/crimsondawn/streamlit_app/smelting_app/thread_ids.json", "r") as file:
        thread_ids = json.load(file) 

# Apply custom formatting to the sidebar navigation
sidebar_title_style = """
    font-size: 24px;
    font-weight: bold;
    border-bottom: 2px solid #f0f0f0;
    margin-bottom: 10px;
"""
sidebar_radio_style = """
    font-size: 18px;
"""

# Apply custom styles to the sidebar elements
st.sidebar.markdown('<p style="' + sidebar_title_style + '">Navigation</p>', unsafe_allow_html=True)

selected_thread = st.sidebar.radio("Select Thread", thread_ids, format_func=lambda x: f"Chat: {x}", key="thread_selector", help="Select the thread")
    
if st.sidebar.button("new chat"):
    create_new_thread()
    streamlit_js_eval(js_expressions="parent.window.location.reload()")


if st.sidebar.button("delete"):
    delete_selected_thread(selected_thread)
    streamlit_js_eval(js_expressions="parent.window.location.reload()")
    
def save_thread_ids():
    thread_ids_json = json.dumps(thread_ids)
    return thread_ids_json

# Export the thread_ids from session state as JSON file
btn = st.sidebar.download_button("Download threads as JSON",
                                save_thread_ids(), 
                                file_name="thread_ids.json"
                                )



if selected_thread:
    st.write(f"messages for thread id: {selected_thread}")

    if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat thread
        message = {
        "role": "user",
        "content": prompt,
        "attachments": [
            { "file_id": messageID, "tools": [{"type": "file_search"}] }
        ],
        }

        message_appended = client.beta.threads.messages.create(
            thread_id=selected_thread,
            role=message["role"],
            content=message["content"]
        )
        run = client.beta.threads.runs.create_and_poll(
            thread_id=selected_thread,
            assistant_id=assistantID,
        )

    # obtain messages for the selected thread
    messages = client.beta.threads.messages.list(thread_id=selected_thread)
    
    # display messages
    for message in reversed(messages.data):
        with st.chat_message(message.role):
            st.write(message.content[0].text.value)