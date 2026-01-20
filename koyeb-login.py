from playwright.sync_api import sync_playwright
import os
import requests
import time

def send_telegram_message(message):
    bot_token = os.environ.get('TEL_TOK')
    chat_id = os.environ.get('TEL_ID')
    if not bot_token or not chat_id: return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def login_koyeb(email, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 模拟真实浏览器特征
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # 定义截图文件名（处理特殊字符）
        safe_email = email.replace('@', '_').replace('.', '_')
        screenshot_path = f"error_{safe_email}.png"

        try:
            # 1. 访问登录页
            page.goto("https://app.koyeb.com/auth/signin", wait_until="networkidle")
            
            # 2. 填写邮箱
            page.wait_for_selector('input[name="email"]', timeout=10000)
            page.fill('input[name="email"]', email)
            page.click('button[type="submit"]')
            print(f"[{email}] 已输入邮箱，正在跳转...")

            # 3. 填写密码
            page.wait_for_selector('input[name="password"]', timeout=10000)
            page.fill('input[name="password"]', password)
            
            # 点击登录，并等待页面发生显著变化
            page.click('button[type="submit"]')
            print(f"[{email}] 已输入密码，提交登录...")

            # 4. 验证成功或处理弹窗
            # 策略：等待直到 URL 包含 dashboard，或者出现特定的“跳过”按钮
            try:
                # 尝试等待进入控制台的关键特征，缩短超时到 15s
                # 如果是新账号，可能会卡在验证页面，这时候截图最有用
                page.wait_for_url("**/dashboard**", timeout=15000)
                return f"账号 {email} 登录成功!"
            except:
                # 如果没到 dashboard，检查是否有“Skip”按钮
                skip = page.query_selector('text="Skip for now", text="Maybe later"')
                if skip:
                    skip.click()
                    page.wait_for_timeout(2000)
                    return f"账号 {email} 登录成功 (已跳过弹窗)!"
                
                # 如果还是没成功，抛出异常进入截图流程
                raise Exception("未检测到登录成功的控制台页面或跳过按钮")

        except Exception as e:
            # 【核心功能】保存出错瞬间的截图
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"[{email}] 调试截图已保存至: {screenshot_path}")
            except Exception as screenshot_err:
                print(f"[{email}] 截图保存失败: {screenshot_err}")
                
            return f"账号 {email} 登录出错: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    # 原有逻辑保持不变...
    accounts = os.environ.get('KOY_ACC', '').split()
    login_statuses = []
    for account in accounts:
        if ':' not in account: continue
        email, password = account.split(':')
        status = login_koyeb(email, password)
        login_statuses.append(status)
        print(status)
    if login_statuses:
        send_telegram_message("Koyeb登录报告:\n\n" + "\n".join(login_statuses))
