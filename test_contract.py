"""Test fetching contract details from Impact API."""
import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

account_sid = os.getenv("IMPACT_ACCOUNT_SID")
auth_token = os.getenv("IMPACT_AUTH_TOKEN")

print("Testing Impact Contract API")
print("=" * 50)

# First, get a campaign
url = f"https://api.impact.com/Mediapartners/{account_sid}/Campaigns"
params = {"PageSize": 1, "CampaignState": "ACTIVE"}

response = requests.get(
    url,
    params=params,
    auth=(account_sid, auth_token),
    headers={"Accept": "application/json", "Content-Type": "application/json"}
)

if response.status_code == 200:
    data = response.json()
    campaigns = data.get("Campaigns", [])

    if campaigns:
        campaign = campaigns[0]
        print(f"\nCampaign: {campaign.get('CampaignName')}")
        print(f"Contract URI: {campaign.get('ContractUri')}")

        # Fetch contract details
        contract_uri = campaign.get("ContractUri")
        if contract_uri:
            print(f"\nFetching contract from: https://api.impact.com{contract_uri}")

            contract_response = requests.get(
                f"https://api.impact.com{contract_uri}",
                auth=(account_sid, auth_token),
                headers={"Accept": "application/json"}
            )

            print(f"Status Code: {contract_response.status_code}")

            if contract_response.status_code == 200:
                contract = contract_response.json()
                print("\nContract Data:")
                print(json.dumps(contract, indent=2))
            else:
                print(f"Error: {contract_response.text}")
else:
    print(f"Error fetching campaigns: {response.status_code}")
    print(response.text)
