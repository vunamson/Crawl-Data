import os
import asyncio
import pandas as pd
import cloudscraper
import json
from openpyxl import Workbook
from bs4 import BeautifulSoup
from slugify import slugify
from playwright.async_api import async_playwright

# 📁 Ghi dữ liệu vào file Excel sau khi crawl xong
def save_to_excel(data, file_name):
    wb = Workbook()
    ws = wb.active
    ws.append(["store", "title", "product_link", "image_link", "date_published", "is_order", "slug", "object_id", "object_name"])
    
    for row in data:
        ws.append(list(row.values()))
    
    wb.save(file_name)

def is_product_in_cart(soup):
    try:
        cart_script_tag = soup.find('script', string=lambda t: t and 'wpmDataLayer' in t)
        if not cart_script_tag:
            return False

        cart_data_str = cart_script_tag.string.split('window.wpmDataLayer = ')[-1].strip().rstrip(';')
        if not cart_data_str:
            return False

        cart_data = json.loads(cart_data_str)
        cart_items = cart_data.get("cart", {}).get("items", [])
        return len(cart_items) > 0
    except json.JSONDecodeError:
        print("⚠️ Lỗi JSON khi kiểm tra giỏ hàng - Có thể dữ liệu bị trống hoặc không hợp lệ.")
        return False
    except Exception as e:
        print(f"⚠️ Lỗi khi kiểm tra giỏ hàng: {e}")
        return False

# 🔎 Phân tích HTML để lấy thông tin sản phẩm
def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('h1')
    title_text = title.text.strip() if title else 'No Title'

    script_tag = soup.find('script', {'class': 'rank-math-schema-pro', 'type': 'application/ld+json'})
    date_published, product_link, image_link = "Not Found", "Not Found", "Not Found"
    is_order = is_product_in_cart(soup)
    if script_tag:
        try:
            data = json.loads(script_tag.string)
            for item in data.get("@graph", []):
                if item.get("@type") == "ItemPage":
                    date_published = item.get("datePublished", "Not Found")
                    product_link = item.get("url", "Not Found")
                if item.get("@type") == "Product":
                    images = item.get("image", [])
                    if isinstance(images, list) and images:
                        image_link = images[0]
        except json.JSONDecodeError:
            print("⚠️ Lỗi JSON khi phân tích dữ liệu sản phẩm.")

    return {
        'title': title_text,
        'product_link': product_link,
        'image_link': image_link,
        'date_published': date_published,
        'is_order': is_order
    }

# 🌐 Hàm tải trang web bằng CloudScraper hoặc Playwright
async def fetch_page(object_id):
    url = f"https://keeptee.com/?attachment_id={object_id}"

    try:
        # 🟢 1. Thử tải trang bằng CloudScraper trước (nhanh hơn)
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url)
        if response.status_code == 200:
            data = parse_html(response.text)
            return data

        print(f"⚠️ CloudScraper thất bại cho {object_id}, thử lại với Playwright...")

        # 🟢 2. Nếu CloudScraper thất bại, dùng Playwright để mô phỏng trình duyệt
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=10000)
            html = await page.content()
            data = parse_html(html)
            await browser.close()
            return data

    except Exception as e:
        print(f"⚠️ Lỗi khi tải trang {object_id}: {e}")
        return None

# 🚀 Hàm chính để chạy chương trình
async def main():
    start, end = 1736700, 1736800
    object_ids = list(range(start, end + 1))

    tasks = [fetch_page(object_id) for object_id in object_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Lọc ra kết quả hợp lệ và ghi vào file Excel sau khi crawl xong
    valid_results = []
    for idx, res in enumerate(results):
        if res:
            object_id = object_ids[idx]
            slug = slugify(res['title'], allow_unicode=True).lower()
            valid_results.append({
                'store': 'keeptee.com',
                'title': res['title'],
                'product_link': res['product_link'],
                'image_link': res['image_link'],
                'date_published': res['date_published'],
                'is_order': res['is_order'],  # Chưa kiểm tra giỏ hàng
                'slug': slug,
                'object_id': object_id,
                'object_name': 'product'
            })

    save_to_excel(valid_results, "crawled_keeptee_data.xlsx")

    print("🎉 Crawl hoàn tất!")
    print("📊 Tổng số sản phẩm crawl được:", len(valid_results))

if __name__ == "__main__":
    asyncio.run(main())
