# backend/rag_engine.py
"""
RAG Engine: Uses LangChain and FAISS to retrieve historical incident reports 
based on live sensor telemetry.
"""
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
# 👇 FIXED: Changed from langchain.schema to langchain_core.documents
from langchain_core.documents import Document 

class RAGEngine:
    def __init__(self):
        print("🧠 Initializing Lightweight RAG Engine (CPU)...")
        
        # Load the lightweight embedding model (Runs on CPU, no GPU needed)
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        
        # 📚 Historical Incident Database (Simulated Vector Store)
        self.incidents = [
            Document(page_content="Incident 2021-04: High gas levels (45%) in Zone B led to a minor flash fire. Root cause: faulty pressure relief valve. Action: Evacuate zone, close main isolation valve.", metadata={"gas": 45, "pressure": 1800}),
            Document(page_content="Incident 2019-08: Thermal runaway detected when temperature exceeded 65°C and pressure spiked to 2500 bar. Result: Chemical vat rupture. Action: Activate emergency cooling, vent pressure.", metadata={"temp": 68, "pressure": 2500}),
            Document(page_content="Incident 2022-11: Gas leak at 38% combined with high vibration. Cause: Pipeline corrosion. Action: Halt hot work, deploy gas suppression foam.", metadata={"gas": 38}),
            Document(page_content="Incident 2020-02: Pressure drop followed by gas spike. Cause: Water ingress into gas line. Action: Drain line, check moisture traps.", metadata={"pressure": 1500, "gas": 42}),
            Document(page_content="Standard Operating Procedure (SOP): If gas > 40%, immediately revoke all hot-work permits and sound facility alarm.", metadata={"type": "SOP"}),
            Document(page_content="Incident 2018-05: Confined space entry halted due to O2 deficiency (<19.5%). Action: Deploy ventilation fans before re-entry.", metadata={"o2": 18.0}),
        ]
        
        print("📚 Indexing historical incidents into FAISS...")
        # Create the FAISS vector store
        self.vectorstore = FAISS.from_documents(self.incidents, self.embeddings)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2}) # Retrieve top 2 most relevant incidents
        print("✅ RAG Engine ready. Historical incidents indexed.")

    def get_context(self, query: str) -> str:
        """Searches the vector database for relevant incidents based on the query."""
        docs = self.retriever.invoke(query)
        if not docs:
            return "No historical incidents found matching current conditions."
        
        context = "\n📜 HISTORICAL INCIDENTS & PROTOCOLS:\n"
        for i, doc in enumerate(docs, 1):
            context += f"  {i}. {doc.page_content}\n"
        return context

# Global instance
rag_engine = RAGEngine()