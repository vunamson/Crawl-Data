import os
import asyncio
import aiohttp
import pandas as pd
from openpyxl import load_workbook, Workbook
from bs4 import BeautifulSoup
from slugify import slugify

# Đọc dữ liệu từ file Excel
def read_excel_data(file_name):
    if os.path.exists(file_name):
        return pd.read_excel(file_name).to_dict(orient='records')
    return []

# Kiểm tra xem slug có tồn tại trong dữ liệu hay không
def is_slug_exists(data, slug):
    return any(item['slug'] == slug for item in data)

# Ghi dữ liệu vào file Excel
def append_to_excel(data, file_name):
    existing_data = read_excel_data(file_name)
    new_data = [item for item in data if not is_slug_exists(existing_data, item['slug'])]
    
    if new_data:
        existing_data.extend(new_data)
        df = pd.DataFrame(existing_data)
        df.to_excel(file_name, index=False)

# Phân tích HTML để lấy tiêu đề
def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    # Xuất HTML ra file JavaScript
    with open("soup_output.js", "w", encoding="utf-8") as f:
        f.write(f"const soup = `{soup}`;")
    print('soup',soup)
    title = soup.find('h1')
    return {'title': title.text.strip() if title else 'No Title'}

# Hàm crawl một trang cụ thể
async def crawl_page(session, object_id):
    url = f"https://keeptee.com/?attachment_id={object_id}"
    
    try:
        async with session.get(url) as response:
            html = await response.text()
            data = parse_html(html)
            slug = slugify(data['title'], allow_unicode=True).lower()  # Sửa lỗi `unicode`
            result = {
                'store': 'keeptee.com',
                'title': data['title'],
                'link': f"https://keeptee.com/product/{slug}",
                'slug': slug,
                'object_id': object_id,
                'object_name': 'product'
            }
            
            print(result)
            # append_to_excel([result], "crawled_keeptee_data.xlsx")
            return result
    except Exception as e:
        print(f"Error crawling page {object_id} {url}: {e}")
        return None

# Hàm chính để chạy chương trình
async def main():
    start, end = 1736766, 1736766
    object_ids = list(range(start, end + 1))
    
    async with aiohttp.ClientSession() as session:
        tasks = [crawl_page(session, object_id) for object_id in object_ids]
        results = await asyncio.gather(*tasks)
        
        print("Crawling completed!")
        print("Results:", results)

if __name__ == "__main__":
    asyncio.run(main())
