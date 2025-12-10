from typing import Dict, List, Any
import os
import requests
import json
from dotenv import load_dotenv
from pinecone import Pinecone
try:
    from google_images_search import GoogleImagesSearch
except ImportError:
    GoogleImagesSearch = None
    print("Warning: google_images_search not found or curses missing. Image search will be disabled.")

from requests.exceptions import RequestException
from django.core.cache import cache
import random
load_dotenv()
global gis
if GoogleImagesSearch:
    gis = GoogleImagesSearch(developer_key=os.getenv("GOOGLE_API_KEY"), custom_search_cx=os.getenv("CX"))
else:
    gis = None

OR_API_KEY=os.getenv("OPEN_ROUTER_API_KEY")
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("notecraft")
except Exception as e:
    print(f"Warning: Pinecone initialization failed: {e}")
    index = None

topics_query:str="Generate key gameplay aspects for Teamfight Tactics (Golden Spatula) related to this topic. " \
"If specific strategies or compositions are mentioned, retain them. " \
    "The output should only contain the subtopics and not the content." \
    """the output should in form of raw json in the ```json box nothing else in format- namespace:(one of namespace from given list)""" \
    "topics:(list of strings no numbers or bullets eg- ['early_game_strategy','item_builds']) "\
    "eg-{'namespace': 'compositions', 'topics': ['level_8_board', 'carry_items', ....]}"\
    "namespace list-compositions,items,champions,traits,augments,economy_leveling,positioning,patch_notes,game_mechanics"

def request_OpenRouter(query:str)->str:
    if not OR_API_KEY or OR_API_KEY == "your_openrouter_api_key":
        raise Exception("API Key 未配置。请在 .env 文件中设置 OPEN_ROUTER_API_KEY。")

    # 使用 SiliconCloud (硅基流动) API
    # 文档: https://docs.siliconflow.cn/
    response = requests.post(
        url="https://api.siliconflow.cn/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OR_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            # 这里使用 Qwen2.5-7B-Instruct，它是免费且强大的模型
            # 如果你想用更强的模型，可以换成 "Qwen/Qwen2.5-72B-Instruct" (可能收费)
            # 或者 "deepseek-ai/DeepSeek-V3"
            "model": "Qwen/Qwen2.5-7B-Instruct", 
            "messages": [
            {
                "role": "user",
                "content": f"{query}"
            }
            ],
            "stream": False
        })
        )
    
    if response.status_code != 200:
        error_msg = f"OpenRouter API Error: {response.status_code} - {response.text}"
        raise Exception(error_msg)

    try:
        return response.json()['choices'][0]['message']['content']
    except (KeyError, json.JSONDecodeError) as e:
        raise Exception(f"Invalid response from OpenRouter: {response.text}")



def get_context(topic:str,namespace:str)->Dict:

    try:
        query_embedding=pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[topic],
                parameters={"input_type": "query"},
            )[0].values
        results = index.query(
                namespace=namespace,
                vector=query_embedding,
                top_k=3,
                include_metadata=True
            )
        if results.matches: # type: ignore
                # Fetch relevant documents from Pinecone
                relevant_docs = [
                    match.metadata["text"] for match in results.matches # type: ignore
                ]
                return {"message": "Relevant documents found", "documents": relevant_docs}
        else:
            return{"message":"No relevant documents found"}
    except Exception as e:
            print(e)
            return {"message": "Error querying Pinecone", "error": str(e)}


def google_search_image(query: str) -> str:
    if not gis:
        return "https://via.placeholder.com/150"
    try:
        gis.search(search_params={'q': query, 'num': 1})
        image_url = gis.results()[0].url if gis.results() else "https://via.placeholder.com/150"

        return image_url
    except (IndexError, RequestException, Exception):
        return "https://via.placeholder.com/150"

def new_image(query:str)->str:
    if not gis:
        return "https://via.placeholder.com/150"
    gis.search(search_params={'q': query, 'num': 5})
    image_url = gis.results()[random.randint(0,5)].url if gis.results() else "https://via.placeholder.com/150"
    return image_url
if __name__ == "__main__":
    print(google_search_image("Eiffel Tower"))
