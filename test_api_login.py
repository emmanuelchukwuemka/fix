import requests
import json

# Test admin login
url = "http://localhost:5000/api/auth/login"
payload = {
    "email": "admin@myfigpoint.com",
    "password": "MyFigPoint2025"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")