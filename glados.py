# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import os
import time

# 使用补全后的标准 Windows Chrome 指纹，确保服务器认为你是真人
REAL_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def glados_checkin(cookie_string):
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent=REAL_USER_AGENT,
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 注入你提供的 Cookie
        cookies_list = []
        for part in cookie_string.split(';'):
            if '=' in part:
                name, value = part.strip().split('=', 1)
                cookies_list.append({
                    'name': name,
                    'value': value,
                    'domain': '.glados.rocks',
                    'path': '/'
                })
        context.add_cookies(cookies_list)
        
        page = context.new_page()

        try:
            print(f">>> [Playwright] 正在使用 Cookie 访问...")
            
            # 1. 访问签到页
            page.goto("https://glados.rocks/console/checkin")
            page.wait_for_timeout(5000) # 等待盾

            # 2. 检查 Cookie 是否有效
            if "login" in page.url:
                return "【失败】Cookie 无效，已跳转至登录页！"

            print(">>> [Playwright] 寻找签到按钮...")
            
            # 尝试定位按钮
            checkin_btn = page.locator("button").filter(has_text="签到")
            if checkin_btn.count() == 0:
                checkin_btn = page.locator("button").filter(has_text="Checkin")

            # 3. 核心操作：点击
            final_msg = "未执行操作"
            if checkin_btn.count() > 0 and checkin_btn.is_visible():
                btn_text_before = checkin_btn.first.inner_text()
                print(f">>> 找到按钮，当前文字: {btn_text_before}")
                
                # 点击！
                checkin_btn.first.click(force=True)
                page.wait_for_timeout(3000)
                
                # 再次获取文字，确认变没变
                btn_text_after = checkin_btn.first.inner_text()
                final_msg = f"已点击，按钮文字从[{btn_text_before}]变为[{btn_text_after}]"
            else:
                # 找不到按钮，可能是已经签到了
                final_msg = "未找到签到按钮（可能今日已签到）"

            # 4. 获取天数 (从界面读取)
            try:
                # 尝试从界面读取天数，比调接口稳
                days = page.locator(".u-h1").first.inner_text()
                # 去除可能的非数字字符
                import re
                days_num = re.findall(r"\d+\.?\d*", days)
                days_str = days_num[0] if days_num else days
            except:
                # 兜底：调接口查
                status_js = """async () => {
                    const res = await fetch("https://glados.rocks/api/user/status");
                    return res.json();
                }"""
                res = page.evaluate(status_js)
                days_str = res.get("data", {}).get("leftDays", "获取失败")

            return f"------------------------------\n【执行结果】: {final_msg}\n【当前剩余天数】: {str(int(float(days_str))) if str(days_str).replace('.','',1).isdigit() else days_str} 天\n------------------------------"

        except Exception as e:
            return f"【运行报错】: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    cookie_env = os.environ.get("GLADOS_COOKIE")
    if not cookie_env:
        print("❌ 请先更新 GitHub Secrets！")
        exit(1)
        
    for idx, cookie in enumerate(cookie_env.split('&')):
        print(f"正在执行第 {idx+1} 个账号...")
        print(glados_checkin(cookie))
