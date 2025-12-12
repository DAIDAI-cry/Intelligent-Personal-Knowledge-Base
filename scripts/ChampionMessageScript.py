import time
import json
import re
import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ================= 配置区域 =================
# 修改为本地msedgedriver路径
DRIVER_PATH = r"D:\Program Files(x86)\edgedriver_win64\msedgedriver.exe" 
# ===========================================

# 优先计算项目根目录以便保存到 datas/OriginData
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

def extract_first_percentage(text):
    """
    从文本中提取第一个百分比数值
    """
    if not text:
        return ""
    match = re.search(r"(\d+(?:\.\d+)?%)", text)
    if match:
        return match.group(1)
    return text.strip()

def scrape_champions_to_json():
    # Edge 选项配置
    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument("--headless=new")
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--no-sandbox')
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0')
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # 初始化驱动
    try:
        service = Service(executable_path=DRIVER_PATH)
        driver = webdriver.Edge(service=service, options=edge_options)
    except Exception as e:
        print(f"驱动初始化失败，请检查路径是否正确: {DRIVER_PATH}")
        print(f"错误信息: {e}")
        return

    vectors_list = []
    
    try:
        url = "https://op.gg/zh-cn/tft/meta-trends/champion"
        print(f"正在访问: {url}")
        driver.get(url)

        # 等待数据加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
        )
        time.sleep(3) # 等待渲染

        # 第一步：收集所有英雄的基本信息和详情页 URL
        print("正在收集英雄列表信息...")
        champion_list_data = []
        
        # 等待数据加载
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "tbody"))
        )
        time.sleep(3) # 等待渲染

        rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        total_champions = len(rows)
        print(f"检测到 {total_champions} 个英雄，开始收集信息...")
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for i, row in enumerate(rows):
            try:
                row_html = row.get_attribute('outerHTML')
                row_soup = BeautifulSoup(row_html, 'html.parser')
                cols = row_soup.find_all('td')
                
                if len(cols) < 7:
                    continue
                
                # 提取基本信息
                champion_name = ""
                name_elem = cols[1].find('strong')
                if name_elem:
                    champion_name = name_elem.get_text(strip=True)
                else:
                    champion_name = cols[1].get_text(strip=True)
                    match = re.match(r"([^\d]+)", champion_name)
                    if match:
                        champion_name = match.group(1).strip()
                
                if not champion_name:
                    continue

                cost_str = cols[2].get_text(strip=True)
                cost = cost_str.replace('$', '') if '$' in cost_str else cost_str
                list_avg_rank = cols[3].get_text(strip=True)
                top4_rate = extract_first_percentage(cols[4].get_text(strip=True))
                win_rate = extract_first_percentage(cols[5].get_text(strip=True))
                pick_count = cols[6].get_text(strip=True)
                
                # 提取 URL
                detail_url = None
                link_elem = row_soup.find('a')
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    detail_url = href if href.startswith('http') else f"https://op.gg{href}"
                else:
                    # 尝试从图片 src 提取 Key
                    # src=".../tft16_baronnashor.tft_set16.png..."
                    img_elem = row_soup.find('img')
                    if img_elem and img_elem.get('src'):
                        src = img_elem.get('src')
                        # 提取文件名
                        filename = src.split('/')[-1]
                        # 提取 Key (去除 .tft_set16.png 等后缀)
                        # 通常是 tft16_name.suffix
                        key = filename.split('.')[0]
                        if key:
                            # 构造 URL
                            detail_url = f"https://op.gg/zh-cn/tft/meta-trends/champion/{key}"


                
                champion_list_data.append({
                    "name": champion_name,
                    "cost": cost,
                    "avg_rank": list_avg_rank,
                    "top4_rate": top4_rate,
                    "win_rate": win_rate,
                    "pick_count": pick_count,
                    "detail_url": detail_url
                })
            except Exception as e:
                print(f"解析行 {i} 失败: {e}")
                continue
        
        print(f"成功收集 {len(champion_list_data)} 个英雄的信息，开始抓取详情...")
        
        # 第二步：遍历列表抓取详情
        # target_champs = ['瑞兹', '岩宝', '峡谷先锋']
        for i, champ_data in enumerate(champion_list_data):
            # if champ_data['name'] not in target_champs: continue
            print(f"[{i+1}/{len(champion_list_data)}] 正在处理: {champ_data['name']}")
            
            # 初始化默认值
            recommended_items = []
            skill_desc = "暂无技能信息"
            stats = {}
            traits = []
            
            detail_url = champ_data['detail_url']
            champion_name = champ_data['name']
            cost = champ_data['cost']
            list_avg_rank = champ_data['avg_rank']
            top4_rate = champ_data['top4_rate']
            win_rate = champ_data['win_rate']
            pick_count = champ_data['pick_count']
            
            try:
                if detail_url:
                    driver.get(detail_url)
                    # 等待加载
                    try:
                        WebDriverWait(driver, 8).until(
                            EC.presence_of_element_located((By.TAG_NAME, "h2"))
                        )
                        time.sleep(1.5)
                    except:
                        pass
                    
                    detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    # 1. 推荐装备
                    target_headers = detail_soup.find_all(string=re.compile(r"推荐|Items|道具"))
                    for header_text in target_headers:
                        header_parent = header_text.parent
                        container = header_parent.find_parent('div')
                        if container:
                            tables = container.find_all('table')
                            if tables:
                                item_rows = tables[0].find_all('tr')
                                for tr in item_rows:
                                    imgs = tr.find_all('img')
                                    if imgs:
                                        alt = imgs[0].get('alt')
                                        if alt and alt not in recommended_items:
                                            recommended_items.append(alt)
                                recommended_items = recommended_items[:6]
                                break

                    # --- JSON 数据提取 (Stats & Traits & Skills) ---
                    print(f"  -> [JSON] 尝试从页面数据提取属性和羁绊...")
                    
                    # HTML Fallback for Skill Description
                    html_skill_desc = ""
                    try:
                        # Look for skill description in HTML
                        # Common structure: div with class containing "skill" or "ability"
                        skill_section = detail_soup.find('div', class_=re.compile(r'skill|ability', re.I))
                        if skill_section:
                            html_skill_desc = skill_section.get_text(strip=True)
                        else:
                            # Try searching for the section header
                            header = detail_soup.find(string=re.compile(r"技能|Skill|Ability"))
                            if header:
                                container = header.find_parent('div')
                                if container:
                                    html_skill_desc = container.get_text(strip=True)
                    except:
                        pass

                    champion_eng_name = ""
                    if detail_url:
                        parts = detail_url.rstrip('/').split('/')
                        if parts:
                            champion_eng_name = parts[-1].split('?')[0]
                    
                    if champion_eng_name:
                        try:
                            page_source = driver.page_source
                            patterns = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', page_source, re.DOTALL)
                            
                            # Pre-decode all chunks
                            all_decoded_chunks = []
                            for idx, raw_data in enumerate(patterns):
                                try:
                                    # Handle Next.js Flight format "id:json"
                                    if ':' in raw_data:
                                        # raw_data is the string inside push([1, "..."])
                                        # It is already a string literal.
                                        # We need to unescape it to get the real string.
                                        json_str = f'"{raw_data}"'
                                        decoded_str = json.loads(json_str)
                                        
                                        if ':' in decoded_str:
                                            _, real_json_part = decoded_str.split(':', 1)
                                            decoded = json.loads(real_json_part)
                                            all_decoded_chunks.append(decoded)
                                except:
                                    pass
                            
                            # Recursive search for champion object
                            target_obj = None
                            
                            def find_champion_obj(obj, target_name_cn, target_name_eng):
                                if isinstance(obj, dict):
                                    # Check name match
                                    if obj.get('name') == target_name_cn:
                                        return obj
                                    # Check key match (fallback)
                                    if obj.get('_key') and target_name_eng.lower() in obj.get('_key').lower():
                                        return obj
                                    
                                    for v in obj.values():
                                        res = find_champion_obj(v, target_name_cn, target_name_eng)
                                        if res: return res
                                elif isinstance(obj, list):
                                    for item in obj:
                                        res = find_champion_obj(item, target_name_cn, target_name_eng)
                                        if res: return res
                                return None

                            target_obj = None
                            for chunk in all_decoded_chunks:
                                target_obj = find_champion_obj(chunk, champion_name, champion_eng_name)
                                if target_obj: break
                            
                            if target_obj:
                                # Extract Stats
                                if 'stats' in target_obj:
                                    s = target_obj['stats']
                                    stats = {
                                        "health": s.get('hp'),
                                        "mana": s.get('mana'),
                                        "initial_mana": s.get('initialMana'),
                                        "attack_damage": s.get('damage'),
                                        "armor": s.get('armor'),
                                        "magic_resist": s.get('magicResist'),
                                        "attack_speed": s.get('attackSpeed'),
                                        "attack_range": s.get('range')
                                    }
                                    # Filter None
                                    stats = {k: v for k, v in stats.items() if v is not None}
                                
                                # Extract Traits
                                if 'traits' in target_obj:
                                    t_data = target_obj['traits']
                                    if isinstance(t_data, list):
                                        traits = [t if isinstance(t, str) else t.get('name') for t in t_data]
                                        traits = [t for t in traits if t]
                                
                                # Extract Ability
                                if 'ability' in target_obj:
                                    ab = target_obj['ability']
                                    desc = ab.get('desc', '')
                                    variables = ab.get('variables', [])
                                    
                                    # Variable Replacement
                                    if variables:
                                        for var in variables:
                                            name = var.get('name')
                                            values = var.get('value')
                                            if name and values:
                                                vals = values[:3]
                                                if all(v == vals[0] for v in vals):
                                                    val_str = str(vals[0])
                                                else:
                                                    val_str = " / ".join([str(v) for v in vals])
                                                
                                                pattern = f"@{name}@"
                                                desc = desc.replace(pattern, f"[{val_str}]")
                                                
                                                pattern_100 = f"@{name}*100@"
                                                if pattern_100 in desc:
                                                    vals_100 = [v * 100 for v in vals]
                                                    if all(v == vals_100[0] for v in vals_100):
                                                        val_str_100 = f"{vals_100[0]:.0f}"
                                                    else:
                                                        val_str_100 = " / ".join([f"{v:.0f}" for v in vals_100])
                                                    desc = desc.replace(pattern_100, f"[{val_str_100}]%")

                                    # Cleanup HTML
                                    desc = re.sub(r'<[^>]+>', '', desc)
                                    desc = desc.replace('%i:scaleAP%', '').replace('%i:scaleAD%', '').replace('%i:scaleHealth%', '')
                                    
                                    # Check if desc is a placeholder like $2c
                                    if desc.startswith('$'):
                                        print(f"  -> [JSON] 技能描述是占位符 {desc}，尝试使用 HTML 提取结果")
                                        if html_skill_desc:
                                            skill_desc = html_skill_desc
                                            print(f"  -> [HTML] 使用 HTML 提取的技能描述")
                                        else:
                                            skill_desc = f"暂无详细描述 (JSON: {desc})"
                                    else:
                                        skill_desc = desc
                                        print(f"  -> [JSON] 成功提取技能描述")
                                
                                if stats:
                                    print(f"  -> [JSON] 成功提取属性: {len(stats)} 项")
                                    print(f"  -> [JSON] 成功提取羁绊: {traits}")
                            
                            else:
                                print(f"  -> [JSON] 未找到英雄对象: {champion_name}")

                        except Exception as e:
                            print(f"  -> [JSON] 提取过程出错: {e}")
                            import traceback
                            traceback.print_exc()
                else:
                    print("  -> 无详情页 URL，跳过详情抓取")
                
                # --- 构建 Metadata ---
                stats_str = ", ".join([f"{k}: {v}" for k, v in stats.items()]) if stats else "暂无基础属性"
                traits_str = ", ".join(traits) if traits else "暂无羁绊信息"

                full_text_desc = (
                    f"英雄名称: {champion_name}。 "
                    f"费用: {cost}费。 "
                    f"羁绊: {traits_str}。 "
                    f"基础属性: {stats_str}。 "
                    f"统计数据: 平均排名 {list_avg_rank}，前四率 {top4_rate}，登顶率 {win_rate}，选取次数 {pick_count}。 "
                    f"推荐装备: {', '.join(recommended_items) if recommended_items else '暂无数据'}。 "
                    f"技能信息: {skill_desc}。"
                )

                vector_item = {
                    "id": f"tft_champion_{champion_name}",
                    "values": [],
                    "metadata": {
                        "text": full_text_desc,
                        "type": "Champion",
                        "champion_name": champion_name,
                        "cost": cost,
                        "traits": traits,
                        "base_stats": stats,
                        "avg_rank": list_avg_rank,
                        "top4_rate": top4_rate,
                        "win_rate": win_rate,
                        "pick_count": pick_count,
                        "recommended_items": recommended_items,
                        "skill_description": skill_desc,
                        "source_url": detail_url if detail_url else url,
                        "crawled_at": current_time,
                        "category": "TFT_Champion_Stats"
                    }
                }
                vectors_list.append(vector_item)
                
            except Exception as e:
                print(f"处理第 {i+1} 个英雄时出错: {e}")
                # 确保切回主窗口
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[0])
                continue

    except Exception as e:
        print(f"运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'driver' in locals():
            driver.quit()

    # 生成最终 JSON
    final_data = {
        "vectors": vectors_list
    }

    # 保存到项目的 datas/OriginData 目录
    output_dir = PROJECT_ROOT / "datas" / "OriginData"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "opgg_tft_champions.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n成功！共抓取 {len(vectors_list)} 条数据，已保存至 {output_path}")

if __name__ == "__main__":
    scrape_champions_to_json()
