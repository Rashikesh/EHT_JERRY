import os
import threading
from langchain_core.embeddings import Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer


class LightweightEmbeddings(Embeddings):
    """
    TF-IDF based embeddings — no torch, no model downloads.
    Replaces HuggingFaceEmbeddings to stay within Render's 512MB free-tier RAM.
    Trade-off: keyword matching instead of semantic similarity (fine for demo/hackathon).
    """

    def __init__(self, max_features: int = 384):
        self.vectorizer = TfidfVectorizer(max_features=max_features)
        self._fitted = False

    def fit(self, texts: list[str]):
        self.vectorizer.fit(texts)
        self._fitted = True

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not self._fitted:
            self.fit(texts)
        return self.vectorizer.transform(texts).toarray().tolist()

    def embed_query(self, text: str) -> list[float]:
        if not self._fitted:
            # Can't embed a single query without a fitted corpus; return zero vector
            return [0.0] * 384
        return self.vectorizer.transform([text]).toarray()[0].tolist()


class RAGEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        # 🚀 LAZY LOADING: Do NOT load heavy models here!
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        print("🧠 RAG Engine initialized (Lazy Mode - saving memory).")

    def _load_models(self):
        """Load models ONLY when the first query happens — lightweight, no torch."""
        if self.embeddings is not None:
            return  # Already loaded

        print("⏳ Loading lightweight TF-IDF embeddings (no torch, no downloads)...")

        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        self.embeddings = LightweightEmbeddings(max_features=384)

        pdf_path = os.path.join(os.path.dirname(__file__), "..", "assets", "OSHA3151.pdf")

        if os.path.exists(pdf_path):
            print(f"📄 Loading real safety document: {pdf_path}...")
            try:
                from pypdf import PdfReader
                reader = PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = text_splitter.split_text(text)
                docs = [Document(page_content=chunk) for chunk in chunks[:50]]
                print(f"📚 Indexing {len(docs)} chunks into FAISS...")
                self.vectorstore = FAISS.from_documents(docs, self.embeddings)
            except Exception as e:
                print(f"⚠️ Error parsing PDF: {e}. Falling back to hardcoded data.")
                self._load_fallback_data()
        else:
            print(f"⚠️ PDF not found at {pdf_path}. Falling back to hardcoded data.")
            self._load_fallback_data()

        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2})
        print("✅ RAG engine ready (TF-IDF + FAISS).")

    def _load_fallback_data(self):
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document

        incidents = [
            Document(page_content="Incident 2021-04: High gas levels (45%) in Zone B led to a minor flash fire. Action: Evacuate zone, close main isolation valve."),
            Document(page_content="Standard Operating Procedure (SOP): If gas > 40%, immediately revoke all hot-work permits and sound facility alarm."),
            Document(page_content="Incident 2019-08: Thermal runaway detected when temperature exceeded 65°C and pressure spiked to 2500 bar. Action: Activate emergency cooling."),
        ]
        self.vectorstore = FAISS.from_documents(incidents, self.embeddings)

    def get_context(self, query: str) -> str:
        """Retrieve relevant safety context for a given query."""
        self._load_models()

        docs = self.retriever.invoke(query)
        if not docs:
            return "No historical incidents found matching current conditions."

        context = "\n📜 RETRIEVED FROM OSHA SAFETY MANUAL:\n"
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            context += f"  {i}. {content}\n"
        return context


rag_engine = RAGEngine()