"""
RAG Pipeline Module (v2 — Optimized)
=====================================
Core Retrieval-Augmented Generation pipeline for the CRM Business Assistant.
Handles document loading, chunking, embedding, vector storage, and retrieval-augmented response generation.

Optimizations over v1:
    - Increased chunk size (500→800) for better context coverage
    - Increased chunk overlap (50→100) to preserve cross-boundary information
    - Increased top-k retrieval (5→8) to support multi-hop reasoning
    - Custom system prompt for grounded, faithful responses
    - Reduced max_tokens (1000→500) for faster response times
    - Separate chunking strategy for CRM records vs knowledge base docs

Architecture:
    Documents -> Chunking -> Embeddings -> ChromaDB Vector Store
    User Query -> Retrieval -> Context Augmentation -> LLM Generation -> Response
"""

import os
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferWindowMemory

load_dotenv()

# ─── Configuration ───────────────────────────────────────────────
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base")
CRM_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_crm_data.json")
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

# Chunking parameters (OPTIMIZED: larger chunks for better context)
KB_CHUNK_SIZE = 800      # Up from 500 — knowledge base docs need more context per chunk
KB_CHUNK_OVERLAP = 100   # Up from 50 — preserves information at chunk boundaries
CRM_CHUNK_SIZE = 600     # CRM records are smaller, moderate chunk size
CRM_CHUNK_OVERLAP = 50

# Retrieval parameters
TOP_K = 8  # Up from 5 — allows multi-hop queries to pull from more sources

# Custom system prompt for grounded responses
SYSTEM_PROMPT = """You are a professional CRM business assistant for NexusFlow Solutions.
Your role is to help sales representatives and managers by answering questions about:
- Customer contacts, their details, and relationship history
- Sales deals, pipeline stages, and forecasts
- Invoices, payment statuses, and financial summaries
- Company products, pricing, policies, and processes

CRITICAL RULES:
1. ONLY answer based on the context provided. Do not make up or assume information.
2. If the context does not contain enough information to fully answer the question, clearly state what information is missing rather than guessing.
3. When combining information from multiple records, clearly attribute which data comes from where.
4. For numerical data (amounts, scores, dates), be precise — do not round or estimate.
5. Always maintain a professional, helpful tone appropriate for a business setting.
6. If asked about a person, company, or record that does not exist in the context, say you don't have that information.
"""


