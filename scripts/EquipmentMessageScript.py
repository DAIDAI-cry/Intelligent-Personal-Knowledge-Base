import time
import json
import re
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv

# ================= 配置区域 =================
#修改为本地msedgedriver路径
DRIVER_PATH = r"D:\Program Files(x86)\edgedriver_win64\msedgedriver.exe" 
# ===========================================

# 优先计算项目根目录以便保存到 datas/OriginData
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

def extract_first_percentage(text):
    """
    从文本中提取第一个百分比数值，解决 '57.79%57.79%' 重复问题
    """
    if not text:
        return ""
    # 匹配 数字 + 可选小数点 + 数字 + %
    match = re.search(r"(\d+(?:\.\d+)?%)", text)
    if match:
        return match.group(1)
    return text.strip()

def scrape_opgg_to_json():
    # Edge 选项配置
    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0')
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # 初始化驱动（指定路径）
    try:
        service = Service(executable_path=DRIVER_PATH)
        driver = webdriver.Edge(service=service, options=edge_options)
    except Exception as e:
        print(f"驱动初始化失败，请检查路径是否正确: {DRIVER_PATH}")
        print(f"错误信息: {e}")
        return

    vectors_list = []
    
    try:
        url = "https://op.gg/zh-cn/tft/meta-trends/item"
        print(f"正在访问: {url}")
        driver.get(url)

        # 等待数据加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
        )
        time.sleep(3) # 等待图片等资源渲染

        # 获取页面源码解析
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # --- 关键修改：寻找正确的表格 ---
        target_table = None
        tables = soup.find_all('table')
        
        for table in tables:
            # 检查表头是否包含关键列名
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            if "道具" in headers and "平均名次" in headers:
                target_table = table
                break
        
        if not target_table:
            print("错误：未找到包含'道具'和'平均名次'的表格，页面结构可能已变更。")
            return

        print("已定位到目标表格，开始解析...")
        
        tbody = target_table.find('tbody')
        rows = tbody.find_all('tr')
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 遍历每一行
        for index, row in enumerate(rows):
            cols = row.find_all('td')
            if not cols or len(cols) < 6:
                continue

            # 提取基础信息
            # 注意：OP.GG 表格第一列通常是排名(#)，第二列是道具
            
            # 1. 道具名称与合成
            item_col = cols[1]
            item_name = item_col.get_text(strip=True)
            
            # 提取合成公式
            recipe_imgs = item_col.find_all('img')
            all_imgs_alt = [img.get('alt') for img in recipe_imgs if img.get('alt')]
            
            recipe_str = ""
            # 逻辑：通常如果 >=3 张图，最后两张是配方。如果只有1张，是不可合成装备。
            # 排除掉主图（通常主图alt和item_name相似），剩下的如果刚好是2个，就是配方。
            if len(all_imgs_alt) >= 3:
                recipe_str = f"{all_imgs_alt[-2]} + {all_imgs_alt[-1]}"
            elif len(all_imgs_alt) == 2:
                # 某些情况可能只有2张图（主图+1个组件? 不常见），暂且认为无配方或特殊
                pass
            
            if not recipe_str and "纹章" in item_name:
                 recipe_str = "无/不可合成" # 显式标记，或者留空 ""

            # 2. 统计数据 (应用去重函数)
            avg_rank = cols[2].get_text(strip=True)
            top4_rate = extract_first_percentage(cols[3].get_text(strip=True))
            win_rate = extract_first_percentage(cols[4].get_text(strip=True))
            pick_count = cols[5].get_text(strip=True)

            # 3. 推荐英雄
            recommend_col = cols[6]
            champ_imgs = recommend_col.find_all('img')
            recommended_champs = [img.get('alt') for img in champ_imgs if img.get('alt')]
            
            # 4. 构建 Metadata
            full_text_desc = (
                f"道具名称: {item_name}。 "
                f"合成公式: {recipe_str if recipe_str else '无/不可合成'}。 "
                f"统计数据: 平均排名 {avg_rank}，前四率 {top4_rate}，登顶率 {win_rate}，选取次数 {pick_count}。 "
                f"推荐英雄: {', '.join(recommended_champs)}。"
            )

            # 构建符合要求的 JSON 对象
            #处理特殊情况
            indexSpecial = index - int(index != 0) * 6
            vector_item = {
                "id": f"tft_item_{indexSpecial}_{item_name}",
                "values": [],  # 保持为空
                "metadata": {
                    "text": full_text_desc,
                    "type": "Item",
                    "item_name": item_name,
                    "recipe": recipe_str,
                    "avg_rank": avg_rank,
                    "top4_rate": top4_rate,
                    "win_rate": win_rate,
                    "pick_count": pick_count,
                    "recommended_champions": recommended_champs,
                    "source_url": url,
                    "crawled_at": current_time,
                    "category": "TFT_Item_Stats"
                }
            }
            if index not in range(1, 6):
                vectors_list.append(vector_item)
                print(f"已处理: {item_name}")

    except Exception as e:
        print(f"运行出错: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

    # 生成最终 JSON
    final_data = {
        "vectors": vectors_list
    }

    # 保存到项目的 datas/OriginData 目录（参考 EmbedItemsScript 写法）
    output_dir = PROJECT_ROOT / "datas" / "OriginData"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "opgg_tft_items.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n成功！共抓取 {len(vectors_list)} 条数据，已保存至 {output_path}")

if __name__ == "__main__":
    scrape_opgg_to_json()