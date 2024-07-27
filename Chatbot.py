from openai import OpenAI
import streamlit as st

# Retrieve the API key from Streamlit secrets
openai_api_key = st.secrets["openai"]["api_key"]

client = OpenAI(api_key=openai_api_key)
with st.sidebar:
    st.text_input("OpenAI API Key (Loaded from secrets)", value=openai_api_key, type="password", disabled=True)
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

uploaded_files = st.file_uploader("Upload an image or PDF", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.type in ["image/jpeg", "image/png"]:
            st.image(uploaded_file)
        elif uploaded_file.type == "application/pdf":
            st.write(f"Uploaded PDF: {uploaded_file.name}")
            st.download_button("Download PDF", uploaded_file.getvalue(), file_name=uploaded_file.name)
            # Convert PDF to bytes
            pdf_bytes = uploaded_file.getvalue()
            # Add a message indicating the presence of the PDF
            st.session_state["messages"].append({"role": "system", "content": f"[Attached PDF: {uploaded_file.name}]"})

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    user_message = {"role": "user", "content": prompt}
    if uploaded_files:
        user_message["content"] += f"\n\n[Attached PDF: {uploaded_files[0].name}]"

    st.session_state.messages.append(user_message)
    st.chat_message("user").write(user_message["content"])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a helpful assistant."}] + st.session_state.messages
        )
        msg = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
