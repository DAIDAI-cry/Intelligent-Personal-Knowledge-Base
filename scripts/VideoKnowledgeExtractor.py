import os
import json
import cv2
import time
import math
import datetime
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from yt_dlp import YoutubeDL
from PIL import Image
'''
脚本功能说明
自动下载：使用 yt-dlp 自动下载您配置的 B 站视频到本地临时文件。
字幕同步：读取同目录下的 VideoCaption.json，并将其按时间窗口（默认 30 秒）进行切分。
智能抽帧：自动提取每个时间窗口中间时刻的关键帧图片。
多模态分析：将 [关键帧图片] + [该时段字幕] 同时发送给 Google Gemini 3.0 flash。
结构化输出：要求 Gemini 结合画面（识别图表、概率、装备公式）和字幕，直接输出 JSON 格式的知识点。

使用该脚本需求：
1. 在项目根目录的 .env 文件中配置 GOOGLE_API_KEY。
2. 安装必要的依赖库
3. 在脚本顶部配置 VIDEO_URL 和其他参数。
4.在脚本同目录下准备好 VideoCaption.json 字幕文件。
'''
# ================= 配置区域 =================
# 1. B站视频链接 (请在此处修改)
VIDEO_URL = "https://www.bilibili.com/video/BV1rJqnBDEao" 
# 自动提取视频ID
VIDEO_ID = VIDEO_URL.rstrip('/').split('/')[-1].split('?')[0]

# 2. 字幕文件路径 (脚本同目录下的 VideoCaption.json)
SCRIPT_DIR = Path(__file__).parent
CAPTION_PATH = SCRIPT_DIR / "VideoCaption.json"

# 3. 输出文件路径
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "datas" / "OriginData"
OUTPUT_FILE = OUTPUT_DIR / f"video_knowledge_{VIDEO_ID}.json"

# 4. 切片时间窗口 (秒)
# Gemini 3.0 Flash 上下文很长，可以适当设大一点，比如 30-60秒
TIME_WINDOW = 30
# ===========================================

# 加载环境变量
load_dotenv(PROJECT_ROOT / ".env")
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("请在 .env 文件中配置 GOOGLE_API_KEY")

genai.configure(api_key=api_key)

def download_video(url, output_path):
    """使用 yt-dlp 下载视频"""
    if os.path.exists(output_path):
        print(f"视频已存在，跳过下载: {output_path}")
        return

    print(f"正在下载视频: {url} ...")
    
    # 策略: 仅下载视频流 (Video Only)
    # 原因: 
    # 1. B站该视频仅提供分离的音视频流 (DASH)，合并需要 FFmpeg。
    # 2. 我们的脚本只需要提取画面帧进行 OCR/视觉分析，不需要音频 (字幕已由 JSON 提供)。
    # 3. 这样可以避免安装 FFmpeg 的麻烦。
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]/bestvideo', # 优先下载 MP4 格式的纯视频流
        'outtmpl': str(output_path),
        'quiet': False,
        'no_warnings': False
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("下载完成 (仅视频流)！")
    except Exception as e:
        print(f"下载失败: {e}")
        raise e

def load_captions(json_path):
    """读取并解析字幕文件"""
    if not json_path.exists():
        raise FileNotFoundError(f"未找到字幕文件: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取 body 部分
    return data.get('body', [])

def extract_frame(video_path, timestamp_sec):
    """提取指定时间点的帧"""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    
    # 跳转到指定时间
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        # OpenCV 是 BGR，转为 RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
    return None

def analyze_with_gemini(image, subtitle_text, start_time, end_time):
    """调用 Gemini 3.0 Flash 进行多模态分析"""
    model = genai.GenerativeModel('gemini-3-flash-preview')
    
    prompt = f"""
    你是一个《金铲铲之战/云顶之弈》的游戏专家。
    我将提供一张游戏视频的截图（时间段：{start_time}s - {end_time}s）以及该时间段内的解说字幕。
    
    请注意：
    1. 字幕可能只是口语，信息不全。
    2. **屏幕上的文字、图表、装备图标、羁绊结构**往往包含更关键的数据（如具体的概率数值、羁绊效果、装备合成公式），请务必仔细识别图片内容。
    3. 请结合“画面视觉信息”和“字幕解说”，总结出核心知识点。
    
    字幕内容：
    "{subtitle_text}"
    
    请输出一个 JSON 数组，每个元素包含以下字段：
    - category: 知识点分类（如：装备系统、海克斯、运营节奏、英雄技能）
    - question: 用户可能会问的问题（用于检索）
    - content: 详细的知识回答（融合了画面和字幕的完整信息）
    - keywords: 关键词列表
    
    请直接返回 JSON 格式，不要包含 Markdown 标记。
    """
    
    try:
        # 发送图片和文本
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        print(f"Gemini API 调用失败: {e}")
        return "[]"

def clean_json_string(json_str):
    """清洗 Gemini 返回的 JSON 字符串"""
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:]
    if json_str.startswith("```"):
        json_str = json_str[3:]
    if json_str.endswith("```"):
        json_str = json_str[:-3]
    return json_str