def load_knowledge_base_documents():
    """
    Load all markdown documents from the knowledge base directory.
    Each document is tagged with metadata (source filename) for source attribution.
    """
    documents = []
    for filename in os.listdir(KNOWLEDGE_BASE_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(KNOWLEDGE_BASE_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            documents.append(Document(
                page_content=content,
                metadata={"source": filename, "type": "knowledge_base"}
            ))
            print(f"  Loaded: {filename} ({len(content)} characters)")
    return documents


def load_crm_data_as_documents():
    """
    Load CRM data (contacts, interactions, invoices, deals) and convert
    each record into a Document object for embedding and retrieval.
    
    OPTIMIZATION: Each CRM record includes cross-references to related records
    to improve multi-hop reasoning capability.
    """
    with open(CRM_DATA_PATH, "r", encoding="utf-8") as f:
        crm_data = json.load(f)

    documents = []

    # Build lookup maps for cross-referencing
    contacts_map = {c["id"]: c for c in crm_data["contacts"]}

    # Convert contacts to documents (enriched with related data summary)
    for contact in crm_data["contacts"]:
        # Find related interactions
        related_interactions = [i for i in crm_data["interactions"] if i["contact_id"] == contact["id"]]
        interaction_summary = ""
        if related_interactions:
            interaction_summary = "\nRecent Interactions:\n"
            for inter in sorted(related_interactions, key=lambda x: x["date"], reverse=True)[:3]:
                interaction_summary += f"  - {inter['date']} ({inter['type']}): {inter['subject']} — {inter['summary'][:100]}\n"

        # Find related invoices
        related_invoices = [i for i in crm_data["invoices"] if i["contact_id"] == contact["id"]]
        invoice_summary = ""
        if related_invoices:
            invoice_summary = "\nInvoices:\n"
            for inv in related_invoices:
                invoice_summary += f"  - {inv['id']}: £{inv['amount']:,.2f} ({inv['status']}) — {inv['description']}\n"

        # Find related deals
        related_deals = [d for d in crm_data["deals"] if d["contact_id"] == contact["id"]]
        deal_summary = ""
        if related_deals:
            deal_summary = "\nDeals:\n"
            for deal in related_deals:
                deal_summary += f"  - {deal['deal_name']}: £{deal['value']:,.2f} ({deal['stage']}, {deal['probability']}% probability)\n"

        content = (
            f"Contact: {contact['first_name']} {contact['last_name']}\n"
            f"Company: {contact['company']}\n"
            f"Job Title: {contact['job_title']}\n"
            f"Email: {contact['email']}\n"
            f"Phone: {contact['phone']}\n"
            f"Industry: {contact['industry']}\n"
            f"Lead Status: {contact['lead_status']}\n"
            f"Lead Score: {contact['lead_score']}\n"
            f"Assigned Rep: {contact['assigned_rep']}\n"
            f"Last Contact: {contact['last_contact_date']}\n"
            f"Notes: {contact['notes']}"
            f"{interaction_summary}"
            f"{invoice_summary}"
            f"{deal_summary}"
        )
        documents.append(Document(
            page_content=content,
            metadata={"source": "crm_contacts", "type": "crm_data", "record_id": contact["id"]}
        ))

    # Convert interactions to documents (enriched with contact name)
    for interaction in crm_data["interactions"]:
        contact = contacts_map.get(interaction["contact_id"], {})
        contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        company = contact.get("company", "Unknown")

        content = (
            f"Interaction Record ({interaction['type']})\n"
            f"Contact: {contact_name} ({company})\n"
            f"Contact ID: {interaction['contact_id']}\n"
            f"Date: {interaction['date']}\n"
            f"Subject: {interaction['subject']}\n"
            f"Summary: {interaction['summary']}\n"
            f"Sentiment: {interaction['sentiment']}\n"
            f"Sales Rep: {interaction['rep']}"
        )
        documents.append(Document(
            page_content=content,
            metadata={"source": "crm_interactions", "type": "crm_data", "record_id": interaction["id"]}
        ))

    # Convert invoices to documents (enriched with contact name)
    for invoice in crm_data["invoices"]:
        contact = contacts_map.get(invoice["contact_id"], {})
        contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()

        content = (
            f"Invoice: {invoice['id']}\n"
            f"Contact: {contact_name}\n"
            f"Company: {invoice['company']}\n"
            f"Amount: £{invoice['amount']:,.2f}\n"
            f"Status: {invoice['status']}\n"
            f"Issue Date: {invoice['issue_date']}\n"
            f"Due Date: {invoice['due_date']}\n"
            f"Description: {invoice['description']}\n"
            f"Payment Date: {invoice['payment_date'] or 'Not yet paid'}"
        )
        documents.append(Document(
            page_content=content,
            metadata={"source": "crm_invoices", "type": "crm_data", "record_id": invoice["id"]}
        ))

    # Convert deals to documents (enriched with contact name)
    for deal in crm_data["deals"]:
        contact = contacts_map.get(deal["contact_id"], {})
        contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()

        content = (
            f"Deal: {deal['deal_name']}\n"
            f"Contact: {contact_name}\n"
            f"Company: {deal['company']}\n"
            f"Value: £{deal['value']:,.2f}\n"
            f"Stage: {deal['stage']}\n"
            f"Probability: {deal['probability']}%\n"
            f"Expected Close: {deal['expected_close']}\n"
            f"Sales Rep: {deal['rep']}"
        )
        documents.append(Document(
            page_content=content,
            metadata={"source": "crm_deals", "type": "crm_data", "record_id": deal["id"]}
        ))

    print(f"  Loaded CRM data: {len(crm_data['contacts'])} contacts (enriched with cross-references), "
          f"{len(crm_data['interactions'])} interactions, "
          f"{len(crm_data['invoices'])} invoices, "
          f"{len(crm_data['deals'])} deals")

    return documents


def chunk_documents(documents):
    """
    Split documents into chunks using different strategies
    for knowledge base docs vs CRM records.
    """
    kb_docs = [d for d in documents if d.metadata.get("type") == "knowledge_base"]
    crm_docs = [d for d in documents if d.metadata.get("type") == "crm_data"]

    # Knowledge base: larger chunks for richer context
    kb_splitter = RecursiveCharacterTextSplitter(
        chunk_size=KB_CHUNK_SIZE,
        chunk_overlap=KB_CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    kb_chunks = kb_splitter.split_documents(kb_docs)

    # CRM data: moderate chunks, most records fit in one chunk
    crm_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CRM_CHUNK_SIZE,
        chunk_overlap=CRM_CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    crm_chunks = crm_splitter.split_documents(crm_docs)

    all_chunks = kb_chunks + crm_chunks
    print(f"  Knowledge base: {len(kb_chunks)} chunks (size={KB_CHUNK_SIZE}, overlap={KB_CHUNK_OVERLAP})")
    print(f"  CRM data: {len(crm_chunks)} chunks (size={CRM_CHUNK_SIZE}, overlap={CRM_CHUNK_OVERLAP})")
    print(f"  Total: {len(all_chunks)} chunks")
    return all_chunks


def create_vector_store(chunks):
    """
    Create or load a ChromaDB vector store with OpenAI embeddings.
    Embeds all document chunks and stores them for semantic retrieval.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )
    print(f"  Vector store created with {vector_store._collection.count()} vectors")
    return vector_store


def load_vector_store():
    """Load an existing vector store from disk."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(
        persist_directory=CHROMA_PERSIST_DIR,
        embedding_function=embeddings
    )
    print(f"  Loaded vector store with {vector_store._collection.count()} vectors")
    return vector_store


def build_rag_chain(vector_store):
    """
    Build the complete RAG chain with optimized parameters.
    """
    # Initialize LLM with optimized settings
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,   # Slightly lower for more deterministic responses
        max_tokens=500     # Reduced from 1000 — faster responses, less rambling
    )

    # Configure retriever with increased top-k
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K}
    )

    # Conversation memory (keeps last 5 exchanges for context)
    memory = ConversationBufferWindowMemory(
        k=5,
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    # Build conversational retrieval chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        verbose=False,
        combine_docs_chain_kwargs={
            "prompt": ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("human", "Context:\n{context}\n\nQuestion: {question}")
            ])
        }
    )

    return chain


