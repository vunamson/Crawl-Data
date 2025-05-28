import asyncio
import random
import re
from urllib.parse import parse_qs, urlencode, urlparse
from datetime import datetime, timezone
import json
import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiohttp import ClientTimeout

# === Cấu hình Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Crawl Data Git\Crawl-Data\credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1c_omcHE3AMkUBxFS1Cckwcw0A-fBX5FV6dbJYn_Jg5s").worksheet("CRAWL")

urls = sheet.col_values(1)[1:]
extra_data = sheet.col_values(2)[1:]
desc_data = sheet.col_values(3)[1:] if len(sheet.col_values(3)) >= 1 else []
price_data = sheet.col_values(4)[1:] if len(sheet.col_values(4)) >= 1 else []
categories = sheet.col_values(5)[1:] if len(sheet.col_values(5)) >= 1 else []
tag = sheet.col_values(6)[1:] if len(sheet.col_values(6)) >= 1 else []
remote_words = sheet.col_values(7)[1:] if len(sheet.col_values(6)) >= 1 else []

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


start_date = datetime(2025, 3, 1, tzinfo=timezone.utc)
end_date = datetime(2025, 4, 18, tzinfo=timezone.utc)

async def fetch(session, url):
    async with semaphore:
        try:
            async with session.get(url, timeout=20, allow_redirects=True) as res:
                final_url = str(res.url)
                if final_url != url:
                    print(f"⚠️ Redirected from {url} → {final_url} — dừng crawl.")
                    return None
                return await res.text() if res.status == 200 else None
        except Exception as e:
            print(f"❌ {url} - {e}")
            return None


def is_valid_date_published(date_raw: str) -> bool:
    """
    Kiểm tra datePublished có nằm trong khoảng thời gian hợp lệ hay không.
    Hỗ trợ cả ISO format và timestamp dạng số nguyên.
    """
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
    
def extract_date_published(obj) -> str:
    """
    Duyệt tất cả đối tượng JSON để tìm datePublished (dù nằm trong list, @graph, hay object).
    Trả về date_raw dạng string hoặc "" nếu không tìm thấy.
    """
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

def build_paged_url(category_url, page):
    parsed = urlparse(category_url)
    base_path = parsed.path.rstrip('/')
    query = parse_qs(parsed.query)
    query_str = f"?{urlencode(query, doseq=True)}" if query else ""

    if page == 1:
        return f"{parsed.scheme}://{parsed.netloc}{base_path}/{query_str}"
    else:
        return f"{parsed.scheme}://{parsed.netloc}{base_path}/page/{page}/{query_str}"

async def get_all_product_links(session, category_url):
    product_links = []
    page = 1
    while True:
        paged_url = build_paged_url(category_url, page)

        print(f"🔎 Fetching: {paged_url}")
        html = await fetch(session, paged_url)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        links_no_class = soup.select("a[aria-label]:not([class])")
        link_class = soup.select("a.woocommerce-LoopProduct-link")
        links = links_no_class if len(links_no_class) > 0 else link_class
        new_links = [a.get("href") for a in links if a.get("href")]

        # Dừng nếu không có link mới
        if not new_links or set(new_links).issubset(set(product_links)):
            break

        product_links.extend(new_links)
        page += 1

    return list(set(product_links))

def clean_image_url(url):
    return re.sub(r'-\d{2,4}x\d{2,4}(?=\.(jpg|png|jpeg|webp))', '', url)

