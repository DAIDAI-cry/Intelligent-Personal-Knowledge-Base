import json
from pathlib import Path

# ================= 全局配置参数 =================
# 单个 Chunk 的最大字符长度
# 注意：这里是字符数(Character)，不是 Token 数。
# 如果使用 OpenAI 模型，通常 1 Token ≈ 1.5~2 字符 (中文)。
# 建议根据 Embedding 模型的限制设置，例如 500-1000 字符。
MAX_CHUNK_SIZE = 800 

# 切分时的重叠字符长度 (Overlap)
# 保证上下文的连续性，避免关键信息被切断。
OVERLAP_SIZE = 150
# ===============================================

# 路径配置
SCRIPT_DIR = Path(__file__).parent
# 修改：由于脚本在 scripts/Chunk-Embed-Upsert 下，需要向上两级才能找到项目根目录
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_DIR = PROJECT_ROOT / "datas" / "OriginData"
OUTPUT_DIR = PROJECT_ROOT / "datas" / "ChunkedData"

def chunk_text(text, max_size, overlap):
    """
    将文本切分为多个片段，包含重叠部分。
    """
    if not text:
        return []
    
    text_len = len(text)
    
    # 如果文本长度小于最大限制，直接返回原文本
    if text_len <= max_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < text_len:
        end = min(start + max_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)
        
        # 如果已经到达末尾，结束循环
        if end == text_len:
            break
            
        # 计算下一次的起始位置 (当前结束位置 - 重叠部分)
        start = end - overlap
        
        # 防止死循环（如果 overlap 设置得比 max_size 还大，或者逻辑错误）
        if start >= end:
            start = end
            
    return chunks

def process_file(file_path):
    """
    处理单个 JSON 文件
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        original_vectors = data.get("vectors", [])
        chunked_vectors = []
        
        print(f"正在处理文件: {file_path.name} (包含 {len(original_vectors)} 条原始数据)")
        
        for item in original_vectors:
            original_id = item.get('id')
            metadata = item.get('metadata', {})
            text_content = metadata.get('text', '')
            
            # 执行切分
            text_chunks = chunk_text(text_content, MAX_CHUNK_SIZE, OVERLAP_SIZE)
            
            # 为每个 chunk 创建新的向量对象
            for i, chunk_text_content in enumerate(text_chunks):
                # 深拷贝 metadata 以避免修改原始引用
                new_metadata = metadata.copy()
                
                # 更新 metadata 中的 text 为当前 chunk 的内容
                new_metadata['text'] = chunk_text_content
                
                # 添加分块信息到 metadata (可选，方便调试)
                new_metadata['chunk_index'] = i
                new_metadata['total_chunks'] = len(text_chunks)
                new_metadata['parent_id'] = original_id
                
                # 构建新的 ID
                # 格式: 原ID_chunk_0, 原ID_chunk_1
                new_id = f"{original_id}_chunk_{i}"
                
                new_vector_item = {
                    "id": new_id,
                    "values": [], # 保持为空，等待 Embedding 步骤填充
                    "metadata": new_metadata
                }
                
                chunked_vectors.append(new_vector_item)
        
        # 准备保存
        output_data = {"vectors": chunked_vectors}
        output_file_path = OUTPUT_DIR / f"{file_path.stem}_chunked.json"
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"  -> 生成 {len(chunked_vectors)} 个 Chunk片段")
        print(f"  -> 已保存至: {output_file_path}")
        
    except Exception as e:
        print(f"处理文件 {file_path.name} 时出错: {e}")

def main():
    # 1. 确保输出目录存在
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"已创建输出目录: {OUTPUT_DIR}")
        
    # 2. 检查输入目录
    if not INPUT_DIR.exists():
        print(f"错误: 输入目录不存在 {INPUT_DIR}")
        return

    # 3. 获取所有 JSON 文件
    json_files = list(INPUT_DIR.glob("*.json"))
    
    if not json_files:
        print(f"在 {INPUT_DIR} 中未找到 JSON 文件。")
        return
        
    print(f"开始处理 Chunking... (Max Size: {MAX_CHUNK_SIZE}, Overlap: {OVERLAP_SIZE})")
    print("-" * 50)

    # 4. 遍历处理
    for json_file in json_files:
        process_file(json_file)
        
    print("-" * 50)
    print("所有文件处理完成。")

if __name__ == "__main__":
    main()