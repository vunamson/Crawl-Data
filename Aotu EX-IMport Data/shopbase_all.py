import requests
import pandas as pd
from requests.adapters import HTTPAdapter, Retry
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === Cấu hình Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Crawl Data Git\Crawl-Data\credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1c_omcHE3AMkUBxFS1Cckwcw0A-fBX5FV6dbJYn_Jg5s").worksheet("Jerseyteamsstores")


df = pd.DataFrame({
    "url_template": sheet.col_values(1)[1:],  # cột A
    "sku_prefix":   sheet.col_values(2)[1:],  # cột B
    "description":  sheet.col_values(3)[1:],  # cột C
    "price":        sheet.col_values(4)[1:],  # cột D
    "categories" : sheet.col_values(5)[1:],  # cột E
    "tag" : sheet.col_values(6)[1:],  # cột F
    "base_domain":  sheet.col_values(7)[1:],  # cột G
    "remove_words":  sheet.col_values(8)[1:],  # cột H: các từ cần xóa, ngăn cách bằng dấu ','
})

session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

# urls = sheet.col_values(1)[1:]
# extra_data = sheet.col_values(2)[1:]
# desc_data = sheet.col_values(3)[1:] if len(sheet.col_values(3)) >= 1 else []
# price_data = sheet.col_values(4)[1:] if len(sheet.col_values(4)) >= 1 else []
# header_url = sheet.col_values(6)[1:] if len(sheet.col_values(6)) >= 1 else []
# base_domain_list = sheet.col_values(7)[1:] if len(sheet.col_values(7)) >= 1 else []

# === Cấu hình request ===
headers_template = {
    "accept": "*/*",
    "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
    "content-type": "application/json",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "x-shopbase-checkout-token": "6c1fac36640d45d9af27b003f86e2e86",
    "x-shopbase-session-id": "FtCoecN3XiuDuRuUluybT"
}

cookies = {
    "X-Buyer-AB-Test-Checked": "true",
    "_fbp": "fb.1.1741945018824.702834164788775582",
    "_gid": "GA1.2.987927778.1741945019",
    "X-Global-Market-Currency": "AUD",
    "X-Global-Market": "AU",
    "_gcl_au": "1.1.1606874354.1741945019.303658258.1742001523.1742001803",
    "_ga_JEN2K57V1W": "GS1.1.1742001359.2.1.1742002074.59.0.0",
    "_ga": "GA1.2.245994788.1741945019",
    "_gat_gtag_UA_256447824_1": "1"
}

# === Header CSV theo chuẩn bạn yêu cầu ===
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

results = []

# === Bắt đầu crawl từng URL ===
for _, row in df.iterrows():
    url_template = str(row.iloc[0]).strip()
    sku_prefix    = str(row.iloc[1]).strip() or "SKU"
    description   = str(row.iloc[2]).strip()
    price         = str(row.iloc[3]).strip() or "0"
    categories = str(row.iloc[4]).strip()
    tag = str(row.iloc[5]).strip()
    base_domain   = str(row.iloc[6]).strip()
    # lấy danh sách từ cần loại bỏ, split theo dấu phẩy
    to_remove = [w.strip() for w in row["remove_words"].split(",") if w.strip()]

    print(f"🔍 Bắt đầu crawl: {sku_prefix} - {url_template}")
    
    for page in range(1, 2100):
        url = url_template.format(page=page)
        print('dang crawl url -------' , url)
        try:
            # url = url_template.format(page=page)
            response = session.get(url, headers=headers_template, cookies=cookies, timeout=10)
            print(f"[{sku_prefix}] Trang {page}: Status {response.status_code}")

            if response.status_code != 200:
                print('❌ Lỗi kết nối thất bại với status {response.status_code}')
                continue

            data = response.json()
            items = data.get("result", {}).get("items", [])
            if not items:
                break

            for record_idx, item in enumerate(items):
                prod_id = item.get("id")
                rec_url = f"{base_domain}/api/recsys/cross-sell.json?product_id={prod_id}"
                rec_resp = session.get(rec_url, headers=headers_template, cookies=cookies, timeout=10)
                rec_products = rec_resp.json().get("products", [])
                detail = next((p for p in rec_products if p.get("id") == prod_id), None)

                if detail:
                    name = detail.get("title", item.get("title", ""))
                    for w in to_remove:
                        name = name.replace(w, "")
                    name = name.strip()
                    images = detail.get("images", [])
                else:
                    name = item.get("title", "")
                    images = item.get("images", [])

                img_links = [img.get("src") for img in images if img.get("src")]
                img_links_str = ", ".join(img_links)
                print(f"✅ {name} ({len(img_links)} ảnh)")
                # Append dữ liệu theo format yêu cầu
                results.append([
                    "", "simple",
                    f"{sku_prefix}-{100000 + 2 * (record_idx + len(results))}",
                    name, 1, 0, "visible", "", description, "", "", "taxable", "", 1, "", "", 0, 0,
                    "", "", "", "", 1, "", "", price, categories, tag, "", img_links_str,
                    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
                ])
            # time.sleep()
        except Exception as e:
            print(f"❌ Lỗi khi xử lý {url} trang {page}: {e}")
            break

# === Xuất file Excel ===
if results:
    df = pd.DataFrame(results, columns=header)
    df.to_csv("shopbase_jerseyteamsstores_all.csv", index=False, encoding="utf-8-sig")
    print("✅ Dữ liệu đã được lưu vào racame_output.csv")
else:
    print("⚠️ Không có dữ liệu để lưu.")
