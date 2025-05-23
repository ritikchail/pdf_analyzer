import streamlit as st
from processing import process_pdf
from session_manager import init_user_session, get_user_id, cleanup_chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv
import atexit
import os


os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

load_dotenv()
# Initialize session
user_id = init_user_session()
user_data = st.session_state.user_sessions[user_id]

# --- UI ---
st.title("📄 PDF Chat Assistant")

# Sidebar for file upload
with st.sidebar:
    st.header("Document Upload")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_file and uploaded_file.name not in user_data["processed_files"]:
        with st.spinner("Processing PDF..."):
            # try:
                user_data["vectorstore"] = process_pdf(uploaded_file, user_id)
                user_data["processed_files"].add(uploaded_file.name)
                user_data["current_file"] = uploaded_file.name
                st.success("PDF processed!")
            # except Exception as e:
            #     st.error(f"Error: some error")

if st.sidebar.button("🧹 Delete All My Data"):
    if cleanup_chroma(f"chroma_db_{user_id}"):
        st.success("Data wiped!")
    else:
        st.error("Retry or contact support")  # Refresh UI
# Display chat messages
chat_container = st.container()  # 🚀 Key fix: Isolate chat display
with chat_container:  # Wrap message display
    for msg in user_data["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# Chat input
if prompt := st.chat_input("Ask about your PDF"):
    # Add user message
    user_data["messages"].append({"role": "user", "content": prompt})
    # st.write(prompt)
    st.chat_message("user").write(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Simple QA flow
                llm  = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash-latest",
                    google_api_key= st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY")) ,  # From Streamlit secrets
                    temperature=0.3
                )
                
                if "vectorstore" in user_data:
                    retriever = user_data["vectorstore"].as_retriever(k=2)
                    qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)
                    response = qa_chain.invoke(prompt)["result"]
                else:
                    response = "Please upload a PDF first"
                
                st.write(response)
                user_data["messages"].append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.write(error_msg)
                user_data["messages"].append({"role": "assistant", "content": error_msg})

atexit.register(cleanup_chroma, f"chroma_db_{user_id}")
# Clear session when tab is closed (handled automatically by cleanup)