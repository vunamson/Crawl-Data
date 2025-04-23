from sys import _xoptions
import random, threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC

# === Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Crawl Data Git\Crawl-Data\credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1c_omcHE3AMkUBxFS1Cckwcw0A-fBX5FV6dbJYn_Jg5s").worksheet("CRAWL")
urls = sheet.col_values(1)[1:]
extra_data = sheet.col_values(2)[1:]
desc_data = sheet.col_values(3)[1:]
price_data = sheet.col_values(4)[1:]

# === Selenium driver ===
def get_random_user_agent():
    chrome_version = f"{random.randint(2, 200)}.0.0.0"
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

def create_driver():
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.set_capability('LT:Options', _xoptions)
    options.add_argument(f"--user-agent={get_random_user_agent()}")
    return uc.Chrome(options=options,version_main=135)

# === Data storage ===
data = []
data_lock = threading.Lock()
semaphore = threading.Semaphore(2)

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

# === Lấy link sản phẩm từ trang category ===
def get_all_product_links(driver, url):
    driver.get(url)
    product_links = set()
    while True:
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            links = driver.find_elements(By.CSS_SELECTOR, "a[aria-label]:not([class])")
            for link in links:
                href = link.get_attribute("href")
                if href:
                    product_links.add(href)

            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next"))
            )
            if next_button.get_attribute("aria-disabled") == "true":
                break
            next_button.click()
        except (TimeoutException, NoSuchElementException):
            break
    return list(product_links)

# === Crawl chi tiết từng sản phẩm ===
def crawl_product(driver, link, sku_prefix, description, price_value, record):
    driver.get(link)
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.product-title')))
    name = driver.find_element(By.CSS_SELECTOR, 'h1.product-title').text.strip()
    image_main = driver.find_elements(By.CSS_SELECTOR, 'img.skip-lazy')
    main_img = image_main[0].get_attribute("src") if image_main else ""
    img_elements = driver.find_elements(By.XPATH, '//img[@class="attachment-woocommerce_thumbnail"]')
    img_links = [img.get_attribute("src") for img in img_elements]
    img_links_str = ", ".join(img_links) if img_links else main_img

    with data_lock:
        data.append([
            "", "simple", f"{sku_prefix}-{100000 + 2 * record}", name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
            "", "", "", "", 1, "", "", price_value, sku_prefix, sku_prefix, "", img_links_str,
            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",""
        ])

# === Task chính mỗi URL ===
def crawl_url(args):
    url, sku_prefix, price_value, description = args
    driver = create_driver()
    try:
        product_links = get_all_product_links(driver, url)
        for record, link in enumerate(product_links):
            try:
                crawl_product(driver, link, sku_prefix, description, price_value, record)
            except Exception as e:
                print(f"❌ Lỗi khi crawl sản phẩm {link}: {e}")
    except Exception as e:
        print(f"❌ Lỗi khi truy cập URL {url}: {e}")
    finally:
        driver.quit()

# === Tạo danh sách task và chạy đa luồng ===
tasks = [
    (urls[i], extra_data[i] if i < len(extra_data) else "SKU", price_data[i] if i < len(price_data) else "0", desc_data[i] if i < len(desc_data) else "")
    for i in range(len(urls))
]

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(crawl_url, tasks)

pd.DataFrame(data, columns=header).to_csv("woo_products_parallel.csv", index=False, encoding="utf-8-sig")
print("🎉 Đã hoàn thành crawl toàn bộ dữ liệu!")