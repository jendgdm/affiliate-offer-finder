"""Impact.com marketplace scraper — discover programs to apply to."""
import requests
import re
import time
from typing import List, Optional
from bs4 import BeautifulSoup
from networks.base import BaseNetwork
from models.offer import Offer


class ImpactMarketplaceNetwork(BaseNetwork):
    """Scrape the affi.io directory for Impact.com affiliate programs."""

    DIRECTORY_URL = "https://affi.io/n/impactradius"

    def __init__(self):
        super().__init__()
        self.network_name = "impact_marketplace"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        })

    def test_connection(self) -> bool:
        try:
            r = self.session.get(self.DIRECTORY_URL, timeout=10)
            return r.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_offers(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_epc: Optional[float] = None,
        limit: int = 50,
    ) -> List[Offer]:
        """Scrape Impact marketplace programs from affi.io directory."""
        all_programs = []
        pages_needed = max(1, (limit + 49) // 50)  # 50 per page
        pages_needed = min(pages_needed, 10)  # cap at 10 pages (500 programs)

        for page in range(1, pages_needed + 1):
            try:
                url = f"{self.DIRECTORY_URL}?page={page}"
                print(f"Impact Marketplace: Scraping page {page}...")
                r = self.session.get(url, timeout=15)
                if r.status_code != 200:
                    break

                programs = self._parse_directory_page(r.text)
                if not programs:
                    break

                all_programs.extend(programs)
                print(f"  Page {page}: {len(programs)} programs (total: {len(all_programs)})")

                if len(all_programs) >= limit:
                    break

                if page < pages_needed:
                    time.sleep(0.5)

            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                break

        # Filter by keyword if provided
        if keyword:
            kw = keyword.lower()
            all_programs = [p for p in all_programs if kw in p["name"].lower()]

        # Convert to Offer objects
        offers = []
        for idx, prog in enumerate(all_programs[:limit], 1):
            offers.append(Offer(
                id=f"impact-mp-{prog['slug']}",
                name=prog["name"],
                description=f"Impact.com affiliate program. Apply at impact.com to promote {prog['name']}.",
                network="impact_marketplace",
                advertiser_name=prog["name"],
                advertiser_id=f"imp-mp-{prog['slug']}",
                commission_type="Varies",
                commission_value=None,
                category="Direct Brand",
                tracking_url=f"https://app.impact.com/campaign-mediapartner-signup/{prog['slug']}.brand",
                landing_page_url=prog.get("website"),
            ))

        print(f"Impact Marketplace: Returning {len(offers)} programs")
        return offers

    def get_offer_details(self, offer_id: str) -> Optional[Offer]:
        return None

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_directory_page(self, html_text: str) -> list:
        """Parse a single page of the affi.io directory table."""
        soup = BeautifulSoup(html_text, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        programs = []
        for row in table.find_all("tr")[1:]:  # skip header
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            # Column 1: name + link
            link = cells[1].find("a")
            if not link:
                continue

            name = link.get_text(strip=True)
            href = link.get("href", "")
            slug = href.replace("/m/", "").strip("/") if "/m/" in href else name.lower().replace(" ", "-")

            # Column 2: country
            country = cells[2].get_text(strip=True)

            # Column 3: status
            status = cells[3].get_text(strip=True)
            if status.lower() != "opened":
                continue  # skip closed/paused

            programs.append({
                "name": name,
                "slug": slug,
                "country": country,
                "status": status,
            })

        return programs
