from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import CharacterTextSplitter

INCIDENT_REPORTS = [
    "Incident #402: On March 12, 2023, a hot work permit was issued while gas levels were at 42%. A spark ignited the vapor, causing a flash fire in Zone B. 3 workers injured.",
    "Incident #118: Pressure spike to 2500 bar combined with high temperature (65°C) led to a valve failure. Permit to work was not revoked in time.",
    "Incident #891: Shift change overlap caused confusion. A new crew started welding while gas sensors were reading 45%. Explosion in the main pipeline.",
    "Safety Protocol 7A: All hot work permits must be immediately suspended if combustible gas levels exceed 40% LEL. Failure to do so violates OSHA standard 1910.252.",
    "Incident #205: Temperature exceeded 70°C during a pressure test. The relief valve failed to open because the digital interlock was bypassed."
]

class RAGEngine:
    def __init__(self):
        print("🧠 Initializing Lightweight RAG Engine (CPU)...")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=0)
        texts = text_splitter.split_text(" ".join(INCIDENT_REPORTS))
        self.vectorstore = FAISS.from_texts(texts, self.embeddings)
        print("✅ RAG Engine ready. Historical incidents indexed.")

    def get_safety_justification(self, sensor_data: dict) -> str:
        gas = sensor_data.get("gas", 0)
        pressure = sensor_data.get("pressure", 0)
        temp = sensor_data.get("temperature", 0)

        query = ""
        if gas > 40: query += f"High gas levels at {gas}%. Hot work danger. "
        if pressure > 2400: query += f"High pressure at {pressure} bar. Valve failure risk. "
        if temp > 65: query += f"High temperature at {temp}°C. "
        
        if not query: return "All parameters within normal operating limits."

        docs = self.vectorstore.similarity_search(query, k=2)
        response = f"⚠️ AI SAFETY ALERT: {query.strip()}\n\n📚 Historical Precedents Found:\n"
        for i, doc in enumerate(docs, 1):
            response += f"  {i}. {doc.page_content}\n"
        return response

rag_engine = RAGEngine()
