"""Test Impact Campaign Discovery/Marketplace API."""
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

account_sid = os.getenv("IMPACT_ACCOUNT_SID")
auth_token = os.getenv("IMPACT_AUTH_TOKEN")

print("Testing Impact Campaign Discovery")
print("=" * 50)

# Try different discovery endpoints
endpoints = [
    f"/Mediapartners/{account_sid}/CampaignCatalog",
    f"/Mediapartners/{account_sid}/CampaignSearch",
    f"/Mediapartners/{account_sid}/Marketplace",
    f"/Catalog/Campaigns",
]

for endpoint in endpoints:
    print(f"\nTrying: {endpoint}")
    url = f"https://api.impact.com{endpoint}"

    response = requests.get(
        url,
        params={"PageSize": 3},
        auth=(account_sid, auth_token),
        headers={"Accept": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ Success!")
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        break
    elif response.status_code == 404:
        print("❌ Endpoint not found")
    elif response.status_code == 403:
        print("⚠️ Access denied (scope not enabled)")
    else:
        print(f"Error: {response.text[:200]}")
