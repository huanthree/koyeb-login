from playwright.sync_api import sync_playwright
import os
import requests
import time

def send_telegram_message(message):
    bot_token = os.environ.get('TEL_TOK')
    chat_id = os.environ.get('TEL_ID')
    if not bot_token or not chat_id:
        print("Telegram 配置缺失，跳过发送")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"发送消息失败: {e}")

def login_koyeb(email, password):
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = context.new_page()

        try:
            # 1. 访问登录页面
            page.goto("https://app.koyeb.com/auth/signin")
            
            # 2. 输入邮箱并继续
            page.wait_for_selector('input[name="email"]')
            page.fill('input[name="email"]', email)
            # 点击 "Continue" 或 "继续" 按钮
            page.click('button[type="submit"]')
            print(f"[{email}] 已输入邮箱，正在跳转...")

            # 3. 输入密码并登录
            # 等待密码输入框出现
            page.wait_for_selector('input[name="password"]', timeout=10000)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            print(f"[{email}] 已输入密码，正在登录...")

            # 4. 处理“Skip for now”或类似提示页面
            # 有时 Koyeb 会提示设置 2FA 或更新信息，点击“Skip”
            try:
                # 尝试寻找包含 "Skip" 文本的按钮，限时 5 秒
                skip_button = page.wait_for_selector('text="Skip for now", text="Maybe later"', timeout=5000)
                if skip_button:
                    skip_button.click()
                    print(f"[{email}] 已跳过提示信息")
            except:
                # 如果没出现跳过按钮，则认为是直接进入了仪表盘
                pass

            # 5. 验证是否登录成功
            # 检查 URL 是否包含 dashboard 或直接跳转
            page.wait_for_url("https://app.koyeb.com/*", timeout=10000)
            
            # 检查是否依然有报错信息
            error_message = page.query_selector('.MuiAlert-message')
            if error_message:
                return f"账号 {email} 登录异常: {error_message.inner_text()}"
            
            return f"账号 {email} 登录成功!"

        except Exception as e:
            return f"账号 {email} 登录出错: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    accounts_str = os.environ.get('KOY_ACC', '')
    if not accounts_str:
        print("未检测到 KOY_ACC 环境变量")
        exit(1)
        
    accounts = accounts_str.split()
    login_statuses = []

    for account in accounts:
        if ':' not in account:
            continue
        email, password = account.split(':', 1)
        status = login_koyeb(email, password)
        login_statuses.append(status)
        print(status)

    if login_statuses:
        message = "?? *Koyeb 自动登录任务报告*:\n\n" + "\n".join(login_statuses)
        send_telegram_message(message)
