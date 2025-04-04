import asyncio
import aiohttp
import json
import pandas as pd

url = "https://racame.shop/api/recsys/cross-sell.json"
headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "priority": "u=1, i",
    "referer": "https://racame.shop/collections/nfl/products/davante-adams-17-las-vegas-raiders-women-s-game-jersey-black",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "x-lang": "en-us",
    "x-shopbase-checkout-token": "14cd7502b11446a7a77c14387009f986",
    "x-shopbase-session-id": "uAL43C42F00nWVWj41ohW"
}

request_counter = 0

async def fetch(session, product_id, semaphore,counter_lock):
    global request_counter    
    async with semaphore:
        async with counter_lock:
            request_counter += 1
            if request_counter % 1000 == 0:
                print(f"⏳ Sent {request_counter} từ từ đợi 40s để nghỉ đã ....")
                await asyncio.sleep(40)
        params = {
            "product_id": str(product_id),
            "source": "bundle",
            "rules": "best_seller_same_collection,same_collection,same_type,title_similarity,same_tag,lower_price,same_product"
        }
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 429:
                    print(f"⚠️ Rate limit hit for ID {product_id}. Sleeping 30s and retrying...")
                    await asyncio.sleep(60)
                    return await fetch(session, product_id, semaphore, counter_lock)

                if response.content_type != "application/json":
                    print(f"❌ Unexpected content type for ID {product_id}: {response.content_type}")
                    return None
                data = await response.json()
                products = data.get("products", [])
                if isinstance(products, list) and len(products) > 0:
                    print(f"✅ Fetched ID {product_id} with {len(products)} products")
                    return products[0]  # lấy phần tử đầu tiên
                else:
                    print(f"❌ ID {product_id} returned no products.")
                    return None
        except Exception as e:
            print(f"❌ Error fetching ID {product_id}: {e}")
            return None

async def main(start_id, end_id, max_concurrent_requests):
    global request_counter
    counter_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, product_id, semaphore, counter_lock) for product_id in range(start_id, end_id + 1)]
        results = await asyncio.gather(*tasks)

    # Trích xuất dữ liệu từ mỗi first_item
    extracted_data = []
    seen_names = set()
    for first_item in results:
        if first_item:
            name = first_item.get("title", "")
            if name and name not in seen_names:
                seen_names.add(name)
                images = first_item.get("images", [])
                extracted_data.append({
                    "ID": first_item.get("id", ""),
                    "Name": name,
                    "URL Link": f'https://racame.shop/collections/nfl/products/{first_item.get("handle", "")}',
                    "List Link Images": ",".join(img.get("src", "") for img in images),
                    "Type": first_item.get("product_type", "")
                })

    # Xuất dữ liệu ra file Excel
    df = pd.DataFrame(extracted_data)
    excel_output_path = "recame_nfl_v1_0403.xlsx"
    df.to_excel(excel_output_path, index=False, sheet_name="Product Data")

    print(f"\n✅ DONE. Total products saved: {len(df)} rows → {excel_output_path}")

if __name__ == "__main__":
    start_id = 1000000541422000
    end_id =   1000000541442000
    max_concurrent_requests = 2
    asyncio.run(main(start_id, end_id, max_concurrent_requests))
