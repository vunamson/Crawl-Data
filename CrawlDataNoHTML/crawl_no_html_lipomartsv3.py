import os
import asyncio
import aiohttp
import pandas as pd
from openpyxl import Workbook
from bs4 import BeautifulSoup
from slugify import slugify
import json
from datetime import datetime


# Ghi dữ liệu vào file Excel
def save_to_excel(data, file_name):
    wb = Workbook()
    ws = wb.active
    ws.append(["store", "title", "product_link", "image_link", "date", "sku"])
    
    for row in data:
        ws.append(list(row.values()))
    
    wb.save(file_name)

# Kiểm tra xem sản phẩm có trong giỏ hàng không
def is_product_in_cart(soup):
    try:
        cart_script_tag = soup.find('script', string=lambda t: t and 'wpmDataLayer' in t)
        if not cart_script_tag:
            return False

        cart_data_str = cart_script_tag.string.split('window.wpmDataLayer = ')[-1].strip().rstrip(';')
        cart_data = json.loads(cart_data_str)
        cart_items = cart_data.get("cart", {}).get("items", [])
        return len(cart_items) > 0
    except Exception as e:
        print(f"Lỗi khi kiểm tra giỏ hàng: {e}")
        return False

# Phân tích HTML để lấy thông tin sản phẩm
def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('h1')
    title_text = title.text.strip() if title else 'No Title'

    script_tag = soup.find('script', type="application/ld+json")
    sku, date_published = "Not Found", "Not Found"
    image_links = []

    if script_tag:
        try:
            data = json.loads(script_tag.string)
            if isinstance(data, dict) and data.get("@type") == "Product":
                # Lấy tên sản phẩm từ dữ liệu JSON
                title_text = data.get("name", title_text)
                # Lấy sku và chuyển đổi date
                text = data.get("sku", "Not Found")
                sku = text.split("_")[0]
                date_string =  str(text.split("_")[1])[:8]
                print('date_string' ,date_string)
                if date_string:
                    try:
                        date_obj = datetime.strptime(date_string, '%Y%m%d')
                        date_published = date_obj.strftime('%Y/%m/%d')
                    except ValueError:
                        date_published = "Invalid Date"

                # Lấy tất cả các ảnh
                img_tags = soup.find_all('img', class_="sgub-product-image-main")
                image_links = img_tags[0].get('data-src') if img_tags else ""
        except json.JSONDecodeError:
            print("Lỗi giải mã JSON trong thẻ script")
    product_link = soup.find("link", rel="canonical")["href"] if soup.find("link", rel="canonical") else None
    if product_link : 
        return {
            'title': title_text,
            'product_link': product_link,
            'image_link': image_links if image_links else '',
            'date_published': date_published,
            'sku': sku,
        }

# Hàm crawl một trang cụ thể với giới hạn request
async def crawl_page(sem, session, object_id, max_retries=1):
    url = f"https://lipomarts.com/?attachment_id={object_id}"

    async with sem:  # Giới hạn số lượng request đồng thời
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

                    # Nếu trang lỗi 524 xuất hiện trong nội dung, bỏ qua request
                    if "Error code 524" in html:
                        print(f"⚠️ Trang {object_id} bị lỗi 524 - Bỏ qua.")
                        return None

                    data = parse_html(html)
                    slug = slugify(data['title'], allow_unicode=True).lower()
                    if data : 
                        result = {
                            'store': 'lipomarts.com',
                            'title': data['title'],
                            'product_link': data['product_link'],
                            'image_link': data['image_link'],
                            'date_published': data['date_published'],
                            'sku': data['sku'],
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


# Hàm chính để chạy chương trình với giới hạn 30 request đồng thời
async def main():
    start, end = 1210000, 1220000
    object_ids = list(range(start, end + 1))

    # Giới hạn số luồng request (có thể thay đổi giá trị này để điều chỉnh số lượng request đồng thời)
    num_of_concurrent_requests = 5  # Điều chỉnh số lượng request đồng thời tại đây
    sem = asyncio.Semaphore(num_of_concurrent_requests)

    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(crawl_page(sem, session, object_id)) for object_id in object_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_results = [r for r in results if r]
    save_to_excel(valid_results, "crawled_lipomarts_datav2-28-03.xlsx")

    print("🎉 Crawl hoàn tất!")
    print("📊 Tổng số sản phẩm crawl được:", len([r for r in results if r]))

if __name__ == "__main__":
    asyncio.run(main())
