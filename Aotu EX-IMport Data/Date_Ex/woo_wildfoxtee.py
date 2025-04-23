import asyncio
from datetime import datetime, timezone
import json
import random
from urllib.parse import parse_qs, urlencode, urlparse
import aiohttp
import nest_asyncio
from bs4 import BeautifulSoup
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials


start_date = datetime(2025, 4, 1, tzinfo=timezone.utc)
end_date = datetime(2025, 4, 16, tzinfo=timezone.utc)

CONCURRENT_LIMIT = 20
START_ID = 380000
END_ID = 400000

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Crawl Data Git\Crawl-Data\credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1c_omcHE3AMkUBxFS1Cckwcw0A-fBX5FV6dbJYn_Jg5s").worksheet("2D")

urls = sheet.col_values(1)[1:]
extra_data = sheet.col_values(2)[1:]
desc_data = sheet.col_values(3)[1:] if len(sheet.col_values(3)) >= 1 else []
price_data = sheet.col_values(4)[1:] if len(sheet.col_values(4)) >= 1 else []

header = ["ID", "Type", "SKU", "Name", "Published", "Is featured?", "Visibility in catalog", "Short description", "Description",
          "Date sale price starts", "Date sale price ends", "Tax status", "Tax class", "In stock?", "Stock", "Low stock amount",
          "Backorders allowed?", "Sold individually?", "Weight (kg)", "Length (cm)", "Width (cm)", "Height (cm)", "Allow customer reviews?",
          "Purchase note", "Sale price", "Regular price", "Categories", "Tags", "Shipping class", "Images",
          "Download limit", "Download expiry days", "Parent", "Grouped products", "Upsells", "Cross-sells",
          "External URL", "Button text", "Position",
          "Attribute 1 name", "Attribute 1 value(s)", "Attribute 1 visible", "Attribute 1 global", "Attribute 1 default",
          "Attribute 2 name", "Attribute 2 value(s)", "Attribute 2 visible", "Attribute 2 global", "Attribute 2 default",
          "Attribute 3 name", "Attribute 3 value(s)", "Attribute 3 visible", "Attribute 3 global", "Attribute 3 default",
          "Meta: hwp_product_gtin"]

headers = {"User-Agent": "Mozilla/5.0"}

async def fetch(session, url):
    try:
        async with session.get(url, timeout=20) as res:
            if res.status != 200:
                return None
            return await res.text()
    except Exception:
        return None
    
def extract_date_published(obj) -> str:
    if isinstance(obj, dict):
        if "datePublished" in obj:
            return obj["datePublished"]
        for value in obj.values():
            result = extract_date_published(value)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = extract_date_published(item)
            if result:
                return result
    return ""

def is_valid_date_published(date_raw: str) -> bool:
    try:
        if isinstance(date_raw, str) and date_raw.isdigit():
            date_pub = datetime.fromtimestamp(int(date_raw))
        elif isinstance(date_raw, str):
            date_pub = datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
        else:
            return False
        return start_date <= date_pub <= end_date
    except Exception:
        return False
    
async def parse_product(sem, session, object_id, record_idx):
    async with sem:
        url = f"https://wildfoxtee.com/?page_id={object_id}"
        html = await fetch(session, url)
        if not html or "Error code 524" in html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find("h1", class_="product-title") or soup.find("h1")
        name = title_tag.text.strip() if title_tag else "N/A"

        # script_tag = soup.find('script', type='application/ld+json')
        # if not script_tag:
        #     return None

        # try:
        #     ld_json = json.loads(script_tag.string)
        #     date_raw = extract_date_published(ld_json)
        #     if not is_valid_date_published(date_raw):
        #         print(f"⏳ Bỏ qua {object_id} – ngày không hợp lệ: {date_raw}")
        #         return None
        # except Exception:
        #     return None

        main_image_tag = soup.select_one('img.skip-lazy')
        main_image = main_image_tag['src'] if main_image_tag and main_image_tag.get("src") else ""

        thumbnail_imgs = [
            img.get("src") for img in soup.find_all("img")
            if img.get("class") == ["attachment-woocommerce_thumbnail"] and img.get("src")
        ]
        all_images = ", ".join(thumbnail_imgs) if thumbnail_imgs else main_image

        print(f"✅ {object_id}: {name},(✅{len(thumbnail_imgs)} ảnh)")
        return [
            "", "simple", f"{extra_data[0]}-{100000 + 2 * record_idx}", name, 1, 0, "visible", "", desc_data[0], "", "", "taxable", "", 1, "", "", 0, 0,
            "", "", "", "", 1, "", "", price_data[0], extra_data[0], extra_data[0], "", all_images,
            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
        ]
    
async def main():
    object_ids = list(range(START_ID, END_ID + 1))
    data = []
    sem = asyncio.Semaphore(CONCURRENT_LIMIT)

    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [
            parse_product(sem, session, oid, idx)
            for idx, oid in enumerate(object_ids)
        ]
        results = await asyncio.gather(*tasks)
        data = [r for r in results if r]

    df = pd.DataFrame(data, columns=header)
    df.to_csv("merged_keeptee_woo_data.csv", index=False, encoding="utf-8-sig")
    print("✅ Đã lưu file merged_keeptee_woo_data.csv")

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
