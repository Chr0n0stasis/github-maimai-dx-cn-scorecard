#!/usr/bin/env python3
"""
Maimai DX 玩家信息卡片生成器
用于生成类似 maimai 上屏展示的 SVG 图片，可嵌入 GitHub README
"""

import requests
import sys
import base64
import os
from datetime import datetime

# 默认配置文件路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TITLE_FILE = os.path.join(SCRIPT_DIR, "title.txt")
BACKGROUNDS_DIR = os.path.join(SCRIPT_DIR, "backgrounds")


def load_title_from_file(filepath=TITLE_FILE):
    """从文件加载称号"""
    if not os.path.exists(filepath):
        return ""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释行
            if line and not line.startswith('#'):
                return line
    return ""


def find_background_image(backgrounds_dir=BACKGROUNDS_DIR):
    """自动查找背景图片（取第一个找到的图片）"""
    if not os.path.exists(backgrounds_dir):
        return None
    
    supported_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    for filename in os.listdir(backgrounds_dir):
        if filename.lower().endswith(supported_exts) and not filename.startswith('.'):
            return os.path.join(backgrounds_dir, filename)
    return None


def get_player_data(username=None, qq=None):
    """获取玩家数据"""
    payload = {"b50": "1"}
    if username:
        payload["username"] = username
    elif qq:
        payload["qq"] = qq
    else:
        raise ValueError("必须提供 username 或 qq")
    
    response = requests.post(
        "https://www.diving-fish.com/api/maimaidxprober/query/player",
        json=payload,
        timeout=10
    )
    
    if response.status_code == 400:
        raise Exception("用户不存在")
    elif response.status_code == 403:
        raise Exception("用户已设置隐私或未同意用户协议")
    elif response.status_code != 200:
        raise Exception(f"API 请求失败: {response.status_code}")
    
    return response.json()

def get_rating_color(rating):
    """根据 Rating 返回对应颜色"""
    if rating < 1000:
        return "#FFFFFF"  # 白
    elif rating < 2000:
        return "#00BFFF"  # 蓝
    elif rating < 4000:
        return "#00FF00"  # 绿
    elif rating < 7000:
        return "#FFFF00"  # 黄
    elif rating < 10000:
        return "#FF6347"  # 红
    elif rating < 12000:
        return "#9932CC"  # 紫
    elif rating < 13000:
        return "#CD7F32"  # 铜
    elif rating < 14000:
        return "#C0C0C0"  # 银
    elif rating < 14500:
        return "#FFD700"  # 金
    elif rating < 15000:
        return "#E5E4E2"  # 白金
    else:
        return "url(#rainbow)"  # 彩虹渐变

def get_rating_bg_class(rating):
    """获取 Rating 背景样式"""
    if rating >= 15000:
        return "rainbow-bg"
    return ""

def get_dan_name(additional_rating):
    """获取段位名称"""
    dan_names = [
        "初学者", "一段", "二段", "三段", "四段", "五段",
        "六段", "七段", "八段", "九段", "十段",
        "真初段", "真二段", "真三段", "真四段", "真五段",
        "真六段", "真七段", "真八段", "真九段", "真十段",
        "真皆传", "里皆传"
    ]
    if 0 <= additional_rating < len(dan_names):
        return dan_names[additional_rating]
    return "未知"

def image_to_base64(image_path):
    """将图片转换为 base64 编码"""
    if not image_path or not os.path.exists(image_path):
        return None
    
    # 获取图片类型
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    mime_type = mime_types.get(ext, 'image/png')
    
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    
    return f"data:{mime_type};base64,{encoded}"


