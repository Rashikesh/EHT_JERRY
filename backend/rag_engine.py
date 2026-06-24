# backend/rag_engine.py
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGEngine:
    def __init__(self):
        print("🧠 Initializing Lightweight RAG Engine (CPU)...")
        
        # Load the lightweight embedding model
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        
        pdf_path = "osha_h2s.pdf"
        
        if os.path.exists(pdf_path):
            print(f"📄 Loading real safety document: {pdf_path}...")
            try:
                from pypdf import PdfReader # pypdf is the modern version of PyPDF2
                reader = PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Chunk the text
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = text_splitter.split_text(text)
                
                # Create Documents
                docs = [Document(page_content=chunk) for chunk in chunks[:50]] # Limit to first 50 chunks to save RAM/time
                
                print(f"📚 Indexing {len(docs)} chunks into FAISS...")
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
        """Fallback if PDF fails to load"""
        incidents = [
            Document(page_content="Incident 2021-04: High gas levels (45%) in Zone B led to a minor flash fire. Action: Evacuate zone, close main isolation valve."),
            Document(page_content="Standard Operating Procedure (SOP): If gas > 40%, immediately revoke all hot-work permits and sound facility alarm."),
        ]
        self.vectorstore = FAISS.from_documents(incidents, self.embeddings)

    def get_context(self, query: str) -> str:
        docs = self.retriever.invoke(query)
        if not docs:
            return "No historical incidents found matching current conditions."
        
        context = "\n📜 RETRIEVED FROM OSHA SAFETY MANUAL:\n"
        for i, doc in enumerate(docs, 1):
            # Truncate long chunks for the UI
            content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            context += f"  {i}. {content}\n"
        return context

rag_engine = RAGEngine()