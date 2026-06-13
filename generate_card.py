#!/usr/bin/env python3
"""
Maimai DX 玩家信息卡片生成器 (Lxns API 版)
用于生成类似 maimai 上屏展示的 SVG 图片，可嵌入 GitHub README
"""

import requests
import sys
import base64
import os
import urllib.request
from datetime import datetime

# 默认配置文件路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 布局配置参数 (可在 GUI 编辑器 editor.html 中调节并复制替换)
# ==========================================
# Name Plate
PLATE_X = 32
PLATE_Y = 22
PLATE_W = 720
PLATE_H = 116

# Avatar (Rounded Corner Box)
AVATAR_X = 41
AVATAR_Y = 31
AVATAR_SIZE = 97
AVATAR_RX = 0

# Player custom title (Trophy)
TROPHY_X = 161
TROPHY_Y = 130
TROPHY_SIZE = 15

# Player name (Name)
NAME_X = 158
NAME_Y = 97
NAME_Y_NOTROPHY = 86
NAME_SIZE = 22

# Player name background box (Name BG)
NAME_BG_X = 150
NAME_BG_Y = 76
NAME_BG_W = 265
NAME_BG_H = 28
NAME_BG_RX = 8

# Rating Panel Base
RATING_X = 148
RATING_Y = 24
RATING_W = 191
RATING_H = 52

# Rating Digits (Numbers)
DIGITS_X = 237
DIGITS_Y = 41
DIGITS_SPACING = 14.9

# Star Ribbon
STAR_X = 323
STAR_Y = 32

# Class Badge (B5, S0, etc.)
CLASS_X = 346
CLASS_Y = 27

# Dan Title Stamp (初心者, etc.)
DAN_X = 338
DAN_Y = 72

# B35/B15 Progress Bar
PROG_X = 29
PROG_Y = 143
PROG_W = 243
PROG_TEXT_OFFSET = 21



def fetch_image_as_base64(url):
    """
    下载图片并转换为 base64 data URI
    """
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            content_type = r.headers.get("Content-Type", "image/png")
            encoded = base64.b64encode(r.content).decode('utf-8')
            return f"data:{content_type};base64,{encoded}"
    except Exception as e:
        print(f"警告: 无法下载图片 {url}: {e}")
    return None

def load_local_image_as_base64(filename):
    """
    加载本地图片并转换为 base64 data URI
    """
    try:
        path = os.path.join(SCRIPT_DIR, 'assets', filename)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"警告: 无法加载本地图片 {filename}: {e}")
    return None

def to_full_width(text):
    """
    将半角英文字母、数字和符号转换为全角字符，以符合 maimai 游戏内显示的字体排版
    """
    if not text:
        return ""
    res = []
    for c in str(text):
        code = ord(c)
        if code == 32:  # 半角空格 -> 全角空格
            res.append(chr(12288))
        elif 33 <= code <= 126:  # 半角英数和符号 -> 全角
            res.append(chr(code + 65248))
        else:
            res.append(c)
    return "".join(res)

