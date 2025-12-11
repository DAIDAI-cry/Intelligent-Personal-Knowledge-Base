import json
import time
import os
from pathlib import Path
from pinecone import Pinecone
from dotenv import load_dotenv

# --- 配置部分 ---
# 优先计算路径以加载 .env
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise SystemExit("错误: 未在项目根目录的 .env 中找到 PINECONE_API_KEY，请添加后重试。")

# 你的 Index 名称
INDEX_NAME = "teamfight-tactics-knowledges"

# 输入文件路径 (Embed 脚本生成的输出文件)
INPUT_FILE = PROJECT_ROOT / "datas" / "EmbeddedData" / "opgg_tft_items_embedded.json"

def clean_metadata(metadata):
    """
    清洗元数据：
    动态遍历所有字段，尝试将看起来像数字的字符串转换为 float 或 int。
    这样可以适应不同数据源的不同字段结构。
    """
    cleaned = metadata.copy()
    
    for key, value in cleaned.items():
        # Pinecone 元数据只支持 str, int, float, bool, list[str]
        # 我们主要关注将字符串类型的数字转换为真正的数字
        if isinstance(value, str):
            # 1. 预处理：移除常见的非数字字符 (%, #, ,)
            # 注意：不要移除小数点(.)和负号(-)
            clean_val = value.replace('%', '').replace('#', '').replace(',', '').strip()
            
            # 2. 尝试转换
            try:
                # 优先尝试转为 float
                float_val = float(clean_val)
                
                # 3. 优化：如果是整数（如 4.0），转为 int 看起来更整洁
                if float_val.is_integer():
                    cleaned[key] = int(float_val)
                else:
                    cleaned[key] = float_val
            except ValueError:
                # 转换失败（说明是纯文本，如 "TFT_Item"），保留原样
                pass
        
        # 额外安全检查：Pinecone 不支持 None/Null 值
        elif value is None:
            cleaned[key] = ""  # 或者直接 del cleaned[key]

    return cleaned

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

    # 3. 读取包含向量的数据文件
    if not INPUT_FILE.exists():
        print(f"错误: 找不到输入文件 {INPUT_FILE}")
        print("请先运行 EmbedItemsScript.py 生成数据。")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get("vectors", [])
    total_items = len(items)
    print(f"读取到 {total_items} 条待上传数据。")

    # 4. 准备并批量上传 (Upsert)
    # Pinecone 建议每次 Upsert 的 batch size 在 100-200 左右
    batch_size = 100
    vectors_to_upsert = []

    for i, item in enumerate(items):
        # 检查是否有向量数据
        if not item.get('values'):
            print(f"警告: ID {item.get('id')} 缺少向量数据，跳过。")
            continue

        # --- 修复 ID 非 ASCII 问题 ---
        # 原始 ID: "tft_item_0_鬼索的狂暴之刃+"
        # 我们可以保留原始 ID 在 metadata 中以便人类阅读，但 Pinecone 的主键 ID 必须是 ASCII
        original_id = item['id']
        
        # 方法：将非 ASCII 字符转换为 Python 的 unicode escape 序列 (例如 \u9b3c)
        # 或者更简单：直接把中文部分 encode 为 hex 或 base64，或者直接用索引
        # 这里使用 encode('unicode_escape') 是一种保留语义且兼容 ASCII 的方式
        ascii_id = original_id.encode('unicode_escape').decode('ascii')
        
        # 清洗元数据 (关键步骤，为了支持 Filter)
        cleaned_meta = clean_metadata(item.get('metadata', {}))
        
        # 建议：把原始的可读 ID 存入 metadata，方便以后反查
        cleaned_meta['original_id'] = original_id

        # 构建 Pinecone 向量对象
        vector_record = {
            "id": ascii_id,  # 使用转换后的 ASCII ID
            "values": item['values'],
            "metadata": cleaned_meta
        }
        vectors_to_upsert.append(vector_record)

        # 当达到 batch_size 或最后一条数据时，执行上传
        if len(vectors_to_upsert) >= batch_size or i == total_items - 1:
            try:
                index.upsert(vectors=vectors_to_upsert)
                print(f"已上传批次: {i - len(vectors_to_upsert) + 1} 到 {i} (共 {len(vectors_to_upsert)} 条)")
                vectors_to_upsert = [] # 清空列表
                time.sleep(0.2) # 稍微暂停，避免过于频繁请求
            except Exception as e:
                print(f"上传批次失败: {e}")

    print("\n所有数据上传完成！")
    
    # 5. 验证上传结果
    time.sleep(2) # 等待索引更新
    final_stats = index.describe_index_stats()
    print(f"最终索引统计: {final_stats}")

if __name__ == "__main__":
    main()