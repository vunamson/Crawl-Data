import requests
import pandas as pd
import time
from requests.exceptions import ConnectionError, Timeout
from urllib3.exceptions import ProtocolError


BASE_URL       = "https://noaweather.com/wp-json/wc/v3/products"
CK, CS         = "ck_ad85bc0fe8241b2db94a65ec9b971c402fda6749", "cs_3ebdbead13332abcdd04d3557be68f834395ec18"
PER_PAGE       = 100   # giảm số sản phẩm mỗi request
MAX_RETRIES    = 3
BACKOFF_FACTOR = 5    # giây tăng dần
# 🔹 Thông tin API WooCommerce
# BASE_URL = "https://noaweather.com/wp-json/wc/v3/products"
# CONSUMER_KEY = "ck_ad85bc0fe8241b2db94a65ec9b971c402fda6749"
# CONSUMER_SECRET = "cs_3ebdbead13332abcdd04d3557be68f834395ec18"

session = requests.Session()
session.auth    = (CK, CS)
session.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def get_all_products():
    """
    Lấy tất cả sản phẩm từ WooCommerce bằng API (không lọc theo category)
    """
    page = 1
    all_products = []

    while True:
        print(f"🔄 Lấy trang {page} (per_page={PER_PAGE})…")
        for attempt in range(1, MAX_RETRIES+1):
            try:
                resp = session.get(
                    BASE_URL,
                    params={"per_page": PER_PAGE, "page": page},
                    timeout=(5, 30)
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except (ConnectionError, ProtocolError, Timeout) as e:
                wait = BACKOFF_FACTOR * attempt
                print(f"⚠️ Lỗi kết nối (lần {attempt}): {e}. Đợi {wait}s rồi thử lại…")
                time.sleep(wait)
        else:
            print("❌ Retry vượt quá giới hạn, thoát vòng lặp.")
            return all_products

        if not data:
            print("✅ Hết sản phẩm, kết thúc.")
            break

        all_products.extend(data)
        page += 1
        time.sleep(10)  # đợi lâu hơn giữa các trang

    print(f"✅ Tổng {len(all_products)} sản phẩm.")
    return all_products

def save_to_excel(products):
    """
    Xuất danh sách sản phẩm ra file Excel
    """
    if not products:
        print("⚠️ Không có sản phẩm nào để lưu!")
        return

    df = pd.DataFrame([
        {
            "Product ID": p["id"],
            "Name": p["name"],
            "Product Link": p["permalink"],
            "List Image Links": ", ".join(img["src"] for img in p.get("images", [])),
            "Price": p["price"],
            "Categories": ", ".join(cat["name"] for cat in p.get("categories", [])),
            "Category IDs": ", ".join(str(cat["id"]) for cat in p.get("categories", [])),
            "SKU": p["sku"],
            "Description": p["description"],
        }
        for p in products
    ])

    df = df[df["List Image Links"] != ""]  # Bỏ những sản phẩm không có ảnh

    file_name = f"all_products_noaweather.xlsx"
    df.to_excel(file_name, index=False)
    print(f"📂 Đã lưu danh sách sản phẩm vào file `{file_name}`!")

# Gọi hàm để lấy và lưu dữ liệu
products = get_all_products()
save_to_excel(products)
