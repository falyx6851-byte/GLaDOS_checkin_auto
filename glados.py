# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import os
import time

def glados_checkin(cookie_string):
    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 1. 注入 Cookie
        cookies_list = []
        for part in cookie_string.split(';'):
            if '=' in part:
                name, value = part.strip().split('=', 1)
                cookies_list.append({
                    'name': name,
                    'value': value,
                    'domain': '.glados.rocks', # 这里用 rocks 兼容性更好，它会自动跳
                    'path': '/'
                })
        if cookies_list:
            context.add_cookies(cookies_list)
        
        page = context.new_page()

        try:
            print(">>> [Playwright] 正在打开页面...")
            # 访问签到页
            page.goto("https://glados.rocks/console/checkin")
            
            # 等待页面加载（有时候会有 Cloudflare 的盾，多等几秒）
            page.wait_for_timeout(5000)
            
            # 检查是否需要登录（如果 Cookie 失效，页面会跳转到登录页）
            if "login" in page.url:
                return "【失败】Cookie 已失效，请重新获取！"

            print(">>> [Playwright] 寻找签到按钮...")
            
            # 2. 核心大招：寻找页面上的“签到”按钮并点击
            # 我们尝试找包含“签到”或者“Checkin”字样的按钮
            checkin_btn = page.locator("button").filter(has_text="签到")
            
            if checkin_btn.count() == 0:
                checkin_btn = page.locator("button").filter(has_text="Checkin")
            
            # 如果找不到按钮，可能已经签到过了，或者页面结构变了
            if checkin_btn.count() > 0 and checkin_btn.is_visible():
                print(">>> 点击签到按钮！")
                checkin_btn.first.click()
                # 点完之后等一会，让它弹出结果
                page.wait_for_timeout(3000)
                msg = "【操作完成】已模拟点击签到"
            else:
                # 也有可能今天已经签过了，按钮变成了“已签到”
                msg = "【跳过】未找到签到按钮（可能已签到）"

            # 3. 最后查询一下天数，确认战果
            try:
                # 提取页面显示的剩余天数（直接从界面上读，不发请求了）
                # 这里假设界面上有个元素显示天数，如果找不到就兜底查接口
                status_js = """
                    async () => {
                        const response = await fetch("https://glados.rocks/api/user/status");
                        const data = await response.json();
                        return data;
                    }
                """
                status_res = page.evaluate(status_js)
                days = status_res.get("data", {}).get("leftDays", "?")
            except:
                days = "未知"

            return f"------------------------------\n{msg}\n【当前剩余天数】: {int(float(days)) if str(days).replace('.','',1).isdigit() else days} 天\n------------------------------"

        except Exception as e:
            # 截个图方便调试（虽然在 Actions 里看不到，但报错信息里可能会有提示）
            return f"【运行报错】: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    cookie_env = os.environ.get("GLADOS_COOKIE")
    if not cookie_env:
        print("❌ 错误：未配置 GLADOS_COOKIE")
        exit(1)
        
    for idx, cookie in enumerate(cookie_env.split('&')):
        print(f"正在执行第 {idx+1} 个账号...")
        print(glados_checkin(cookie))
