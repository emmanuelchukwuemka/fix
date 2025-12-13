import requests
import json

# Step 1: Login and get the token
login_url = "http://localhost:5000/api/auth/login"
login_payload = {
    "email": "admin@myfigpoint.com",
    "password": "MyFigPoint2025"
}
login_headers = {
    "Content-Type": "application/json"
}

print("Step 1: Logging in...")
login_response = requests.post(login_url, data=json.dumps(login_payload), headers=login_headers)
print("Login Status Code:", login_response.status_code)

if login_response.status_code == 200:
    login_data = login_response.json()
    token = login_data.get('access_token')
    print("Token received:", token[:20] + "..." if token else "None")
    
    # Step 2: Use the token to access the dashboard stats API
    if token:
        dashboard_url = "http://localhost:5000/api/admin/dashboard/stats"
        dashboard_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("\nStep 2: Accessing dashboard stats...")
        dashboard_response = requests.get(dashboard_url, headers=dashboard_headers)
        print("Dashboard Status Code:", dashboard_response.status_code)
        print("Dashboard Response:", dashboard_response.json())
    else:
        print("No token received from login")
else:
    print("Login failed:", login_response.json())