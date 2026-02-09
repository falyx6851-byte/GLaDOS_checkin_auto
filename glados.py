# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import os
import re

# 你的 Windows Chrome 指纹
REAL_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def glados_checkin(cookie_string):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent=REAL_USER_AGENT,
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 注入 Cookie
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
            print(f">>> [Playwright] 正在访问...")
            page.goto("https://glados.rocks/console/checkin")
            # 等待页面 JS 加载完成
            page.wait_for_selector("body", timeout=15000)
            page.wait_for_timeout(5000)

            if "login" in page.url:
                return "【失败】Cookie 无效，已跳转至登录页！"

            # --- 1. 执行签到 ---
            print(">>> [Playwright] 寻找签到按钮...")
            checkin_btn = page.locator("button").filter(has_text="签到")
            if checkin_btn.count() == 0:
                checkin_btn = page.locator("button").filter(has_text="Checkin")

            msg = "未执行操作"
            if checkin_btn.count() > 0 and checkin_btn.is_visible():
                print(f">>> 找到按钮，点击中...")
                checkin_btn.first.click(force=True)
                msg = "已点击按钮"
                
                # 【优化点1】点击后，耐心等待 10 秒，让子弹飞一会儿
                print(">>> 等待 10 秒让数据同步...")
                page.wait_for_timeout(10000)
            else:
                msg = "未找到按钮 (可能今日已签过)"

            # --- 2. 刷新页面 (关键优化) ---
            print(">>> 正在刷新页面以获取最新历史...")
            page.reload()
            # 刷新后再次等待加载
            page.wait_for_timeout(5000)

            # --- 3. 核对 History 记录 ---
            print(">>> 读取最新 History 记录...")
            history_info = "未获取到记录"
            try:
                # 等待表格出现
                page.wait_for_selector("table tbody tr", timeout=10000)
                # 读取第一行
                first_row = page.locator("table tbody tr").first
                if first_row.is_visible():
                    history_text = first_row.inner_text()
                    history_info = history_text.replace("\n", " | ")
                else:
                    history_info = "表格为空"
            except Exception as h_err:
                history_info = f"表格读取未就绪: {str(h_err)}"

            # --- 4. 获取剩余天数 ---
            try:
                days_text = page.locator(".u-h1").first.inner_text()
                days_num = re.findall(r"\d+\.?\d*", days_text)
                days_str = days_num[0] if days_num else days_text
            except:
                days_str = "?"

            return (f"------------------------------\n"
                    f"【操作状态】: {msg}\n"
                    f"【刷新后最新历史】: {history_info}\n"
                    f"【当前天数】: {days_str}\n"
                    f"------------------------------")

        except Exception as e:
            return f"【运行报错】: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    cookie_env = os.environ.get("GLADOS_COOKIE")
    if not cookie_env:
        print("❌ 请检查 Secrets 配置")
        exit(1)
        
    for idx, cookie in enumerate(cookie_env.split('&')):
        print(f"正在执行第 {idx+1} 个账号...")
        print(glados_checkin(cookie))
