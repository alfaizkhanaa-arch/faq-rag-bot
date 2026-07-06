import os
import tempfile
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chat_models import init_chat_model
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────
# Load LLM
# ─────────────────────────────────────
def load_llm():
    print("[INFO] Loading LLM...")
    llm = init_chat_model("groq:llama-3.1-8b-instant")
    print("[SUCCESS] LLM loaded!")
    return llm

# ─────────────────────────────────────
# Load Embeddings
# ─────────────────────────────────────
def load_embeddings():
    print("[INFO] Loading embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name    = "sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs  = {"device": "cpu"},
        encode_kwargs = {"normalize_embeddings": True}
    )
    print("[SUCCESS] Embeddings loaded!")
    return embeddings

# ─────────────────────────────────────
# Load Single Document
# ─────────────────────────────────────
def load_documents(file_path, file_name):
    """Auto detect file type and load"""

    ext = os.path.splitext(file_name)[1].lower()
    print(f"[INFO] Loading {file_name} ({ext})")

    # ✅ FIX 1: Use elif not if
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = UnstructuredWordDocumentLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(
            f"Unsupported file type: {ext}\n"
            "Supported: PDF, DOCX, TXT"
        )

    docs = loader.load()
    print(f"[SUCCESS] Loaded {len(docs)} pages")
    return docs

# ─────────────────────────────────────
# Process FAQ Documents
# ─────────────────────────────────────
def process_faq_documents(uploaded_files, embeddings):

    all_docs = []
    errors   = []

    for uploaded_file in uploaded_files:
        tmp_path = None

        try:
            # ✅ FIX 2: Correct ext extraction
            ext = os.path.splitext(
                uploaded_file.name      # ✅ singular
            )[1].lower()               # ✅ [1] on splitext

            # ✅ FIX 3: docs outside with block
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=ext
            ) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name    # ✅ only save path

            # ✅ Load outside with block
            docs = load_documents(
                tmp_path,
                uploaded_file.name
            )

            # Add metadata
            for doc in docs:
                doc.metadata["source"]    = uploaded_file.name
                doc.metadata["file_type"] = ext.replace(".", "")

            all_docs.extend(docs)
            print(f"[SUCCESS] {uploaded_file.name} processed")

        except Exception as e:
            error_msg = f"{uploaded_file.name}: {str(e)}"
            errors.append(error_msg)
            print(f"[ERROR] {error_msg}")
            continue

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Check docs loaded
    if len(all_docs) == 0:
        raise ValueError(
            "No documents could be loaded!\n"
            "Please check your files and try again.\n"
            f"Errors: {errors}"
        )

    print(f"[INFO] Total pages loaded: {len(all_docs)}")

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = 800,
        chunk_overlap = 100,
        # ✅ FIX 4: comma after "\n"
        separators    = [
            "\n\n",
            "\n",       # ✅ comma added
            "Q:",
            "A:",
            " ",
            ""
        ]
    )
    chunks = splitter.split_documents(all_docs)

    # Filter empty
    chunks = [
        c for c in chunks
        if c.page_content.strip()
    ]

    print(f"[INFO] Valid chunks: {len(chunks)}")

    if len(chunks) == 0:
        raise ValueError(
            "No valid text chunks found!\n"
            "Please check your documents have text."
        )

    # Create vector store
    print("[INFO] Creating vector store...")

    vectorstore = Chroma.from_documents(
        documents       = chunks,
        embedding       = embeddings,
        collection_name = "faq_collection"
    )

    print("[SUCCESS] Vector store created!")
    return vectorstore, chunks, errors

# ─────────────────────────────────────
# Build FAQ Chain
# ─────────────────────────────────────
def build_faq_chain(vectorstore, llm):

    retriever = vectorstore.as_retriever(
        search_type   = "similarity",
        search_kwargs = {"k": 3}
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are a helpful FAQ assistant.
        Answer the user question based ONLY
        on the provided context.

        Rules:
        - If the answer is in the context,
          answer clearly and directly.
        - If the answer is NOT in the context,
          say "I don't have information about
          that in the uploaded documents."
        - Do NOT make up answers.
        - Keep responses under 3 sentences.
        - Be polite and professional.

        Context:
        {context}
        """),
        ("human", "{question}")
    ])

    def format_docs(docs):
        return "\n\n---\n\n".join([
            f"[From: {doc.metadata.get('source', 'Unknown')}]\n"
            f"{doc.page_content}"
            for doc in docs
        ])

    chain = (
        {
            "context" : retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever

# ─────────────────────────────────────
# Get Confidence Score
# ─────────────────────────────────────
def get_confidence_score(docs, question):

    if not docs:
        return "Low", 0

    top_doc        = docs[0].page_content.lower()
    question_words = set(question.lower().split())

    # Remove stop words
    stop_words = {
        "what", "how", "when", "where",
        "why", "is", "are", "do", "does",
        "can", "the", "a", "an", "i", "my"
    }
    question_words -= stop_words

    if not question_words:
        return "Medium", 50

    # ✅ FIX 5: iterate over question_words not question
    overlap = sum(
        1 for word in question_words    # ✅ fixed
        if word in top_doc
    )

    ratio = overlap / len(question_words) \
            if question_words else 0

    score = int(ratio * 100)

    if ratio > 0.5:
        return "High", score
    elif ratio > 0.2:
        return "Medium", score
    else:
        return "Low", score