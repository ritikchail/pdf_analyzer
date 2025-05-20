from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import tempfile
import os
from dotenv import load_dotenv

def process_pdf(uploaded_file, user_id):
    """Handle PDF processing and return vectorstore"""
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    # Load and split PDF
    loader = PyPDFLoader(tmp_path)
    pages = loader.load()
    
    # Split text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    chunks = text_splitter.split_documents(pages)
    
    # Add metadata
    for chunk in chunks:
        chunk.metadata["source"] = uploaded_file.name
    
    # Create/update vectorstore
    embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key= st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))  # From Streamlit secrets
)
    vectorstore = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=f"./chroma_db_{user_id}"
    )
    
    # Clean up temp file
    os.unlink(tmp_path)
    
    return vectorstore