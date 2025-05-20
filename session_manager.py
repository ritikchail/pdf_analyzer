import hashlib
import streamlit as st
import shutil
import os
from streamlit.runtime.scriptrunner import get_script_run_ctx

def get_user_id():
    if "user_id" not in st.session_state:
        try:
            ctx = st.runtime.scriptrunner.get_script_run_ctx()
            session_id = ctx.session_id if ctx else str(id(st.session_state))
        except:
            session_id = str(id(st.session_state))
        
        st.session_state.user_id = hashlib.md5(session_id.encode()).hexdigest()
    return st.session_state.user_id

def init_user_session():
    """Initialize or clear user session"""
    user_id = get_user_id()
    
    if "user_sessions" not in st.session_state:
        st.session_state.user_sessions = {}
    
    # Clear previous session data if exists
    # if user_id in st.session_state.user_sessions:
    #     clear_user_session(user_id)
    
    # Initialize fresh session
        st.session_state.user_sessions[user_id] = {
            "messages": [{"role": "assistant", "content": "Upload a PDF to get started!"}],
            "processed_files": set(),
            "current_file": None
        }
    return user_id

def clear_user_session(user_id):
    """Clean up Chroma DB files when session ends"""
    chroma_path = f"./chroma_db_{user_id}"
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)

# def cleanup_chroma(user_id):
#     """Atomic cleanup that always runs"""
#     chroma_path = f"./chroma_db_{user_id}"
#     try:
#         if os.path.exists(chroma_path):
#             shutil.rmtree(chroma_path, ignore_errors=True)
#     except:
#         pass  # Prevents any cleanup from crashing the ap

def cleanup_chroma(path):
    """Atomic, deployment-safe cleanup"""
    try:
        # 1. Unlock files (critical for Windows/cloud)
        for root, dirs, files in os.walk(path):
            for file in files:
                os.chmod(os.path.join(root, file), 0o777)  # Force unlock
        
        # 2. Atomic deletion (works on all OS)
        shutil.rmtree(path, ignore_errors=True)
        
        # 3. Verify
        return not os.path.exists(path)
    except:
        return False