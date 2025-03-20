import requests
import pandas as pd

# 🔹 Thông tin API WooCommerce
BASE_URL = "https://davidress.com/wp-json/wc/v3/products"  # Thay bằng URL website của bạn
CONSUMER_KEY = "ck_140a74832b999d10f1f5b7b6f97ae8ddc25e835a"
CONSUMER_SECRET = "cs_d290713d3e1199c51a22dc1e85707bb24bcce769"
CATEGORY_ID = 364

def get_all_products(category_id):
    """
    Lấy tất cả sản phẩm từ WooCommerce bằng API
    """
    page = 1
    per_page = 100  # Số sản phẩm mỗi lần request (tối đa 100)
    all_products = []

    while True:
        print(f"🔄 Đang lấy dữ liệu trang {page}...")
        response = requests.get(
            f"{BASE_URL}?category={category_id}&per_page={per_page}&page={page}",
            auth=(CONSUMER_KEY, CONSUMER_SECRET)
        )

        if response.status_code == 200:
            products = response.json()
            if not products:
                break  # Nếu không còn sản phẩm, dừng vòng lặp
            all_products.extend(products)
            page += 1
        else:
            print(f"⚠️ Lỗi {response.status_code}: {response.text}")
            break

    print(f"✅ Lấy thành công {len(all_products)} sản phẩm!")
    return all_products

def save_to_excel(products, category_id):
    """
    Xuất danh sách sản phẩm thuộc danh mục ra file Excel
    """
    if not products:
        print("⚠️ Không có sản phẩm nào để lưu!")
        return

    df = pd.DataFrame([
        {
            "Product ID": p["id"],
            "Name": p["name"],
            "Product Link": p["permalink"],
            "List Image Links": ", ".join(img["src"] for img in p.get("images", [])),  # Lấy danh sách ảnh, ngăn cách bởi dấu `,`
            "Price": p["price"],
            "Categories": ", ".join(cat["name"] for cat in p.get("categories", []))  # Lấy danh sách danh mục
        }
        for p in products
    ])

    # Lưu vào file Excel
    file_name = f"products_category_{category_id}.xlsx"
    df.to_excel(file_name, index=False)
    print(f"📂 Đã lưu danh sách sản phẩm vào file `{file_name}`!")

# Lấy danh sách sản phẩm
products_in_category  = get_all_products(CATEGORY_ID)
print('all_products',products_in_category )
# Xuất dữ liệu ra file Excel
save_to_excel(products_in_category , CATEGORY_ID)