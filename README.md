# 💬 FAQ Bot using RAG (Retrieval-Augmented Generation)

An AI-powered FAQ chatbot that answers questions from uploaded documents using **LangChain**, **ChromaDB**, **Hugging Face Embeddings**, **Groq LLM**, and **Streamlit**.

Users can upload **PDF, DOCX, and TXT** documents, and the chatbot retrieves the most relevant information before generating accurate, context-aware answers.


---

## 🚀 Features

* 📄 Upload multiple **PDF, DOCX, and TXT** documents
* 📑 Automatic document loading based on file type
* ✂️ Intelligent text chunking using `RecursiveCharacterTextSplitter`
* 🔍 Semantic search using Hugging Face embeddings
* 🗂️ Vector storage with ChromaDB
* 🤖 AI-powered question answering using a Large Language Model
* 📚 Displays the source document for each answer
* 📊 Confidence score for retrieved answers
* 💬 Interactive Streamlit chat interface
* ⚡ Fast and context-aware document retrieval


---

## 🛠️ Tech Stack

* Python
* Streamlit
* LangChain
* ChromaDB
* Hugging Face Embeddings
* Groq LLM
* RecursiveCharacterTextSplitter

---

## 📂 Project Structure

```text
faq-rag-bot/
│
├── app/
│   ├── app.py
│   ├── rag.py
│   ├── utils.py
│   └── requirements.txt
│
├── data/
│   └── sample_faq.txt
│
├── screenshots/
│
├── README.md
└── requirements.txt
```

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/faq-rag-bot.git
cd faq-rag-bot
```

Create a virtual environment (recommended):

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
```

---

## ▶️ Run the Application

```bash
streamlit run app/app.py
```

Open the local URL displayed by Streamlit in your browser.

---

## 💡 How It Works

1. Upload one or more FAQ documents.
2. Documents are loaded and split into smaller chunks.
3. Chunks are converted into embeddings.
4. Embeddings are stored in ChromaDB.
5. The retriever finds the most relevant chunks for each user question.
6. The LLM generates an answer using the retrieved context.
7. The chatbot displays the answer along with the source document and confidence level.

---

## 📸 Screenshots

Add screenshots of:

* Home Page
* Document Upload
* Processing Documents
* Chat Interface
* Answer with Source Information

Store them inside the `screenshots/` folder.

---

## 🔮 Future Improvements

* Support DOCX and Markdown files
* Conversation memory
* Chat history export
* Persistent vector database
* OCR support for scanned PDFs
* Multi-language document support
* Citation highlighting
* Docker deployment

---

## 📚 Sample Questions

* What services do you offer?
* How do I reset my password?
* What is the refund policy?
* How can I contact customer support?
* What are your business hours?

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Alfaiz Khan**

If you found this project helpful, consider giving it a ⭐ on GitHub.