def generate_svg_card(player_data, custom_title="", custom_bg=""):
    """生成 SVG 格式的玩家信息卡片
    
    Args:
        player_data: API 返回的玩家数据
        custom_title: 自定义称号文本
        custom_bg: 自定义背景图片路径
    """
    nickname = player_data.get('nickname', '未知')
    rating = player_data.get('rating', 0)
    plate = player_data.get('plate', '')
    dan = player_data.get('additional_rating', 0)
    title = custom_title  # 使用自定义称号
    
    # 计算 B50 Rating
    dx_charts = player_data.get('charts', {}).get('dx', [])
    sd_charts = player_data.get('charts', {}).get('sd', [])
    
    # 排序并取前15个DX成绩和前35个SD成绩
    dx_sorted = sorted(dx_charts, key=lambda x: x.get('ra', 0), reverse=True)[:15]
    sd_sorted = sorted(sd_charts, key=lambda x: x.get('ra', 0), reverse=True)[:35]
    
    dx_rating = sum(chart.get('ra', 0) for chart in dx_sorted)
    sd_rating = sum(chart.get('ra', 0) for chart in sd_sorted)
    
    rating_color = get_rating_color(rating)
    dan_name = get_dan_name(dan)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 计算最高成绩
    all_charts = dx_charts + sd_charts
    best_achievement = max((c.get('achievements', 0) for c in all_charts), default=0) if all_charts else 0
    
    # 处理背景图片
    bg_image_data = image_to_base64(custom_bg) if custom_bg else None
    
    # 背景元素
    if bg_image_data:
        bg_element = f'''<image href="{bg_image_data}" x="0" y="0" width="495" height="195" preserveAspectRatio="xMidYMid slice" clip-path="url(#rounded-clip)"/>
  <rect width="495" height="195" fill="rgba(0,0,0,0.5)" rx="10"/>'''
    else:
        bg_element = '<rect width="495" height="195" fill="url(#bg-gradient)" rx="10"/>'
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="495" height="195" viewBox="0 0 495 195">
  <defs>
    <linearGradient id="rainbow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#ff0000"/>
      <stop offset="16%" style="stop-color:#ff8000"/>
      <stop offset="33%" style="stop-color:#ffff00"/>
      <stop offset="50%" style="stop-color:#00ff00"/>
      <stop offset="66%" style="stop-color:#00ffff"/>
      <stop offset="83%" style="stop-color:#0080ff"/>
      <stop offset="100%" style="stop-color:#ff00ff"/>
    </linearGradient>
    <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e"/>
      <stop offset="100%" style="stop-color:#16213e"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <clipPath id="rounded-clip">
      <rect width="495" height="195" rx="10"/>
    </clipPath>
  </defs>
  
  <!-- 背景 -->
  {bg_element}
  
  <!-- 边框装饰 -->
  <rect x="2" y="2" width="491" height="191" fill="none" stroke="#4a4a6a" stroke-width="2" rx="9"/>
  
  <!-- 顶部装饰条 -->
  <rect x="10" y="10" width="475" height="4" fill="#ff6b9d" rx="2"/>
  
  <!-- 标题区域 -->
  <text x="20" y="45" font-family="Arial, sans-serif" font-size="12" fill="#888">
    <tspan>maimai DX</tspan>
  </text>
  
  <!-- 玩家昵称 -->
  <text x="20" y="75" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#ffffff" filter="url(#glow)">
    {escape_xml(nickname)}
  </text>
  
  <!-- Rating 显示 -->
  <text x="20" y="105" font-family="Arial, sans-serif" font-size="14" fill="#aaa">Rating</text>
  <text x="80" y="105" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="{rating_color}">
    {rating}
  </text>
  
  <!-- 段位 -->
  <rect x="180" y="88" width="80" height="24" fill="#2a2a4a" rx="4"/>
  <text x="220" y="105" font-family="Arial, sans-serif" font-size="14" fill="#ffd700" text-anchor="middle">
    {dan_name}
  </text>
  
  <!-- 称号 -->
  <text x="20" y="132" font-family="Arial, sans-serif" font-size="12" fill="#aaa">称号</text>
  <text x="60" y="132" font-family="Arial, sans-serif" font-size="13" fill="#c9a0dc">
    {escape_xml(title) if title else '(未设置)'}
  </text>
  
  <!-- 牌子 (仅在有牌子时显示) -->
  {f'''<text x="20" y="155" font-family="Arial, sans-serif" font-size="12" fill="#aaa">牌子</text>
  <text x="60" y="155" font-family="Arial, sans-serif" font-size="13" fill="#ffd700">{escape_xml(plate)}</text>''' if plate else ''}
  
  <!-- 分割线 -->
  <line x1="280" y1="30" x2="280" y2="165" stroke="#3a3a5a" stroke-width="1"/>
  
  <!-- 右侧数据面板 -->
  <text x="300" y="50" font-family="Arial, sans-serif" font-size="12" fill="#888">Best 50 详情</text>
  
  <!-- DX Rating -->
  <rect x="300" y="60" width="175" height="35" fill="#1e3a5f" rx="4"/>
  <text x="310" y="78" font-family="Arial, sans-serif" font-size="11" fill="#4da6ff">B15</text>
  <text x="465" y="85" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#4da6ff" text-anchor="end">
    {dx_rating}
  </text>
  
  <!-- SD Rating -->
  <rect x="300" y="100" width="175" height="35" fill="#5f3a1e" rx="4"/>
  <text x="310" y="118" font-family="Arial, sans-serif" font-size="11" fill="#ffa64d">B35</text>
  <text x="465" y="125" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#ffa64d" text-anchor="end">
    {sd_rating}
  </text>
  
  <!-- 底部时间戳 -->
  <text x="20" y="180" font-family="Arial, sans-serif" font-size="10" fill="#555">
    更新于 {timestamp} · Powered by diving-fish
  </text>
</svg>'''
    
    return svg

def escape_xml(text):
    """转义 XML 特殊字符"""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='生成 maimai DX 玩家信息卡片')
    parser.add_argument('--username', '-u', help='查分器用户名')
    parser.add_argument('--qq', '-q', help='绑定的QQ号')
    parser.add_argument('--output', '-o', default='maimai-card.svg', help='输出文件路径')
    parser.add_argument('--title', '-t', help='自定义称号 (不指定则从 title.txt 读取)')
    parser.add_argument('--background', '-b', help='自定义背景图片路径 (不指定则从 backgrounds/ 自动查找)')
    
    args = parser.parse_args()
    
    if not args.username and not args.qq:
        print("错误: 必须提供 --username 或 --qq 参数")
        sys.exit(1)
    
    try:
        print(f"正在获取玩家数据...")
        data = get_player_data(username=args.username, qq=args.qq)
        
        # 加载称号：命令行参数 > title.txt
        title = args.title if args.title else load_title_from_file()
        
        # 加载背景：命令行参数 > backgrounds/ 文件夹
        background = args.background if args.background else find_background_image()
        
        print(f"玩家: {data.get('nickname', '未知')}")
        print(f"Rating: {data.get('rating', 0)}")
        print(f"称号: {title or '(未设置，编辑 title.txt 添加)'}")
        print(f"背景: {background or '(未设置，放入 backgrounds/ 文件夹)'}")
        
        print(f"正在生成卡片...")
        svg = generate_svg_card(data, custom_title=title, custom_bg=background or '')
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(svg)
        
        print(f"✅ 卡片已生成: {args.output}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
