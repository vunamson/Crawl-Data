import random, time
import pandas as pd
from sys import _xoptions
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# === Cấu hình Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Crawl Data Git\Crawl-Data\credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1c_omcHE3AMkUBxFS1Cckwcw0A-fBX5FV6dbJYn_Jg5s").worksheet("CRAWL")
urls = sheet.col_values(1)[1:]
extra_data = sheet.col_values(2)[1:]
desc_data = sheet.col_values(3)[1:] if len(sheet.row_values(3)) >= 3 else []
price_data = sheet.col_values(4)[1:] if len(sheet.row_values(4)) >= 4 else []

# === Hàm tiện ích ===
def get_random_user_agent():
    chrome_version = f"{random.randint(2, 200)}.0.0.0"
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

def create_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.set_capability('LT:Options', _xoptions)
    # options.add_argument(f"user-agent={get_random_user_agent()}")
    user_agent = get_random_user_agent()
    options.add_argument(f"--user-agent={user_agent}")
    print("🆕 Khởi tạo trình duyệt với User-Agent mới.")
    return uc.Chrome(headless=False, options=options)

# === Crawl từng sản phẩm ===
driver = create_driver()
data = []
header = ["ID","Type","SKU","Name","Published","Is featured?","Visibility in catalog","Short description","Description",
          "Date sale price starts","Date sale price ends","Tax status","Tax class","In stock?","Stock","Low stock amount",
          "Backorders allowed?","Sold individually?","Weight (kg)","Length (cm)","Width (cm)","Height (cm)","Allow customer reviews?",
          "Purchase note","Sale price","Regular price","Categories","Tags","Shipping class","Images",
          "Download limit","Download expiry days","Parent","Grouped products","Upsells","Cross-sells",
          "External URL","Button text","Position",
          "Attribute 1 name","Attribute 1 value(s)","Attribute 1 visible","Attribute 1 global","Attribute 1 default",
          "Attribute 2 name","Attribute 2 value(s)","Attribute 2 visible","Attribute 2 global","Attribute 2 default",
          "Attribute 3 name","Attribute 3 value(s)","Attribute 3 visible","Attribute 3 global","Attribute 3 default",
          "Meta: hwp_product_gtin"]

def add_data(url,sku_prefix,price_value,description,driver):
    driver.get(url)
    product_links = []
    while True:
        try:
            # if(count == 41): break
            # count = count + 1 
            # Đợi trang tải hoàn tất trước khi lấy dữ liệu
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            # time.sleep(3)
            # Lấy tất cả ảnh sản phẩm trên trang hiện tại
            links = driver.find_elements(By.CSS_SELECTOR, "a[aria-label]:not([class])")
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
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next"))
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


    print('product_links' , len(product_links) ,product_links[len(product_links) -1])

    # 3️⃣ Crawl dữ liệu từng sản phẩm
    record = 0
    for index, link in enumerate(product_links):
        try:
            driver.get(link)
            print(f"🔍 Đang lấy dữ liệu từ: {link} ({index + 1}/{len(product_links)})")
            # Sử dụng WebDriverWait thay vì time.sleep()
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.product-title'))
            )

            # Tìm danh sách màu sắc (nếu có)
            color_buttons = driver.find_elements(By.CSS_SELECTOR, 'a[data-trk-id="color-selector"]')

            if color_buttons:
                for button in color_buttons:                    
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)  # Giảm thời gian sleep
                        name_element = driver.find_element(By.CSS_SELECTOR, 'h1.product-title')
                        name = name_element.text.strip() if name_element else "N/A"
                        # Lấy danh sách ảnh sau khi chọn màu
                        image_main = driver.find_elements(By.CSS_SELECTOR, 'img.skip-lazy')
                        image_main_src = image_main[0].get_attribute("src") if image_main else ""
                        img_elements = driver.find_elements(By.XPATH,'//img[@class="attachment-woocommerce_thumbnail"]')
                        img_links = [img.get_attribute("src") for img in img_elements] 

                        # Lưu dữ liệu
                        img_links_str = ", ".join(img_links) if img_links else image_main_src
                        data.append([
                            "", "simple", f"{sku_prefix}-{100000 + 2 * record}", name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
                            "", "", "", "", 1, "", "", price_value, sku_prefix, sku_prefix, "", img_links_str,
                            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",""
                        ])
                        record = record+1
                        print(f"✅ {name} ({len(img_links)} ảnh)")
                    except Exception as e:
                        print(f"⚠️ Lỗi khi click màu: {e}")
            else:
                name_element = driver.find_element(By.CSS_SELECTOR, 'h1.product-title')
                name = name_element.text.strip() if name_element else "N/A"
                image_main = driver.find_elements(By.CSS_SELECTOR, 'img.skip-lazy')
                image_main_src = image_main[0].get_attribute("src") if image_main else ""
                img_elements = driver.find_elements(By.XPATH,'//img[@class="attachment-woocommerce_thumbnail"]')
                img_links = [img.get_attribute("src") for img in img_elements]
                img_links_str = ", ".join(img_links) if img_links else image_main_src
                data.append([
                    "", "simple", f"{sku_prefix}-{100000 + 2 * record}", name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
                    "", "", "", "", 1, "", "", price_value, sku_prefix, sku_prefix, "", img_links_str,
                    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",""
                ])
                record = record+1
                print(f"✅ {name} ({len(img_links)} ảnh)")

        except Exception as e:
            print(f"❌ Lỗi khi crawl {link}: {e}")
            driver.quit()
            # time.sleep(10)
            driver = create_driver()
    return driver

for idx, url in enumerate(urls):

    sku_prefix = extra_data[idx] if idx < len(extra_data) else "SKU"
    description = desc_data[idx] if idx < len(desc_data) else ""
    price = price_data[idx] if idx < len(price_data) else "0"
    # sku = f"{sku_prefix}-{100000 + 2 * idx}"

    try:
        add_data(url,sku_prefix,price,description,driver)
    except Exception as e:
        print(f"❌ Lỗi tại {url}: {e}")

driver.quit()
df = pd.DataFrame(data, columns=header)
df.to_csv("woo_products.csv", index=False, encoding="utf-8-sig")
print("🎉 Hoàn tất! Dữ liệu đã được lưu vào woo_products.csv")
