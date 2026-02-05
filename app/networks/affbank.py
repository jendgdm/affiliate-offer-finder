"""Affbank integration for discovering affiliate offers."""
import requests
from typing import List, Optional
from networks.base import BaseNetwork
from models.offer import Offer
import re
from bs4 import BeautifulSoup


class AffbankNetwork(BaseNetwork):
    """Affbank affiliate offer directory scraper."""

    BASE_URL = "https://affbank.com"

    def __init__(self):
        """Initialize Affbank scraper."""
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def test_connection(self) -> bool:
        """Test if Affbank is accessible."""
        try:
            response = self.session.get(f"{self.BASE_URL}/offers/", timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def search_offers(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_epc: Optional[float] = None,
        limit: int = 50
    ) -> List[Offer]:
        """
        Search for affiliate offers on Affbank.

        Args:
            keyword: Search term (optional - will browse all if not provided)
            category: Category filter (not used for now)
            min_epc: Minimum EPC filter (not used for now)
            limit: Maximum number of offers to return

        Returns:
            List of Offer objects from Affbank
        """
        offers = []

        try:
            # Affbank browse URL - can add search later
            # For now, we'll scrape their offers page
            if keyword:
                # Try search URL format
                url = f"{self.BASE_URL}/offers/?search={keyword}"
            else:
                url = f"{self.BASE_URL}/offers/"

            print(f"Scraping Affbank: {url}")

            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                print(f"Affbank returned status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the main offers table
            table = soup.find('table')

            if not table:
                print("No table found on Affbank")
                return []

            # Get all offer rows (skip header row)
            rows = table.find_all('tr')[1:]  # Skip header

            print(f"Found {len(rows)} offers on Affbank")

            for idx, row in enumerate(rows[:limit], 1):
                try:
                    cells = row.find_all(['td', 'th'])

                    if len(cells) < 4:
                        continue

                    # Cell 0: Offer name
                    name_cell = cells[0]
                    name_link = name_cell.find('a')

                    if not name_link:
                        continue

                    offer_name = name_link.get_text(strip=True)
                    offer_path = name_link.get('href', '')
                    offer_url = f"{self.BASE_URL}{offer_path}" if offer_path.startswith('/') else offer_path

                    # Extract category from name (e.g., "PIN-UP Casino - EC CPA")
                    # Clean up category tags like "Sponsored", "Gambling & betting"
                    clean_name = re.sub(r'(Sponsored|Gambling & betting|Dating|Finance|Sweepstakes)', '', offer_name)
                    clean_name = re.sub(r'\s+', ' ', clean_name).strip()

                    # Cell 1: Network
                    network_cell = cells[1]
                    network_link = network_cell.find('a')
                    network_name = network_link.get_text(strip=True) if network_link else "Unknown"

                    # Cell 2: Country
                    country = cells[2].get_text(strip=True) if len(cells) > 2 else ""

                    # Cell 3: Payout
                    payout_text = cells[3].get_text(strip=True) if len(cells) > 3 else ""

                    # Parse payout
                    commission_type = "CPA"
                    commission_value = None

                    # Check for dollar amount
                    dollar_match = re.search(r'\$(\d+(?:\.\d{2})?)', payout_text)
                    if dollar_match:
                        commission_value = float(dollar_match.group(1))
                        commission_type = "Fixed"
                    else:
                        # Check for percentage
                        pct_match = re.search(r'(\d+)%', payout_text)
                        if pct_match:
                            commission_value = float(pct_match.group(1))
                            commission_type = "Percentage"

                    # Build description
                    description = f"Affiliate offer from {network_name}"
                    if country:
                        description += f" (Country: {country})"
                    if commission_value:
                        if commission_type == "Fixed":
                            description += f" - Earn ${int(commission_value)}"
                        else:
                            description += f" - Earn {int(commission_value)}%"

                    # Filter by keyword if provided
                    if keyword:
                        keyword_lower = keyword.lower()
                        searchable_text = f"{offer_name} {network_name}".lower()
                        if keyword_lower not in searchable_text:
                            continue

                    offers.append(
                        Offer(
                            id=f"affbank-{idx}",
                            name=clean_name,
                            description=description,
                            network=network_name.lower(),
                            advertiser_name=clean_name.split()[0] if clean_name else "Unknown",
                            advertiser_id=f"affbank-{idx}",
                            commission_type=commission_type,
                            commission_value=commission_value,
                            epc=None,
                            tracking_url=offer_url,
                            landing_page_url=offer_url,
                            youtube_score=None,
                            category="Direct Brand"  # Affbank listings are direct offers
                        )
                    )

                except Exception as e:
                    print(f"Error parsing Affbank offer {idx}: {e}")
                    continue

            print(f"Successfully scraped {len(offers)} offers from Affbank")

        except Exception as e:
            print(f"Error scraping Affbank: {e}")

        return offers

    def get_offer_details(self, offer_id: str) -> Optional[Offer]:
        """Get offer details (not implemented)."""
        return None
