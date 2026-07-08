import os
import threading
import numpy as np
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TfidfEmbeddings(Embeddings):
    """Lightweight TF-IDF based embeddings, no heavy ML models required."""

    def __init__(self, max_features: int = 512):
        self.vectorizer = TfidfVectorizer(max_features=max_features)
        self._fitted = False

    def _to_dense_unit(self, matrix) -> List[List[float]]:
        arr = matrix.toarray().astype(float)
        # pad/truncate isn't needed since vectorizer is shared and fixed vocab after fit
        return arr.tolist()

    def fit(self, texts: List[str]):
        self.vectorizer.fit(texts)
        self._fitted = True

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self._fitted:
            self.fit(texts)
        matrix = self.vectorizer.transform(texts)
        return self._to_dense_unit(matrix)

    def embed_query(self, text: str) -> List[float]:
        if not self._fitted:
            # Fallback: fit on the single query if nothing was fitted yet (shouldn't normally happen)
            self.fit([text])
        matrix = self.vectorizer.transform([text])
        return self._to_dense_unit(matrix)[0]


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

        print("🧠 Initializing Lightweight RAG Engine (CPU, TF-IDF)...")
        self.embeddings = TfidfEmbeddings()

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

                # Fit TF-IDF vocabulary on the actual corpus before embedding
                self.embeddings.fit([d.page_content for d in docs])
                self.vectorstore = FAISS.from_documents(docs, self.embeddings)
            except Exception as e:
                print(f"⚠️ Error parsing PDF: {e}. Falling back to hardcoded data.")
                self._load_fallback_data()
        else:
            print(f"⚠️ PDF not found at {pdf_path}. Falling back to hardcoded data.")
            self._load_fallback_data()

        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2})
        print("✅ RAG Engine ready. Historical incidents indexed.")

    def _load_fallback_data(self):
        incidents = [
            Document(page_content="Incident 2021-04: High gas levels (45%) in Zone B led to a minor flash fire. Action: Evacuate zone, close main isolation valve."),
            Document(page_content="Standard Operating Procedure (SOP): If gas > 40%, immediately revoke all hot-work permits and sound facility alarm."),
            Document(page_content="Incident 2019-08: Thermal runaway detected when temperature exceeded 65°C and pressure spiked to 2500 bar. Action: Activate emergency cooling."),
        ]
        self.embeddings.fit([d.page_content for d in incidents])
        self.vectorstore = FAISS.from_documents(incidents, self.embeddings)

    def get_context(self, query: str) -> str:
        docs = self.retriever.invoke(query)
        if not docs:
            return "No historical incidents found matching current conditions."

        context = "\n📜 RETRIEVED FROM OSHA SAFETY MANUAL:\n"
        for i, doc in enumerate(docs, 1):
            content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            context += f"  {i}. {content}\n"
        return context


rag_engine = RAGEngine()