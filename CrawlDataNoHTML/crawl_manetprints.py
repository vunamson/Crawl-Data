import os
import asyncio
import aiohttp
import pandas as pd
from openpyxl import Workbook
from bs4 import BeautifulSoup
from slugify import slugify
import json
import time

# Ghi dữ liệu vào file Excel
def save_to_excel(data, file_name):
    wb = Workbook()
    ws = wb.active
    ws.append(["store", "title", "product_link", "image_link", "date_published", "slug", "object_id", "object_name", "type", "price"])

    for row in data:
        ws.append(list(row.values()))

    wb.save(file_name)

# Kiểm tra xem sản phẩm có trong giỏ hàng không

# Phân tích HTML để lấy thông tin sản phẩm
def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    title = soup.find('h1')
    title_text = title.text.strip() if title else 'No Title'

    script_tag = soup.find('script', {'type': 'application/ld+json', 'class': 'saswp-schema-markup-output'})
    date_published, product_link, image_link, price, sku, p_type = "Not Found", "Not Found", "Not Found", "Not Found", "", "unknown"
    
    image_links = []
    for img_tag in soup.find_all('img'):
        classes = img_tag.get('class', [])
        if any("attachment-300x300" in cls for cls in classes):
            src = img_tag.get('src')
            if src:
                image_links.append(src)

    image_link_jerssey = ",".join(image_links) if image_links else ""
    
    if script_tag:
        try:
            data = json.loads(script_tag.string)
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Product":
                        sku = item.get("sku", "")
                        price = item.get("offers", {}).get("price", "Not Found")
                        product_link = item.get("url", product_link)
                        images = item.get("image", [])
                        if isinstance(images, list) and images:                                
                            image_link_hoodie = images[0].get("url", images[0] if  isinstance(images[0], str)   else "Not Found")
                    elif item.get("@type") == "ImageObject":
                        date_published = item.get("datePublished", date_published)
                        product_link = item.get("url", product_link)
        except json.JSONDecodeError:
            print("Error decoding JSON in script tag")

    if "MLB" in sku:
        p_type = "jersey"
    elif "SPO" in sku:
        p_type = "hoodie"

    return {
        'title': title_text,
        'product_link': product_link,
        'image_link': image_link_jerssey if image_link_jerssey else image_link_hoodie,
        'date_published': date_published,
        'price': price,
        'type': p_type
    }

# Hàm crawl một trang cụ thể với giới hạn request
async def crawl_page(sem, session, object_id, max_retries=1):
    url = f"https://us.manetprints.co/?attachment_id={object_id}"

    async with sem:
        for attempt in range(max_retries):
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 524:
                        print(f"⚠️ Lỗi 524 Timeout - Thử lại {attempt + 1}/{max_retries} cho {object_id}")
                        await asyncio.sleep(5)
                        continue

                    if response.status != 200:
                        print(f"❌ Lỗi HTTP {response.status} - Bỏ qua {object_id}")
                        return None

                    html = await response.text()
                    if "Error code 524" in html:
                        print(f"⚠️ Trang {object_id} bị lỗi 524 - Bỏ qua.")
                        return None

                    data = parse_html(html)
                    slug = slugify(data['title'], allow_unicode=True).lower()

                    result = {
                        'store': 'manetprints.com',
                        'title': data['title'],
                        'product_link': data['product_link'],
                        'image_link': data['image_link'],
                        'date_published': data['date_published'],
                        'slug': slug,
                        'object_id': object_id,
                        'object_name': 'product',
                        'type': data['type'],
                        'price': data['price']
                    }
                    print(f"✅ {object_id}: {data['title']}")
                    return result
            except asyncio.TimeoutError:
                print(f"⚠️ Request Timeout {object_id} - Thử lại {attempt + 1}/{max_retries}")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"⚠️ Lỗi khi crawl {object_id} {url}: {e}")
                return None

    print(f"❌ Bỏ qua {object_id} sau {max_retries} lần thử thất bại")
    return None

# Hàm chính để chạy chương trình
async def main():
    start, end = 128000, 228000
    object_ids = list(range(start, end + 1))
    sem = asyncio.Semaphore(5)

    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(crawl_page(sem, session, object_id)) for object_id in object_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    filtered_results = [r for r in results if isinstance(r, dict) and r.get('type') != 'unknown']

    # Loại bỏ trùng lặp theo product_link và image_link
    seen_links = set()
    unique_results = []
    for item in filtered_results:
        key = (item['product_link'])
        if key not in seen_links:
            seen_links.add(key)
            unique_results.append(item)

    save_to_excel(unique_results, "crawled_manetprints_datav2.xlsx")

    print("🎉 Crawl hoàn tất!")
    print("📊 Tổng số sản phẩm crawl được:", len(unique_results))

if __name__ == "__main__":
    asyncio.run(main())
