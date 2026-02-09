# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import os
import re
import time

# 模拟 Windows Chrome 122，保持和你本地一致
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
        
        # --- 1. 注入 Cookie (关键修改：domain 设为 .glados.cloud) ---
        cookies_list = []
        for part in cookie_string.split(';'):
            if '=' in part:
                name, value = part.strip().split('=', 1)
                cookies_list.append({
                    'name': name,
                    'value': value,
                    'domain': '.glados.cloud',  # 这里必须是 cloud
                    'path': '/'
                })
        context.add_cookies(cookies_list)
        
        page = context.new_page()

        try:
            target_url = "https://glados.cloud/console/checkin"
            print(f">>> [Playwright] 正在访问: {target_url}")
            
            page.goto(target_url)
            # 等待页面加载，React 应用需要时间渲染
            page.wait_for_timeout(8000)

            # 截图保存初始状态
            page.screenshot(path="evidence.png")

            # 检查是否掉登录
            if "login" in page.url:
                return "【失败】Cookie 无效或域名不匹配，已跳转至登录页！请重新在 .cloud 域名下抓取 Cookie。"

            # --- 2. 寻找并点击按钮 ---
            print(">>> [Playwright] 寻找签到按钮...")
            # 尝试多种定位方式
            checkin_btn = page.locator("button").filter(has_text="签到")
            if checkin_btn.count() == 0:
                checkin_btn = page.locator("button").filter(has_text="Checkin")

            msg = "未执行操作"
            if checkin_btn.count() > 0 and checkin_btn.is_visible():
                print(f">>> 找到按钮，点击中...")
                checkin_btn.first.click(force=True)
                msg = "已点击按钮"
                
                # 点击后等待 10 秒，让数据提交
                print(">>> 点击完成，等待 10 秒...")
                page.wait_for_timeout(10000)
            else:
                msg = "未找到按钮 (可能今日已签过)"

            # --- 3. 刷新页面验证结果 ---
            print(">>> 正在刷新页面读取最新历史...")
            page.reload()
            page.wait_for_timeout(5000)
            # 再次截图，方便看结果
            page.screenshot(path="evidence.png")

            # --- 4. 读取 History ---
            history_info = "未获取到记录"
            try:
                # 等待表格出现
                page.wait_for_selector("table tbody tr", timeout=5000)
                first_row = page.locator("table tbody tr").first
                if first_row.is_visible():
                    history_text = first_row.inner_text()
                    history_info = history_text.replace("\n", " | ")
                else:
                    history_info = "表格为空"
            except:
                history_info = "表格读取失败 (可能未加载)"

            # --- 5. 读取剩余天数 ---
            try:
                days_text = page.locator(".u-h1").first.inner_text()
                days_num = re.findall(r"\d+\.?\d*", days_text)
                days_str = days_num[0] if days_num else days_text
            except:
                days_str = "?"

            return (f"------------------------------\n"
                    f"【操作状态】: {msg}\n"
                    f"【最新历史】: {history_info}\n"
                    f"【当前天数】: {days_str}\n"
                    f"------------------------------")

        except Exception as e:
            return f"【运行报错】: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    cookie_env = os.environ.get("GLADOS_COOKIE")
    if not cookie_env:
        print("❌ 未检测到 Cookie，请检查 GitHub Secrets！")
        exit(1)
        
    for idx, cookie in enumerate(cookie_env.split('&')):
        print(f"正在执行第 {idx+1} 个账号...")
        print(glados_checkin(cookie))
