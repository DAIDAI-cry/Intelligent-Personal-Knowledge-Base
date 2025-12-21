import json
import os
from abc import ABC, abstractmethod

class BasePineconeProcessor(ABC):
    def __init__(self, input_path, output_path, source_name, doc_type="knowledge_base", version="1.0"):
        self.input_path = input_path
        self.output_path = output_path
        self.source_name = source_name
        self.doc_type = doc_type
        self.version = version
        self.raw_text = ""
        self.chunks = [] # 存储 {"content": "...", "category": "..."}

    def load_text(self):
        """读取文本文件"""
        if not os.path.exists(self.input_path):
            # 如果文件不存在，尝试作为原始字符串处理（兼容硬编码数据模式）
            return
        
        with open(self.input_path, 'r', encoding='utf-8') as f:
            self.raw_text = f.read()
        print(f"已加载文件: {self.input_path}")

    def split_into_chunks(self, max_chars=500):
        """
        默认分块逻辑：按行读取，合并直到达到 max_chars。
        子类可以重写此方法以实现更精细的语义分块。
        """
        if not self.raw_text:
            return

        lines = self.raw_text.split('\n')
        current_text = []
        current_len = 0
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if current_len + len(line) > max_chars and current_text:
                text_block = "".join(current_text)
                # 默认分类为 General，子类可通过 get_category 细化
                self.chunks.append({"content": text_block, "category": "General"})
                current_text = []
                current_len = 0
            
            current_text.append(line + "，")
            current_len += len(line)
            
        if current_text:
            self.chunks.append({"content": "".join(current_text), "category": "General"})

    @abstractmethod
    def clean_text(self, text):
        """子类必须实现：清洗文本（修正OCR错误等）"""
        pass

    @abstractmethod
    def get_category(self, text):
        """子类必须实现：根据文本内容判断分类"""
        pass

    def process(self):
        self.load_text()
        
        # 如果子类没有在 load_text 中填充 self.chunks (例如硬编码数据)，则执行默认分块
        if not self.chunks and self.raw_text:
            self.split_into_chunks()
        
        pinecone_vectors = []
        
        for idx, item in enumerate(self.chunks):
            # 1. 获取内容和分类
            if isinstance(item, dict):
                content = item.get("content", "")
                category = item.get("category") or self.get_category(content)
            else:
                content = item
                category = self.get_category(content)

            # 2. 清洗
            cleaned_text = self.clean_text(content)
            
            # 3. 上下文注入
            enriched_text = f"【{category}】 {cleaned_text}"
            
            # 4. 构建 Metadata
            # 基础字段
            metadata = {
                "text": enriched_text, # 核心字段
                "source": self.source_name,
                "category": category,
                "type": self.doc_type, # 核心字段：类型
                "version": self.version,
                "char_count": len(enriched_text)
            }

            # 扩展字段：如果 item 是字典，将其他描述性字段（如 title, description, tags）也合并进来
            if isinstance(item, dict):
                for k, v in item.items():
                    if k not in ["content", "category"]:
                        metadata[k] = v
            
            # 兜底：确保有 title
            if "title" not in metadata:
                metadata["title"] = f"{category} - {self.source_name}"

            record = {
                "id": f"{self.source_name}_{idx+1:03d}",
                "values": [], # 预留给 Embedding
                "metadata": metadata
            }
            pinecone_vectors.append(record)
            
        # 5. 包装成 {"vectors": [...]} 结构
        final_output = {"vectors": pinecone_vectors}
        self.save_to_json(final_output)

    def save_to_json(self, data):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"处理完成！已生成符合 OriginData 规范的文件: {self.output_path}")
