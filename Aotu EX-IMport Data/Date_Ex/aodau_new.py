import asyncio
import json
from datetime import datetime
import random
import os
import re
from sys import _xoptions

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC

import time
from urllib.parse import parse_qs, urlencode, urlparse
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Cấu hình Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Crawl Data Git\Crawl-Data\credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1s1xkT3iscHI_ADUztr0z-xNyMLKjBSJl_lPAwbjN7S4").worksheet("CRAWL AUTHENTIC")

urls = sheet.col_values(1)[1:]
extra_data = sheet.col_values(2)[1:]
desc_data = sheet.col_values(3)[1:] if len(sheet.col_values(3)) >= 1 else []
price_data = sheet.col_values(4)[1:] if len(sheet.col_values(4)) >= 1 else []
header_url = sheet.col_values(6)[1:] if len(sheet.col_values(4)) >= 1 else []


headers = {"User-Agent": "Mozilla/5.0"}
semaphore = asyncio.Semaphore(10)
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

        
def build_paged_url(category_url, page):
    if page == 1:
        return category_url
    if '?' in category_url:
        return f"{category_url}&pageNumber={page}"
    else:
        return f"{category_url}?pageNumber={page}"
    
def check_publish_date(driver, url):
    try:
        # driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        page_source = driver.page_source
        # source = driver.execute_cdp_cmd("Page.getResourceContent", {"frameId": "1", "url": url})
        webGoLiveDate = None
        # print('webGoLiveDate',webGoLiveDate)
        str_page_source = str(page_source)
        print('len' , len(str_page_source))
        indices = [i for i in range(len(str_page_source)) if str_page_source.startswith("webGoLiveDate", i)]
        for idx in indices:
            start_idx = idx + len("webGoLiveDate") +2  # Đầu tiên sau "webGoLiveDate"
            end_idx = start_idx + 10  # Lấy 10 ký tự sau đó
            snippet = page_source[start_idx:end_idx]
            print('snippet' , snippet )
            if snippet.isdigit():                                                
                webGoLiveDate = int(snippet)
            else : 'khong phai so nguyen'
        print('webGoLiveDate' ,webGoLiveDate)
        if webGoLiveDate:
            # start_idx = webGoLiveDate + len(webGoLiveDate) + 2
            # end_idx = page_source.find(',', start_idx)
            # timestamp_str = page_source[start_idx:end_idx].strip()
            
            # Chuyển Unix timestamp sang datetime
            publish_date = datetime.fromtimestamp(int(webGoLiveDate))
            print('publish_date',publish_date)
            start_date = datetime(2025, 3, 1, 0, 0, 0)
            end_date = datetime(2025, 4, 9, 0, 0, 0)
            print('start_date' ,start_date <= publish_date < end_date )
            if start_date <= publish_date < end_date :
                return publish_date
            else: return None
    except Exception as e:
        print(f"Lỗi kiểm tra ngày đăng: {e}")
    return None 

def check_publish_date_false(driver, url):
    try:
        # driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        page_source = driver.page_source
        # source = driver.execute_cdp_cmd("Page.getResourceContent", {"frameId": "1", "url": url})
        webGoLiveDate = None
        # print('webGoLiveDate',webGoLiveDate)
        str_page_source = str(page_source)
        print('len' , len(str_page_source))
        indices = [i for i in range(len(str_page_source)) if str_page_source.startswith("webGoLiveDate", i)]
        for idx in indices:
            start_idx = idx + len("webGoLiveDate") +2  # Đầu tiên sau "webGoLiveDate"
            end_idx = start_idx + 10  # Lấy 10 ký tự sau đó
            snippet = page_source[start_idx:end_idx]
            print('snippet' , snippet )
            if snippet.isdigit():                                                
                webGoLiveDate = int(snippet)
            else : 'khong phai so nguyen'
        print('webGoLiveDate' ,webGoLiveDate)
        if webGoLiveDate:
            # start_idx = webGoLiveDate + len(webGoLiveDate) + 2
            # end_idx = page_source.find(',', start_idx)
            # timestamp_str = page_source[start_idx:end_idx].strip()
            
            # Chuyển Unix timestamp sang datetime
            publish_date = datetime.fromtimestamp(int(webGoLiveDate))
            start_date = datetime(2025, 3, 1, 0, 0, 0)
            end_date = datetime(2025, 4, 9, 0, 0, 0)
            print('start_date' ,start_date <= publish_date < end_date )
            return start_date > publish_date 
    except Exception as e:
        print(f"Lỗi kiểm tra ngày đăng: {e}")
    return False 

