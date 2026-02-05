"""Impact.com API integration."""
import requests
from typing import List, Optional
from networks.base import BaseNetwork
from models.offer import Offer
from config import Config


class ImpactNetwork(BaseNetwork):
    """Impact.com affiliate network integration."""

    BASE_URL = "https://api.impact.com"

    def __init__(self):
        """Initialize Impact API client."""
        super().__init__()
        self.account_sid = Config.IMPACT_ACCOUNT_SID
        self.auth_token = Config.IMPACT_AUTH_TOKEN
        self.session = requests.Session()
        self.session.auth = (self.account_sid, self.auth_token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

    def test_connection(self) -> bool:
        """Test API credentials."""
        try:
            # Try to fetch account info
            response = self.session.get(
                f"{self.BASE_URL}/Mediapartners/{self.account_sid}/Campaigns",
                params={"PageSize": 1}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Impact API connection failed: {e}")
            return False

    def search_offers(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_epc: Optional[float] = None,
        limit: int = 50
    ) -> List[Offer]:
        """
        Search for campaigns/offers on Impact.

        Impact calls them "Campaigns" (not offers).
        """
        try:
            params = {
                "PageSize": limit,
                "CampaignState": "ACTIVE"  # Only active campaigns
            }

            if category:
                params["CampaignCategory"] = category

            response = self.session.get(
                f"{self.BASE_URL}/Mediapartners/{self.account_sid}/Campaigns",
                params=params
            )

            if response.status_code != 200:
                print(f"Impact API error: {response.status_code} - {response.text}")
                return []

            data = response.json()
            campaigns = data.get("Campaigns", [])

            print(f"Impact API: Found {len(campaigns)} campaigns")

            offers = []
            for campaign in campaigns:
                # Filter by keyword if provided
                if keyword:
                    name = campaign.get("CampaignName", "").lower()
                    desc = campaign.get("CampaignDescription", "").lower()
                    if keyword.lower() not in name and keyword.lower() not in desc:
                        continue

                offer = self._parse_campaign_to_offer(campaign)

                # Fetch commission details from contract
                self._add_contract_details(offer, campaign)

                # Filter by min EPC if provided
                if min_epc and (not offer.epc or offer.epc < min_epc):
                    continue

                offer.calculate_youtube_score()
                offers.append(offer)

            # Sort by YouTube score (highest first)
            offers.sort(key=lambda x: x.youtube_score or 0, reverse=True)

            print(f"Impact API: Returning {len(offers)} offers after filtering")

            return offers

        except Exception as e:
            print(f"Error searching Impact offers: {e}")
            return []

    def get_offer_details(self, offer_id: str) -> Optional[Offer]:
        """Get detailed campaign information."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/Mediapartners/{self.account_sid}/Campaigns/{offer_id}"
            )

            if response.status_code != 200:
                return None

            campaign = response.json()
            offer = self._parse_campaign_to_offer(campaign)
            offer.calculate_youtube_score()

            return offer

        except Exception as e:
            print(f"Error fetching Impact campaign {offer_id}: {e}")
            return None

    def _add_contract_details(self, offer: Offer, campaign: dict) -> None:
        """
        Fetch and add contract details (commission info) to an offer.

        Args:
            offer: The offer to enhance with contract data
            campaign: The campaign data containing the contract URI
        """
        try:
            # Get the active contract URI from campaign
            contract_uri = campaign.get("ContractUri")
            if not contract_uri:
                return

            # Fetch contract details
            response = self.session.get(f"{self.BASE_URL}{contract_uri}")

            if response.status_code != 200:
                return

            contract = response.json()

            # Extract event payouts (commission structure)
            terms = contract.get("Terms", {})
            event_payouts = terms.get("EventPayouts", [])

            if event_payouts:
                # Get the first event payout (usually the primary commission)
                first_event = event_payouts[0]

                # Update commission type based on event category
                event_category = first_event.get("EventCategory", "")
                if "SALE" in event_category.upper():
                    offer.commission_type = "CPS"
                elif "LEAD" in event_category.upper():
                    offer.commission_type = "CPL"
                else:
                    offer.commission_type = "CPA"

                # Get default payout rate (percentage) or fixed amount
                default_payout_rate = first_event.get("DefaultPayoutRate")

                if default_payout_rate:
                    # Percentage-based commission
                    offer.commission_value = float(default_payout_rate)

                # Check payout groups for fixed amounts
                payout_groups = first_event.get("PayoutGroups", [])
                if payout_groups and not default_payout_rate:
                    # Get the first payout group's amount
                    first_group = payout_groups[0]
                    payout_amount = first_group.get("Payout")

                    if payout_amount:
                        offer.commission_value = float(payout_amount)

        except Exception as e:
            # Silent fail - just continue without contract data
            print(f"Could not fetch contract for {offer.name}: {e}")

    def _parse_campaign_to_offer(self, campaign: dict) -> Offer:
        """Convert Impact campaign to standardized Offer model."""

        # Extract commission info (Impact can have multiple action types)
        # Note: Basic campaign list doesn't include Actions/Payout
        # We'll need to fetch Contract details for commission info
        commission_type = "CPS"  # Default for most Impact campaigns
        commission_value = None

        # Impact uses "Actions" for commission structure
        actions = campaign.get("Actions", [])
        if actions:
            first_action = actions[0]
            commission_type = first_action.get("Type", "CPA")  # "SALE", "LEAD", etc.

            # Try to get default payout
            payout = first_action.get("Payout")
            if payout:
                commission_value = float(payout.get("Default", {}).get("Amount", 0))

        # Get stats if available
        stats = campaign.get("Stats", {})
        epc = stats.get("EPC")
        conversion_rate = stats.get("ConversionRate")

        # Use correct field names from Impact API
        return Offer(
            id=str(campaign.get("CampaignId", "")),
            name=campaign.get("CampaignName", "Unknown"),
            description=campaign.get("CampaignDescription"),
            network="impact",
            advertiser_name=campaign.get("AdvertiserName", "Unknown"),
            advertiser_id=str(campaign.get("AdvertiserId", "")),
            commission_type=commission_type,
            commission_value=commission_value,
            epc=float(epc) if epc else None,
            conversion_rate=float(conversion_rate) if conversion_rate else None,
            category=campaign.get("Category"),
            tracking_url=campaign.get("TrackingLink"),
            landing_page_url=campaign.get("CampaignUrl"),
            popularity_score=stats.get("PopularityScore") if stats else None
        )
