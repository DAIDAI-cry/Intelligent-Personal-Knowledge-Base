import time
import json
import re
import datetime
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from dotenv import load_dotenv

# ================= 配置区域 =================
DRIVER_PATH = r"D:\Program Files(x86)\edgedriver_win64\msedgedriver.exe" 
# ===========================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

def scrape_comps_to_json():
    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument("--headless=new")
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_argument("--log-level=3")  # Suppress console logs
    edge_options.add_argument("--silent")       # Suppress console logs
    edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0')
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    try:
        service = Service(executable_path=DRIVER_PATH, log_output=subprocess.DEVNULL)
        driver = webdriver.Edge(service=service, options=edge_options)
    except Exception as e:
        print(f"驱动初始化失败: {e}")
        return

    comps_list = []
    
    try:
        url = "https://op.gg/zh-cn/tft/meta-trends/comps"
        print(f"正在访问: {url}")
        driver.get(url)
        time.sleep(5) # 等待数据加载

        page_source = driver.page_source
        
        # 提取 JSON 数据块
        patterns = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', page_source, re.DOTALL)
        
        all_decoded_chunks = []
        for idx, raw_data in enumerate(patterns):
            try:
                if ':' in raw_data:
                    json_str = f'"{raw_data}"'
                    decoded_str = json.loads(json_str)
                    if ':' in decoded_str:
                        _, real_json_part = decoded_str.split(':', 1)
                        decoded = json.loads(real_json_part)
                        all_decoded_chunks.append(decoded)
            except:
                pass
        
        print(f"提取到 {len(all_decoded_chunks)} 个数据块，开始解析阵容...")

        # 递归查找阵容列表
        # 目标特征: 包含 'teamCode', 'units', 'stat' 的对象
        found_comps = []

        def find_comps_recursive(obj):
            if isinstance(obj, dict):
                if 'teamCode' in obj and 'units' in obj and 'stat' in obj:
                    found_comps.append(obj)
                else:
                    for v in obj.values():
                        find_comps_recursive(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_comps_recursive(item)

        for chunk in all_decoded_chunks:
            find_comps_recursive(chunk)

        print(f"找到 {len(found_comps)} 个阵容数据")

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for comp_data in found_comps:
            try:
                # Helper for safe dict access
                def safe_get(d, key, default=None):
                    if not isinstance(d, dict): return default if default is not None else {}
                    val = d.get(key)
                    return val if val is not None else (default if default is not None else {})

                # 提取基本信息
                raw_name = safe_get(comp_data, 'name')
                if isinstance(raw_name, dict):
                    comp_name = raw_name.get('zh_CN', raw_name.get('en_US', '未命名阵容'))
                else:
                    comp_name = str(raw_name) if raw_name else '未命名阵容'
                
                team_code = comp_data.get('teamCode')
                
                # 提取统计数据
                stat = safe_get(comp_data, 'stat')
                op_tier = stat.get('opTier', 'Unknown')
                # 使用 label 统计数据，更符合页面显示
                deck_stats = safe_get(stat, 'label')
                
                avg_rank = deck_stats.get('avgPlacement')
                win_rate = deck_stats.get('winRate')
                top4_rate = deck_stats.get('top4Rate')
                pick_rate = deck_stats.get('pickRate')
                
                # 格式化百分比
                if win_rate: win_rate = f"{win_rate * 100:.2f}%"
                if top4_rate: top4_rate = f"{top4_rate * 100:.2f}%"
                if pick_rate: pick_rate = f"{pick_rate * 100:.2f}%"

                # 提取单位
                units = []
                raw_units = safe_get(comp_data, 'units', [])
                if isinstance(raw_units, list):
                    for u in raw_units:
                        if not isinstance(u, dict): continue
                        meta = safe_get(u, 'meta')
                        unit_name = meta.get('name', u.get('key'))
                        cost = meta.get('cost')
                        tier = u.get('tier') # 星级
                        items = u.get('items', [])
                        cell = safe_get(u, 'cell')
                        
                        units.append({
                            "name": unit_name,
                            "cost": cost,
                            "star_level": tier,
                            "items": items,
                            "position": f"({cell.get('x')}, {cell.get('y')})"
                        })

                # 提取羁绊 (只保留激活的)
                traits = []
                raw_traits = safe_get(comp_data, 'traits', [])
                if isinstance(raw_traits, list):
                    for t in raw_traits:
                        if not isinstance(t, dict): continue
                        meta = safe_get(t, 'meta')
                        trait_name = meta.get('name', t.get('key'))
                        num_units = t.get('numUnits')
                        style = t.get('style') # 0=None, 1=Bronze, 2=Silver, 3=Gold, 4=Prismatic
                        
                        if style and style > 0:
                            traits.append({
                                "name": trait_name,
                                "count": num_units,
                                "style": style
                            })

                # 提取早期/中期阵容
                early_comp = safe_get(comp_data, 'early')
                mid_comp = safe_get(comp_data, 'middle')
                
                def process_stage_comp(stage_data):
                    if not stage_data or not isinstance(stage_data, dict): return None
                    stage_units = []
                    raw_stage_units = safe_get(stage_data, 'units', [])
                    if isinstance(raw_stage_units, list):
                        for u in raw_stage_units:
                            if not isinstance(u, dict): continue
                            char_id = u.get('characterId')
                            cell = safe_get(u, 'cell')
                            stage_units.append({
                                "id": char_id,
                                "position": f"({cell.get('x')}, {cell.get('y')})"
                            })
                    return {
                        "level": stage_data.get('level'),
                        "units": stage_units
                    }

                early_info = process_stage_comp(early_comp)
                mid_info = process_stage_comp(mid_comp)

                # 构建描述文本
                units_str = ", ".join([f"{u['name']}({u['star_level']}星)" for u in units])
                traits_str = ", ".join([f"{t['count']}{t['name']}" for t in traits])
                
                full_text = (
                    f"阵容名称: {comp_name}。 "
                    f"评级: {op_tier}。 "
                    f"平均排名: {avg_rank}。 "
                    f"前四率: {top4_rate}。 "
                    f"登顶率: {win_rate}。 "
                    f"核心英雄: {units_str}。 "
                    f"激活羁绊: {traits_str}。"
                )
                
                if early_info:
                    full_text += f" 早期过渡(Lv{early_info['level']}): {len(early_info['units'])}个单位。"
                if mid_info:
                    full_text += f" 中期过渡(Lv{mid_info['level']}): {len(mid_info['units'])}个单位。"

                vector_item = {
                    "id": f"tft_comp_{team_code}",
                    "values": [],
                    "metadata": {
                        "text": full_text,
                        "type": "Composition",
                        "comp_name": comp_name,
                        "tier": op_tier,
                        "avg_rank": avg_rank,
                        "win_rate": win_rate,
                        "top4_rate": top4_rate,
                        "pick_rate": pick_rate,
                        "units": units,
                        "traits": traits,
                        "early_comp": early_info,
                        "mid_comp": mid_info,
                        "source_url": url,
                        "crawled_at": current_time,
                        "category": "TFT_Comp_Stats"
                    }
                }
                comps_list.append(vector_item)

            except Exception as e:
                print(f"解析阵容出错: {e}")
                continue

    except Exception as e:
        print(f"运行出错: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

    # 保存结果
    final_data = {
        "vectors": comps_list
    }

    output_dir = PROJECT_ROOT / "datas" / "OriginData"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "opgg_tft_comps.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n成功！共抓取 {len(comps_list)} 条阵容数据，已保存至 {output_path}")

if __name__ == "__main__":
    scrape_comps_to_json()
