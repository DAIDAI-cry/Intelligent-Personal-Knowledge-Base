#!/usr/bin/env python3
"""
convert_hex_to_vectors.py
"""

import requests
import json
import sys
from pathlib import Path

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


def fetch_hex_json(url: str) -> dict:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return json.loads(resp.text)


def convert_to_vectors(hex_json: dict) -> dict:
    if "data" not in hex_json:
        raise ValueError("下载的 JSON 中未发现 'data' 字段")

    vectors = []
    data = hex_json["data"]

    for idx, (key, item) in enumerate(data.items()):
        name = item.get("name") or str(item.get("id") or key)
        desc = item.get("desc") or ""
        level = str(item.get("level", "1"))
        quality = QUALITY_MAP.get(level, "白银")

        # 判断hex_type：包含金币或经验则为经济型，否则为战力型海克斯
        effect_text = desc.lower()  # 转为小写避免大小写问题
        if "金币" in effect_text or "经验" in effect_text:
            hex_type = "经济型"
        else:
            hex_type = "战力型海克斯"

        vector_id = f"tft_augment_{idx}_{name}"

        full_text = (
            f"{desc}"
            f"向量类型：{CLASS}。"
            f"名字：{name}。"
            f"赛季：{SEASON}。"
            f"强化符文（海克斯）等级：{level}。"
            f"强化符文（海克斯）品质：{quality}。"
        )

        vectors.append({
            "id": vector_id,
            "values": [],
            "metadata": {
                "name": name,
                "season": SEASON,
                "class": CLASS,
                "type": TYPE,
                "augment_level": level,
                "quality": quality,
                "hex_type": hex_type,
                "effect": desc,
                "text": full_text,
                
            }
        })

    return {"vectors": vectors}


def save_json(obj: dict, path: Path):
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    print("开始下载并转换 hex.js ...")
    try:
        hex_json = fetch_hex_json(HEX_URL)
        vectors_obj = convert_to_vectors(hex_json)
        save_json(vectors_obj, OUTPUT_FILE)
    except Exception as e:
        print(f"失败: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"成功！已生成 {OUTPUT_FILE} ，共 {len(vectors_obj['vectors'])} 条")


if __name__ == "__main__":
    main()