import random
from sys import _xoptions
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# 1️⃣ Cấu hình Selenium (tăng tốc trình duyệt)
# chrome_options = Options()
# chrome_options.add_argument("--headless")  # Chạy không hiển thị trình duyệt
# chrome_options.add_argument("--disable-gpu")  # Tắt GPU tăng hiệu suất
# chrome_options.add_argument("--no-sandbox")  # Bỏ hạn chế sandbox
# chrome_options.add_argument("--disable-dev-shm-usage")  # Hỗ trợ chạy trên server
# chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Giảm khả năng bị phát hiện bot
# chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")


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
    user_agent = get_random_user_agent()
    chrome_options.add_argument(f"user-agent={user_agent}")
    
    print(f"🆕 Đã thay đổi User-Agent: {user_agent}")
    return uc.Chrome(headless=False)


driver = create_driver()
product_links = []
url = "https://lipomarts.com/product-category/nhl/?orderby=date"
time.sleep(5)
# count = 1 ; 
# for page in range(1,1000) :
#     try : 
#         link_url = url if page == 1 else f"https://lipomarts.com/product-category/nhl/page/{page}/?orderby=date"
#         driver.get(link_url)
#         WebDriverWait(driver, 15).until(
#                 EC.presence_of_element_located((By.TAG_NAME, 'body'))
#         )
#         if page == 1 : time.sleep(5)
#         links = driver.find_elements(By.CSS_SELECTOR, 'a[href][aria-label]:not([class])')
#         # driver.find_elements(By.CSS_SELECTOR, 'a.woocommerce-loop-product__link')
#         # driver.find_elements(By.CSS_SELECTOR, 'a[href][aria-label]:not([class])')
#         print('links' ,page ,'----', links)
#         for link in links:
#             href = link.get_attribute("href")
#             if href and href not in product_links and "https" in href:
#                 # if check_publish_date(browser, href):
#                 product_links.append(href)
#     except TimeoutException:
#         print("Không tìm thấy phần tử mong muốn, thoát chương trình.")
#         break
            
# print('product_links' , len(product_links) ,product_links)

# 3️⃣ Crawl dữ liệu từng sản phẩm
data = []
for page in range(1260462,1262956):
    try:
        driver.get(f"https://lipomarts.com/?attachment_id={page}")
        # Sử dụng WebDriverWait thay vì time.sleep()
        # WebDriverWait(driver, 2).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.product_title'))
        # )
        print('dang crawl tư id ------' , page)
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
        #             price_list = driver.find_elements(By.CSS_SELECTOR, 'span.sr-only')
        #             price = price_list[0].text.strip() if price_list else "Không có giá"

        #             # Lưu dữ liệu
        #             img_links_str = ", ".join(img_links) if img_links else "LỖI"
        #             data.append([name, img_links_str,price])
        #             print(f"✅ {name} ({len(img_links)} ảnh)")
        #         except Exception as e:
        #             print(f"⚠️ Lỗi khi click màu: {e}")
        #             data.append([name, "LỖI"])
        # else:
        name_element = driver.find_element(By.CSS_SELECTOR, 'h1.product_title')
        name = name_element.text.strip() if name_element else "N/A"
        img_elements = driver.find_elements(By.CSS_SELECTOR, 'img.sgub-product-image-main')
        img_links = [img.get_attribute("data-src") for img in img_elements]
        img_links_str = ", ".join(img_links) if img_links else "LỖI"
        data.append([name, img_links_str])
        print(f"✅ {name} ({len(img_links)} ảnh)")

    except Exception as e:
        continue
        driver = create_driver()

# 4️⃣ Lưu dữ liệu vào file Excel
driver.quit()
del driver
df = pd.DataFrame(data, columns=["Name", "Image Links"])
df.to_excel("output2.xlsx", index=False, engine="openpyxl")

print("🎉 Dữ liệu đã được lưu vào output1.xlsx!")