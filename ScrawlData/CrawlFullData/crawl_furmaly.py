import time, random
import pandas as pd
from sys import _xoptions
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def get_random_user_agent():    
    chrome_version = f"{random.randint(2, 200)}.0.0.0"  # Tạo số ngẫu nhiên từ 2.0.0.0 - 200.0.0.0
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"

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
base_url = "https://furmaly.com/product-category/mlb-23/?orderby=date"
driver.get(base_url)
product_links = []

# 1️⃣ Crawl tất cả link sản phẩm qua phân trang
page = 1
while True:
    page = page+ 1
    # print(f"🔗 Đang lấy links từ trang {page}: {url}")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, 'body'))
    )
    # links = driver.find_elements(By.CSS_SELECTOR, "h2.woocommerce-loop-product__title")
    # if not links:
    #     print("✅ Không còn trang tiếp theo.")
    #     break

    for el in driver.find_elements(By.CSS_SELECTOR, 'a.woocommerce-LoopProduct-link'):
        href = el.get_attribute("href")
        if href not in product_links:
            product_links.append(href)

    try:
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Next']"))
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

# 2️⃣ Crawl dữ liệu từng sản phẩm
data = []
for index, link in enumerate(product_links):
    print(f"\n📦 Crawling sản phẩm {index + 1}/{len(product_links)}: {link}")
    try:
        driver.get(link)
        time.sleep(3)
        # WebDriverWait(driver, 15).until(
        #     EC.presence_of_element_located((By.TAG_NAME, 'body'))
        # )
        product_name = driver.find_element(By.CSS_SELECTOR, 'h1.product_title').text.strip()
        print('product_name' ,product_name)
    except TimeoutException:
        print(f"⚠️ Timeout khi mở sản phẩm: {link} → bỏ qua.")
        data.append([f"TIMEOUT - {link}", ""])
        continue
    except Exception as e:
        print(f"❌ Lỗi khác khi mở sản phẩm: {link} → {e}")
        data.append([f"ERROR - {link}", ""])
        continue
    # Xử lý select Style
    try:        
        style_select = Select(driver.find_element(By.ID, "pa_style"))
        style_options = [opt for opt in style_select.options if opt.get_attribute("value") != ""]
        for style in style_options:
            style_value = style.get_attribute("value")
            style_select.select_by_value(style_value)
            time.sleep(1)
            print('style',style)
            # Kiểm tra select Player
            try:
                # player_select = Select(driver.find_element(By.CSS_SELECTOR, 'select#pa_player[data-show_option_none="yes"]'))
                # player_options = [opt for opt in player_select.options if opt.get_attribute("value") != ""]
                player_select = Select(driver.find_element(By.ID, "pa_player"))
                player_options = [opt for opt in player_select.options if opt.get_attribute("value") != ""]
                for player in player_options:
                    print('player',player)
                    player_value = player.get_attribute("value")
                    player_select.select_by_value(player_value)
                    time.sleep(1)

                    # Crawl ảnh
                    images = driver.find_elements(By.CSS_SELECTOR, ".flickity-slider img")
                    img_links = [img.get_attribute("src") for img in images if img.get_attribute("src")]
                    combined_name = f"{player.text} - {product_name} - {style.text}"
                    data.append([combined_name,img_links[0]])

            except NoSuchElementException:
                # Không có Player
                images = driver.find_elements(By.CSS_SELECTOR, ".flickity-slider img")
                img_links = [img.get_attribute("src") for img in images if img.get_attribute("src")]
                combined_name = f"{product_name} - {style.text}"
                data.append([combined_name,img_links[0]])

    except NoSuchElementException:
        # Không có Style
        images = driver.find_elements(By.CSS_SELECTOR, ".flickity-slider img")
        img_links = [img.get_attribute("src") for img in images if img.get_attribute("src")]
        data.append([product_name,img_links[0]])

# 3️⃣ Xuất ra file Excel
df = pd.DataFrame(data, columns=["Name", "Image Links"])
df.to_excel("furmaly_products.xlsx", index=False, engine="openpyxl")
driver.quit()
print("\n🎉 Hoàn tất! Đã lưu dữ liệu vào furmaly_products.xlsx")
