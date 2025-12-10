import os
import tempfile
import requests
import uuid
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from pinecone import Pinecone
from django.conf import settings
#from langchain.schema import HumanMessage, SystemMessage
from langchain_core.messages import HumanMessage, SystemMessage
load_dotenv()

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "notecraft"

if not PINECONE_API_KEY:
    print("Warning: PINECONE_API_KEY not found.")
    pc = None
else:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
    except Exception as e:
        print(f"Error initializing Pinecone: {e}")
        pc = None

def get_index():
    if not pc:
        raise ValueError("Pinecone not initialized")
    return pc.Index(INDEX_NAME)

def process_pdf_from_url(pdf_url: str):
    """
    Downloads PDF from URL, processes it, and stores in vector DB
    """
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            response = requests.get(pdf_url)
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        # Process the temporary file
        process_pdf_to_vector_db(temp_file_path)

        # Clean up
        os.remove(temp_file_path)
        return True
    except Exception as e:
        print(f"Error processing PDF from URL: {e}")
        return False

def process_pdf_to_vector_db(pdf_path: str):
    """
    Reads PDF, splits text, and stores in Pinecone
    """
    if not pc:
        raise ValueError("Pinecone not initialized")

    try:
        # 1. Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # 2. Split Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)

        # 3. Vectorize and Store in Pinecone
        index = get_index()
        
        # Batch process to avoid hitting limits
        batch_size = 96 
        print(f"Processing {len(texts)} chunks for Pinecone...")
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_texts = [t.page_content for t in batch]
            
            # Generate embeddings using Pinecone Inference API
            # Using llama-text-embed-v2 as in myutils.py
            embeddings_response = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=batch_texts,
                parameters={"input_type": "passage"}
            )
            
            vectors = []
            for j, embedding_data in enumerate(embeddings_response):
                doc_id = str(uuid.uuid4())
                
                # Prepare metadata
                metadata = {
                    "text": batch_texts[j],
                    "source": batch[j].metadata.get("source", pdf_path),
                    "page": batch[j].metadata.get("page", 0)
                }
                
                vectors.append({
                    "id": doc_id,
                    "values": embedding_data['values'],
                    "metadata": metadata
                })
            
            # Upsert to Pinecone (default namespace)
            index.upsert(vectors=vectors)
            
        print(f"Successfully added {pdf_path} to Pinecone knowledge base")
        return True
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise e

def query_ai(query: str):
    """
    Queries the AI with the given question using RAG (Pinecone + OpenRouter)
    """
    try:
        if not pc:
            raise ValueError("Pinecone not initialized")
            
        # 1. Embed Query
        query_embedding = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[query],
            parameters={"input_type": "query"}
        )[0]['values']
        
        # 2. Search Pinecone
        index = get_index()
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
            # namespace="" # Use default namespace
        )
        
        context_text = ""
        sources = []
        if results.matches:
            for match in results.matches:
                if match.metadata and "text" in match.metadata:
                    context_text += match.metadata["text"] + "\n\n"
                    sources.append(match.metadata.get("source", "unknown"))
        
        if not context_text:
            context_text = "No relevant context found in the knowledge base."

        # 3. Initialize LLM with OpenRouter
        open_router_key = os.getenv("OPEN_ROUTER_API_KEY")
        if not open_router_key:
            raise ValueError("OPEN_ROUTER_API_KEY not found in environment variables")

        print(f"Initializing ChatOpenAI with model: meta-llama/llama-3.3-70b-instruct:free")
        
        llm = ChatOpenAI(
            model="meta-llama/llama-3.3-70b-instruct:free", 
            api_key=open_router_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0
        )

        # 4. Construct Prompt
        system_prompt = """
        你是一个《金铲铲之战》（Teamfight Tactics）的高手教练和智能助手。
        请根据下方的【参考资料】回答用户的问题。
        如果资料里没有提到，就诚实地说不知道，不要编造羁绊或装备数据。
        """
        
        user_prompt = f"""
        【参考资料】：
        {context_text}
        
        用户问题：{query}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # 5. Invoke LLM
        response = llm.invoke(messages)
        
        return {
            "answer": response.content,
            "sources": list(set(sources))
        }
    except Exception as e:
        print(f"AI Query Error: {e}")
        raise e
