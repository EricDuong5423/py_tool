import asyncio
import schedule
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Bot

# Cấu hình log
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

chat_id = "-4774579999"
client = MongoClient('mongodb://foo:bar@103.140.249.159:27017/')
db = client["intern-tool"]
collection = db["company-image"]
bot = Bot(token="8020956192:AAFXZl4p1MD5kmEBU0ceGlSd_hRQpdz9Q0U")

options = Options()
options.add_argument('--headless')  # chạy ngầm, không mở trình duyệt
driver = webdriver.Chrome(options=options)

def get_logo_urls():
    """Lấy danh sách URL logo từ trang web"""
    driver.get("https://internship.cse.hcmut.edu.vn/")  # Thay bằng URL trang web
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[style*='background-image']"))
    )
    logos = driver.find_elements(By.CSS_SELECTOR, "[style*='background-image']")
    urls = []
    for logo in logos:
        style = logo.get_attribute("style")
        start = style.find('url("') + 5
        end = style.find('")', start)
        img_url = "https://internship.cse.hcmut.edu.vn"+style[start:end]
        urls.append(img_url)

    return urls

async def check_new_logos():
    """Kiểm tra logo mới và gửi thông báo Telegram"""
    new_logos = []
    current_logos = get_logo_urls()# Lấy các logo hiện tại
    script = """"""
    for logo in current_logos:
        if collection.find_one({"url": logo}) is None:
            new_logos.append(logo)
            collection.insert_one({"url": logo})  # Lưu logo mới vào DB

    if new_logos:
        messages = []
        message = f"🔥 Phát hiện ra {len(new_logos)} công ty mới!\n" + "\n".join(new_logos)
        messages.append(message)
        message = "Truy cập ngay ở đường link sau đây: https://internship.cse.hcmut.edu.vn/"
        messages.append(message)

        # Gửi tin nhắn Telegram
        for msg in messages:
            await bot.send_message(chat_id=chat_id, text=msg)
        logging.info("✅ Đã gửi thông báo Telegram!")

def run_async_job():
    """Bọc hàm async thành đồng bộ"""
    asyncio.run(check_new_logos())

# Lên lịch công việc mỗi 1 giây
schedule.every(1).minutes.do(run_async_job)

# Vòng lặp kiểm tra và thực thi công việc
while True:
    schedule.run_pending()  # Kiểm tra và chạy các tác vụ đã lên lịch
    time.sleep(1)  # Đợi 1 giây trước khi kiểm tra lại