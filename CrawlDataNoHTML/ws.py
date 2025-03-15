import requests

BASE_URL = "https://ladyjacket.com/wp-json/wc/v3"
ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsImtpZCI6Imdlbi1haV8xNzIyMzY1MDAwIiwidHlwIjoiSldUIn0.eyJhdWQiOiI5YTJmNzliMi1lNDc1LTExZWYtYmY4Zi00ZTAxM2UyZGRkZTQiLCJleHAiOjE3NDE2NzgwMjAsImp0aSI6IjcyMzYwNGFhLWRhODAtNDA2Ni05YmIxLTJiYWY0NmQyZTdhOSIsImlhdCI6MTc0MTY3NzcyMCwiaXNzIjoiZ2VuLWFpLWFwaSIsIm5iZiI6MTc0MTY3NzcyMCwic3ViIjoiMTcxLjIyNC43Mi4yMDEiLCJ0ZWFtX2lkIjoxNDY4MDkxMywibGVhZl9hZ2VudCI6eyJ1dWlkIjoiMDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAwIn0sIm1vZGVsIjp7InV1aWQiOiIwMDAwMDAwMC0wMDAwLTAwMDAtMDAwMC0wMDAwMDAwMDAwMDAifX0.SGVjHqwOn3TAuK26CSArqwTpLhn0PlJosCOTcOOGqI20IozJNHx-jaF_nmAsVGCKXLoJBc-N4CTuiib2DklO8w"

def refresh_access_token():
    url = "https://ladyjacket.com/wp-json/jwt-auth/v1/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6Imdlbi1haV8xNzIyMzY1MDAwIiwidHlwIjoiSldUIn0.eyJhdWQiOiJnZW4tYWktYXBpIiwiZXhwIjoxNzQxNzY0MTIwLCJqdGkiOiJjOGM3Y2RkOC0xNmU0LTRmOWItOWFlNC1lOWFlM2NmMGM3YzgiLCJpYXQiOjE3NDE2Nzc3MjAsImlzcyI6Imdlbi1haS1hcGkiLCJuYmYiOjE3NDE2Nzc3MjAsInN1YiI6IjE3MS4yMjQuNzIuMjAxIn0.sXqE7C_xCE0cFeamCJgOEWyZL1z4w3DGHXfdRVoDoPCi4hQAqh8kZr_i5_MZxHiMe2kX0U-Imu4uZK2VRC5_gQ"
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data["token"]  # Lấy Access Token mới
    else:
        print("❌ Lỗi khi refresh token:", response.text)
        return None

def get_all_products():
    page = 1
    products = []
    
    while True:
        url = f"{BASE_URL}/products?per_page=100&page={page}"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:
            print("Access Token expired! Please refresh the token.")
            break
        
        data = response.json()
        if not data:
            break  # Dừng nếu không còn sản phẩm
        
        products.extend(data)
        page += 1  # Chuyển sang trang tiếp theo

    return products

all_products = get_all_products()
print(f"Tổng số sản phẩm: {len(all_products)}")