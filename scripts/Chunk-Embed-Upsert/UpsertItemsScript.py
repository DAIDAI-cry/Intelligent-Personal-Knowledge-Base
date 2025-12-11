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

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise SystemExit("错误: 未在项目根目录的 .env 中找到 PINECONE_API_KEY，请添加后重试。")

# 你的 Index 名称
INDEX_NAME = "teamfight-tactics-knowledges"

# 输入目录 (Embed 脚本生成的输出目录)
INPUT_DIR = PROJECT_ROOT / "datas" / "EmbeddedData"

def clean_metadata(metadata):
    """
    清洗元数据：
    动态遍历所有字段，尝试将看起来像数字的字符串转换为 float 或 int。
    包含百分比处理 (55.5% -> 0.555)。
    """
    cleaned = metadata.copy()
    
    for key, value in cleaned.items():
        # Pinecone 元数据只支持 str, int, float, bool, list[str]
        if isinstance(value, str):
            # 0. 检查特殊含义符号
            is_percent = '%' in value
            
            # 1. 预处理：移除常见的非数字字符 (%, #, ,)
            clean_val = value.replace('%', '').replace('#', '').replace(',', '').strip()
            
            # 2. 尝试转换
            try:
                # 优先尝试转为 float
                float_val = float(clean_val)
                
                # 如果原值包含%，则数值除以 100
                if is_percent:
                    float_val = float_val / 100.0
                
                # 3. 优化：如果是整数，转为 int
                if float_val.is_integer():
                    cleaned[key] = int(float_val)
                else:
                    # 保留一定精度
                    cleaned[key] = round(float_val, 6)
            except ValueError:
                # 转换失败保留原样
                pass
        
        # 额外安全检查：Pinecone 不支持 None/Null 值
        elif value is None:
            cleaned[key] = ""

    return cleaned

def process_file(index, file_path):
    """
    读取单个文件并上传数据到 Pinecone
    """
    print(f"正在处理文件: {file_path.name}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  -> 读取文件失败 {file_path}: {e}")
        return

    items = data.get("vectors", [])
    total_items = len(items)
    print(f"  -> 读取到 {total_items} 条待上传数据。")

    if total_items == 0:
        print("  -> 数据为空，跳过。")
        return

    # Pinecone 建议每次 Upsert 的 batch size 在 100-200 左右
    batch_size = 100
    vectors_to_upsert = []

    for i, item in enumerate(items):
        # 检查是否有向量数据
        if not item.get('values'):
            print(f"  -> 警告: ID {item.get('id')} 缺少向量数据，跳过。")
            continue

        # --- 修复 ID 非 ASCII 问题 ---
        original_id = item['id']
        # 将非 ASCII 字符转换为 Python 的 unicode escape 序列 (例如 \u9b3c)
        # 这样既满足 Pinecone 的 ASCII 要求，又保留了原始 ID 的信息
        ascii_id = original_id.encode('unicode_escape').decode('ascii')
        
        # 清洗元数据
        cleaned_meta = clean_metadata(item.get('metadata', {}))
        
        # 把原始的可读 ID 存入 metadata，方便以后反查
        cleaned_meta['original_id'] = original_id

        # 构建 Pinecone 向量对象
        vector_record = {
            "id": ascii_id,
            "values": item['values'],
            "metadata": cleaned_meta
        }
        vectors_to_upsert.append(vector_record)

        # 当达到 batch_size 或最后一条数据时，执行上传
        if len(vectors_to_upsert) >= batch_size or i == total_items - 1:
            try:
                index.upsert(vectors=vectors_to_upsert)
                print(f"  -> 已上传批次: {i - len(vectors_to_upsert) + 1} 到 {i} (共 {len(vectors_to_upsert)} 条)")
                vectors_to_upsert = [] # 清空列表
                time.sleep(0.2) # 稍微暂停，避免过于频繁请求
            except Exception as e:
                print(f"  -> 上传批次失败: {e}")
    
    print(f"  -> 文件 {file_path.name} 处理完成。\n")

def main():
    # 1. 初始化 Pinecone 客户端
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # 2. 连接到索引
    print(f"正在连接到索引: {INDEX_NAME}...")
    try:
        index = pc.Index(INDEX_NAME)
        # 简单检查索引状态
        stats = index.describe_index_stats()
        print(f"索引状态: {stats}")
    except Exception as e:
        print(f"连接索引失败: {e}")
        return

    # 3. 检查输入目录
    if not INPUT_DIR.exists():
        print(f"错误: 输入目录不存在 {INPUT_DIR}")
        print("请先运行 EmbedItemsScript.py 生成数据。")
        return

    # 4. 获取所有 JSON 文件
    json_files = list(INPUT_DIR.glob("*.json"))
    
    if not json_files:
        print(f"在 {INPUT_DIR} 中未找到 JSON 文件。")
        return

    print(f"开始批量上传... 共找到 {len(json_files)} 个文件")
    print("-" * 50)

    # 5. 遍历处理每个文件
    for json_file in json_files:
        process_file(index, json_file)

    print("-" * 50)
    print("所有数据上传完成！")
    
    # 6. 验证上传结果
    time.sleep(2) # 等待索引更新
    final_stats = index.describe_index_stats()
    print(f"最终索引统计: {final_stats}")

if __name__ == "__main__":
    main()