# -*- coding: utf-8 -*-
import requests
import json
import os
import time

# -------------------------------------------------------------------------------------------
# 核心逻辑：模拟浏览器行为，绕过服务端检测
# -------------------------------------------------------------------------------------------

def glados_checkin(cookie):
    # 1. 准备 URL
    checkin_url = "https://glados.rocks/api/user/checkin"
    status_url = "https://glados.rocks/api/user/status"
    
    # 2. 构造请求头 (这一步最关键，结合了你发的源码分析，我们必须模拟完整浏览器头)
    headers = {
        "cookie": cookie,
        "referer": "https://glados.rocks/console/checkin",  # 告诉服务器：我是从签到页过来的
        "origin": "https://glados.rocks",                   # 告诉服务器：请求来源是官网
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "content-type": "application/json;charset=UTF-8",
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8"
    }

    # 3. 构造负载数据
    payload = {
        "token": "glados.network"
    }

    try:
        # --- 动作 A: 执行签到 ---
        print(">>> 开始尝试签到...")
        response = requests.post(checkin_url, headers=headers, data=json.dumps(payload))
        
        # 解析返回结果
        if response.status_code != 200:
            return f"【网络错误】: HTTP {response.status_code}"
            
        res_json = response.json()
        message = res_json.get("message", "未知响应")
        
        # --- 动作 B: 查询最新天数 (用于验证是否真的成功) ---
        print(">>> 正在验证签到结果...")
        time.sleep(1) # 稍微歇一下，模拟人类操作
        status_resp = requests.get(status_url, headers=headers)
        if status_resp.status_code == 200:
            days = status_resp.json().get("data", {}).get("leftDays")
            days_str = f"{int(float(days))}" if days else "未知"
        else:
            days_str = "查询失败"

        # 组合最终报告
        return f"------------------------------\n【签到状态】: {message}\n【剩余天数】: {days_str} 天\n------------------------------"

    except Exception as e:
        return f"【脚本异常】: {str(e)}"

# -------------------------------------------------------------------------------------------
# 主程序入口
# -------------------------------------------------------------------------------------------
if __name__ == "__main__":
    # 从 GitHub Secrets 获取 Cookie
    cookie_string = os.environ.get("GLADOS_COOKIE")
    
    if not cookie_string:
        print("❌ 错误：未检测到 GLADOS_COOKIE，请在 GitHub Secrets 中配置。")
        exit(1)
    
    # 支持多账号（以 & 分隔）
    cookies = cookie_string.split("&")
    
    for idx, cookie in enumerate(cookies):
        print(f"\n正在处理第 {idx+1} 个账号...")
        result = glados_checkin(cookie)
        print(result)