def main():
    # 1. 准备路径
    temp_video_path = SCRIPT_DIR / "temp_video.mp4"
    
    # 2. 下载视频
    download_video(VIDEO_URL, temp_video_path)
    
    # 3. 加载字幕
    captions = load_captions(CAPTION_PATH)
    if not captions:
        print("字幕为空，退出。")
        return

    # 4. 分段处理
    video_duration = captions[-1]['to']
    num_chunks = math.ceil(video_duration / TIME_WINDOW)
    
    all_knowledge_points = []
    
    print(f"视频总时长: {video_duration}秒，将分为 {num_chunks} 个片段进行处理...")
    
    for i in range(num_chunks):
        start_t = i * TIME_WINDOW
        end_t = min((i + 1) * TIME_WINDOW, video_duration)
        
        # 4.1 获取该时间段内的所有字幕
        chunk_captions = [
            c['content'] for c in captions 
            if c['from'] >= start_t and c['from'] < end_t
        ]
        subtitle_text = " ".join(chunk_captions)
        
        if not subtitle_text.strip():
            continue
            
        print(f"\n--- 处理片段 {i+1}/{num_chunks} ({start_t}s - {end_t}s) ---")
        
        # 4.2 提取中间时刻的关键帧
        mid_time = (start_t + end_t) / 2
        image = extract_frame(temp_video_path, mid_time)
        
        if image:
            # 4.3 调用 Gemini
            print("正在调用 Gemini 3.0 Flash 进行多模态分析...")
            json_response = analyze_with_gemini(image, subtitle_text, start_t, end_t)
            
            # 4.4 解析结果
            try:
                cleaned_json = clean_json_string(json_response)
                points = json.loads(cleaned_json)
                if isinstance(points, list):
                    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for idx, point in enumerate(points):
                        # Generate ID
                        item_id = f"video_{VIDEO_ID}_chunk_{i}_{idx}"
                        
                        # Construct rich metadata
                        metadata = {
                            "text": f"问题：{point.get('question', '')}\n答案：{point.get('content', '')}",
                            "type": "VideoKnowledge",
                            "category": point.get('category', '未分类'),
                            "question": point.get('question', ''),
                            "content": point.get('content', ''),
                            "keywords": point.get('keywords', []),
                            "video_id": VIDEO_ID,
                            "video_url": VIDEO_URL,
                            "timestamp_start": start_t,
                            "timestamp_end": end_t,
                            "crawled_at": current_time_str
                        }
                        
                        vector_item = {
                            "id": item_id,
                            "values": [],
                            "metadata": metadata
                        }
                        all_knowledge_points.append(vector_item)
                    print(f"成功提取 {len(points)} 个知识点")
                else:
                    print("API 返回格式异常，跳过")
            except json.JSONDecodeError:
                print(f"JSON 解析失败，原始内容: {json_response[:100]}...")
        else:
            print("无法提取帧，跳过")
            
        # 避免触发 API 速率限制
        time.sleep(2)

    # 5. 保存结果
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
    final_output = {
        "vectors": all_knowledge_points
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
        
    print(f"\n处理完成！所有知识点已保存至: {OUTPUT_FILE}")
    
    # 可选：删除临时视频
    if temp_video_path.exists():
        os.remove(temp_video_path)

if __name__ == "__main__":
    main()
