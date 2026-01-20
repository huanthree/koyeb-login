from playwright.sync_api import sync_playwright
import os
import requests
import time

def send_telegram_message(message):
    bot_token = os.environ.get('TEL_TOK')
    chat_id = os.environ.get('TEL_ID')
    if not bot_token or not chat_id:
        print("Telegram 配置缺失，跳过发送消息")
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
        # 启动浏览器，设置模拟窗口大小
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # 预设截图文件名（处理特殊字符以防报错）
        safe_email = email.replace('@', '_').replace('.', '_')
        screenshot_path = f"error_{safe_email}.png"

        try:
            # 1. 访问登录页面
            page.goto("https://app.koyeb.com/auth/signin", wait_until="networkidle")
            
            # 2. 填写邮箱并点击继续
            page.wait_for_selector('input[name="email"]', timeout=15000)
            page.fill('input[name="email"]', email)
            page.click('button[type="submit"]')
            print(f"[{email}] 第一步：邮箱已提交")

            # 3. 填写密码并登录
            # Koyeb 现在会在新页面或动态加载密码框
            page.wait_for_selector('input[name="password"]', timeout=15000)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            print(f"[{email}] 第二步：密码已提交")

            # 4. 验证登录结果或处理弹窗
            try:
                # 等待直到进入 dashboard 控制台
                page.wait_for_url("**/dashboard**", timeout=20000)
                return f"账号 {email} 登录成功!"
            except:
                # 检查是否有 "Skip for now" 类的按钮（处理 2FA 提示）
                skip_btn = page.query_selector('text="Skip for now", text="Maybe later"')
                if skip_btn:
                    skip_btn.click()
                    page.wait_for_timeout(3000)
                    return f"账号 {email} 登录成功 (已跳过引导弹窗)!"
                
                # 如果既没进入 dashboard 也没找到跳过按钮，抛出错误以便截图
                raise Exception("无法确认登录状态，可能出现了验证码或新的引导页面")

        except Exception as e:
            # 捕获异常并截图
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"[{email}] 登录失败，已保存调试截图: {screenshot_path}")
            except Exception as se:
                print(f"[{email}] 截图失败: {se}")
            return f"账号 {email} 登录出错: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    # 从环境变量获取账号信息，格式为 "email1:pass1 email2:pass2"
    accounts_env = os.environ.get('KOY_ACC', '')
    if not accounts_env:
        print("错误：未找到 KOY_ACC 环境变量")
        exit(1)
        
    accounts = accounts_env.split()
    login_statuses = []

    for account in accounts:
        if ':' not in account:
            continue
        email, password = account.split(':', 1)
        status = login_koyeb(email, password)
        login_statuses.append(status)
        print(status)

    if login_statuses:
        report = "?? *Koyeb 自动登录任务报告*:\n\n" + "\n".join(login_statuses)
        send_telegram_message(report)
