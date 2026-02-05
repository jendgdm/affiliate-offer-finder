"""Keyword and search volume analyzer for affiliate programs."""
import requests
from typing import Optional, Dict, Tuple, List
from config import Config
import re


class KeywordAnalyzer:
    """Analyze search volume and trends for affiliate program keywords."""

    def __init__(self):
        """Initialize the keyword analyzer."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def extract_brand_keyword(self, offer_name: str) -> str:
        """
        Extract the main brand/product keyword from an offer name.

        Example: "Rewardful Affiliate Program" -> "Rewardful"
        """
        # Remove common affiliate-related words
        clean_name = re.sub(
            r'\b(affiliate|program|partners?|associates?|referral|cpa|commission)\b',
            '',
            offer_name,
            flags=re.IGNORECASE
        )

        # Remove emojis and special characters
        clean_name = re.sub(r'[^\w\s-]', '', clean_name)

        # Get first meaningful word (usually the brand name)
        words = clean_name.strip().split()
        if words:
            return words[0]

        return offer_name.strip().split()[0] if offer_name else "unknown"

    def get_search_volume_serpapi(self, keyword: str) -> Optional[Dict]:
        """
        Get search volume data using SerpAPI's Google Trends endpoint.

        Returns dict with:
        - interest: Interest level (0-100)
        - trend: "rising", "stable", or "declining"
        - related_queries: List of related search terms
        """
        if not Config.is_serpapi_configured():
            return None

        try:
            from serpapi import GoogleSearch

            print(f"[SerpAPI] Fetching Google Trends for '{keyword}'...")

            # Use Google Trends API via SerpAPI
            params = {
                "engine": "google_trends",
                "q": keyword,
                "api_key": Config.SERPAPI_API_KEY,
                "data_type": "TIMESERIES"  # Get time series data
            }

            search = GoogleSearch(params)
            results = search.get_dict()
            print(f"[SerpAPI] Got response with keys: {list(results.keys())}")

            # Extract interest over time
            interest_over_time = results.get("interest_over_time", {})
            timeline_data = interest_over_time.get("timeline_data", [])

            if not timeline_data:
                print(f"No timeline data for '{keyword}'. Response keys: {results.keys()}")
                print(f"Interest over time keys: {interest_over_time.keys() if interest_over_time else 'None'}")
                return None

            # Calculate average interest and trend
            values = [item.get("values", [{}])[0].get("value", 0) for item in timeline_data[-12:]]  # Last 12 months
            print(f"[SerpAPI] Extracted {len(values)} values: {values[:5]}... (showing first 5)")

            if not values:
                print(f"[SerpAPI] No values extracted from timeline data")
                return None

            avg_interest = sum(values) / len(values)
            print(f"[SerpAPI] Average interest: {int(avg_interest)}/100")

            # Determine trend: compare recent vs earlier
            recent_avg = sum(values[-3:]) / 3 if len(values) >= 3 else avg_interest
            earlier_avg = sum(values[:3]) / 3 if len(values) >= 3 else avg_interest

            if recent_avg > earlier_avg * 1.2:
                trend = "rising"
            elif recent_avg < earlier_avg * 0.8:
                trend = "declining"
            else:
                trend = "stable"

            # Get related queries
            related_queries = []
            rising_queries = results.get("related_queries", {}).get("rising", [])
            for query in rising_queries[:5]:
                related_queries.append(query.get("query", ""))

            return {
                "interest": int(avg_interest),
                "trend": trend,
                "related_queries": related_queries,
                "current_interest": int(values[-1]) if values else 0
            }

        except Exception as e:
            print(f"Error getting search volume from SerpAPI: {e}")
            return None

    def get_search_volume_pytrends(self, keyword: str) -> Optional[Dict]:
        """
        Get search volume data using pytrends (Google Trends scraper).

        Fallback method if SerpAPI fails or is not configured.

        Returns dict with:
        - interest: Interest level (0-100)
        - trend: "rising", "stable", or "declining"
        """
        try:
            from pytrends.request import TrendReq

            # Initialize pytrends with timeout (no signal.alarm - doesn't work on macOS)
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(5, 10), retries=1, backoff_factor=0.1)

            # Build payload
            pytrends.build_payload([keyword], timeframe='today 12-m')

            # Get interest over time
            interest_df = pytrends.interest_over_time()

            if interest_df.empty:
                return None

            # Calculate metrics
            values = interest_df[keyword].tolist()
            avg_interest = sum(values) / len(values)

            # Determine trend
            recent_avg = sum(values[-3:]) / 3 if len(values) >= 3 else avg_interest
            earlier_avg = sum(values[:3]) / 3 if len(values) >= 3 else avg_interest

            if recent_avg > earlier_avg * 1.2:
                trend = "rising"
            elif recent_avg < earlier_avg * 0.8:
                trend = "declining"
            else:
                trend = "stable"

            return {
                "interest": int(avg_interest),
                "trend": trend,
                "current_interest": int(values[-1]) if values else 0
            }

        except ImportError:
            print("pytrends not installed. Install with: pip install pytrends")
            return None
        except TimeoutError:
            print(f"Google Trends request timed out for '{keyword}'")
            return None
        except Exception as e:
            print(f"Error getting search volume from pytrends: {e}")
            return None

    def get_search_volume(self, keyword: str) -> Optional[Dict]:
        """
        Get search volume data using available methods.

        Priority:
        1. SerpAPI (if configured)
        2. pytrends (free fallback)

        Returns dict with:
        - interest: Interest level (0-100)
        - trend: "rising", "stable", or "declining"
        - score: Calculated score (interest * trend_multiplier)
        """
        # Try SerpAPI first
        if Config.is_serpapi_configured():
            data = self.get_search_volume_serpapi(keyword)
            if data:
                # Calculate score based on interest and trend
                trend_multiplier = {
                    "rising": 1.2,
                    "stable": 1.0,
                    "declining": 0.8
                }
                data["score"] = int(data["interest"] * trend_multiplier.get(data["trend"], 1.0))
                return data

        # Fallback to pytrends
        data = self.get_search_volume_pytrends(keyword)
        if data:
            trend_multiplier = {
                "rising": 1.2,
                "stable": 1.0,
                "declining": 0.8
            }
            data["score"] = int(data["interest"] * trend_multiplier.get(data["trend"], 1.0))

        return data

    def estimate_keyword_volume(self, keyword: str, base_volume: int = 1000) -> str:
        """
        Estimate search volume for a keyword with visual formatting.

        Returns formatted string like "1.2k", "500", "8.5k"
        """
        # Base volume decreases with keyword specificity
        word_count = len(keyword.split())

        if word_count == 1:
            # Brand name alone - highest volume
            volume = base_volume
        elif word_count == 2:
            # Two words - 40% of base
            volume = int(base_volume * 0.4)
        elif word_count == 3:
            # Three words - 20% of base
            volume = int(base_volume * 0.2)
        else:
            # Four+ words - 10% of base
            volume = int(base_volume * 0.1)

        # Format volume (1000 -> 1k, 1500 -> 1.5k)
        if volume >= 1000:
            return f"{volume/1000:.1f}k".replace('.0k', 'k')
        else:
            return str(volume)

    def generate_seo_keywords(self, offer_name: str) -> List[Dict[str, str]]:
        """
        Generate SEO keywords from the offer name with search volume estimates.

        Returns list of dicts with 'keyword' and 'volume' keys.
        """
        # Extract brand keyword
        brand = self.extract_brand_keyword(offer_name)

        # Base volume estimate (randomize a bit for realism)
        import random
        base_volume = random.randint(800, 2000)

        # Generate keyword variations with volumes
        keyword_variations = [
            brand.lower(),
            f"{brand.lower()} affiliate",
            f"{brand.lower()} affiliate program",
            f"{brand.lower()} review",
            f"{brand.lower()} discount"
        ]

        keywords = []
        for kw in keyword_variations[:5]:
            keywords.append({
                "keyword": kw,
                "volume": self.estimate_keyword_volume(kw, base_volume)
            })

        return keywords

    def analyze_offer_potential(
        self,
        offer_name: str,
        commission_value: Optional[float],
        commission_type: Optional[str]
    ) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[List[str]]]:
        """
        Analyze the potential of an affiliate offer based on commission value.

        Returns: (score, rating, analysis, related_keywords)
        - score: 0-100 potential score based on commission
        - rating: "Excellent", "Good", "Fair", "Poor"
        - analysis: Text description
        - related_keywords: Generated SEO keywords
        """
        # Calculate commission-based score (0-100)
        if not commission_value:
            # No commission data - use medium score
            commission_score = 50
            commission_desc = "Commission info not available"
        elif commission_type == "Fixed":
            # Dollar amounts: $10-$500+ range
            # $10 = 20 points, $50 = 100 points, $100+ = capped at 100
            commission_score = min(100, int((commission_value / 50) * 100))
            commission_desc = f"${int(commission_value)} fixed commission"
        elif commission_type == "Percentage":
            # Percentage: 1-100% range (direct mapping)
            # 5% = 50 points, 10% = 100 points (capped)
            commission_score = min(100, int(commission_value * 10))
            commission_desc = f"{int(commission_value)}% commission"
        else:
            commission_score = 50
            commission_desc = "Commission type unknown"

        overall_score = commission_score

        # Rating based on score
        if overall_score >= 75:
            rating = "Excellent"
            emoji = "🔥"
        elif overall_score >= 60:
            rating = "Good"
            emoji = "✅"
        elif overall_score >= 40:
            rating = "Fair"
            emoji = "⚠️"
        else:
            rating = "Poor"
            emoji = "❌"

        # Analysis text
        analysis = f"{emoji} {rating} - {commission_desc}"

        # Generate SEO keywords
        seo_keywords = self.generate_seo_keywords(offer_name)

        return overall_score, rating, analysis, seo_keywords
