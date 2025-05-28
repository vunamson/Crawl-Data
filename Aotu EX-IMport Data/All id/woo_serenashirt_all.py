import os
import asyncio
import random
import aiohttp
import pandas as pd
from openpyxl import Workbook
from bs4 import BeautifulSoup
from slugify import slugify
import csv
import json
import time

# Ghi dữ liệu vào file Excel
HEADERS = [
    "ID","Type","SKU","Name","Published","Is featured?","Visibility in catalog","Short description","Description",
    "Date sale price starts","Date sale price ends","Tax status","Tax class","In stock?","Stock","Low stock amount",
    "Backorders allowed?","Sold individually?","Weight (kg)","Length (cm)","Width (cm)","Height (cm)","Allow customer reviews?",
    "Purchase note","Sale price","Regular price","Categories","Tags","Shipping class","Images",
    "Download limit","Download expiry days","Parent","Grouped products","Upsells","Cross-sells",
    "External URL","Button text","Position",
    "Attribute 1 name","Attribute 1 value(s)","Attribute 1 visible","Attribute 1 global","Attribute 1 default",
    "Attribute 2 name","Attribute 2 value(s)","Attribute 2 visible","Attribute 2 global","Attribute 2 default",
    "Attribute 3 name","Attribute 3 value(s)","Attribute 3 visible","Attribute 3 global","Attribute 3 default",
    "Meta: hwp_product_gtin","ID site"
]

def save_to_csv(data, file_name):
    """Ghi dữ liệu ra file CSV."""
    with open(file_name, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(data)
    print(f"✅ Đã lưu {len(data)} dòng vào {file_name}")

# 1. Chuẩn bị danh sách User-Agent thật
USER_AGENTS = [
    # Một vài User-Agent thông dụng của Chrome, Firefox...
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    # bạn có thể thêm list từ fake-useragent
]

# 2. Tạo session với headers mặc định
async def create_session():
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://serenashirt.com/",
        "Connection": "keep-alive",
    }
    # trust_env=True để dùng proxy/setting môi trường nếu có
    return aiohttp.ClientSession(headers=headers, trust_env=True)

# 3. Trước khi crawl, ghé qua trang chủ để lấy cookie phiên
async def init_cookies(session):
    try:
        async with session.get("https://serenashirt.com/", timeout=10) as resp:
            # đọc và bỏ qua nội dung, cookie sẽ được lưu tự động trong session
            await resp.text()
    except Exception as e:
        print("⚠️ Không lấy được cookie từ trang chủ:", e)

# Kiểm tra xem sản phẩm có trong giỏ hàng không

# Phân tích HTML để lấy thông tin sản phẩm
def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    # 1. Lấy name
    h1 = soup.find('h1', class_='product-title product_title entry-title')
    name = h1.get_text(strip=True) if h1 else 'No Title'

    # 2. Lấy list image links chỉ khi class list == ['attachment-woocommerce_thumbnail']
    img_tags = soup.find_all('img', class_='attachment-woocommerce_thumbnail')
    img_links = []
    for img in img_tags:
        classes = img.get('class', [])
        if classes == ['attachment-woocommerce_thumbnail']:
            src = img.get('src')
            if src:
                img_links.append(src)
    img_links_str = ', '.join(img_links)

    return {
        'name': name,
        'img_links_str': img_links_str
    }


# Hàm crawl một trang cụ thể với giới hạn request
async def crawl_page(sem, session, object_id, max_retries=3):
    url = f"https://serenashirt.com/?post_type=prudut&page_id={object_id}"

    async with sem:  # Giới hạn số lượng request đồng thời
        for attempt in range(max_retries):
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 524:
                        print(f"⚠️ Lỗi 524 Timeout - Thử lại {attempt + 1}/{max_retries} cho {object_id}")
                        # await asyncio.sleep(5)
                        continue
                    if response.status == 500:
                        time.sleep(60)
                        print(f"❌ limit request")
                        return None

                    if response.status != 200:
                        print(f"❌ Lỗi HTTP {response.status} - Bỏ qua {object_id}")
                        return None

                    html = await response.text()

                    # Nếu trang lỗi 524 xuất hiện trong nội dung, bỏ qua request
                    if "Error code 524" in html:
                        print(f"⚠️ Trang {object_id} bị lỗi 524 - Bỏ qua.")
                        return None

                    data = parse_html(html)
                    name = data['name']
                    img_links_str = data['img_links_str']

                    sku_prefix = ""  # ví dụ
                    record_idx = object_id - 0  # tuỳ bạn tính
                    description = ""         # tuỳ logic
                    price = ""  

                    row = [
                        "",                                 # ID
                        "simple",                           # Type
                        f"{100000 + 2 * record_idx}",  # SKU
                        name,                               # Name
                        1, 0, "visible", "",                # Published, Is featured?, Visibility, Short desc
                        description,                        # Description
                        "", "",                            # Date sale price starts/ends
                        "taxable", "",                      # Tax status/Class
                        1, "", "", 0, 0,                   # In stock?, Stock, Low stock amt, Backorders, Sold individually
                        "", "", "", "",                    # Weight, Length, Width, Height
                        1, "", "",                         # Allow reviews?, Purchase note, Sale price placeholder
                        price,                             # Regular price (nếu bạn để ngược thì hoán vị)
                        sku_prefix, sku_prefix, "",        # Categories, Tags, Shipping class
                        img_links_str,
                        "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",                     # Images
                        object_id,
                        # phần còn lại là các cột rỗng đến hết
                    ]
                    print(f"✅ {object_id}: {data['name']}")
                    return row
            except asyncio.TimeoutError:
                print(f"⚠️ Request Timeout {object_id} - Thử lại {attempt + 1}/{max_retries}")
                # await asyncio.sleep(5)
            except Exception as e:
                print(f"⚠️ Lỗi khi crawl {object_id} {url}: {e}")
                return None

    print(f"❌ Bỏ qua {object_id} sau {max_retries} lần thử thất bại")
    return None

# Hàm chính để chạy chương trình với giới hạn 30 request đồng thời
async def main():
    start_id = 1562999
    end_id   = 1592999

    sem = asyncio.Semaphore(5)  # Giới hạn 30 request đồng thời
      # 1. Khởi tạo session với headers giả lập trình duyệt
    session = await create_session()

    # 2. Ghé qua trang chủ để thu cookie phiên
    await init_cookies(session)
    tasks = [
        crawl_page(sem, session, pid, max_retries=1)
        for pid in range(start_id, end_id + 1)
    ]
    results = await asyncio.gather(*tasks)
    # async with aiohttp.ClientSession() as session:
    #     tasks = [
    #         crawl_page(sem, session, pid,1) 
    #         for pid in range(start_id, end_id + 1)
    #     ]
    #     results = await asyncio.gather(*tasks)

    rows = [r for r in results if r]
    save_to_csv(rows, "crawled_serenashirt_data_1562999-1592999.csv")

    print("🎉 Crawl hoàn tất!")
    print("📊 Tổng số sản phẩm crawl được:", len([r for r in results if r]))

if __name__ == "__main__":
    asyncio.run(main())