# -*- coding: utf-8 -*- 
from playwright.sync_api import sync_playwright
import os
import json
import time

def glados_checkin(cookie_string):
    with sync_playwright() as p:
        # 启动浏览器 (headless=True 无头模式)
        # args 参数是为了尽可能模拟真实环境，规避检测
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        # 创建上下文，并注入 User-Agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 注入 Cookie
        # Playwright 需要 domain, path 等字段
        cookies = []
        for item in cookie_string.split(';'):
            if '=' in item:
                k, v = item.strip().split('=', 1)
                cookies.append({
                    'name': k, 
                    'value': v, 
                    'domain': '.glados.rocks', 
                    'path': '/'
                })
        context.add_cookies(cookies)

        page = context.new_page()

        try:
            print(">>> [Playwright] 正在访问签到页...")
            # 1. 访问页面，触发 Cloudflare 验证
            page.goto("https://glados.rocks/console/checkin")
            # 等待 5 秒，让 CF 盾飞一会儿
            page.wait_for_timeout(5000)

            print(">>> [Playwright] 执行签到...")
            # 2. 也是通过 JS 执行 Fetch，这样最稳，因为它带上了当前页面的所有指纹
            checkin_js = """
                async () => {
                    const response = await fetch("https://glados.rocks/api/user/checkin", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({token: "glados.network"})
                    });
                    return response.json();
                }
            """
            result = page.evaluate(checkin_js)
            
            # 3. 获取剩余天数
            status_js = """
                async () => {
                    const response = await fetch("https://glados.rocks/api/user/status");
                    return response.json();
                }
            """
            status_res = page.evaluate(status_js)
            days = status_res.get("data", {}).get("leftDays", "?")

            return f"------------------------------\n【Playwright 结果】: {result.get('message')}\n【剩余天数】: {int(float(days))} 天\n------------------------------"

        except Exception as e:
            return f"【运行报错】: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    cookie_string = os.environ.get("GLADOS_COOKIE")
    if not cookie_string:
        print("❌ 未配置 COOKIE")
        exit(1)
        
    for idx, cookie in enumerate(cookie_string.split('&')):
        print(f"正在执行第 {idx+1} 个账号...")
        print(glados_checkin(cookie))
