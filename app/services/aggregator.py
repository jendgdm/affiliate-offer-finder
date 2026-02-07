"""Aggregate offers from multiple networks."""
from typing import List, Optional
from models.offer import Offer
from networks.impact import ImpactNetwork
from networks.offervault import OfferVaultNetwork
from networks.affbank import AffbankNetwork
from services.keyword_analyzer import KeywordAnalyzer
from services.brand_metrics import BrandMetricsAnalyzer
from services.sheets_cache import SheetsCacheService
from config import Config


class OfferAggregator:
    """Aggregate and rank offers from multiple affiliate networks."""

    def __init__(self):
        """Initialize network clients based on available credentials."""
        self.networks = []
        self.discovery_networks = []
        self.keyword_analyzer = KeywordAnalyzer()
        self.brand_metrics_analyzer = BrandMetricsAnalyzer()

        # Google Sheets cache
        self.sheets_cache = None
        if Config.is_sheets_configured():
            try:
                self.sheets_cache = SheetsCacheService()
                print("Google Sheets cache: Connected")
            except Exception as e:
                print(f"Google Sheets cache: Failed to connect - {e}")

        # Impact.com API (requires credentials)
        if Config.is_impact_configured():
            self.networks.append(ImpactNetwork())

        # Add discovery networks (no credentials needed)
        self.discovery_networks.append(OfferVaultNetwork())  # SerpAPI + Google search
        self.discovery_networks.append(AffbankNetwork())     # Affbank directory scraping

        # TODO: Add CJ, Awin, Partnerstack when implemented

    def get_available_networks(self) -> List[str]:
        """Get list of configured network names."""
        return [network.network_name for network in self.networks]

    def test_all_connections(self) -> dict:
        """Test connections to all configured networks."""
        results = {}
        for network in self.networks:
            results[network.network_name] = network.test_connection()
        return results

    def search_all_networks(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_epc: Optional[float] = None,
        min_commission: Optional[float] = None,
        limit_per_network: int = 50
    ) -> List[Offer]:
        """
        Search across all configured networks and combine results.

        Args:
            keyword: Search term
            category: Filter by category
            min_epc: Minimum EPC filter
            min_commission: Minimum commission value
            limit_per_network: Max results per network

        Returns:
            Combined and ranked list of offers
        """
        all_offers = []

        print(f"Aggregator: Searching {len(self.networks)} networks")

        for network in self.networks:
            try:
                print(f"Aggregator: Searching {network.network_name}...")
                offers = network.search_offers(
                    keyword=keyword,
                    category=category,
                    min_epc=min_epc,
                    limit=limit_per_network
                )
                print(f"Aggregator: Got {len(offers)} offers from {network.network_name}")
                all_offers.extend(offers)
            except Exception as e:
                print(f"Error searching {network.network_name}: {e}")

        # Apply additional filters
        if min_commission:
            all_offers = [
                offer for offer in all_offers
                if offer.commission_value and offer.commission_value >= min_commission
            ]

        # Sort by YouTube score (highest first)
        all_offers.sort(key=lambda x: x.youtube_score or 0, reverse=True)

        print(f"Aggregator: Returning {len(all_offers)} total offers")

        return all_offers

    def analyze_offers_potential(self, offers: List[Offer], analyze_top_n: int = 10) -> List[Offer]:
        """
        Analyze offers with search volume and potential score.

        Args:
            offers: List of offers to analyze
            analyze_top_n: Only analyze top N offers (for speed)

        Returns:
            Offers with added search volume analysis and scalability metrics
        """
        print(f"\nAnalyzing potential of top {analyze_top_n} offers...")

        for idx, offer in enumerate(offers[:analyze_top_n], 1):
            try:
                print(f"  Analyzing #{idx}: {offer.name[:40]}...")

                # Analyze keyword potential and SEO
                score, rating, analysis, related_keywords = self.keyword_analyzer.analyze_offer_potential(
                    offer.name,
                    offer.commission_value,
                    offer.commission_type
                )

                if score is not None:
                    offer.potential_score = score
                    offer.potential_rating = rating
                    offer.potential_analysis = analysis
                    offer.related_keywords = related_keywords

                    print(f"    → Score: {score}/100 ({rating})")
                    if related_keywords:
                        print(f"    → Related keywords: {', '.join([kw['keyword'] for kw in related_keywords[:3]])}")

                # Analyze brand scalability metrics
                scalability_data = self.brand_metrics_analyzer.analyze_brand_scalability(
                    offer.name,
                    offer.commission_value
                )

                offer.scalability_score = scalability_data["scalability_score"]
                offer.cookie_duration = scalability_data["cookie_duration"]
                offer.traffic_monthly = scalability_data["traffic_monthly"]
                offer.growth_percentage = scalability_data["growth_percentage"]
                offer.competition_level = scalability_data["competition_level"]
                offer.domain_authority = scalability_data["domain_authority"]
                offer.instagram_followers = scalability_data["instagram_followers"]

            except Exception as e:
                print(f"  Error analyzing offer {idx}: {e}")
                continue

        return offers

    def search_discovery_networks(
        self,
        keyword: Optional[str] = None,
        limit: int = 20,
        analyze_potential: bool = True,
        force_refresh: bool = False
    ) -> List[Offer]:
        """
        Search discovery networks with Google Sheets daily caching.

        If a Google Sheet cache is configured and today's data exists,
        reads from the sheet instead of calling SERP API.

        Args:
            keyword: Search keyword
            limit: Max results
            analyze_potential: Whether to analyze search volume/potential
            force_refresh: Bypass cache and fetch fresh data from APIs
        """
        effective_keyword = keyword if keyword else "software"

        # Check Google Sheets cache first
        if self.sheets_cache and not force_refresh:
            try:
                if self.sheets_cache.is_cache_fresh(effective_keyword):
                    print(f"Cache HIT: Reading '{effective_keyword}' from Google Sheets")
                    cached_offers = self.sheets_cache.read_offers(effective_keyword)
                    if cached_offers:
                        print(f"Cache: Loaded {len(cached_offers)} offers from sheet")
                        return cached_offers
                    print("Cache: Sheet tab exists but is empty, fetching fresh data")
            except Exception as e:
                print(f"Cache read error: {e}")

        # Cache MISS or force refresh — fetch from APIs
        all_offers = []

        # Search Impact.com API (if configured)
        for network in self.networks:
            try:
                print(f"Discovery: Searching {network.network_name}...")
                offers = network.search_offers(
                    keyword=keyword,
                    limit=limit
                )
                print(f"Discovery: Got {len(offers)} offers from {network.network_name}")
                all_offers.extend(offers)
            except Exception as e:
                print(f"Error searching {network.network_name}: {e}")

        # Search discovery networks (scraping-based)
        print(f"Discovery: Searching {len(self.discovery_networks)} discovery sources")

        for network in self.discovery_networks:
            try:
                print(f"Discovery: Searching {network.network_name}...")
                offers = network.search_offers(
                    keyword=keyword,
                    limit=limit
                )
                print(f"Discovery: Got {len(offers)} offers from {network.network_name}")
                all_offers.extend(offers)
            except Exception as e:
                print(f"Error searching {network.network_name}: {e}")

        # Analyze potential of ALL offers
        if analyze_potential and all_offers:
            all_offers = self.analyze_offers_potential(all_offers, analyze_top_n=len(all_offers))

        # Write results to Google Sheets cache
        if self.sheets_cache and all_offers:
            try:
                self.sheets_cache.write_offers(effective_keyword, all_offers)
                print(f"Cache: Wrote {len(all_offers)} offers to Google Sheet")
            except Exception as e:
                print(f"Cache write error: {e}")

        return all_offers

    def get_top_youtube_offers(
        self,
        keyword: Optional[str] = None,
        min_youtube_score: float = 50.0,
        limit: int = 20
    ) -> List[Offer]:
        """
        Get top offers specifically ranked for YouTube promotion.

        Args:
            keyword: Optional keyword filter
            min_youtube_score: Minimum YouTube suitability score (0-100)
            limit: Max results to return

        Returns:
            Top-ranked offers for YouTube
        """
        offers = self.search_all_networks(keyword=keyword)

        # Filter by YouTube score
        youtube_offers = [
            offer for offer in offers
            if offer.youtube_score and offer.youtube_score >= min_youtube_score
        ]

        return youtube_offers[:limit]
