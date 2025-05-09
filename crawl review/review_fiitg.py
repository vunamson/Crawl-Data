import random
from sys import _xoptions
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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


def get_reviews(driver):
    reviews = set()
    seen_ids = set()

    while True:
        # Lấy tất cả các thẻ review hiển thị
        cards = driver.find_elements(By.CSS_SELECTOR, "div.grid-item-wrap.has-img")

        for card in cards:
            try:
                data_id = card.get_attribute("data-id")
                if data_id in seen_ids:
                    continue
                seen_ids.add(data_id)

                driver.execute_script("arguments[0].scrollIntoView(true);", card)
                time.sleep(0.5)
                card.click()

                # Chờ popup hiện
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "css-10vg0z8"))
                )

                # Kiểm tra có hình ảnh
                try:
                    img = driver.find_element(By.CSS_SELECTOR, "img.fadeIn")
                    name = img.get_attribute("alt")
                    img_src = img.get_attribute("src")
                    reviews.add((name, img_src))
                except:
                    pass

                # Kiểm tra có video
                try:
                    iframe = driver.find_element(By.ID, "loox-video-player")
                    video_src = iframe.get_attribute("src")
                    text = driver.find_element(By.CSS_SELECTOR, "div.pre-wrap.normal-text").text
                    reviews.add((text, video_src))
                except:
                    pass

                # Đóng popup
                try:
                    close_btn = driver.find_element(By.CLASS_NAME, "close-btn")
                    close_btn.click()
                    time.sleep(0.5)
                except:
                    pass

            except Exception as e:
                print(f"Error: {e}")

        # Tìm nút "Show more reviews"
        try:
            load_more = driver.find_element(By.ID, "loadMore")
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
            time.sleep(0.5)
            load_more.click()
            time.sleep(3)  # đợi phần mới hiện ra
        except:
            print("Không còn nút Show More hoặc đã đến cuối.")
            break

    return list(reviews)

# === MAIN ===
driver = create_driver()
driver.get("https://www.fiitg.com/pages/customer-review/")  # 🔁 Thay link trang reviews vào đây

time.sleep(5)  # chờ load trang

results = get_reviews(driver)

# Xuất ra file Excel
df = pd.DataFrame(results, columns=["Content_or_Reviewer", "Media_URL"])
df.to_excel("review_media_results.xlsx", index=False)

print("✅ Đã lưu kết quả vào review_media_results.xlsx")
driver.quit()

# Hiển thị kết quả
for r in results:
    print(r)
