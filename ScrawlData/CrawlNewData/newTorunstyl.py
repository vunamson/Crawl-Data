from datetime import datetime
import random
from sys import _xoptions
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time


def get_random_user_agent():    
    chrome_version = f"{random.randint(2, 200)}.0.0.0"  # Tạo số ngẫu nhiên từ 2.0.0.0 - 200.0.0.0
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

# proxies = load_proxies()

# 🛠️ Hàm tạo WebDriver với User-Agent mới
def create_driver(): 
    chrome_options = uc.ChromeOptions()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.set_capability('LT:Options', _xoptions)

    # if proxy:
    #     chrome_options.add_argument(f"--proxy-server={proxy}")
    #     print(f"🔄 Đang sử dụng Proxy: {proxy}")
    # 🔄 Thêm User-Agent ngẫu nhiên
    user_agent = get_random_user_agent()
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    print(f"🆕 Đã thay đổi User-Agent: {user_agent}")
    # return uc.Chrome(headless=False)
    return uc.Chrome(headless=False)
# Khởi tạo WebDriver duy nhất (tránh tạo lại mỗi lần lặp)
# current_proxy = get_random_proxy(proxies)
def check_publish_date(driver, url):
    try:
        # driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        page_source = driver.page_source
        # source = driver.execute_cdp_cmd("Page.getResourceContent", {"frameId": "1", "url": url})
        datePublished = None
        # print('webGoLiveDate',webGoLiveDate)
        str_page_source = str(page_source)
        print('len' , len(str_page_source))
        indices = [i for i in range(len(str_page_source)) if str_page_source.startswith("datePublished", i)]
        for idx in indices:
            start_idx = idx + len("webGoLiveDate") +3  # Đầu tiên sau "webGoLiveDate"
            end_idx = start_idx + 25  # Lấy 10 ký tự sau đó
            snippet = page_source[start_idx:end_idx]
            datePublished = datetime.strptime(snippet, "%Y-%m-%dT%H:%M:%S%z")
            print('snippet' , snippet,datePublished )
           
        if datePublished:
            # start_idx = webGoLiveDate + len(webGoLiveDate) + 2
            # end_idx = page_source.find(',', start_idx)
            # timestamp_str = page_source[start_idx:end_idx].strip()
            
            # Chuyển Unix timestamp sang datetime
            publish_date = datePublished.replace(tzinfo=None)
            print('publish_date',publish_date)
            start_date = datetime(2025, 2, 24, 0, 0, 0)
            end_date = datetime(2025, 2, 27, 0, 0, 0)
            print('start_date' ,start_date <= publish_date < end_date )
            return start_date <= publish_date < end_date
    except Exception as e:
        print(f"Lỗi kiểm tra ngày đăng: {e}")
    return False 


driver = create_driver()
product_links = []
url = "https://torunstyle.com/product-category/hoodie/?orderby=date"
driver.get(url)
time.sleep(5)
count = 0

while True:
    try:
        if(count == 2) : break
        count = count + 1
        # Đợi trang tải hoàn tất trước khi lấy dữ liệu
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        # Lấy tất cả ảnh sản phẩm trên trang hiện tại
        links = driver.find_elements(By.CSS_SELECTOR, "a[aria-label]")
        print('links', len(links)) 
        # Lưu danh sách các link sản phẩm
        for link in links:
            href = link.get_attribute("href")
            if href and href not in product_links:
                # if check_publish_date(browser, href):
                product_links.append(href)

        # Kiểm tra xem có nút next page hay không
        
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


# 3️⃣ Crawl dữ liệu từng sản phẩm
data = []
for index, link in enumerate(product_links):
    try:
        # print('index' , index)
        # if index > 0 and index  == 1 : 
            # driver.quit()
            # driver = create_driver()
            # driver.delete_all_cookies()
            # print('if')
            # current_proxy = get_random_proxy(proxies)
            # driver = create_driver(current_proxy)
        # else : print('else')
        driver.get(link)
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if check_publish_date(driver,link) :

        # if index == 0 : check_publish_date(driver,link)
        # else: break
            print(f"🔍 Đang lấy dữ liệu từ: {link} ({index + 1}/{len(product_links)})")
            # Sử dụng WebDriverWait thay vì time.sleep()
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
                # EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-talos="labelPdpProductTitle"]'))
            )

            # Lấy tên sản phẩm

            # Tìm danh sách màu sắc (nếu có)
            # color_buttons = driver.find_elements(By.CSS_SELECTOR, 'a[data-trk-id="color-selector"]')

            # if color_buttons:
            #     for button in color_buttons:
                    
            #         try:
            #             driver.execute_script("arguments[0].click();", button)
            #             time.sleep(1)  # Giảm thời gian sleep
            #             name_element = driver.find_element(By.CSS_SELECTOR, 'h1[data-talos="labelPdpProductTitle"]')
            #             name = name_element.text.strip() if name_element else "N/A"
            #             # Lấy danh sách ảnh sau khi chọn màu
            #             img_elements = driver.find_elements(By.CSS_SELECTOR, 'img.thumbnail-image')
            #             img_links = [img.get_attribute("src") for img in img_elements]

            #             # Lưu dữ liệu
            #             img_links_str = ", ".join(img_links) if img_links else "LỖI"
            #             data.append([name, img_links_str])
            #             print(f"✅ {name} ({len(img_links)} ảnh)")
            #         except Exception as e:
            #             print(f"⚠️ Lỗi khi click màu: {e}")
            #             data.append([name, "LỖI"])
            # else:
            name_element = driver.find_element(By.CSS_SELECTOR, 'h1.entry-title')
            name = name_element.text.strip() if name_element else "N/A"
            img_elements = driver.find_elements(By.CSS_SELECTOR, 'img.attachment-woocommerce_thumbnail[alt=""]')
            img_links = [img.get_attribute("src") for img in img_elements]
            print('img_links' ,img_links ,name)

            img_links_str = ", ".join(img_links) if img_links else "LỖI"
            print('img_links_str' ,img_links_str)
            data.append([name, img_links_str])
            print(f"✅ {name} ({len(img_links)} ảnh)")

    except Exception as e:
        print(f"❌ Lỗi khi crawl {link}: {e}")
        driver.quit()
        time.sleep(10)
        driver = create_driver()
        data.append(["LỖI", "LỖI"])

# 4️⃣ Lưu dữ liệu vào file Excel
driver.quit()
del driver
df = pd.DataFrame(data, columns=["Name", "Image Links"])
df.to_excel("output2.xlsx", index=False, engine="openpyxl")

print("🎉 Dữ liệu đã được lưu vào output1.xlsx!")