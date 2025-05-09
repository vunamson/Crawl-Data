import requests
import pandas as pd
import time

# 🔹 Thông tin API WooCommerce
BASE_URL = "https://luxinshoes.com/wp-json/wc/v3/products"
CONSUMER_KEY = "ck_8cefa1d518006ccaee178f71e452757e91d20b23"
CONSUMER_SECRET = "cs_05f41803467c28748d41d970a4fafc6144bbdb87"

def get_all_products():
    """
    Lấy tất cả sản phẩm từ WooCommerce bằng API (không lọc theo category)
    """
    page = 1
    per_page = 100  # Số sản phẩm mỗi lần request (tối đa 100)
    all_products = []

    while True:
        print(f"🔄 Đang lấy dữ liệu trang {page}...")
        response = requests.get(
            f"{BASE_URL}?per_page={per_page}&page={page}",
            auth=(CONSUMER_KEY, CONSUMER_SECRET)
        )
        time.sleep(20)
        page += 1
        if response.status_code == 200:
            try:
                products = response.json()
                if not products:
                    print(f"✅ Không còn sản phẩm ở trang {page}, kết thúc.")
                    break
                all_products.extend(products)
            except ValueError:
                print(f"❌ Không thể phân tích JSON tại trang {page}. Nội dung trả về:\n{response.text}")
                continue
        else:
            print(f"⚠️ Lỗi {response.status_code}: {response.text}")
            continue

    print(f"✅ Lấy thành công {len(all_products)} sản phẩm!")
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

    file_name = f"all_products_luxinshoes.xlsx"
    df.to_excel(file_name, index=False)
    print(f"📂 Đã lưu danh sách sản phẩm vào file `{file_name}`!")

# Gọi hàm để lấy và lưu dữ liệu
products = get_all_products()
save_to_excel(products)
