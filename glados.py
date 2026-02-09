import requests
import json
import os

# 1. 从环境变量获取 Cookie
# 这里的 environ.get 会去读取你在 GitHub Secrets 里填的 GLADOS_COOKIE
cookies = os.environ.get("GLADOS_COOKIE", []).split("&")

# 2. 如果没填 Cookie 就报错退出
if not cookies or cookies[0] == "":
    print("【Error】请在 Github Secrets 中设置 GLADOS_COOKIE")
    exit(1)

def checkin(cookie):
    # 这是目前最新的 API 地址
    checkin_url = "https://glados.rocks/api/user/checkin"
    status_url = "https://glados.rocks/api/user/status"
    
    # 【关键修改】伪装成浏览器，骗过服务器的检测
    headers = {
        "cookie": cookie,
        "referer": "https://glados.rocks/console/checkin",
        "origin": "https://glados.rocks",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "content-type": "application/json;charset=UTF-8"
    }

    payload = {
        "token": "glados.network"
    }

    try:
        # 3. 发送签到请求
        checkin_res = requests.post(checkin_url, headers=headers, data=json.dumps(payload)).json()
        
        # 4. 获取剩余天数用于展示
        status_res = requests.get(status_url, headers=headers).json()
        days = status_res.get("data", {}).get("leftDays")
        
        return f"【签到结果】: {checkin_res.get('message')} | 【剩余天数】: {int(float(days))} 天"
        
    except Exception as e:
        return f"【运行出错】: {e}"

# 主程序入口
if __name__ == "__main__":
    for cookie in cookies:
        print(checkin(cookie))
