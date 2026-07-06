import streamlit as st
import sys
import os

sys.path.append(
    os.path.dirname(os.path.abspath(__file__))
)

from rag import (
    load_llm,
    load_embeddings,
    process_faq_documents,
    build_faq_chain,
    get_confidence_score
)
from  utills import (
    display_chat
    
)

# ─────────────────────────────────────
# Page Config
# ─────────────────────────────────────
st.set_page_config(
    page_title = "FAQ Bot",
    page_icon  = "💬",
    layout     = "wide"
)

# ─────────────────────────────────────
# Load Models
# ─────────────────────────────────────
@st.cache_resource(show_spinner="Loading AI Model...")
def get_llm():
    return load_llm()

@st.cache_resource(show_spinner="Loading Embeddings...")
def get_embeddings():
    return load_embeddings()

llm        = get_llm()
embeddings = get_embeddings()

# ─────────────────────────────────────
# Session State
# ─────────────────────────────────────
defaults = {
    "messages"    : [],
    "faq_chain"   : None,
    "retriever"   : None,
    "chunks"      : None,
    "doc_names"   : [],
    "processed"   : False,
    "show_sources": True
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────
# Title
# ─────────────────────────────────────
st.title("💬 FAQ Bot")
st.write("Upload FAQ documents and get instant answers!")
st.divider()

# ─────────────────────────────────────
# Sidebar
# ─────────────────────────────────────
with st.sidebar:
    st.title("Settings")
    st.divider()

    st.subheader("Upload FAQ Documents")
    st.write("Supported: PDF, DOCX, TXT")

    uploaded_files = st.file_uploader(
        "Choose files",
        type                  = ["pdf", "docx", "txt"],
        accept_multiple_files = True
    )

    if uploaded_files:
        st.write(f"Selected: {len(uploaded_files)} file(s)")
        for f in uploaded_files:
            st.write(f"  - {f.name}")

        if st.button(
            "Process Documents",
            use_container_width = True,
            type                = "primary"
        ):
            with st.spinner("Processing..."):
                try:
                    vectorstore, chunks, errors = (
                        process_faq_documents(
                            uploaded_files,
                            embeddings
                        )
                    )

                    chain, retriever = build_faq_chain(
                        vectorstore, llm
                    )

                    st.session_state.faq_chain = chain
                    st.session_state.retriever = retriever
                    st.session_state.chunks    = chunks
                    st.session_state.doc_names = [
                        f.name for f in uploaded_files
                    ]
                    st.session_state.processed = True
                    st.session_state.messages  = []

                    st.success(
                        f"Done! {len(chunks)} chunks!"
                    )

                    if errors:
                        for err in errors:
                            st.warning(f"Warning: {err}")

                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()

    # Stats
    if st.session_state.processed:
        st.subheader("Stats")
        st.metric("Chunks", len(st.session_state.chunks))
        st.metric("Files",  len(st.session_state.doc_names))
        st.write("Loaded Files:")
        for name in st.session_state.doc_names:
            st.write(f"  - {name}")

    st.divider()

    # Settings
    st.subheader("Options")
    st.session_state.show_sources = st.toggle(
        "Show Sources", value=True
    )

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("Reset Everything", use_container_width=True):
        for key in defaults:
            st.session_state[key] = defaults[key]
        st.rerun()

    st.divider()

    if st.session_state.processed:
        st.success("Ready!")
    else:
        st.warning("Upload documents first")

# ─────────────────────────────────────
# Main Area
# ─────────────────────────────────────
if not st.session_state.processed:

    st.info("Upload FAQ documents from sidebar!")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### Step 1
        Upload FAQ docs
        from sidebar
        """)
    with col2:
        st.markdown("""
        ### Step 2
        Click Process
        Documents
        """)
    with col3:
        st.markdown("""
        ### Step 3
        Ask questions
        and get answers
        """)

else:
    # ── Suggestions ──────────────────
    st.write("Quick Questions:")
    suggestions = [
        "What are business hours?",
        "How to reset password?",
        "What is refund policy?",
        "How to contact support?"
    ]

    cols = st.columns(len(suggestions))
    for i, s in enumerate(suggestions):
        with cols[i]:
            if st.button(
                s,
                key = f"sug_{i}",
                use_container_width=True
            ):
                with st.spinner("Searching..."):
                    try:
                        # Get docs
                        docs = st.session_state.retriever.invoke(s)

                        # ✅ CORRECT - unpack 2 values
                        conf, score = get_confidence_score(
                            docs, s
                        )

                        # Get source
                        source = (
                            docs[0].metadata.get("source", "N/A")
                            if docs else "N/A"
                        )

                        # Get answer
                        answer = st.session_state.faq_chain.invoke(s)

                        # Save messages
                        st.session_state.messages.append({
                            "role"   : "human",
                            "content": s
                        })
                        st.session_state.messages.append({
                            "role"      : "ai",
                            "content"   : answer,
                            "confidence": conf,
                            "score"     : score,
                            "source"    : source
                        })
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    st.divider()

    # ── Chat History ─────────────────
    display_chat(st.session_state.messages)

    # ── Chat Input ───────────────────
    if prompt := st.chat_input("Type your question..."):

        # Show human message
        with st.chat_message("human"):
            st.write(prompt)

        st.session_state.messages.append({
            "role"   : "human",
            "content": prompt
        })

        # Get AI response
        with st.chat_message("ai"):
            with st.spinner("Searching FAQ..."):
                try:
                    # Get docs
                    docs = st.session_state.retriever.invoke(
                        prompt
                    )

                    # ✅ CORRECT - unpack 2 values
                    conf, score = get_confidence_score(
                        docs, prompt
                    )

                    # Get source
                    source = (
                        docs[0].metadata.get("source", "N/A")
                        if docs else "N/A"
                    )

                    # Get answer
                    answer = st.session_state.faq_chain.invoke(
                        prompt
                    )

                    # Show answer
                    st.write(answer)

                    # Show confidence
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if conf == "High":
                            st.success(f"Confidence: {conf}")
                        elif conf == "Medium":
                            st.warning(f"Confidence: {conf}")
                        else:
                            st.error(f"Confidence: {conf}")

                    with col2:
                        st.info(f"Score: {score}%")

                    with col3:
                        st.caption(f"Source: {source}")

                    # Show sources
                    if st.session_state.show_sources:
                        display_sources(docs)

                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    answer = "Sorry error occurred."
                    conf   = "Low"
                    score  = 0
                    source = "N/A"

        # Save AI message
        st.session_state.messages.append({
            "role"      : "ai",
            "content"   : answer,
            "confidence": conf,
            "score"     : score,
            "source"    : source
        })