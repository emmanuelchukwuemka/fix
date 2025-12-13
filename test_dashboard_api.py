import requests
import json

# Test the dashboard stats API with the token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc2NTY2NzAyNSwianRpIjoiNmFiYTk3OGQtOGU4Yi00YzFhLTgyZWMtZWVlM2MzNzlkYTM4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NjU2NjcwMjUsImV4cCI6MTc2NTY2NzkyNX0.W0-wSJBP0JVlhZHjq-L3qqi4T9D-AEivfuiLCw8DkRE"
url = "http://localhost:5000/api/admin/dashboard/stats"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.json())