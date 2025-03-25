import requests
import pandas as pd
from datetime import datetime
import time

config_df = pd.read_excel(r"C:\Crawl Data Git\Crawl-Data\Crawl Data Show Api\DATA JSTST.xlsx")  # ← sửa tên file nếu khác

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

def check_publish_date(webGoLiveDate):
    try:
        if webGoLiveDate:
            # start_idx = webGoLiveDate + len(webGoLiveDate) + 2
            # end_idx = page_source.find(',', start_idx)
            # timestamp_str = page_source[start_idx:end_idx].strip()
            
            # Chuyển Unix timestamp sang datetime
            publish_date = datetime.fromtimestamp(int(webGoLiveDate))
            start_date = datetime(2025, 3, 1, 0, 0, 0)
            end_date = datetime(2025, 3, 23, 0, 0, 0)
            if start_date <= publish_date < end_date:
                return publish_date 
    except Exception as e:
        print(f"Lỗi kiểm tra ngày đăng: {e}")
    return None 

def check_publish_date_start(webGoLiveDate):
    try:
        if webGoLiveDate:
            # start_idx = webGoLiveDate + len(webGoLiveDate) + 2
            # end_idx = page_source.find(',', start_idx)
            # timestamp_str = page_source[start_idx:end_idx].strip()
            
            # Chuyển Unix timestamp sang datetime
            publish_date = datetime.fromtimestamp(int(webGoLiveDate))
            start_date = datetime(2025, 3, 1, 0, 0, 0)
            # end_date = datetime(2025, 2, 19, 0, 0, 0)
            if start_date > publish_date :
                return False 
    except Exception as e:
        print(f"Lỗi kiểm tra ngày đăng: {e}")
    return True

for index, row in config_df.iterrows():
    sku = row.iloc[0]
    url_template = str(row.iloc[2]).strip()
    # headers_json = str(row.iloc[3]).strip()
    product_header = str(row.iloc[3])
    for page in range(1, 1000):
        url = url_template.format(page=page)
        headers = headers_template.copy()
        # headers["referer"] = headers_json
        try:
            response = requests.get(url, headers=headers, cookies=cookies,timeout=10)
            print(f"Trang {page}: Status Code {response.status_code}" , url  )
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "result" in data and "items" in data["result"]:
                        items = data["result"]["items"]
                        print(f"Số sản phẩm trên trang {page}: {len(items)}")
                        if len(items) == 0 : break
                        # Thêm URL đầy đủ cho mỗi sản phẩm
                        for item in items:
                            item["product_url"] = f"{product_header}{item['handle']}"
                            if check_publish_date_start(item["updated_at"]) :
                                date_check = check_publish_date(item["updated_at"]) 
                                if date_check :
                                    item["Date"] = date_check
                                    item["SKU Store"] = sku
                                    data_list.append(item)
                                else : 
                                    continue
                            else : break
                        # data_list.extend(items)
                    else:
                        print("Không tìm thấy mục 'items' trong dữ liệu trả về.")
                        break  # Dừng nếu không còn dữ liệu
                except Exception as e:
                    print(f"Lỗi xử lý JSON trên trang {page}: {e}")
                    break
            else:
                print(f"Lỗi khi lấy dữ liệu trang {page}")
                break
                # time.sleep(10)
            
            # time.sleep(1)  # Tránh bị chặn vì gửi request quá nhanh
        except Exception as e:
                print(f"Lỗi xử lý JSON trên trang {page}: {e}")
                time.sleep(10)

    print(f"Tổng số sản phẩm lấy được: {len(data_list)}")

# Lưu vào file Excel
if data_list:
    df = pd.DataFrame(data_list)
    df.to_excel("products_data.xlsx", index=False)
    print("Dữ liệu đã được lưu vào products_data.xlsx")
else:
    print("Không có dữ liệu để lưu.")
