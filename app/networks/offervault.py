"""OfferVault integration for discovering new affiliate offers."""
import requests
from typing import List, Optional, Tuple
from networks.base import BaseNetwork
from models.offer import Offer
from config import Config
import json
import re
from bs4 import BeautifulSoup
import time
from serpapi import GoogleSearch


class OfferVaultNetwork(BaseNetwork):
    """OfferVault affiliate offer discovery."""

    BASE_URL = "https://offervault.com"

    def __init__(self):
        """Initialize OfferVault scraper."""
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://offervault.com/"
        })

    def test_connection(self) -> bool:
        """Test if OfferVault is accessible."""
        try:
            response = self.session.get(self.BASE_URL, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def _extract_affiliate_details(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Extract commission details from a direct brand affiliate page.

        Returns: (commission_badge, commission_type, commission_value)
        - commission_badge: Short text like "Earn 25%" or "Earn $150"
        - commission_type: "Percentage" or "Fixed"
        - commission_value: Numeric value
        """
        try:
            # Very short timeout for speed
            response = self.session.get(url, timeout=2)
            if response.status_code != 200:
                return None, None, None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Get all text content
            text = soup.get_text(separator=' ', strip=True)

            # Context-aware patterns: Look for commission-specific dollar amounts first
            # These patterns prioritize context like "earn", "commission", "per customer"
            dollar_context_patterns = [
                r'earn\s+\$(\d+)',  # "earn $150"
                r'\$(\d+)\s+(?:per|for|commission)',  # "$150 per customer", "$150 commission"
                r'(?:commission|payout|earn|get paid)\s+(?:of|is)?\s*\$(\d+)',  # "commission of $150"
                r'\$(\d+)\s+(?:per\s+)?(?:sale|customer|referral|signup)',  # "$150 per sale"
            ]

            for pattern in dollar_context_patterns:
                dollar_match = re.search(pattern, text, re.IGNORECASE)
                if dollar_match:
                    dollar_value = float(dollar_match.group(1))
                    if dollar_value >= 10:  # Filter out small amounts
                        badge = f"Earn ${int(dollar_value)}"
                        return badge, "Fixed", dollar_value

            # Context-aware patterns: Look for commission-specific percentages
            pct_context_patterns = [
                r'earn\s+(\d+)%',  # "earn 25%"
                r'(\d+)%\s+commission',  # "25% commission"
                r'commission\s+(?:of|is)?\s*(\d+)%',  # "commission of 25%"
                r'(\d+)%\s+(?:on|per)',  # "25% on sales"
            ]

            for pattern in pct_context_patterns:
                pct_match = re.search(pattern, text, re.IGNORECASE)
                if pct_match:
                    pct_value = float(pct_match.group(1))
                    if 1 <= pct_value <= 100:  # Reasonable commission range
                        badge = f"Earn {int(pct_value)}%"
                        return badge, "Percentage", pct_value

            # Fallback: Look for any dollar amount (if no context-specific patterns found)
            dollar_fallback = re.search(r'\$(\d+)', text)
            if dollar_fallback:
                dollar_value = float(dollar_fallback.group(1))
                if dollar_value >= 10:  # Filter out small amounts
                    badge = f"Earn ${int(dollar_value)}"
                    return badge, "Fixed", dollar_value

            # Fallback: Look for any percentage (last resort)
            pct_fallback = re.search(r'(\d+)%', text)
            if pct_fallback:
                pct_value = float(pct_fallback.group(1))
                if 1 <= pct_value <= 100:  # Reasonable commission range
                    badge = f"Earn {int(pct_value)}%"
                    return badge, "Percentage", pct_value

            return None, None, None

        except Exception as e:
            print(f"Error extracting details from {url}: {e}")
            return None, None, None

    def search_offers(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_epc: Optional[float] = None,
        limit: int = 50
    ) -> List[Offer]:
        """
        Search for affiliate programs using multiple methods.

        Priority:
        1. Direct OfferVault scraping (fastest, most offers)
        2. SerpAPI Google search (high quality, categorized)
        3. Discovery offers (fallback)
        """
        if not keyword:
            keyword = "software"  # Default search term

        try:
            # Method 1: Try direct OfferVault scraping first
            print("Method 1: Trying direct OfferVault scraping...")
            ov_offers = self._scrape_offervault_direct(keyword, limit)

            if ov_offers and len(ov_offers) >= 10:
                print(f"✓ Success! Got {len(ov_offers)} offers from OfferVault directly")
                return ov_offers

            # Method 2: Try SerpAPI for Google search results
            print("Method 2: Trying SerpAPI Google search...")
            serp_offers = self._scrape_affiliate_programs(keyword, limit)

            if serp_offers and len(serp_offers) >= 5:
                print(f"✓ Success! Got {len(serp_offers)} offers from SerpAPI")
                return serp_offers

            # Method 3: Fallback to discovery offers
            print("Method 3: Using discovery offers as fallback")
            return self._create_discovery_offers(keyword, limit)

        except Exception as e:
            print(f"OfferVault search error: {e}")
            return self._create_discovery_offers(keyword, limit)

    def _scrape_offervault_direct(self, keyword: str, limit: int = 50) -> List[Offer]:
        """
        Scrape OfferVault website directly for affiliate offers.

        Args:
            keyword: Search term (e.g., "software", "hosting")
            limit: Maximum number of offers to return

        Returns:
            List of Offer objects from OfferVault
        """
        offers = []

        try:
            # OfferVault search URL format
            search_url = f"{self.BASE_URL}/search/?query={keyword}"

            print(f"Scraping OfferVault directly: {search_url}")

            response = self.session.get(search_url, timeout=10)

            if response.status_code != 200:
                print(f"OfferVault returned status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find offer listings - OfferVault typically uses table rows or card divs
            # We need to inspect their HTML structure
            offer_rows = soup.find_all('tr', class_='offer-row') or \
                        soup.find_all('div', class_='offer-item') or \
                        soup.find_all('div', class_='offer-card')

            print(f"Found {len(offer_rows)} offer listings")

            for idx, row in enumerate(offer_rows[:limit], 1):
                try:
                    # Extract offer details from the row
                    # This will need to be adjusted based on OfferVault's actual HTML structure

                    # Try to find offer name
                    name_elem = row.find('a', class_='offer-name') or \
                               row.find('td', class_='name') or \
                               row.find('h3') or \
                               row.find('a')

                    if not name_elem:
                        continue

                    offer_name = name_elem.get_text(strip=True)
                    offer_url = name_elem.get('href', '')

                    # Make URL absolute if relative
                    if offer_url and not offer_url.startswith('http'):
                        offer_url = f"{self.BASE_URL}{offer_url}"

                    # Extract network
                    network_elem = row.find('td', class_='network') or \
                                  row.find('span', class_='network') or \
                                  row.find(text=re.compile(r'Network:', re.I))

                    network_name = network_elem.get_text(strip=True) if network_elem else "Unknown"
                    network_name = re.sub(r'Network:\s*', '', network_name, flags=re.I)

                    # Extract payout/commission
                    payout_elem = row.find('td', class_='payout') or \
                                 row.find('span', class_='payout') or \
                                 row.find(text=re.compile(r'\$\d+'))

                    commission_type = "CPA"
                    commission_value = None

                    if payout_elem:
                        payout_text = payout_elem.get_text(strip=True) if hasattr(payout_elem, 'get_text') else str(payout_elem)

                        # Extract dollar amount
                        dollar_match = re.search(r'\$(\d+(?:\.\d{2})?)', payout_text)
                        if dollar_match:
                            commission_value = float(dollar_match.group(1))
                            commission_type = "Fixed"
                        else:
                            # Extract percentage
                            pct_match = re.search(r'(\d+)%', payout_text)
                            if pct_match:
                                commission_value = float(pct_match.group(1))
                                commission_type = "Percentage"

                    # Extract category
                    category_elem = row.find('td', class_='category') or \
                                   row.find('span', class_='category')

                    offer_category = category_elem.get_text(strip=True) if category_elem else keyword

                    # Extract description if available
                    desc_elem = row.find('td', class_='description') or \
                               row.find('p', class_='description')

                    description = desc_elem.get_text(strip=True) if desc_elem else \
                                 f"Affiliate offer from {network_name} in the {offer_category} category"

                    offers.append(
                        Offer(
                            id=f"offervault-direct-{idx}",
                            name=offer_name,
                            description=description,
                            network=network_name.lower(),
                            advertiser_name=offer_name.split()[0] if offer_name else "Unknown",
                            advertiser_id=f"ov-{idx}",
                            commission_type=commission_type,
                            commission_value=commission_value,
                            epc=None,
                            tracking_url=offer_url,
                            landing_page_url=offer_url,
                            youtube_score=None,
                            category="Direct Brand"
                        )
                    )

                except Exception as e:
                    print(f"Error parsing offer {idx}: {e}")
                    continue

            print(f"Successfully scraped {len(offers)} offers from OfferVault")

        except Exception as e:
            print(f"Error scraping OfferVault directly: {e}")

        return offers

    def _scrape_affiliate_programs(self, keyword: str, limit: int = 20) -> List[Offer]:
        """
        Use SerpAPI to get real affiliate programs from Google search.

        Searches for '[keyword] affiliate program' and extracts top results.
        """
        offers = []

        # Check if SerpAPI is configured
        if not Config.is_serpapi_configured():
            print("SerpAPI not configured - falling back to discovery offers")
            return []

        # Automatically search for affiliate programs based on keyword
        # User types niche (e.g., "software"), we search for "software affiliate program"
        query = f"{keyword} affiliate program"

        print(f"Discovery: Searching Google for '{query}' via SerpAPI...")

        try:
            # Use pagination to get more results
            # Google returns ~10 results per page, so we need multiple requests
            pages_needed = min(3, (limit + 9) // 10)  # Max 3 pages (30 results) for speed
            all_organic_results = []

            for page in range(pages_needed):
                start_index = page * 10

                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": Config.SERPAPI_API_KEY,
                    "num": 10,  # Google returns max ~10 per request
                    "start": start_index  # Pagination
                }

                search = GoogleSearch(params)
                results = search.get_dict()

                if page == 0:
                    print(f"SerpAPI Response: {results.get('search_metadata', {}).get('status', 'unknown')}")

                organic_results = results.get("organic_results", [])
                all_organic_results.extend(organic_results)

                print(f"Page {page + 1}: Found {len(organic_results)} results (Total: {len(all_organic_results)})")

                # Stop if no more results
                if len(organic_results) == 0:
                    break

                # Stop if we have enough
                if len(all_organic_results) >= limit * 2:
                    break

                # Rate limit - small delay between requests
                if page < pages_needed - 1:
                    time.sleep(0.5)

            organic_results = all_organic_results
            print(f"SerpAPI Total: Found {len(organic_results)} organic results across {page + 1} pages")

            direct_brand_count = 0  # Track how many direct brands we've processed
            max_extractions = 5  # Only extract details for first 5 direct brands (for speed)

            for idx, result in enumerate(organic_results, 1):
                try:
                    title = result.get("title", "")
                    url = result.get("link", "")
                    snippet = result.get("snippet", "")

                    if not url or not title:
                        continue

                    # Extract domain for display
                    domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
                    domain_name = domain.group(1) if domain else url

                    # Skip only aggregator sites (not blogs)
                    skip_domains = ['offervault', 'affbank', 'odigger', 'reddit.com', 'quora.com']
                    if any(skip in domain_name.lower() for skip in skip_domains):
                        print(f"Skipping aggregator: {domain_name}")
                        continue

                    # Identify blog posts vs direct brands
                    # Direct Brand = Company's own affiliate program page (e.g., lego.com/affiliate-program)
                    # Blog Post = Third-party listing multiple programs

                    url_lower = url.lower()

                    # Check if this is a direct brand affiliate page
                    # Look for /affiliate, /partner, /associates in the URL path
                    is_direct_brand_page = bool(re.search(r'/(affiliate|partner|associates|referral)', url_lower))

                    # Known blog/review domains
                    blog_domains = [
                        'medium.com', 'blogger.com', 'wordpress.com', 'blogspot.com',
                        'forbes.com', 'entrepreneur.com', 'inc.com', 'techcrunch.com',
                        'venturebeat.com', 'mashable.com', 'cnet.com', 'zdnet.com',
                        'influencermarketinghub.com', 'affiliatebay.net', 'smartpassiveincome.com',
                        'neilpatel.com', 'hubspot.com', 'moz.com', 'searchenginejournal.com',
                        'investopedia.com', 'pcmag.com', 'tomsguide.com', 'wired.com',
                        'themeisle.com', 'wpbeginner.com', 'authorityhacker.com'
                    ]
                    is_blog_domain = any(blog_domain in domain_name.lower() for blog_domain in blog_domains)

                    # Check title for blog post patterns (listicles, comparisons, reviews)
                    title_lower = title.lower()
                    blog_title_patterns = [
                        'best', 'top ', 'list of', 'review', 'comparison', 'vs ',
                        'how to', 'guide', 'ultimate', 'complete', 'beginner',
                        ' programs', ' networks', ' sites', 'revealed'
                    ]

                    # Check for numbered lists (e.g., "15 Best", "Top 10")
                    has_number_pattern = bool(re.search(r'\d+\s+(best|top|great|affiliate)', title_lower))

                    # Check for "X best/top Y" patterns
                    has_listicle_pattern = any(pattern in title_lower for pattern in blog_title_patterns)

                    # Determine category:
                    # - If URL has /affiliate or /partner path AND not a known blog domain → Direct Brand
                    # - If known blog domain OR has listicle patterns → Blog Post
                    if is_direct_brand_page and not is_blog_domain:
                        is_blog_post = False
                    else:
                        is_blog_post = is_blog_domain or has_number_pattern or has_listicle_pattern

                    # Determine category and emoji
                    if is_blog_post:
                        category = "Blog Post"
                        emoji = "📰"
                        description = (
                            f"Blog post listing multiple affiliate programs: {domain_name}\n\n"
                            f"{snippet[:150]}..."
                        )
                    else:
                        category = "Direct Brand"
                        emoji = "🎯"

                        # For Direct Brand, try to extract commission details (but limit to first 10)
                        commission_badge = None
                        commission_type = "Varies"
                        commission_value = None

                        if direct_brand_count < max_extractions:
                            print(f"Extracting details from {domain_name}...")
                            commission_badge, comm_type, comm_value = self._extract_affiliate_details(url)
                            direct_brand_count += 1

                            if commission_badge:
                                commission_type = comm_type
                                commission_value = comm_value
                        else:
                            print(f"Skipping extraction for {domain_name} (limit reached)")

                        # Simple description
                        description = (
                            f"Direct affiliate program from: {domain_name}\n\n"
                            f"{snippet[:150]}..."
                        )

                    offers.append(
                        Offer(
                            id=f"serp-{keyword.lower().replace(' ', '-')}-{idx}",
                            name=f"{emoji} {title[:60]}",
                            description=description,
                            network="discovery",
                            advertiser_name=domain_name,
                            advertiser_id=f"serp-{idx}",
                            commission_type=commission_type if category == "Direct Brand" else "Varies",
                            commission_value=commission_value if category == "Direct Brand" else None,
                            epc=None,
                            tracking_url=url,
                            landing_page_url=url,
                            youtube_score=None,
                            category=category
                        )
                    )

                    if len(offers) >= limit:
                        break

                except Exception as e:
                    print(f"Error parsing result {idx}: {e}")
                    continue

        except Exception as e:
            print(f"Error using SerpAPI: {e}")

        print(f"Discovery: Found {len(offers)} affiliate programs from SerpAPI")
        return offers

    def _create_discovery_offers(self, keyword: str, limit: int = 5) -> List[Offer]:
        """
        Create discovery offers that direct to OfferVault search.

        Since OfferVault requires JavaScript rendering, we provide
        direct links to their search results.
        """
        # Create varied search terms based on the keyword
        if keyword:
            search_variations = [
                (f"All {keyword.title()} Offers", keyword),
                (f"Top {keyword.title()} Programs", keyword),
                (f"High Paying {keyword.title()}", keyword),
                (f"{keyword.title()} CPA Offers", keyword),
                (f"{keyword.title()} Recurring", keyword),
                (f"Best {keyword.title()} Networks", keyword),
                (f"{keyword.title()} Affiliate Programs", keyword),
                (f"New {keyword.title()} Offers", keyword),
            ]
        else:
            # If no keyword, show popular categories
            search_variations = [
                ("Top CPA Offers", "cpa"),
                ("Software & SaaS", "software"),
                ("Health & Wellness", "health"),
                ("Finance & Crypto", "finance"),
                ("Ecommerce Products", "ecommerce"),
                ("Education & Courses", "education"),
                ("Gaming & Entertainment", "gaming"),
                ("VPN & Security", "vpn"),
            ]

        offers = []
        # Create up to 'limit' offers
        for idx, (title, search_term) in enumerate(search_variations[:max(limit, 10)], 1):
            category_url = f"{self.BASE_URL}/?selectedTab=topOffers&search={search_term}&page=1"

            offers.append(
                Offer(
                    id=f"offervault-{search_term.lower().replace(' ', '-')}-{idx}",
                    name=f"🔍 {title}",
                    description=(
                        f"Browse {search_term} offers on OfferVault from 100+ affiliate networks including "
                        f"MaxBounty, ClickBank, CJ, ShareASale, Awin, and more. Click to explore."
                    ),
                    network="offervault",
                    advertiser_name="Discovery",
                    advertiser_id=f"discovery-{idx}",
                    commission_type="Varies",
                    commission_value=None,
                    epc=None,
                    tracking_url=category_url,
                    landing_page_url=category_url,
                    youtube_score=None,
                    category="Blog Post"  # OfferVault shows multiple programs
                )
            )

        return offers

    def _parse_api_response(self, data: dict, keyword: str) -> List[Offer]:
        """Parse OfferVault API response if available."""
        offers = []

        # Try to parse if API returns offer data
        if isinstance(data, dict) and "offers" in data:
            for offer_data in data.get("offers", [])[:20]:
                offers.append(
                    Offer(
                        id=str(offer_data.get("id", "")),
                        name=offer_data.get("name", "Unknown Offer"),
                        description=offer_data.get("description", ""),
                        network="offervault",
                        advertiser_name=offer_data.get("advertiser", "Unknown"),
                        advertiser_id=str(offer_data.get("advertiser_id", "")),
                        commission_type=offer_data.get("payout_type", "CPA"),
                        commission_value=float(offer_data.get("payout", 0)) if offer_data.get("payout") else None,
                        epc=float(offer_data.get("epc", 0)) if offer_data.get("epc") else None,
                        tracking_url=offer_data.get("url", ""),
                        landing_page_url=offer_data.get("url", ""),
                        youtube_score=None
                    )
                )

        # If no offers parsed, fallback to discovery offers
        if not offers:
            return self._create_discovery_offers(keyword)

        return offers

    def get_offer_details(self, offer_id: str) -> Optional[Offer]:
        """Get offer details."""
        return None