def get_player_data_lxns(token=None, qq=None, friend_code=None, dev_token=None):
    """
    从落雪 API 获取玩家信息和 B50 数据
    """
    headers = {}
    player_url = ""
    scores_url = ""
    
    if token:
        headers = {"X-User-Token": token}
        player_url = "https://maimai.lxns.net/api/v0/user/maimai/player"
        scores_url = "https://maimai.lxns.net/api/v0/user/maimai/player/scores"
    elif dev_token:
        headers = {"Authorization": dev_token}
        if qq:
            player_url = f"https://maimai.lxns.net/api/v0/maimai/player/qq/{qq}"
        elif friend_code:
            player_url = f"https://maimai.lxns.net/api/v0/maimai/player/{friend_code}"
        else:
            raise ValueError("使用开发者 Token 必须提供 qq 或 friend_code")
    else:
        raise ValueError("必须提供个人 Token (token) 或 开发者 Token (dev_token)")

    # 1. 获取玩家基础资料
    print(f"正在从落雪 API 获取玩家资料: {player_url}")
    r = requests.get(player_url, headers=headers, timeout=10)
    if r.status_code != 200:
        raise Exception(f"获取玩家信息失败: HTTP {r.status_code}, {r.text}")
    
    res = r.json()
    if not res.get("success"):
        raise Exception(f"获取玩家信息失败: {res.get('message')}")
    
    player_data = res.get("data", {})
    
    # 2. 获取 B50 成绩总和 (旧曲 B35 + 新曲 B15)
    b35 = 0
    b15 = 0
    fc = friend_code or player_data.get("friend_code")
    
    try:
        if token:
            print(f"正在获取所有成绩列表以计算 B50: {scores_url}")
            r_scores = requests.get(scores_url, headers=headers, timeout=10)
            if r_scores.status_code == 200:
                res_scores = r_scores.json()
                if res_scores.get("success"):
                    scores = res_scores.get("data", [])
                    standard_scores = [s for s in scores if s.get("type") == "standard"]
                    dx_scores = [s for s in scores if s.get("type") == "dx"]
                    
                    # 按成绩定数 rating 降序排列 (向下取整)
                    standard_scores.sort(key=lambda x: int(float(x.get("dx_rating", 0))), reverse=True)
                    dx_scores.sort(key=lambda x: int(float(x.get("dx_rating", 0))), reverse=True)
                    
                    # 取旧曲前 35 和新曲前 15
                    b35 = sum(int(float(s.get("dx_rating", 0))) for s in standard_scores[:35])
                    b15 = sum(int(float(s.get("dx_rating", 0))) for s in dx_scores[:15])
        elif dev_token and fc:
            bests_url = f"https://maimai.lxns.net/api/v0/maimai/player/{fc}/bests"
            print(f"正在获取 B50 详情: {bests_url}")
            r_bests = requests.get(bests_url, headers=headers, timeout=10)
            if r_bests.status_code == 200:
                res_bests = r_bests.json()
                if res_bests.get("success"):
                    bests_data = res_bests.get("data", {})
                    b35 = bests_data.get("standard_total", 0)
                    b15 = bests_data.get("dx_total", 0)
    except Exception as e:
        print(f"警告: 无法获取或计算 B50 详情: {e}")
        
    return player_data, b35, b15

def get_dan_name(course_rank):
    """获取段位名称"""
    dan_names = [
        "初学者", "一段", "二段", "三段", "四段", "五段",
        "六段", "七段", "八段", "九段", "十段",
        "真初段", "真二段", "真三段", "真四段", "真五段",
        "真六段", "真七段", "真八段", "真九段", "真十段",
        "真皆传", "里皆传"
    ]
    if 0 <= course_rank < len(dan_names):
        return dan_names[course_rank]
    return "未知"

def get_rating_star_file(rating):
    """根据 Rating 计算对应的星级绶带素材文件名"""
    if rating < 1000:
        return None
        
    # 根据游戏规则判定各段位的基础值和区间宽度
    if rating < 2000: # 蓝
        base, span = 1000, 1000
    elif rating < 4000: # 绿
        base, span = 2000, 2000
    elif rating < 7000: # 橙
        base, span = 4000, 3000
    elif rating < 10000: # 红
        base, span = 7000, 3000
    elif rating < 12000: # 紫
        base, span = 10000, 2000
    elif rating < 13000: # 铜
        base, span = 12000, 1000
    elif rating < 14000: # 银
        base, span = 13000, 1000
    elif rating < 15000: # 金
        base, span = 14000, 1000
    else: # 彩
        base, span = 15000, 1000
        
    offset = rating - base
    star_index = int((offset / span) * 4) + 1
    star_index = max(1, min(4, star_index)) # 限制在 1 到 4 星之间
    
    return f"UI_CMN_DXRating_Star_{star_index:02d}.png"

