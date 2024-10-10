import requests 

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2VtYWlsIjoiZWF3YWQ5MzI5QGdtYWlsLmNvbSIsImV4cCI6MTcyODMyMDQzNH0.ZOakpc8QQJyoj6z2vLtCjd-U3bS5BkUumJCHN9NDoVA"

headers = {
    'Authorization': f'Bearer {token}'
}

response = requests.get("http://localhost:8000/posts/get-user-posts",
              headers=headers)

if response.status_code == 200:
    print(response.json())