async def get_all_product_links(driver,session, category_url):
    product_links = []
    driver.get(category_url)
    time.sleep(10)
    while True:
        try:
            # if(count == 41): break
            # count = count + 1 
            # Đợi trang tải hoàn tất trước khi lấy dữ liệu
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            # Lấy tất cả ảnh sản phẩm trên trang hiện tại
            links = driver.find_elements(By.CSS_SELECTOR, "a.color-black")
            print('links', len(links)) 
            # Lưu danh sách các link sản phẩm
            for link in links:
                href = link.get_attribute("href")
                if href and href not in product_links:
                    # if check_publish_date(browser, href):
                    product_links.append(href)

            # Kiểm tra xem có nút next page hay không
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-trk-id='next-page']"))
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
    # driver.quit()
    return product_links

def clean_image_url(url):
    return re.sub(r'-\d{2,4}x\d{2,4}(?=\.(jpg|png|jpeg|webp))', '', url)

async def parse_product(driver, url, sku_prefix, description, price, record_idx):
    results = []
    try :
        driver.get(url)
        if check_publish_date_false(driver,url) : return "breck"
        date = check_publish_date(driver,url)
        if date :
            try:
                popup_close = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".overlay-close, .popup-close, .lightbox-close"))  # tuỳ vào class của popup
                )
                driver.execute_script("arguments[0].click();", popup_close)
                print("🔒 Đã đóng popup.")
                time.sleep(1)
            except:
                pass
            time.sleep(1)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1[data-talos="labelPdpProductTitle"]'))
            )
            color_buttons = driver.find_elements(By.CSS_SELECTOR, 'a[data-trk-id="color-selector"]')
            if color_buttons:
                for button in color_buttons:    
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)  # Giảm thời gian sleep
                        # name_data_talos = 
                        name_element = driver.find_element(By.CSS_SELECTOR, 'h1[data-talos="labelPdpProductTitle"]')
                        name = name_element.text.strip() if name_element else "N/A"
                        # Lấy danh sách ảnh sau khi chọn màu
                        img_elements1 = driver.find_elements(By.CSS_SELECTOR, 'img.thumbnail-image')
                        img_elements2 = driver.find_elements(By.XPATH, '//img[@loading="lazy" and @alt=""]')
                        img_elements = img_elements1 if len(img_elements1) > 0 else img_elements2
                        img_links = [img.get_attribute("src") for img in img_elements]

                        img_links_str = ", ".join(img_links) if img_links else "LỖI"
                        results.append([
                            "", "simple", f"{sku_prefix}-{100000 + 2 * (record_idx + len(results))}", name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
                            "", "", "", "", 1, "", "", price, sku_prefix, sku_prefix, "", img_links_str,
                            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
                        ])
                        print(f"✅ {name} ({len(img_links)} ảnh)")
                    except Exception as e:
                        print(f"⚠️ Lỗi khi click màu: {e}")
            else:
                name_element = driver.find_element(By.CSS_SELECTOR, 'h1[data-talos="labelPdpProductTitle"]')
                name = name_element.text.strip() if name_element else "N/A"
                img_elements1 = driver.find_elements(By.CSS_SELECTOR, 'img.thumbnail-image')
                img_elements2 = driver.find_elements(By.XPATH, '//img[@loading="lazy" and @alt=""]')
                img_elements = img_elements1 if len(img_elements1) > 0 else img_elements2
                img_links = [img.get_attribute("src") for img in img_elements]
                img_links_str = ", ".join(img_links) if img_links else "LỖI"
                results.append([
                    "", "simple", f"{sku_prefix}-{100000 + 2 * (record_idx + len(results))}", name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
                    "", "", "", "", 1, "", "", price, sku_prefix, sku_prefix, "", img_links_str,
                    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
                ])
                print(f"✅ {name} ({len(img_links)} ảnh)")
    except Exception as e:
        print(f"❌ Lỗi khi crawl {url}: {e}")
        return None
        # driver.quit()
        # time.sleep(10)
        # driver = create_driver()

    return results if len(results) > 0  else None


    # soup = BeautifulSoup(html, "html.parser")
    # os.makedirs("debug_soup", exist_ok=True)
    # with open(f"debug_soup/page_{url}.html", "w", encoding="utf-8") as f:
    #     f.write(html)
    # results = []

    # for script_tag in soup.find_all("script", type="application/ld+json", class_="rank-math-schema-pro"):
    #     try:
    #         data = json.loads(script_tag.string)

    #         if "@graph" in data:
    #             for item in data["@graph"]:
    #                 if item.get("@type") == "Product" and "image" in item and "name" in item:
    #                     name = item["name"].strip()

    #                     images = item["image"]
    #                     img_urls = []

    #                     if isinstance(images, list):
    #                         img_urls.extend(images)
    #                     elif isinstance(images, str):
    #                         img_urls.append(images)
    #                     elif isinstance(images, dict) and "url" in images:
    #                         img_urls.append(images["url"])

    #                     img_links_str = ", ".join([clean_image_url(link) for link in img_urls])

    #                     results.append([
    #                         "", "simple", f"{sku_prefix}-{100000 + 2 * (record_idx + len(results))}", name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
    #                         "", "", "", "", 1, "", "", price, sku_prefix, sku_prefix, "", img_links_str,
    #                         "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
    #                     ])

    #     except Exception as e:
    #         print(f"Error parsing JSON-LD: {e}")

    # # JSON khác: tìm name và image trong "window.__INITIAL_STATE__"
    # for script in soup.find_all("script"):
    #     if script.string and "additionalImages" in script.string:
    #         try:
    #             matches = re.findall(r'"title":"(.*?)".*?"image":\{"src":"(.*?)"\}.*?"additionalImages":(\[.*?\])', script.string)
    #             for title, main_img, additional_raw in matches:
    #                 name = title.strip()
    #                 img_urls = [header_url_index + main_img]

    #                 additional = json.loads(additional_raw.replace("'", '"'))
    #                 for obj in additional:
    #                     img_data = obj.get("image", {})
    #                     if "src" in img_data:
    #                         img_urls.append(header_url_index + img_data["src"])

    #                 img_links_str = ", ".join([clean_image_url(link) for link in img_urls])
    #                 results.append([
    #                     "", "simple", f"{sku_prefix}-{100000 + 2 * (record_idx + len(results))}", name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
    #                     "", "", "", "", 1, "", "", price, sku_prefix, sku_prefix, "", img_links_str,
    #                     "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
    #                 ])
    #         except Exception as e:
    #             print(f"Error parsing JS-embedded product: {e}")

    # # ✅ Loại bỏ sản phẩm trùng name
    # seen_names = set()
    # unique_results = []
    # for row in results:
    #     name = row[3]  # Cột chứa name
    #     if name not in seen_names:
    #         seen_names.add(name)
    #         unique_results.append(row)

    # print(f"✅ {len(unique_results)} sản phẩm hợp lệ trong: {url}")
    # return unique_results


