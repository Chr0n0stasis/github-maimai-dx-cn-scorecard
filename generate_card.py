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

def generate_svg_card(player_data, b35=0, b15=0):
    """
    生成 SVG 格式的玩家卡片 (类似于 maimai 上屏展示)
    """
    name = player_data.get('name', '未知')
    rating = player_data.get('rating', 0)
    
    icon_id = player_data.get('icon', {}).get('id', 1) if player_data.get('icon') else 1
    plate_id = player_data.get('name_plate', {}).get('id', 1) if player_data.get('name_plate') else 1
    frame_id = player_data.get('frame', {}).get('id', 1) if player_data.get('frame') else 1
    
    # 异步下载相关游戏资源并转为 base64
    icon_base64 = fetch_image_as_base64(f"https://assets2.lxns.net/maimai/icon/{icon_id}.png")
    plate_base64 = fetch_image_as_base64(f"https://assets2.lxns.net/maimai/plate/{plate_id}.png")
    frame_base64 = fetch_image_as_base64(f"https://assets2.lxns.net/maimai/frame/{frame_id}.png")
    
    # 获取本地 Rating 资源
    if rating < 1000:
        base_file = "UI_CMN_DXRating_01.png"
    elif rating < 2000:
        base_file = "UI_CMN_DXRating_03.png"
    elif rating < 4000:
        base_file = "UI_CMN_DXRating_04.png"
    elif rating < 7000:
        base_file = "UI_CMN_DXRating_05.png"
    elif rating < 10000:
        base_file = "UI_CMN_DXRating_06.png"
    elif rating < 12000:
        base_file = "UI_CMN_DXRating_07.png"
    elif rating < 13000:
        base_file = "UI_CMN_DXRating_08.png"
    elif rating < 14000:
        base_file = "UI_CMN_DXRating_09.png"
    elif rating < 15000:
        base_file = "UI_CMN_DXRating_11.png"
    else:
        base_file = "UI_CMN_DXRating_12.png"
        
    rating_base_base64 = load_local_image_as_base64(base_file)
    num_spritesheet_base64 = load_local_image_as_base64("UI_NUM_Drating.png")
    
    # 容错处理：如果下载失败则渲染默认形状
    if not frame_base64:
        frame_element = '<rect width="1080" height="160" fill="url(#bg-gradient)" rx="15"/>'
    else:
        frame_element = f'<image href="{frame_base64}" x="0" y="0" width="1080" height="452" preserveAspectRatio="xMidYMin slice" clip-path="url(#rounded-clip)"/>'
        
    if not plate_base64:
        plate_element = '<rect x="185" y="56" width="298" height="48" rx="6" fill="#ffffff" stroke="#e0e0e0" stroke-width="1.5"/>'
    else:
        plate_element = f'<image href="{plate_base64}" x="185" y="56" width="298" height="48" />'
        
    if not icon_base64:
        icon_element = '<circle cx="95" cy="80" r="55" fill="#4a4a5a" /><text x="95" y="85" font-family="Arial" font-size="16" fill="#fff" text-anchor="middle">Icon</text>'
    else:
        icon_element = f'<image href="{icon_base64}" x="40" y="25" width="110" height="110" clip-path="url(#avatar-clip)" />'

    # 绘制 Rating 框和数字
    if not rating_base_base64:
        rating_base_element = '<rect x="185" y="15" width="184" height="36" rx="6" fill="#f5b000" />'
    else:
        rating_base_element = f'<image href="{rating_base_base64}" x="185" y="15" width="184" height="36" />'

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
            dx = 272 + i * 15
            dy = 22
            digits_svg.append(f'''
  <svg x="{dx}" y="{dy}" width="11" height="12.5" viewBox="{sx} {sy} 30 34">
    <image href="{num_spritesheet_base64}" x="0" y="0" width="120" height="136" />
  </svg>''')
        digits_elements = "\n".join(digits_svg)
    else:
        digits_elements = f'<text x="277" y="38" font-family="monospace, Arial" font-size="16" font-weight="bold" fill="#ffffff">{rating}</text>'

    # 计算旧曲与新曲的进度条文本
    if b35 > 0 or b15 > 0:
        progress_text = f"旧曲: {b35} + 新曲: {b15}"
    else:
        progress_text = f"Rating: {rating}"

    # 称号 (Trophy) 渲染
    trophy_name = player_data.get('trophy', {}).get('name', '') if player_data.get('trophy') else ''
    trophy_element = ""
    if trophy_name:
        trophy_esc = escape_xml(trophy_name)
        trophy_element = f'''
  <!-- 称号气泡/贴纸 -->
  <rect x="380" y="66" width="85" height="28" rx="14" fill="#ffffff" stroke="#ff4d4f" stroke-width="1.5" />
  <text x="422.5" y="85" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#ff4d4f" text-anchor="middle">{trophy_esc}</text>
'''

    # 防止玩家名字过长溢出姓名框
    name_esc = escape_xml(name)
    name_attrs = 'font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#111111"'
    if len(name) > 10:
        name_attrs += ' textLength="160" lengthAdjust="spacingAndGlyphs"'

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1080" height="160" viewBox="0 0 1080 160">
  <defs>
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
      <rect width="1080" height="160" rx="15"/>
    </clipPath>
    <clipPath id="avatar-clip">
      <circle cx="95" cy="80" r="55" />
    </clipPath>
  </defs>
  
  <!-- 黑色底框 -->
  <rect width="1080" height="160" fill="#121214" rx="15"/>
  
  <!-- 游戏背景板 Frame -->
  {frame_element}
  
  <!-- 姓名框 Plate -->
  {plate_element}
  
  <!-- 玩家昵称 -->
  <text x="205" y="86" {name_attrs}>{name_esc}</text>
  
  {trophy_element}
  
  <!-- 头像 Icon (置于层级上方并带上圆形白边) -->
  {icon_element}
  <circle cx="95" cy="80" r="55" fill="none" stroke="#ffffff" stroke-width="4" />
  
  <!-- 评分面板 RATING -->
  {rating_base_element}
  {digits_elements}
  
  <!-- B35 + B15 进度条 -->
  <rect x="185" y="110" width="298" height="30" rx="15" fill="#1e1e24" stroke="#4a4a5a" stroke-width="1.5" />
  <rect x="187" y="112" width="294" height="26" rx="13" fill="url(#bar-gradient)" />
  <text x="334" y="130" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#000000" text-anchor="middle">{progress_text}</text>
  
  <!-- 更新时间戳 -->
  <text x="1060" y="145" font-family="Arial, sans-serif" font-size="11" fill="#ffffff" opacity="0.8" text-anchor="end">
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