def generate_svg_card(player_data, b35=0, b15=0):
    """
    生成 SVG 格式的玩家卡片 (类似于 maimai 上屏展示)
    """
    name = player_data.get('name', '未知')
    rating = player_data.get('rating', 0)
    class_rank = player_data.get('class_rank', 0)
    course_rank = player_data.get('course_rank', 0)
    
    icon_id = player_data.get('icon', {}).get('id', 1) if player_data.get('icon') else 1
    plate_id = player_data.get('name_plate', {}).get('id', 1) if player_data.get('name_plate') else 1
    frame_id = player_data.get('frame', {}).get('id', 1) if player_data.get('frame') else 1
    
    # 异步下载相关游戏资源并转为 base64
    icon_base64 = fetch_image_as_base64(f"https://assets2.lxns.net/maimai/icon/{icon_id}.png")
    plate_base64 = fetch_image_as_base64(f"https://assets2.lxns.net/maimai/plate/{plate_id}.png")
    frame_base64 = fetch_image_as_base64(f"https://assets2.lxns.net/maimai/frame/{frame_id}.png")
    
    # 获取本地 Rating 资源
    if rating < 1000:
        base_file = "UI_CMN_DXRating_01.png" # 白
    elif rating < 2000:
        base_file = "UI_CMN_DXRating_02.png" # 蓝
    elif rating < 4000:
        base_file = "UI_CMN_DXRating_03.png" # 绿
    elif rating < 7000:
        base_file = "UI_CMN_DXRating_04.png" # 橙
    elif rating < 10000:
        base_file = "UI_CMN_DXRating_05.png" # 红
    elif rating < 12000:
        base_file = "UI_CMN_DXRating_06.png" # 紫
    elif rating < 13000:
        base_file = "UI_CMN_DXRating_07.png" # 铜
    elif rating < 14000:
        base_file = "UI_CMN_DXRating_08.png" # 银
    elif rating < 15000:
        base_file = "UI_CMN_DXRating_10.png" # 金 (10.png 带有精美格纹，匹配 14000+)
    else:
        base_file = "UI_CMN_DXRating_11.png" # 彩 (11.png 带有彩虹底色，匹配 15000+)
        
    rating_base_base64 = load_local_image_as_base64(base_file)
    num_spritesheet_base64 = load_local_image_as_base64("UI_NUM_Drating.png")
    
    # 获取本地星级绶带资源
    star_file = get_rating_star_file(rating)
    rating_star_base64 = load_local_image_as_base64(star_file) if star_file else None
    
    # 获取本地段位/等级徽章资源
    class_file = f"UI_CMN_Class_S_{class_rank:02d}.png"
    class_badge_base64 = load_local_image_as_base64(class_file)
    
    dan_file = f"UI_CMN_MatchLevel_{course_rank + 1:02d}.png"
    dan_badge_base64 = load_local_image_as_base64(dan_file)
    
    # 容错处理：如果下载失败则渲染默认形状
    if not frame_base64:
        frame_element = '<rect width="1080" height="452" fill="url(#bg-gradient)" rx="15"/>'
    else:
        frame_element = f'<image href="{frame_base64}" x="0" y="0" width="1080" height="452" preserveAspectRatio="xMidYMin slice" clip-path="url(#rounded-clip)"/>'
        
    if not plate_base64:
        plate_element = f'<rect x="{PLATE_X}" y="{PLATE_Y}" width="{PLATE_W}" height="{PLATE_H}" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="1.5"/>'
    else:
        plate_element = f'<image href="{plate_base64}" x="{PLATE_X}" y="{PLATE_Y}" width="{PLATE_W}" height="{PLATE_H}" />'
        
    if not icon_base64:
        icon_element = f'<rect x="{AVATAR_X}" y="{AVATAR_Y}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" rx="{AVATAR_RX}" fill="#4a4a5a" /><text x="{AVATAR_X + AVATAR_SIZE//2}" y="{AVATAR_Y + AVATAR_SIZE//2 + 5}" font-family="Arial" font-size="16" fill="#fff" text-anchor="middle">Icon</text>'
    else:
        icon_element = f'<image href="{icon_base64}" x="{AVATAR_X}" y="{AVATAR_Y}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" clip-path="url(#avatar-clip)" />'

    # 绘制 Rating 框 and 数字
    if not rating_base_base64:
        rating_base_element = f'<rect x="{RATING_X}" y="{RATING_Y}" width="{RATING_W}" height="{RATING_H}" rx="10" fill="#f5b000" />'
    else:
        rating_base_element = f'<image href="{rating_base_base64}" x="{RATING_X}" y="{RATING_Y}" width="{RATING_W}" height="{RATING_H}" />'

    digits_elements = ""
    if num_spritesheet_base64:
        rating_str = f"{rating:05d}"
        digits_svg = []
        for i, char in enumerate(rating_str):
            try:
                val = int(char)
            except ValueError:
                val = 0
            col = val % 4
            row = val // 4
            sx = col * 30
            sy = row * 34
            dx = DIGITS_X + i * DIGITS_SPACING
            dy = DIGITS_Y
            digits_svg.append(f'''
  <svg x="{dx}" y="{dy}" width="15" height="17" viewBox="{sx} {sy} 30 34">
    <image href="{num_spritesheet_base64}" x="0" y="0" width="120" height="136" />
  </svg>''')
        digits_elements = "\n".join(digits_svg)
    else:
        digits_elements = f'<text x="{RATING_X + RATING_W//2}" y="{RATING_Y + RATING_H//2 + 6}" font-family="monospace, Arial" font-size="20" font-weight="bold" fill="#ffffff" text-anchor="middle">{rating}</text>'

    # 绘制 Rating 星级绶带
    rating_star_element = ""
    if rating_star_base64:
        rating_star_element = f'<image href="{rating_star_base64}" x="{STAR_X}" y="{STAR_Y}" width="25" height="42" />'

    # 绘制 Class 徽章 (如 B5 绿牌)
    class_badge_element = ""
    if class_badge_base64:
        class_badge_element = f'<image href="{class_badge_base64}" x="{CLASS_X}" y="{CLASS_Y}" width="75" height="45" />'

    # 绘制 Dan 段位称号图章 (如 红色 "初心者" 图章)
    dan_element = ""
    if dan_badge_base64:
        dan_element = f'<image href="{dan_badge_base64}" x="{DAN_X}" y="{DAN_Y}" width="78" height="36" />'

    # 计算旧曲与新曲的进度条文本
    if b35 > 0 or b15 > 0:
        progress_text = f"旧曲: {b35} + 新曲: {b15}"
    else:
        progress_text = f"Rating: {rating}"

    # 玩家自定义称号 (Trophy) 渲染 - 绘制在姓名框顶部，并动态调整玩家昵称的位置
    trophy_name = player_data.get('trophy', {}).get('name', '') if player_data.get('trophy') else ''
    
    # 将用户名字体转为全角字符
    full_width_name = to_full_width(name)
    name_esc = escape_xml(full_width_name)
    
    # 字体族包含 A-OTF ShinGo Pro 及其常见命名形式以适配各种系统环境
    shingo_font = "A-OTF ShinGo Pro, ShinGoPro, 'A-OTF ShinGo Pro R', 'ShinGo Pro', 'A-OTF ShinGo', 'Hiragino Kaku Gothic ProN', 'MS Gothic', 'Microsoft YaHei', sans-serif"
    name_attrs = f'font-family="{shingo_font}" font-weight="bold" fill="#111111"'
    
    color_map = {
        'rainbow': 'rainbow',
        'gold': 'gold',
        'silver': 'silver',
        'bronze': 'bronze',
        'normal': 'normal',
        'white': 'normal'
    }
    color_val = str(player_data.get('trophy', {}).get('color', 'Normal')).lower()
    color_id = color_map.get(color_val, 'normal')

    if trophy_name:
        trophy_esc = escape_xml(trophy_name)
        # 计算称号背景板的尺寸与位置 (根据 TROPHY_SIZE 动态缩放)
        w_sum = 0
        for char in trophy_name:
            if ord(char) < 128:
                w_sum += TROPHY_SIZE * 0.55
            else:
                w_sum += TROPHY_SIZE * 1.0
        trophy_width = w_sum + (TROPHY_SIZE * 1.33)
        trophy_height = TROPHY_SIZE * 1.5
        trophy_rx = trophy_height / 2
        trophy_rect_x = TROPHY_X - (TROPHY_SIZE * 0.666)
        trophy_rect_y = TROPHY_Y - (TROPHY_SIZE * 1.166)
        
        # 称号背景板和文本
        trophy_element = f'''
  <rect x="{trophy_rect_x}" y="{trophy_rect_y}" width="{trophy_width}" height="{trophy_height}" rx="{trophy_rx}" fill="url(#trophy-{color_id})" stroke="rgba(255,255,255,0.6)" stroke-width="1" />
  <text x="{TROPHY_X}" y="{TROPHY_Y}" font-family="{shingo_font}" font-size="{TROPHY_SIZE}" font-weight="bold" fill="#333333">{trophy_esc}</text>'''
        name_element = f'''
  <rect x="{NAME_BG_X}" y="{NAME_BG_Y}" width="{NAME_BG_W}" height="{NAME_BG_H}" rx="{NAME_BG_RX}" fill="#ffffff" />
  <text x="{NAME_X}" y="{NAME_Y}" font-size="{NAME_SIZE}" {name_attrs}>{name_esc}</text>'''
    else:
        trophy_element = ""
        name_element = f'''
  <rect x="{NAME_BG_X}" y="{NAME_BG_Y}" width="{NAME_BG_W}" height="{NAME_BG_H}" rx="{NAME_BG_RX}" fill="#ffffff" />
  <text x="{NAME_X}" y="{NAME_Y_NOTROPHY}" font-size="{NAME_SIZE}" {name_attrs}>{name_esc}</text>'''

    # 防止玩家名字过长溢出姓名框
    if len(name) > 10:
        name_element = name_element.replace(name_attrs, name_attrs + ' textLength="240" lengthAdjust="spacingAndGlyphs"')

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1080" height="452" viewBox="0 0 1080 452">
  <defs>
    <pattern id="trophy-rainbow" width="36" height="36" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect x="0" width="6" height="36" fill="#ff5e97" />
      <rect x="6" width="6" height="36" fill="#ff8e53" />
      <rect x="12" width="6" height="36" fill="#fffd75" />
      <rect x="18" width="6" height="36" fill="#50ff8e" />
      <rect x="24" width="6" height="36" fill="#50b3ff" />
      <rect x="30" width="6" height="36" fill="#b350ff" />
    </pattern>
    <linearGradient id="trophy-gold" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFE57F"/>
      <stop offset="50%" style="stop-color:#FFD54F"/>
      <stop offset="100%" style="stop-color:#FFC107"/>
    </linearGradient>
    <linearGradient id="trophy-silver" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#F5F5F5"/>
      <stop offset="100%" style="stop-color:#BDBDBD"/>
    </linearGradient>
    <linearGradient id="trophy-bronze" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#D7CCC8"/>
      <stop offset="100%" style="stop-color:#8D6E63"/>
    </linearGradient>
    <linearGradient id="trophy-normal" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFFFFF"/>
      <stop offset="100%" style="stop-color:#ECEFF1"/>
    </linearGradient>
    <linearGradient id="bar-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#ff7e5f"/>
      <stop offset="50%" style="stop-color:#feb47b"/>
      <stop offset="100%" style="stop-color:#00c6ff"/>
    </linearGradient>
    <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e"/>
      <stop offset="100%" style="stop-color:#16213e"/>
    </linearGradient>
    <clipPath id="rounded-clip">
      <rect width="1080" height="452" rx="15"/>
    </clipPath>
    <clipPath id="avatar-clip">
      <rect x="{AVATAR_X}" y="{AVATAR_Y}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" rx="{AVATAR_RX}" />
    </clipPath>
  </defs>
  
  <!-- 黑色底框 -->
  <rect width="1080" height="452" fill="#121214" rx="15"/>
  
  <!-- 游戏背景板 Frame -->
  {frame_element}
  
  <!-- 姓名框 Plate -->
  {plate_element}
  
  <!-- 玩家昵称与自定义称号 -->
  {trophy_element}
  {name_element}
  
  <!-- 段位称号图章 -->
  {dan_element}
  
  <!-- 头像 Icon (带圆角的方形) -->
  {icon_element}
  
  <!-- 评分面板 RATING -->
  {rating_base_element}
  {digits_elements}
  {rating_star_element}
  
  <!-- Class 徽章 (如 B5 绿牌) -->
  {class_badge_element}
  
  <!-- B35 + B15 进度条 -->
  <rect x="{PROG_X}" y="{PROG_Y}" width="{PROG_W}" height="32" rx="16" fill="#1e1e24" stroke="#4a4a5a" stroke-width="1.5" />
  <rect x="{PROG_X + 2}" y="{PROG_Y + 2}" width="{PROG_W - 4}" height="28" rx="14" fill="url(#bar-gradient)" />
  <text x="{PROG_X + PROG_W // 2}" y="{PROG_Y + PROG_TEXT_OFFSET}" font-family="Arial, sans-serif" font-size="15" font-weight="bold" fill="#000000" text-anchor="middle">{progress_text}</text>
  
  <!-- 更新时间戳 -->
  <text x="1060" y="435" font-family="Arial, sans-serif" font-size="11" fill="#ffffff" opacity="0.8" text-anchor="end">
    更新于 {timestamp} · Lxns API
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
    
    parser = argparse.ArgumentParser(description='生成 maimai DX 玩家信息卡片 (Lxns API)')
    parser.add_argument('--token', help='落雪个人 API 密钥 (X-User-Token)')
    parser.add_argument('--dev-token', help='落雪开发者 API 密钥 (Authorization)')
    parser.add_argument('--qq', help='绑定的 QQ 号')
    parser.add_argument('--friend-code', help='好友码')
    parser.add_argument('--output', '-o', default='maimai-card.svg', help='输出文件路径')
    
    args = parser.parse_args()
    
    # 优先读取环境变量，其次读取命令行参数
    token = args.token or os.environ.get("LXNS_TOKEN")
    dev_token = args.dev_token or os.environ.get("LXNS_DEV_TOKEN") if hasattr(args, 'dev_token') else os.environ.get("LXNS_DEV_TOKEN")
    # 兼容 argparse 对带有减号参数的解析
    if not dev_token:
        # 手动解析命令行中可能的 --dev-token
        for idx, arg in enumerate(sys.argv):
            if arg == '--dev-token' and idx + 1 < len(sys.argv):
                dev_token = sys.argv[idx + 1]
                
    qq = args.qq or os.environ.get("MAIMAI_QQ")
    friend_code = args.friend_code or os.environ.get("MAIMAI_FRIEND_CODE")
    
    if not token and not dev_token:
        print("错误: 必须提供个人 Token (通过环境变量 LXNS_TOKEN 或参数 --token) "
              "或 开发者 Token (通过环境变量 LXNS_DEV_TOKEN 或参数 --dev-token)")
        sys.exit(1)
        
    if dev_token and not qq and not friend_code:
        print("错误: 使用开发者 Token 时，必须提供 QQ 号 (--qq) 或 好友码 (--friend-code)")
        sys.exit(1)
    
    try:
        print(f"正在获取玩家数据...")
        player_data, b35, b15 = get_player_data_lxns(
            token=token,
            qq=qq,
            friend_code=friend_code,
            dev_token=dev_token
        )
        
        print(f"玩家: {player_data.get('name', '未知')}")
        print(f"Rating: {player_data.get('rating', 0)}")
        print(f"旧曲 B35: {b35} | 新曲 B15: {b15}")
        
        print(f"正在生成卡片...")
        svg = generate_svg_card(player_data, b35=b35, b15=b15)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(svg)
        
        print(f"✅ 卡片已成功生成: {args.output}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
