# -*- coding: utf-8 -*-
import requests
import json
import os
import time

def glados_checkin(cookie):
    # 恢复使用 rocks 域名，通常这个API更稳定
    checkin_url = "https://glados.rocks/api/user/checkin"
    status_url = "https://glados.rocks/api/user/status"
    
    # 【超级伪装】模拟真实的 Linux Chrome 浏览器请求
    # 只有加上 sec-ch-ua 这些头，服务器才会认为你是真人
    headers = {
        'authority': 'glados.rocks',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.6',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': cookie,
        'origin': 'https://glados.rocks',
        'referer': 'https://glados.rocks/console/checkin',
        # 下面这几行是关键，模拟浏览器的“安全握手”特征
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    payload = {
        "token": "glados.network"
    }

    try:
        print(">>> [模拟真机] 正在尝试签到...")
        # 发送签到请求
        response = requests.post(checkin_url, headers=headers, data=json.dumps(payload))
        
        # 无论签到成功与否，都强制查询一次天数
        time.sleep(1)
        status_resp = requests.get(status_url, headers=headers)
        
        # 解析剩余天数
        if status_resp.status_code == 200:
            raw_days = status_resp.json().get("data", {}).get("leftDays")
            days_str = str(int(float(raw_days)))
        else:
            days_str = "查询失败"

        # 解析签到结果
        if response.status_code == 200:
            res_json = response.json()
            msg = res_json.get("message")
            code = res_json.get("code")
            
            # 这里的逻辑是：只要还能查到天数，哪怕签到报错，我们也认为脚本至少跑通了
            return (f"------------------------------\n"
                    f"【执行结果】: {msg} (Code: {code})\n"
                    f"【剩余天数】: {days_str} 天\n"
                    f"------------------------------")
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