async def parse_product(session, url, sku_prefix, description, price, record_idx,categories_idx,tag_idx,to_remove):
    html = await fetch(session, url)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1", class_="product-title")
    if not title:
        title = soup.find("h1", class_="product_title")

    name = title.text.strip() if title else "N/A"
    for w in to_remove:
        name = name.replace(w, "")
    name = name.strip()


    json_data_list = soup.find_all("script", type="application/ld+json")
    if not json_data_list:
        print(f"⚠️ Không tìm thấy ld+json trong {url}")
        return None
    check_date = None
    for json_data in json_data_list:
        try:
            ld_json = json.loads(json_data.string)
            date_raw = extract_date_published(ld_json)
            print('date_raw',date_raw)
            check_date = is_valid_date_published(date_raw)
            if not check_date:
                print(f"⏳ Bỏ qua vì ngoài khoảng thời gian: {url} ({date_raw})")
                continue
            else : break
        except Exception as e:
            print(f"⚠️ Lỗi phân tích datePublished ở {url} - {e}")
            return None
    
    if not check_date : return None

    # Lấy ảnh chính nếu có
    image_main = soup.select_one('img.skip-lazy')
    main_image = image_main['src'] if image_main and image_main.get("src") else ""

    # Lấy tất cả ảnh phụ
    # img_elements = [
    #     img for img in soup.find_all("img")
    #     if img.get("class") == ["attachment-woocommerce_thumbnail"]
    # ]

    img_urls = []

    for script_tag in soup.find_all("script", type="application/ld+json", class_="rank-math-schema-pro"):
        try:
            data = json.loads(script_tag.string)
            if "@graph" in data:
                for item in data["@graph"]:
                    if item.get("@type") == "Product" and "image" in item:
                        images = item["image"]
                        if isinstance(images, list):
                            for img in images:
                                if isinstance(img, dict) and img.get("@type") == "ImageObject" and "url" in img:
                                    img_urls.append(img["url"])
                        elif isinstance(images, dict) and "url" in images:
                            img_urls.append(images["url"])
        except Exception as e:
            print(f"Error parsing JSON-LD: {e}")

    if not img_urls:
        for script_tag in soup.find_all("script", type="application/ld+json", class_="rank-math-schema"):
            try:
                data = json.loads(script_tag.string)
                if "@graph" in data:
                    for item in data["@graph"]:
                        if item.get("@type") == "Product" and "image" in item:
                            images = item["image"]
                            if isinstance(images, list):
                                for img in images:
                                    if isinstance(img, dict) and img.get("@type") == "ImageObject" and "url" in img:
                                        img_urls.append(img["url"])
                            elif isinstance(images, dict) and "url" in images:
                                img_urls.append(images["url"])
            except Exception as e:
                print(f"Error parsing JSON-LD: {e}")

    # Nếu không có URL nào trong JSON-LD, fallback sang thẻ <img>
    if not img_urls:
        img_elements = soup.find_all("img", class_="attachment-woocommerce_thumbnail",alt = "")
        img_urls = [img.get("src") for img in img_elements if img.get("src")]


    img_links = [clean_image_url(link) for link in img_urls]

    # Ưu tiên ảnh phụ, nếu không có dùng ảnh chính
    img_links_str = ", ".join(img_links) if img_links else main_image
    print(f"✅ {name} ({len(img_links)} ảnh)")
    return [
        "", "simple", f"{sku_prefix}-{100000 + 2 * record_idx}", name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
        "", "", "", "", 1, "", "", price, categories_idx, tag_idx, "", img_links_str,
        "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",""
    ]

async def crawl_all():
    timeout = ClientTimeout(total=30)
    async with aiohttp.ClientSession(headers=headers,timeout=timeout) as session:
        tasks = []
        for idx, cat_url in enumerate(urls):
            sku_prefix = extra_data[idx] if idx < len(extra_data) else "SKU"
            description = desc_data[idx] if idx < len(desc_data) else ""
            price = price_data[idx] if idx < len(price_data) else "0"
            categories_idx = categories[idx] if idx < len(price_data) else ""
            tag_idx = tag[idx] if idx < len(price_data) else ""
            to_remove = [w.strip() for w in remote_words[idx].split(",") if w.strip()]
            print(f"📂 Crawling category: {cat_url}")
            product_links = await get_all_product_links(session, cat_url)
            print(f"🔗 Found {len(product_links)} product links.")

            for record_idx, link in enumerate(product_links):
                tasks.append(parse_product(session, link, sku_prefix, description, price, record_idx,categories_idx,tag_idx,to_remove))

        for coro in asyncio.as_completed(tasks):
            try:
                row = await coro
                if row:
                    data.append(row)
            except Exception as e:
                print(f"❗️ Lỗi khi parse product: {e}")

    df = pd.DataFrame(data, columns=header)
    df.to_csv("woo_products_aiohttp_date.csv", index=False, encoding="utf-8-sig")
    print("🎉 DONE! Data saved to woo_products_aiohttp.csv")

asyncio.run(crawl_all())
