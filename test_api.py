"""Test Impact API connection and data retrieval."""
import sys
sys.path.insert(0, '/Users/jen/Digidom/claude_code/TOOL/app')

from config import Config
from networks.impact import ImpactNetwork

print("=" * 50)
print("Testing Impact API Connection")
print("=" * 50)

# Check if credentials are loaded
print(f"\nAccount SID: {Config.IMPACT_ACCOUNT_SID[:10]}...")
print(f"Auth Token: {Config.IMPACT_AUTH_TOKEN[:10]}...")
print(f"Impact Configured: {Config.is_impact_configured()}")

# Initialize Impact network
print("\nInitializing Impact Network...")
impact = ImpactNetwork()

# Test connection
print("\nTesting connection...")
connection_ok = impact.test_connection()
print(f"Connection successful: {connection_ok}")

if connection_ok:
    # Try to search for offers
    print("\nSearching for offers (no filters)...")
    offers = impact.search_offers(limit=10)

    print(f"\nFound {len(offers)} offers")

    if offers:
        print("\nFirst 3 offers:")
        for i, offer in enumerate(offers[:3], 1):
            print(f"\n{i}. {offer.name}")
            print(f"   Advertiser: {offer.advertiser_name}")
            print(f"   Commission: ${offer.commission_value} ({offer.commission_type})")
            print(f"   EPC: ${offer.epc if offer.epc else 'N/A'}")
            print(f"   YouTube Score: {offer.youtube_score}")
    else:
        print("\nNo offers returned from API")
else:
    print("\nConnection failed. Check your API credentials.")
