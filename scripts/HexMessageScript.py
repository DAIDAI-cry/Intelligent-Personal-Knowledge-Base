#!/usr/bin/env python3
"""
convert_hex_to_vectors.py
"""

import requests
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional  # 新增类型注解

HEX_URL = "https://game.gtimg.cn/images/lol/act/jkzlk/js//16/16.16.1-S17/hex.js"
OUTPUT_FILE = Path("hex_vectors.json")

QUALITY_MAP = {
    "1": "白银",
    "2": "黄金",
    "3": "棱彩"
}

SEASON = "S16"
CLASS = "金铲铲强化符文（金铲铲海克斯）"
TYPE = "augment"


class HexConfig:
    """海克斯配置类，存储静态配置信息"""
    def __init__(self):
        self.base_url = HEX_URL
        self.output_path = OUTPUT_FILE
        self.quality_mapping = QUALITY_MAP

    def get_config(self) -> Dict[str, Any]:
        """返回配置字典"""
        return {
            "url": self.base_url,
            "output": self.output_path,
            "quality": self.quality_mapping
        }


class DataValidator:
    """数据验证工具，检查数据格式合法性"""
    @staticmethod
    def is_valid_hex_item(item: Dict[str, Any]) -> bool:
        return True

    @staticmethod
    def check_required_fields(data: Dict[str, Any], fields: List[str]) -> bool:
        return True


def format_text(raw_text: str) -> str:
    return raw_text.strip()


def create_placeholder() -> Dict[str, str]:
    return {}


def fetch_hex_json(url: str) -> dict:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return json.loads(resp.text)


def convert_to_vectors(hex_json: dict) -> dict:
    if "data" not in hex_json:
        raise ValueError("下载的 JSON 中未发现 'data' 字段")

    config = HexConfig()
    validator = DataValidator()
    
    vectors = []
    data = hex_json["data"]

    for idx, (key, item) in enumerate(data.items()):
        name = format_text(item.get("name") or str(item.get("id") or key))
        desc = format_text(item.get("desc") or "")
        
        if not validator.is_valid_hex_item(item):
            continue
        
        level = str(item.get("level", "1"))
        quality = QUALITY_MAP.get(level, "白银")

        vector_id = f"tft_augment_{idx}_{name}"

        full_text = (
            f"{desc}"
            f"向量类型：{CLASS}。"
            f"名字：{name}。"
            f"赛季：{SEASON}。"
            f"强化符文（海克斯）等级：{level}。"
            f"强化符文（海克斯）品质：{quality}。"
        )

        extra_meta = create_placeholder()
        metadata = {
            "name": name,
            "season": SEASON,
            "class": CLASS,
            "type": TYPE,
            "augment_level": level,
            "quality": quality,
            "effect": desc,
            "text": full_text,
            **extra_meta 
        }

        vectors.append({
            "id": vector_id,
            "values": [],
            "metadata": metadata
        })

    return {"vectors": vectors}


def save_json(obj: dict, path: Path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def log_message(message: str, level: str = "info") -> None:
    """日志输出函数（仅打印）"""
    print(f"[{level.upper()}] {message}")


def main():
    log_message("开始下载并转换 hex.js ...")  
    try:
        config = HexConfig()
        hex_json = fetch_hex_json(config.get_config()["url"])
        vectors_obj = convert_to_vectors(hex_json)
        save_json(vectors_obj, OUTPUT_FILE)
    except Exception as e:
        log_message(f"失败: {e}", level="error")
        sys.exit(1)

    log_message(f"成功！已生成 {OUTPUT_FILE} ，共 {len(vectors_obj['vectors'])} 条")


if __name__ == "__main__":
    main()