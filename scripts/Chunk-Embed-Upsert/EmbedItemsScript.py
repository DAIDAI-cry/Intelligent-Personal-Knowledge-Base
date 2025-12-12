import json
import time
import os
from pathlib import Path
from pinecone import Pinecone
from dotenv import load_dotenv

# --- 配置部分 ---
# 优先计算路径以加载 .env
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# 从环境变量获取 API Key
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# 使用的模型，必须是 Pinecone 支持的模型
MODEL_NAME = "llama-text-embed-v2" 

# 目录配置
# 输入：Chunk 后的数据目录
INPUT_DIR = PROJECT_ROOT / "datas" / "ChunkedData"
# 输出：Embedding 后的数据目录
OUTPUT_DIR = PROJECT_ROOT / "datas" / "EmbeddedData"

def process_file(pc, file_path):
    """
    处理单个 JSON 文件进行 Embedding
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"错误: 无法读取文件 {file_path}: {e}")
        return

    items = data.get("vectors", [])
    total_items = len(items)
    print(f"正在处理文件: {file_path.name} (包含 {total_items} 条数据)")

    if total_items == 0:
        print("  -> 数据为空，跳过。")
        return

    # 批量处理 (为了提高效率和避免速率限制)
    batch_size = 10  # 每次处理 10 条
    
    for i in range(0, total_items, batch_size):
        batch_items = items[i : i + batch_size]
        
        # 提取当前批次的文本列表
        texts_to_embed = [item['metadata']['text'] for item in batch_items]
        
        try:
            # 调用 Pinecone Inference API
            # input_type="passage" 表示我们要存储的是文档段落
            embeddings = pc.inference.embed(
                model=MODEL_NAME,
                inputs=texts_to_embed,
                parameters={"input_type": "passage"}
            )
            
            # 将生成的向量填回对应的 item
            for j, embedding_obj in enumerate(embeddings):
                # embedding_obj['values'] 是向量数组
                batch_items[j]['values'] = embedding_obj['values']
                
            print(f"  -> 进度: {min(i + batch_size, total_items)}/{total_items}")
            
            # 简单的速率限制保护，避免触发 API 限制
            time.sleep(0.2) 

        except Exception as e:
            print(f"  -> 批次处理出错 (索引 {i} - {i+batch_size}): {e}")
            # 可以在这里选择是否跳过或停止

    # 准备保存路径
    # 例如: opgg_tft_items_chunked.json -> opgg_tft_items_chunked_embedded.json
    output_file_path = OUTPUT_DIR / f"{file_path.stem}_embedded.json"
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  -> 已保存至: {output_file_path}")

def main():
    # 1. 初始化 Pinecone 客户端
    if not PINECONE_API_KEY:
        print("错误: 未找到 PINECONE_API_KEY 环境变量")
        return
        
    pc = Pinecone(api_key=PINECONE_API_KEY)
    print(f"正在使用模型: {MODEL_NAME}")

    # 2. 检查输入目录
    if not INPUT_DIR.exists():
        print(f"错误: 输入目录不存在 {INPUT_DIR}")
        print("请先运行 ChunkedItemsScript.py 生成数据。")
        return

    # 3. 获取所有 JSON 文件
    json_files = list(INPUT_DIR.glob("*.json"))
    
    if not json_files:
        print(f"在 {INPUT_DIR} 中未找到 JSON 文件。")
        return

    print(f"开始处理 Embedding... 共找到 {len(json_files)} 个文件")
    print("-" * 50)

    # 4. 遍历处理
    for json_file in json_files:
        process_file(pc, json_file)
        
    print("-" * 50)
    print("所有文件处理完成。")
    print("现在你可以使用 UpsertItemsScript.py 将这些文件上传到 Pinecone。")


if __name__ == "__main__":
    main()