async def crawl_all():

    driver = create_driver()
    async with aiohttp.ClientSession(headers=headers) as session:
        # driver = create_driver()
        for idx, cat_url in enumerate(urls):
            sku_prefix = extra_data[idx] if idx < len(extra_data) else "SKU"
            description = desc_data[idx] if idx < len(desc_data) else ""
            price = price_data[idx] if idx < len(price_data) else "0"
            # header_url_index = header_url[idx] if idx < len(price_data) else "0"
            print(f"📂 Crawling category: {cat_url}")
            product_links = await get_all_product_links(driver,session, cat_url)
            print(f"🔗 Found {len(product_links)} product links.")
            for record_idx, link in enumerate(product_links):
                retries = 0
                while retries < 2:
                    res = await parse_product(driver, link, sku_prefix, description, price, record_idx)
                    if res == "breck" : 
                        retries += 1
                        break
                    if res is not None:
                        for row in res :
                            data.append(row)
                    else:
                        print(f"🔁 Retry {retries + 1} for {link}")
                        driver.quit()
                        time.sleep(10)
                        driver = create_driver()
                        retries += 1
                # tasks.append(parse_product(driver, link, sku_prefix, description, price, record_idx))
        # results = await asyncio.gather(*tasks)
        # for res in results:
        #     if res:
        #         data.append(res)

    df = pd.DataFrame(data, columns=header)
    df.to_csv("ao_dau.csv", index=False, encoding="utf-8-sig")
    print("🎉 DONE! Data saved to ao_dau.csv")

    driver.quit()

asyncio.run(crawl_all())