# ─── Initialization Pipeline ────────────────────────────────────

def initialize_rag_system(force_rebuild=False):
    """
    Complete initialization pipeline.
    """
    print("\n=== Initializing RAG System ===\n")

    # Check if vector store already exists
    if os.path.exists(CHROMA_PERSIST_DIR) and not force_rebuild:
        print("[1/2] Loading existing vector store...")
        vector_store = load_vector_store()
    else:
        print("[1/4] Loading knowledge base documents...")
        kb_docs = load_knowledge_base_documents()

        print("[2/4] Loading CRM data...")
        crm_docs = load_crm_data_as_documents()

        all_documents = kb_docs + crm_docs
        print(f"\n  Total documents loaded: {len(all_documents)}")

        print("\n[3/4] Chunking documents...")
        chunks = chunk_documents(all_documents)

        print("\n[4/4] Creating vector store...")
        vector_store = create_vector_store(chunks)

    print("\n[Final] Building RAG chain...")
    chain = build_rag_chain(vector_store)

    print("\n=== RAG System Ready ===\n")
    return chain


# ─── Query Interface ─────────────────────────────────────────────

def query_rag(chain, question):
    """
    Send a question to the RAG chain and return the response
    along with source documents for attribution.
    """
    result = chain.invoke({"question": question})

    response = {
        "answer": result["answer"],
        "sources": []
    }

    # Extract source attribution
    if "source_documents" in result:
        seen_sources = set()
        for doc in result["source_documents"]:
            source = doc.metadata.get("source", "Unknown")
            if source not in seen_sources:
                seen_sources.add(source)
                response["sources"].append({
                    "source": source,
                    "type": doc.metadata.get("type", "Unknown"),
                    "content_preview": doc.page_content[:200] + "..."
                })

    return response


# ─── Main (for testing) ─────────────────────────────────────────

if __name__ == "__main__":
    chain = initialize_rag_system(force_rebuild=True)

    test_questions = [
        "Who is James Mitchell and what is his current status?",
        "What are the pending invoices?",
        "Tell me about the deals in the negotiation stage",
        "What pricing tiers does NexusFlow offer?",
        "What were the last interactions with GreenLeaf Energy?"
    ]

    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {question}")
        print(f"{'='*60}")
        result = query_rag(chain, question)
        print(f"\nA: {result['answer']}")
        print(f"\nSources: {[s['source'] for s in result['sources']]}")