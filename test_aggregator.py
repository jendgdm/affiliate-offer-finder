"""Test the aggregator exactly as Streamlit would use it."""
import sys
sys.path.insert(0, '/Users/jen/Digidom/claude_code/TOOL/app')

from services.aggregator import OfferAggregator

print("=" * 50)
print("Testing Aggregator (Streamlit Simulation)")
print("=" * 50)

# Initialize aggregator (same as Streamlit)
aggregator = OfferAggregator()

# Check available networks
networks = aggregator.get_available_networks()
print(f"\nAvailable networks: {networks}")

# Search with no filters (same as Streamlit with default values)
print("\nSearching with no filters (keyword=None, min_epc=None, min_commission=None)...")
offers = aggregator.search_all_networks(
    keyword=None,
    min_epc=None,
    min_commission=None,
    limit_per_network=50
)

print(f"\nTotal offers returned: {len(offers)}")

if offers:
    print("\nFirst 3 offers:")
    for i, offer in enumerate(offers[:3], 1):
        print(f"\n{i}. {offer.name}")
        print(f"   YouTube Score: {offer.youtube_score}")
        print(f"   Commission: ${offer.commission_value} ({offer.commission_type})")
        print(f"   EPC: ${offer.epc if offer.epc else 'N/A'}")
else:
    print("\nNo offers returned!")
