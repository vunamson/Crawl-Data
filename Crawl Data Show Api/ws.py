import requests
import pandas as pd
import time

url_template = "https://www.jerseyteamsstores.com/api/catalog/next/products.json?page={}&limit=200&minimal=true&infinite=false&q=hoodie&sort=sold"

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

data_list = []

for page in range(1, 220):
    url = url_template.format(page)
    headers = headers_template.copy()
    headers["referer"] = f"https://www.jerseyteamsstores.com/search?page={page}&limit=200&minimal=true&q=hoodie&infinite=false&sort=sold&sort_field=most_related&sort_direction=desc"
    
    response = requests.get(url, headers=headers, cookies=cookies,timeout=10)
    print(f"Trang {page}: Status Code {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            if "result" in data and "items" in data["result"]:
                items = data["result"]["items"]
                print(f"Số sản phẩm trên trang {page}: {len(items)}")
                
                # Thêm URL đầy đủ cho mỗi sản phẩm
                for item in items:
                    item["product_url"] = f"https://www.jerseyteamsstores.com/products/{item['handle']}"
                
                data_list.extend(items)
            else:
                print("Không tìm thấy mục 'items' trong dữ liệu trả về.")
                break  # Dừng nếu không còn dữ liệu
        except Exception as e:
            print(f"Lỗi xử lý JSON trên trang {page}: {e}")
    else:
        print(f"Lỗi khi lấy dữ liệu trang {page}")
    
    time.sleep(1)  # Tránh bị chặn vì gửi request quá nhanh

print(f"Tổng số sản phẩm lấy được: {len(data_list)}")

# Lưu vào file Excel
if data_list:
    df = pd.DataFrame(data_list)
    df.to_excel("products_data.xlsx", index=False)
    print("Dữ liệu đã được lưu vào products_data.xlsx")
else:
    print("Không có dữ liệu để lưu.")
