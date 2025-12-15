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
INDEX_NAME = "teamfight-tactics-knowledges"

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

        # Initialize LLM first (needed for query expansion)
        open_router_key = os.getenv("OPEN_ROUTER_API_KEY")
        if not open_router_key:
            raise ValueError("OPEN_ROUTER_API_KEY not found in environment variables")

        print(f"Initializing ChatOpenAI with model: deepseek-chat")
        
        llm = ChatOpenAI(
            model="deepseek-chat", 
            api_key=open_router_key,
            base_url="https://api.deepseek.com",
            temperature=0
        )

        # 1. Query Expansion / Keyword Extraction
        # Generate search queries based on user input to capture all entities
        expansion_prompt = """
        你是一个《金铲铲之战》（Teamfight Tactics）的搜索优化助手。
        用户的输入可能包含游戏术语、海克斯强化、英雄或装备。
        请分析用户的输入，提取出需要搜索的核心关键词。
        
        策略：
        1. 如果涉及比较（如“A还是B”），请分别提取 A 和 B。
        2. 识别专有名词，如“升级咯”、“潘朵拉的装备”等海克斯名称。
        3. 如果用户询问某一类别的列表（如“5费卡有哪些”），请生成该类别的多种同义词查询（如“5费英雄”、“5费弈子”、“橙卡”），以增加召回率。
        4. 请直接输出关键词列表，每行一个。不要包含其他文字。
        """
        
        expansion_messages = [
            SystemMessage(content=expansion_prompt),
            HumanMessage(content=query)
        ]
        
        search_queries = []
        try:
            # Use a separate try-except for expansion to not fail the whole request
            expansion_response = llm.invoke(expansion_messages)
            search_queries = [q.strip() for q in expansion_response.content.split('\n') if q.strip()]
            print(f"Generated search queries: {search_queries}")
        except Exception as e:
            print(f"Query expansion failed: {e}")

        # Always include the original query as a fallback/supplement
        if query not in search_queries:
            search_queries.append(query)
            
        # 2. Search Pinecone for each query
        index = get_index()
        seen_ids = set()
        all_matches = []
        
        for q in search_queries:
            try:
                # Embed Query
                query_embedding = pc.inference.embed(
                    model="llama-text-embed-v2",
                    inputs=[q],
                    parameters={"input_type": "query"}
                )[0]['values']
                
                # Search Pinecone
                results = index.query(
                    vector=query_embedding,
                    top_k=1000, # Increased to 20 to capture lists of items (e.g. "all 5 cost units")
                    include_metadata=True
                )
                
                if results.matches:
                    for match in results.matches:
                        if match.id not in seen_ids:
                            seen_ids.add(match.id)
                            all_matches.append(match)
            except Exception as e:
                print(f"Error searching for query '{q}': {e}")

        # Sort by score and take top K
        # We do NOT sort and slice globally anymore to prevent one topic dominating the results.
        # We keep all unique matches from all sub-queries.
        final_matches = all_matches
        
        context_text = ""
        sources = []
        for match in final_matches:
            if match.metadata and "text" in match.metadata:
                context_text += match.metadata["text"] + "\n\n"
                sources.append(match.metadata.get("source", "unknown"))
        
        if not context_text:
            context_text = "No relevant context found in the knowledge base."

        # 3. Construct Prompt for Final Answer
        system_prompt = """
        你是一个《金铲铲之战》（Teamfight Tactics）的高手教练和智能助手。
        请根据下方的【参考资料】回答用户的问题。
        
        回答原则：
        1. **全面性**：如果用户询问列表（如“有哪些5费卡”、“推荐阵容有哪些”），请务必列出资料中提到的**所有**相关条目，不要遗漏。
        2. **准确性**：如果资料里没有提到，就诚实地说不知道，不要编造羁绊或装备数据。
        3. **结构化**：使用 Markdown 列表清晰展示信息，便于阅读。
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
        
        # 4. Invoke LLM
        response = llm.invoke(messages)
        
        return {
            "answer": response.content,
            "sources": list(set(sources))
        }
    except Exception as e:
        print(f"AI Query Error: {e}")
        raise e
