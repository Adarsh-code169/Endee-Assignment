import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="RAG Research Assistant", page_icon="📚", layout="wide")

# --- custom CSS for a polished look ---
st.markdown("""
<style>
    /* main background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }

    /* header styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #818cf8, #a78bfa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 1rem;
        color: #94a3b8;
        margin-top: 0;
        margin-bottom: 2rem;
    }

    /* chat messages */
    .stChatMessage {
        border-radius: 12px;
        border: 1px solid rgba(99, 102, 241, 0.1);
        background: rgba(30, 30, 50, 0.5) !important;
        backdrop-filter: blur(10px);
    }

    /* buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #818cf8, #a78bfa);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        transform: translateY(-1px);
    }

    /* file uploader */
    .stFileUploader {
        border: 2px dashed rgba(99, 102, 241, 0.3);
        border-radius: 10px;
        padding: 1rem;
    }

    /* metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #818cf8;
    }

    /* expander (sources) */
    .streamlit-expanderHeader {
        background: rgba(99, 102, 241, 0.1);
        border-radius: 8px;
    }

    /* chat input */
    .stChatInput {
        border-color: rgba(99, 102, 241, 0.3);
    }

    /* success/error messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1);
        border-left: 4px solid #22c55e;
    }
    .stError {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
    }

    /* divider */
    hr {
        border-color: rgba(99, 102, 241, 0.15);
    }

    /* welcome card */
    .welcome-card {
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 3rem auto;
        max-width: 600px;
    }
    .welcome-card h3 {
        color: #c4b5fd;
        margin-bottom: 1rem;
    }
    .welcome-card p {
        color: #94a3b8;
        font-size: 0.95rem;
    }

    /* status badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-online {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .status-offline {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- sidebar ---
with st.sidebar:
    st.markdown("### 📄 Document Upload")
    st.markdown('<p style="color: #94a3b8; font-size: 0.85rem;">Upload research papers to start asking questions</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded_file and st.button("⬆️ Process Document", use_container_width=True):
        with st.spinner("Processing..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            try:
                resp = requests.post(f"{API_URL}/upload", files=files, timeout=120)
                if resp.status_code == 200:
                    result = resp.json()
                    st.success(f"✅ {result['message']}")
                    st.session_state["doc_count"] = st.session_state.get("doc_count", 0) + 1
                else:
                    st.error(f"Error: {resp.json().get('detail', resp.text)}")
            except requests.ConnectionError:
                st.error("Can't connect to backend — is FastAPI running?")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()

    # stats section
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📄 Docs", st.session_state.get("doc_count", 0))
    with col2:
        st.metric("💬 Chats", len(st.session_state.get("messages", [])) // 2)

    # backend health check
    try:
        health = requests.get(f"{API_URL}/health", timeout=3)
        if health.status_code == 200:
            st.markdown('<span class="status-badge status-online">● Backend Online</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge status-offline">● Backend Offline</span>', unsafe_allow_html=True)
    except:
        st.markdown('<span class="status-badge status-offline">● Backend Offline</span>', unsafe_allow_html=True)

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # footer
    st.markdown("---")
    st.markdown(
        '<p style="color: #64748b; font-size: 0.75rem; text-align: center;">'
        'Built with Endee Vector DB<br>& Groq (Llama 3.1)'
        '</p>',
        unsafe_allow_html=True
    )

# --- main area ---
st.markdown('<h1 class="main-title">📚 Intelligent Research Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Upload papers, ask questions, get cited answers — powered by RAG</p>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# show welcome card if no messages yet
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        <h3>👋 Welcome!</h3>
        <p>
            Upload a research paper using the sidebar, then ask me anything about it.<br><br>
            I'll search through the document semantically and give you answers with page-level citations.
        </p>
    </div>
    """, unsafe_allow_html=True)

# render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("citations"):
            with st.expander("📖 View Sources"):
                for i, c in enumerate(msg["citations"]):
                    st.markdown(f"**Source {i+1}** — `{c.get('filename')}` (Page {c.get('page_number')})")

# handle new message
if prompt := st.chat_input("Ask a question about your documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching & generating answer..."):
            try:
                history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                resp = requests.post(f"{API_URL}/chat", json={"message": prompt, "history": history}, timeout=60)

                if resp.status_code == 200:
                    data = resp.json()
                    st.markdown(data["answer"])

                    citations = data.get("citations", [])
                    if citations:
                        with st.expander("📖 View Sources"):
                            for i, c in enumerate(citations):
                                st.markdown(f"**Source {i+1}** — `{c.get('filename')}` (Page {c.get('page_number')})")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data["answer"],
                        "citations": citations
                    })
                else:
                    st.error(f"Error: {resp.json().get('detail', resp.text)}")
            except requests.ConnectionError:
                st.error("Can't reach the backend — make sure FastAPI is running")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
