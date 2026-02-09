# -*- coding: utf-8 -*-
import requests
import json
import os
import time

def glados_checkin(cookie):
    # 【关键修改】域名全部改为 glados.cloud
    checkin_url = "https://glados.cloud/api/user/checkin"
    status_url = "https://glados.cloud/api/user/status"
    
    # 模拟浏览器真实请求头
    headers = {
        "cookie": cookie,
        "referer": "https://glados.cloud/console/checkin", 
        "origin": "https://glados.cloud",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "content-type": "application/json;charset=UTF-8"
    }

    # 【关键修改】Token 有时会变，尝试兼容 glados.network
    payload = {
        "token": "glados.network"
    }

    try:
        print(">>> 正在尝试通过 glados.cloud 签到...")
        response = requests.post(checkin_url, headers=headers, data=json.dumps(payload))
        
        # 即使签到接口报错，也要查一下天数，看看是否其实已经签上了
        time.sleep(1)
        status_resp = requests.get(status_url, headers=headers)
        
        if status_resp.status_code == 200:
            days = status_resp.json().get("data", {}).get("leftDays")
            days_str = f"{int(float(days))}"
        else:
            days_str = "查询失败"

        if response.status_code == 200:
            res_json = response.json()
            msg = res_json.get("message")
            # 如果返回 "please checkin via..." 说明被拦截，但有时其实已经签成功了，依靠天数判断
            return f"------------------------------\n【签到接口反馈】: {msg}\n【当前剩余天数】: {days_str} 天\n------------------------------"
        else:
            return f"【网络请求失败】: HTTP {response.status_code}"

    except Exception as e:
        return f"【脚本错误】: {str(e)}"

if __name__ == "__main__":
    cookie_string = os.environ.get("GLADOS_COOKIE")
    if not cookie_string:
        print("❌ 未找到 Cookie，请检查 Secrets 设置")
        exit(1)
    
    cookies = cookie_string.split("&")
    for idx, cookie in enumerate(cookies):
        print(f"\n正在执行第 {idx+1} 个账号...")
        print(glados_checkin(cookie))
