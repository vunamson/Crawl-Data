from datetime import datetime
import random
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 🔹 Hàm tạo User-Agent ngẫu nhiên
def get_random_user_agent():
    chrome_version = f"{random.randint(2, 200)}.0.0.0"
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"


# 🔹 Hàm khởi tạo trình duyệt Selenium với User-Agent ngẫu nhiên
def create_driver():
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    user_agent = get_random_user_agent()
    chrome_options.add_argument(f"user-agent={user_agent}")

    print(f"🆕 Đã thay đổi User-Agent: {user_agent}")
    return uc.Chrome(headless=False)


# 🔹 Hàm lấy danh sách URL từ Google Sheets (Sheet "Torunstyle")
def get_urls_from_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\ScrawlData\CrawlNewData\credentials.json", scope)
        client = gspread.authorize(creds)
        sheet_id = "1c_omcHE3AMkUBxFS1Cckwcw0A-fBX5FV6dbJYn_Jg5s"
        sheet = client.open_by_key(sheet_id).worksheet("Torunstyle")

        urls = sheet.col_values(1)[1:]  # Lấy cột A, bỏ qua tiêu đề
        extra_data = sheet.col_values(2)[1:]  # Lấy cột B (nếu có)

        url_data  = []
        for i, url in enumerate(urls):
            url_data.append({
                "url" : url,
                "types" : extra_data[i]
            })

        print(f"✅ Đã lấy {len(urls)} URL từ Google Sheets.")
        return url_data
    except Exception as e:
        print(f"❌ Lỗi khi lấy dữ liệu từ Google Sheets: {e}")
        return {}


# 🔹 Hàm kiểm tra ngày đăng sản phẩm
def check_publish_date(driver, url):
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        page_source = driver.page_source
        indices = [i for i in range(len(page_source)) if page_source.startswith("datePublished", i)]

        for idx in indices:
            start_idx = idx + len("datePublished") + 3
            end_idx = start_idx + 25
            snippet = page_source[start_idx:end_idx]
            try:
                date_published = datetime.strptime(snippet, "%Y-%m-%dT%H:%M:%S%z")
                publish_date = date_published.replace(tzinfo=None)
                print(f"📅 Ngày đăng: {publish_date}")
                start_date = datetime(2025, 3, 3, 0, 0, 0)
                end_date = datetime(2025, 3, 6, 0, 0, 0)
                if start_date <= publish_date < end_date:
                    return publish_date
            except ValueError:
                continue
    except Exception as e:
        print(f"⚠️ Lỗi kiểm tra ngày đăng: {e}")
    return None


# 🔹 Hàm lấy danh sách sản phẩm từ trang category

# 🔹 Hàm crawl dữ liệu sản phẩm từ danh sách link

# 🔹 Hàm lưu dữ liệu vào Google Sheets
def save_to_google_sheets(data):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\ScrawlData\CrawlNewData\credentials.json", scope)
        client = gspread.authorize(creds)
        sheet_id = "1c_omcHE3AMkUBxFS1Cckwcw0A-fBX5FV6dbJYn_Jg5s"
        sheet = client.open_by_key(sheet_id).worksheet("Lấy Link")

        sheet.clear()
        sheet.append_row(["Link Trang", "Link Sản Phẩm", "Giá Trị Từ Torunstyle","Ngày Đăng"])

        if data:
            sheet.update(f"A2:D{len(data)+1}", data)  # Ghi dữ liệu hàng loạt

        print("✅ Dữ liệu đã được lưu vào Google Sheets.")
    except Exception as e:
        print(f"❌ Lỗi khi lưu dữ liệu vào Google Sheets: {e}")

def add_link(scraped_data ,driver,url,type):
    driver.get(url)
    count = 0
    product_links = []
    while True:
        try:
            if(count == 1): break
            count =count +1 
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            links = driver.find_elements(By.CSS_SELECTOR, "a[aria-label]")
            for link in links :
                if link.get_attribute("aria-label") != "Menu": 
                    href = link.get_attribute("href")
                    if href and href not in product_links and  "https" in href and "instagram" not in href and "facebook" not in href and "twitter" not in href:
                        # if check_publish_date(browser, href):
                        product_links.append(href)
            try:            
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next.page-number"))
                )
                aria_disabled = next_button.get_attribute("aria-disabled")

                if aria_disabled == "true":
                    break  # Không còn trang tiếp theo

                next_button.click()
            # Đợi trang mới tải hoàn tất
            # WebDriverWait(browser, 10).until(
            #     EC.staleness_of(images[0])  # Chờ cho trang cũ biến mất
            # )
            except (NoSuchElementException, TimeoutException):
                break
        except TimeoutException:
            print("Không tìm thấy phần tử mong muốn, thoát chương trình.")
            break
    print('product_links',product_links)
    scrawlNew = False
    for index, link in enumerate(product_links):
        try:
            driver.get(link)
            date = check_publish_date(driver,link)
            if date :
                if scrawlNew == False :
                    scraped_data.append([url,link,type,date.strftime('%Y-%m-%d %H:%M:%S')])
                    scrawlNew = True
                else:
                    scraped_data.append(["",link,type,date.strftime('%Y-%m-%d %H:%M:%S')])
                
        except Exception as e:
            print(f"❌ Lỗi khi crawl {link}: {e}")
            driver.quit()
            time.sleep(5)
            driver = create_driver()


# 🔹 Chạy chương trình chính
if __name__ == "__main__":
    driver = create_driver()
    url_data = get_urls_from_sheets()
    print('url_data',url_data)
    scraped_data = []
    for item in url_data:
        print('url,type', item['url'],item['types'])
        add_link(scraped_data,driver, item['url'],item['types'])
        
    print('scraped_data',scraped_data)
    
    

    save_to_google_sheets(scraped_data)

    driver.quit()
    print("🎉 Hoàn tất quá trình crawl dữ liệu!")
