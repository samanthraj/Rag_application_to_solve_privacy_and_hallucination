import os
import uuid
import numpy as np
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader
from langchain_text_splitters import MarkdownTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
from langchain_groq import ChatGroq

# =========================
# 🔹 PATH FIX (IMPORTANT)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_PATH = os.path.join(BASE_DIR, "../data/pdffiles")
VECTOR_DB_PATH = os.path.join(BASE_DIR, "../data/vectorstore")

# =========================
# 🔹 EMBEDDING MODEL
# =========================
class EmbeddingModel:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: List[str]):
        return self.model.encode(texts)


embedding_manager = EmbeddingModel()

# =========================
# 🔹 LOAD DOCUMENTS
# =========================
loader = DirectoryLoader(PDF_PATH, glob="**/*.pdf", loader_cls=PyMuPDFLoader)
documents = loader.load()

# =========================
# 🔹 TEXT SPLITTING
# =========================
splitter = MarkdownTextSplitter(chunk_size=300, chunk_overlap=20)

chunks = []
for doc in documents:
    text_chunks = splitter.split_text(doc.page_content)
    for i, chunk in enumerate(text_chunks):
        chunks.append(
            Document(
                page_content=chunk,
                metadata={**doc.metadata, "chunk_index": i}
            )
        )

# =========================
# 🔹 EMBEDDINGS
# =========================
chunk_texts = [chunk.page_content for chunk in chunks]
embeddings = embedding_manager.generate_embeddings(chunk_texts)

# =========================
# 🔹 VECTOR STORE
# =========================
client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

collection = client.get_or_create_collection(name="rag_data")

# Add only once
if collection.count() == 0:
    collection.add(
        ids=[str(uuid.uuid4()) for _ in chunk_texts],
        embeddings=[e.tolist() for e in embeddings],
        documents=chunk_texts
    )

# =========================
# 🔹 RETRIEVER
# =========================
class RAGRetriever:
    def __init__(self, collection, embedding_manager):
        self.collection = collection
        self.embedding_manager = embedding_manager

    def retrieve(self, query, top_k=3):
        query_embedding = self.embedding_manager.generate_embeddings([query])[0]

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )

        return results.get("documents", [[]])[0]


ragretriever = RAGRetriever(collection, embedding_manager)

# =========================
# 🔹 LLM (FIXED WITH KEY)
# =========================
llm = ChatGroq(
    api_key="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",
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_tokens=1024
)

# =========================
# 🔹 RAG FUNCTION
# =========================
def ragsimple(query: str):
    docs = ragretriever.retrieve(query)

    if not docs:
        return "No relevant documents found."

    context = "\n\n".join(docs)

    prompt = f"""
     You are an expert assistant.

    Use ONLY the given context to answer.

    If answer is not in context, say:
    "I don't know based on provided documents."

    Context:
    {context}

    Question:
    {query}

    Answer clearly and concisely:
    """

    response = llm.invoke(prompt)

    return response.content
   
