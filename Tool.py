import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import requests  # Thêm thư viện requests

# Cấu hình log
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

chat_id = "-4630038358"
client = MongoClient('mongodb://foo:bar@103.140.249.159:27017/')
db = client["intern-tool"]
collection = db["company-image"]

options = Options()
options.add_argument("--headless")  # Chạy không giao diện người dùng
options.add_argument("--no-sandbox")  # Chạy không sandbox
options.add_argument("--disable-dev-shm-usage")  # Khắc phục lỗi thiếu bộ nhớ
options.add_argument("--disable-gpu")  # Tắt GPU nếu không cần thiết

# Khởi tạo ChromeDriver với các tùy chọn trên
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Hàm gửi thông báo Telegram
def send_telegram_message(message):
    bot_token = "8020956192:AAFXZl4p1MD5kmEBU0ceGlSd_hRQpdz9Q0U"  # Thay bằng token bot của bạn
    chat_id = "-4630038358"  # Thay bằng chat ID của bạn
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Kiểm tra lỗi từ API
        print("Đã gửi thông báo thành công!")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi thông báo: {e}")

async def get_logo_urls():
    """Lấy danh sách URL logo từ trang web"""
    try:
        driver.get("https://internship.cse.hcmut.edu.vn/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[style*='background-image']"))
        )
        logos = driver.find_elements(By.CSS_SELECTOR, "[style*='background-image']")
        urls = []
        for logo in logos:
            style = logo.get_attribute("style")
            start = style.find('url("') + 5
            end = style.find('")', start)
            img_url = "https://internship.cse.hcmut.edu.vn" + style[start:end]
            urls.append(img_url)
        return urls
    finally:
        driver.quit()  # Đóng trình duyệt dù có lỗi hay không

async def check_new_logos():
    """Kiểm tra logo mới và gửi thông báo Telegram"""
    new_logos = []
    current_logos = await get_logo_urls()  # Lấy các logo hiện tại
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
            send_telegram_message(msg)  # Gọi hàm gửi tin nhắn
        logging.info("✅ Đã gửi thông báo Telegram!")

async def check_logos():
    while True:
        await check_new_logos()  # Hàm kiểm tra logo mới
        await asyncio.sleep(60)

# Chạy vòng lặp bất đồng bộ khi PM2 khởi động
if __name__ == "__main__":
    asyncio.run(check_logos())
