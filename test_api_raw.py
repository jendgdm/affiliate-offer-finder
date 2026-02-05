"""Test Impact API raw response."""
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

account_sid = os.getenv("IMPACT_ACCOUNT_SID")
auth_token = os.getenv("IMPACT_AUTH_TOKEN")

print("Testing Impact API - Raw Response")
print("=" * 50)

# Make direct API call
url = f"https://api.impact.com/Mediapartners/{account_sid}/Campaigns"
params = {
    "PageSize": 3,
    "CampaignState": "ACTIVE"
}

response = requests.get(
    url,
    params=params,
    auth=(account_sid, auth_token),
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
)

print(f"\nStatus Code: {response.status_code}")
print(f"\nResponse Headers:")
print(json.dumps(dict(response.headers), indent=2))

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse Keys: {data.keys()}")

    if "Campaigns" in data:
        print(f"\nNumber of Campaigns: {len(data['Campaigns'])}")

        if data["Campaigns"]:
            print("\n" + "=" * 50)
            print("First Campaign (full data):")
            print("=" * 50)
            print(json.dumps(data["Campaigns"][0], indent=2))
    else:
        print("\nNo 'Campaigns' key in response")
        print(json.dumps(data, indent=2))
else:
    print(f"\nError: {response.text}")
