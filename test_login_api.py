import requests
import json

# Test the login API directly
url = "http://localhost:5000/api/auth/login"
payload = {
    "email": "admin@myfigpoint.com",
    "password": "MyFigPoint2025"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.json())