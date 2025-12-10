import time
import json
import re
import os
import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# ================= 配置区域 =================
# DRIVER_PATH = r"D:\Program Files(x86)\edgedriver_win64\msedgedriver.exe" # 不再需要手动指定
TARGET_URL = "https://op.gg/zh-cn/tft/meta-trends/tacticians"
OUTPUT_DIR = "datas"
OUTPUT_FILENAME = "opgg_tft_tacticians.json"
# ===========================================

def scrape_tacticians_to_json():
    # Edge 选项配置
    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0')
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # 初始化驱动
    service = None
    try:
        # 尝试自动下载驱动
        driver_path = EdgeChromiumDriverManager().install()
        service = Service(driver_path)
    except Exception as e:
        print(f"自动下载驱动失败: {e}")
        print("尝试直接使用系统路径中的 msedgedriver...")
    
    try:
        if service:
            driver = webdriver.Edge(service=service, options=edge_options)
        else:
            # 如果自动下载失败，尝试直接初始化（依赖系统 PATH）
            driver = webdriver.Edge(options=edge_options)
    except Exception as e:
        print(f"驱动初始化失败: {e}")
        print("请确保已安装 Edge 浏览器驱动 (msedgedriver) 并将其添加到系统 PATH，或者手动指定路径。")
        return

    vectors_list = []
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        print(f"正在访问: {TARGET_URL}")
        driver.get(TARGET_URL)
        
        # 等待表格加载
        wait = WebDriverWait(driver, 20)
        # 假设表格有一个特定的类名或结构，这里尝试等待 tbody
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))
        
        # 稍微等待一下以确保动态内容完全加载
        time.sleep(3)
        
        # 获取页面源码
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找表格行
        # OP.GG 的表格通常在 tbody 中
        tbody = soup.find("tbody")
        if not tbody:
            print("未找到表格内容")
            return

        rows = tbody.find_all("tr")
        print(f"找到 {len(rows)} 行数据")

        for index, row in enumerate(rows):
            cols = row.find_all("td")
            if not cols:
                continue
            
            # 解析每一列的数据
            # 根据之前的文本预览，列的顺序可能是：排名, 英雄/小小英雄信息, 稀有度?, 平均排名, 胜率, 选取次数
            # 具体索引需要根据实际 HTML 调整，这里基于常见结构进行推断
            
            try:
                # 排名
                rank = cols[0].get_text(strip=True)
                
                # 名称 (通常在第二个 td，可能包含图片和多个 span)
                name_cell = cols[1]
                name = name_cell.get_text(strip=True)
                # 尝试提取更干净的名称，如果有 strong 标签
                strong_tag = name_cell.find("strong")
                if strong_tag:
                    name = strong_tag.get_text(strip=True)
                
                # 稀有度/类型 (可能在第三列)
                rarity = cols[2].get_text(strip=True)
                
                # 平均排名
                avg_rank = cols[3].get_text(strip=True)
                
                # 胜率/前四率
                win_rate = cols[4].get_text(strip=True)
                
                # 选取次数 (可能包含逗号)
                pick_count = cols[5].get_text(strip=True)
                
                # 构建描述文本
                full_text_desc = (
                    f"小小英雄: {name}。 "
                    f"稀有度: {rarity}。 "
                    f"统计数据: 平均排名 {avg_rank}，胜率 {win_rate}，选取次数 {pick_count}。"
                )

                vector_item = {
                    "id": f"tft_tactician_{index}_{name}",
                    "values": [],
                    "metadata": {
                        "text": full_text_desc,
                        "tactician_name": name,
                        "rarity": rarity,
                        "avg_rank": avg_rank,
                        "win_rate": win_rate,
                        "pick_count": pick_count,
                        "source_url": TARGET_URL,
                        "crawled_at": current_time,
                        "category": "TFT_Tactician_Stats"
                    }
                }
                
                vectors_list.append(vector_item)
                print(f"已处理: {name}")
                
            except IndexError:
                print(f"跳过格式不匹配的行: {index}")
                continue

    except Exception as e:
        print(f"运行出错: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

    # 确保输出目录存在
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 生成最终 JSON
    final_data = {
        "vectors": vectors_list
    }

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n成功！共抓取 {len(vectors_list)} 条数据，已保存至 {output_path}")

if __name__ == "__main__":
    scrape_tacticians_to_json()
